"""
Vector Store Service (Qdrant Integration via ds-api)
벡터 저장소 서비스 - ds-api를 통한 Qdrant 연동
"""
from qdrant_client import QdrantClient
from typing import List, Dict, Optional
import httpx
import logging

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Qdrant 벡터 저장소 서비스 (ds-api 통합)"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        api_key: str = None,
        ds_api_url: str = "http://localhost:8085"
    ):
        """
        초기화

        Args:
            host: Qdrant 호스트
            port: Qdrant 포트
            api_key: Qdrant API 키
            ds_api_url: ds-api 서버 URL
        """
        self.ds_api_url = ds_api_url
        self.host = host
        self.port = port

        try:
            self.client = QdrantClient(
                host=host,
                port=port,
                api_key=api_key,
                https=False,  # HTTP만 사용
                prefer_grpc=False  # REST API 사용
            )
            logger.info(f"Qdrant client initialized: {host}:{port}")
        except Exception as e:
            logger.warning(f"Failed to initialize Qdrant client: {e}")
            self.client = None

    async def health_check(self) -> bool:
        """
        Qdrant 서버 연결 확인

        Returns:
            bool: 연결 성공 시 True
        """
        if not self.client:
            return False

        try:
            # 컬렉션 목록 조회로 연결 확인
            collections = self.client.get_collections()
            logger.info(f"Qdrant health check successful: {len(collections.collections)} collections")
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.0
    ) -> List[Dict]:
        """
        벡터 검색

        Args:
            collection_name: 컬렉션 이름
            query_vector: 검색 벡터
            limit: 결과 개수
            score_threshold: 최소 스코어

        Returns:
            List[Dict]: 검색 결과
        """
        if not self.client:
            logger.error("Qdrant client not initialized")
            return []

        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold
            )

            # 결과를 딕셔너리 형태로 변환
            search_results = []
            for result in results:
                search_results.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload if result.payload else {}
                })

            logger.info(f"Found {len(search_results)} results in {collection_name}")
            return search_results

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    async def get_collection_info(self, collection_name: str) -> Optional[Dict]:
        """
        컬렉션 정보 조회

        Args:
            collection_name: 컬렉션 이름

        Returns:
            Optional[Dict]: 컬렉션 정보
        """
        if not self.client:
            return None

        try:
            collection_info = self.client.get_collection(collection_name=collection_name)

            return {
                "name": collection_name,
                "vectors_count": collection_info.vectors_count,
                "points_count": collection_info.points_count,
                "status": collection_info.status
            }

        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return None

    async def retrieve_by_ids(
        self,
        collection_name: str,
        ids: List[str]
    ) -> List[Dict]:
        """
        ID로 문서 조회

        Args:
            collection_name: 컬렉션 이름
            ids: 문서 ID 리스트

        Returns:
            List[Dict]: 문서 정보
        """
        if not self.client:
            return []

        try:
            results = self.client.retrieve(
                collection_name=collection_name,
                ids=ids,
                with_payload=True,
                with_vectors=False
            )

            documents = []
            for result in results:
                documents.append({
                    "id": result.id,
                    "payload": result.payload if result.payload else {}
                })

            return documents

        except Exception as e:
            logger.error(f"Failed to retrieve documents: {e}")
            return []

    async def get_document_from_ds_api(self, document_id: str) -> Optional[Dict]:
        """
        ds-api를 통해 Qdrant에서 문서 정보 조회

        Args:
            document_id: 문서 ID (hash)

        Returns:
            Optional[Dict]: 문서 정보
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ds_api_url}/document/info/{document_id}",
                    timeout=10.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Document not found in ds-api: {document_id}")
                    return None

        except Exception as e:
            logger.error(f"Failed to get document from ds-api: {e}")
            return None

    async def download_from_ds_api(self, document_id: str) -> Optional[bytes]:
        """
        ds-api를 통해 MinIO에서 파일 다운로드

        Args:
            document_id: 문서 ID (hash)

        Returns:
            Optional[bytes]: 파일 데이터
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ds_api_url}/download/{document_id}",
                    timeout=30.0
                )

                if response.status_code == 200:
                    return response.content
                else:
                    logger.warning(f"Failed to download from ds-api: {document_id}")
                    return None

        except Exception as e:
            logger.error(f"Failed to download from ds-api: {e}")
            return None

    async def upsert_points(
        self,
        collection_name: str,
        points: List[Dict]
    ) -> bool:
        """
        Qdrant에 벡터 포인트 추가/업데이트

        Args:
            collection_name: 컬렉션 이름
            points: 포인트 리스트 [{"id": str, "vector": List[float], "payload": dict}]

        Returns:
            bool: 성공 시 True
        """
        if not self.client:
            logger.error("Qdrant client not initialized")
            return False

        try:
            from qdrant_client.models import PointStruct

            # PointStruct 객체로 변환
            qdrant_points = []
            for point in points:
                qdrant_points.append(
                    PointStruct(
                        id=point["id"],
                        vector=point["vector"],
                        payload=point.get("payload", {})
                    )
                )

            # Qdrant에 업로드
            self.client.upsert(
                collection_name=collection_name,
                points=qdrant_points
            )

            logger.info(f"Upserted {len(qdrant_points)} points to {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to upsert points: {e}")
            return False

    async def delete_by_document_id(
        self,
        collection_name: str,
        document_id: str
    ) -> bool:
        """
        문서 ID로 모든 청크 삭제

        Args:
            collection_name: 컬렉션 이름
            document_id: 문서 ID

        Returns:
            bool: 성공 시 True
        """
        if not self.client:
            logger.error("Qdrant client not initialized")
            return False

        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            # document_id로 필터링하여 삭제
            self.client.delete(
                collection_name=collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                )
            )

            logger.info(f"Deleted points with document_id={document_id} from {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete points: {e}")
            return False

    async def get_unique_documents(
        self,
        collection_name: str,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Dict], int]:
        """
        Qdrant에서 유니크한 문서 목록 조회 (file_id 기준)

        Args:
            collection_name: 컬렉션 이름
            skip: 스킵할 문서 수
            limit: 가져올 문서 수

        Returns:
            tuple[List[Dict], int]: (문서 목록, 전체 문서 수)
        """
        if not self.client:
            logger.error("Qdrant client not initialized")
            return [], 0

        try:
            # 모든 포인트를 스크롤하면서 유니크한 file_id 수집
            documents_dict = {}
            offset = None
            batch_size = 100
            total_points_processed = 0

            while True:
                # Qdrant scroll API로 배치 가져오기
                result = self.client.scroll(
                    collection_name=collection_name,
                    limit=batch_size,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )

                points, next_offset = result

                if not points:
                    break

                total_points_processed += len(points)

                # file_id 기준으로 유니크한 문서만 저장
                for point in points:
                    payload = point.payload or {}
                    metadata = payload.get("metadata", {})

                    file_id = metadata.get("file_id")
                    if not file_id:
                        continue

                    # 이미 처리한 문서면 스킵
                    if file_id in documents_dict:
                        continue

                    # 문서 정보 저장
                    file_path = metadata.get("file_path", [])
                    title = file_path[0] if file_path else "제목 없음"

                    documents_dict[file_id] = {
                        "id": file_id,
                        "title": title,
                        "file_path": file_path,
                        "metadata_uri": metadata.get("metadata_uri", ""),
                        "doctype": metadata.get("doctype", ""),
                        "token_count": metadata.get("token_count", 0),
                        "migrated": metadata.get("migrated", False)
                    }

                # 다음 오프셋이 없으면 종료
                if next_offset is None:
                    break

                offset = next_offset

                # 충분한 문서를 수집했으면 조기 종료 (성능 최적화)
                if len(documents_dict) >= skip + limit + 1000:
                    break

            # 문서 목록을 리스트로 변환
            all_documents = list(documents_dict.values())
            total_count = len(all_documents)

            # 페이징 적용
            paginated_documents = all_documents[skip:skip + limit]

            logger.info(
                f"Found {total_count} unique documents in {collection_name} "
                f"(processed {total_points_processed} points)"
            )

            return paginated_documents, total_count

        except Exception as e:
            logger.error(f"Failed to get unique documents: {e}")
            return [], 0

    def close(self):
        """연결 종료"""
        if self.client:
            self.client.close()
            logger.info("Qdrant client closed")
