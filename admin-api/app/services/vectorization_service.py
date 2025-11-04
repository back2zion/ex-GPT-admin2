"""
Vectorization Service for Document Processing
학습데이터 관리 - 문서 벡터화 서비스 (vLLM 임베딩 API 사용)
"""
import httpx
from typing import List, Optional, Dict, Any
from app.core.config import settings
from app.models.document_vector import DocumentVector, VectorStatus
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import uuid


class VectorizationService:
    """문서 벡터화 서비스 - vLLM 임베딩 사용"""

    def __init__(self, collection_name: str = None):
        self.qdrant_url = f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
        # Use collection_name parameter for flexibility
        # Default to admin collection, but can be overridden for session files
        self.collection = collection_name or "130825-512-v3"  # Match ex-gpt-api
        self.api_key = settings.QDRANT_API_KEY
        # vLLM 임베딩 엔드포인트 (direct container access via exgpt_net network)
        self.embedding_endpoint = "http://vllm-embeddings:8000/v1/embeddings"
        self.embedding_model = "default-model"  # Qwen3-Embedding-0.6B

    async def chunk_text(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[str]:
        """
        텍스트를 청크로 분할
        Secure: 크기 제한
        """
        if not text:
            return []

        # Security: Limit total text size
        max_text_size = 10_000_000  # 10MB
        if len(text) > max_text_size:
            text = text[:max_text_size]

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap

        return chunks

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        텍스트 임베딩 생성 (vLLM 사용)
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.embedding_endpoint,
                    json={
                        "input": texts,
                        "model": self.embedding_model
                    }
                )
                response.raise_for_status()
                data = response.json()
                return [item["embedding"] for item in data["data"]]
        except Exception as e:
            print(f"Embedding error: {e}")
            raise ValueError(f"임베딩 생성 실패: {e}")

    async def store_vectors_in_qdrant(
        self,
        document_id: int,
        chunks: List[str],
        embeddings: List[List[float]],
        metadata: dict
    ) -> List[str]:
        """
        Qdrant에 벡터 저장
        Returns: List of point IDs
        """
        point_ids = []
        print(f"[VECTORIZATION] Starting Qdrant storage for document {document_id}, {len(chunks)} chunks")
        print(f"[VECTORIZATION] Qdrant URL: {self.qdrant_url}, Collection: {self.collection}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    point_id = str(uuid.uuid4())

                    # Prepare payload
                    payload = {
                        "document_id": document_id,
                        "chunk_index": idx,
                        "chunk_text": chunk[:1000],  # Limit for payload
                        "metadata": metadata
                    }

                    # Store in Qdrant
                    headers = {}
                    if self.api_key:
                        headers["api-key"] = self.api_key

                    print(f"[VECTORIZATION] Storing chunk {idx} with point_id {point_id}")
                    response = await client.put(
                        f"{self.qdrant_url}/collections/{self.collection}/points",
                        json={
                            "points": [{
                                "id": point_id,
                                "vector": {
                                    "default-model": embedding
                                },
                                "payload": payload
                            }]
                        },
                        headers=headers
                    )
                    print(f"[VECTORIZATION] Qdrant response status: {response.status_code}")
                    print(f"[VECTORIZATION] Qdrant response: {response.text[:200]}")
                    response.raise_for_status()
                    point_ids.append(point_id)

            print(f"[VECTORIZATION] Successfully stored {len(point_ids)} vectors in Qdrant")
            return point_ids

        except Exception as e:
            print(f"[VECTORIZATION ERROR] Qdrant storage error: {e}")
            raise ValueError(f"벡터 저장 실패: {e}")

    async def vectorize_document(
        self,
        document_id: int,
        text: str,
        db: AsyncSession,
        metadata: Optional[dict] = None
    ):
        """
        문서 벡터화 전체 프로세스 (vLLM 임베딩 사용)
        """
        if metadata is None:
            metadata = {}

        try:
            # 1. 텍스트 청크 분할
            chunks = await self.chunk_text(text)
            if not chunks:
                return

            # 2. 임베딩 생성 (배치 처리)
            batch_size = 10
            all_embeddings = []

            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                embeddings = await self.get_embeddings(batch)
                all_embeddings.extend(embeddings)

            # 3. Qdrant에 저장
            point_ids = await self.store_vectors_in_qdrant(
                document_id,
                chunks,
                all_embeddings,
                metadata
            )

            # 4. 메타데이터 DB에 저장 (Admin 문서만 - Personal 파일은 Qdrant만 사용)
            # Personal files (session_collection-v2) don't need document_vectors table
            # because they don't exist in the documents table (FK constraint issue)
            if self.collection != "session_collection-v2":
                for idx, (chunk, point_id) in enumerate(zip(chunks, point_ids)):
                    vector_record = DocumentVector(
                        document_id=document_id,
                        qdrant_point_id=point_id,
                        qdrant_collection=self.collection,
                        chunk_index=idx,
                        chunk_text=chunk[:10000],  # Truncate if too long
                        chunk_metadata=metadata,
                        vector_dimension=len(all_embeddings[0]) if all_embeddings else None,
                        embedding_model=self.embedding_model,
                        status=VectorStatus.COMPLETED
                    )
                    db.add(vector_record)

                await db.commit()
            else:
                # Personal files: Qdrant storage only, no DB metadata
                print(f"[VECTORIZATION] Personal file - skipping document_vectors table (Qdrant only)")

        except Exception as e:
            # Mark as failed
            print(f"Vectorization failed for document {document_id}: {e}")

            # Create failed record (Admin 문서만 - Personal 파일은 생략)
            if self.collection != "session_collection-v2":
                failed_record = DocumentVector(
                    document_id=document_id,
                    qdrant_point_id="",
                    qdrant_collection=self.collection,
                    chunk_index=0,
                    status=VectorStatus.FAILED,
                    error_message=str(e)[:1000]
                )
                db.add(failed_record)
                await db.commit()
            else:
                # Personal files: Just log error, no DB save
                print(f"[VECTORIZATION ERROR] Personal file vectorization failed: {e}")

            raise


# Singleton instance
vectorization_service = VectorizationService()
