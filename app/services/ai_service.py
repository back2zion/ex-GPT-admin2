"""
AI Service
AI 모델 연동 (vLLM + RAG)
"""
from typing import AsyncGenerator, List, Dict, Any, Optional
import httpx
import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """
    AI 서비스 (vLLM + Qdrant RAG)

    Features:
        - vLLM OpenAI-compatible API 통합
        - Qdrant 벡터 검색 (RAG)
        - SSE 스트리밍 응답
        - 추론 모드 지원 (DeepSeek-R1 등)
    """

    def __init__(self):
        """
        초기화

        Environment Variables:
            - VLLM_API_URL: vLLM 서버 주소
            - VLLM_MODEL_NAME: 모델 이름
            - QDRANT_HOST: Qdrant 호스트
            - QDRANT_PORT: Qdrant 포트
            - QDRANT_API_KEY: Qdrant API 키
            - QDRANT_COLLECTION: 컬렉션 이름
            - EMBEDDING_API_URL: 임베딩 서버 주소
        """
        self.vllm_api_url = getattr(settings, 'VLLM_API_URL', 'http://localhost:8000/v1')
        self.vllm_model_name = getattr(settings, 'VLLM_MODEL_NAME', 'Qwen/Qwen3-32B-Instruct')
        self.qdrant_host = getattr(settings, 'QDRANT_HOST', 'localhost')
        self.qdrant_port = getattr(settings, 'QDRANT_PORT', 6335)
        self.qdrant_api_key = getattr(settings, 'QDRANT_API_KEY', '')
        self.qdrant_collection = getattr(settings, 'QDRANT_COLLECTION', '130825-512-v3')
        self.embedding_api_url = getattr(settings, 'EMBEDDING_API_URL', 'http://localhost:8001/v1')

        self.qdrant_url = f"http://{self.qdrant_host}:{self.qdrant_port}"

        # HTTP 클라이언트 (타임아웃 설정)
        self.client = httpx.AsyncClient(timeout=300.0)

        logger.info(f"AIService initialized - vLLM: {self.vllm_api_url}, Qdrant: {self.qdrant_url}")

    async def stream_chat(
        self,
        message: str,
        history: List[Dict[str, str]] = None,
        search_documents: bool = False,
        department: Optional[str] = None,
        search_scope: Optional[List[str]] = None,
        max_context_tokens: int = 4000,
        temperature: float = 0.7,
        think_mode: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        채팅 스트리밍 생성

        Args:
            message: 사용자 질문
            history: 대화 이력 [{"role": "user", "content": "..."}, ...]
            search_documents: RAG 문서 검색 활성화
            department: 부서 코드 (문서 필터링)
            search_scope: 검색 범위 (manual, faq 등)
            max_context_tokens: 최대 컨텍스트 토큰 수
            temperature: 샘플링 온도
            think_mode: 추론 모드 (DeepSeek-R1 등)

        Yields:
            str: 스트리밍 텍스트 청크
        """
        try:
            # 1. RAG 문서 검색 (옵션)
            context = ""
            if search_documents:
                search_results = await self._search_documents(
                    query=message,
                    department=department,
                    search_scope=search_scope,
                    limit=5
                )

                if search_results:
                    context = self._format_context(search_results)
                    logger.info(f"RAG context added - {len(search_results)} documents")

            # 2. 메시지 구성
            messages = self._build_messages(
                message=message,
                history=history or [],
                context=context,
                think_mode=think_mode
            )

            # 3. vLLM API 호출 (스트리밍)
            payload = {
                "model": self.vllm_model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_context_tokens,
                "stream": True
            }

            logger.info(f"Calling vLLM API - model: {self.vllm_model_name}, temp: {temperature}")

            async with self.client.stream(
                "POST",
                f"{self.vllm_api_url}/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # "data: " 제거

                        if data_str.strip() == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")

                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPStatusError as e:
            logger.error(f"vLLM API error: {e.response.status_code} - {e.response.text}")
            yield f"\n[오류: AI 서버 응답 실패 ({e.response.status_code})]\n"
        except Exception as e:
            logger.error(f"AI service error: {e}", exc_info=True)
            yield "\n[오류: AI 서비스 오류가 발생했습니다]\n"

    async def _search_documents(
        self,
        query: str,
        department: Optional[str] = None,
        search_scope: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Qdrant 벡터 검색 (RAG)

        Args:
            query: 검색 쿼리
            department: 부서 코드 필터
            search_scope: 검색 범위 필터
            limit: 최대 결과 수

        Returns:
            List[Dict]: 검색 결과
                [{
                    "chunk_text": str,
                    "score": float,
                    "metadata": {
                        "title": str,
                        "document_type": str,
                        "category_name": str
                    }
                }, ...]
        """
        try:
            # 1. 쿼리 임베딩 생성
            embedding = await self._get_embedding(query)

            if not embedding:
                logger.warning("Failed to generate embedding")
                return []

            # 2. Qdrant 필터 구성
            must_filters = []

            if department:
                must_filters.append({
                    "key": "metadata.department",
                    "match": {"value": department}
                })

            if search_scope:
                must_filters.append({
                    "key": "metadata.document_type",
                    "match": {"any": search_scope}
                })

            # 3. Qdrant 검색
            search_payload = {
                "vector": embedding,
                "limit": limit,
                "with_payload": True,
                "with_vector": False
            }

            if must_filters:
                search_payload["filter"] = {"must": must_filters}

            headers = {}
            if self.qdrant_api_key:
                headers["api-key"] = self.qdrant_api_key

            response = await self.client.post(
                f"{self.qdrant_url}/collections/{self.qdrant_collection}/points/search",
                json=search_payload,
                headers=headers
            )
            response.raise_for_status()

            data = response.json()
            results = []

            for point in data.get("result", []):
                payload = point.get("payload", {})
                results.append({
                    "chunk_text": payload.get("chunk_text", ""),
                    "score": point.get("score", 0.0),
                    "metadata": payload.get("metadata", {})
                })

            logger.info(f"Qdrant search completed - {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Qdrant search error: {e}", exc_info=True)
            return []

    async def _get_embedding(self, text: str) -> Optional[List[float]]:
        """
        텍스트 임베딩 생성

        Args:
            text: 임베딩할 텍스트

        Returns:
            List[float]: 임베딩 벡터 (1024-dim for Qwen3-Embedding-0.6B)
        """
        try:
            response = await self.client.post(
                f"{self.embedding_api_url}/embeddings",
                json={
                    "input": text,
                    "model": "Qwen/Qwen3-Embedding-0.6B"
                },
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            data = response.json()
            embedding = data.get("data", [{}])[0].get("embedding", [])

            return embedding

        except Exception as e:
            logger.error(f"Embedding generation error: {e}", exc_info=True)
            return None

    def _build_messages(
        self,
        message: str,
        history: List[Dict[str, str]],
        context: str = "",
        think_mode: bool = False
    ) -> List[Dict[str, str]]:
        """
        메시지 리스트 구성 (vLLM Chat Completions API 형식)

        Args:
            message: 현재 사용자 질문
            history: 대화 이력
            context: RAG 컨텍스트
            think_mode: 추론 모드

        Returns:
            List[Dict]: [{"role": "system", "content": "..."}, ...]
        """
        messages = []

        # 1. System Prompt
        system_prompt = "당신은 유능한 AI 어시스턴트입니다. 사용자의 질문에 정확하고 친절하게 답변하세요."

        if think_mode:
            system_prompt += "\n\n추론 과정을 <think>...</think> 태그 안에 작성한 후, 최종 답변을 제공하세요."

        if context:
            system_prompt += f"\n\n다음 참고 자료를 활용하여 답변하세요:\n\n{context}"

        messages.append({
            "role": "system",
            "content": system_prompt
        })

        # 2. 대화 이력 추가
        for msg in history:
            messages.append(msg)

        # 3. 현재 질문 추가
        messages.append({
            "role": "user",
            "content": message
        })

        return messages

    def _format_context(self, search_results: List[Dict[str, Any]]) -> str:
        """
        검색 결과를 컨텍스트 문자열로 포맷

        Args:
            search_results: Qdrant 검색 결과

        Returns:
            str: 포맷된 컨텍스트
        """
        context_parts = []

        for idx, result in enumerate(search_results, 1):
            metadata = result.get("metadata", {})
            title = metadata.get("title", "제목 없음")
            chunk_text = result.get("chunk_text", "")
            score = result.get("score", 0.0)

            context_parts.append(
                f"[참고자료 {idx}] {title} (관련도: {score:.2f})\n{chunk_text}\n"
            )

        return "\n".join(context_parts)

    async def close(self):
        """HTTP 클라이언트 종료"""
        await self.client.aclose()
        logger.info("AIService closed")


# Singleton 인스턴스
ai_service = AIService()
