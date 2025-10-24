"""
벡터 문서 관리 API 엔드포인트 (Qdrant 기반)
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from datetime import datetime
import logging
import os

from app.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/vector-documents", tags=["admin-vector-documents"])

# Qdrant 설정
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "130825-512-v3")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


def get_vector_store() -> VectorStoreService:
    """VectorStoreService 인스턴스 생성"""
    return VectorStoreService(
        host=QDRANT_HOST,
        port=QDRANT_PORT,
        api_key=QDRANT_API_KEY
    )


@router.get("/stats")
async def get_vector_documents_stats(
    vector_store: VectorStoreService = Depends(get_vector_store)
):
    """
    벡터 문서 통계 조회 (doctype별 문서 수)

    Returns:
        {"total": int, "by_doctype": {...}}
    """
    try:
        documents, total = await vector_store.get_unique_documents(
            collection_name=QDRANT_COLLECTION,
            skip=0,
            limit=10000  # 전체 문서 가져오기
        )

        # doctype별 집계
        doctype_counts = {}
        for doc in documents:
            doctype = doc.get("doctype", "기타")
            doctype_counts[doctype] = doctype_counts.get(doctype, 0) + 1

        return {
            "total": total,
            "by_doctype": doctype_counts
        }

    except Exception as e:
        logger.error(f"Failed to get vector documents stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"벡터 문서 통계 조회 실패: {str(e)}"
        )
    finally:
        vector_store.close()


@router.get("")
async def list_vector_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    search: Optional[str] = None,
    doctype: Optional[str] = None,
    vector_store: VectorStoreService = Depends(get_vector_store)
):
    """
    벡터 문서 목록 조회 (Qdrant에서 실제 데이터 가져오기)

    Args:
        skip: 스킵할 문서 수
        limit: 가져올 문서 수 (최대 1000)
        search: 제목 검색어
        doctype: 문서 타입 필터
        vector_store: VectorStoreService 인스턴스

    Returns:
        {"items": [...], "total": int}
    """
    try:
        # Qdrant에서 유니크한 문서 목록 가져오기
        documents, total = await vector_store.get_unique_documents(
            collection_name=QDRANT_COLLECTION,
            skip=skip,
            limit=limit
        )

        # 필터링 (검색어, 문서 타입)
        if search:
            documents = [
                doc for doc in documents
                if search.lower() in doc.get("title", "").lower()
            ]
            total = len(documents)

        if doctype:
            documents = [
                doc for doc in documents
                if doc.get("doctype") == doctype
            ]
            total = len(documents)

        # 응답 형식 변환 (프론트엔드 호환)
        formatted_docs = []
        for doc in documents:
            formatted_docs.append({
                "id": doc["id"],
                "title": doc["title"],
                "file_path": doc.get("file_path", []),
                "metadata_uri": doc.get("metadata_uri", ""),
                "doctype": doc.get("doctype", "D"),
                "token_count": doc.get("token_count", 0),
                "is_active": doc.get("migrated", True),  # migrated를 is_active로 매핑
                "created_at": None,  # Qdrant에는 없음
            })

        logger.info(f"Returned {len(formatted_docs)} documents from Qdrant (total: {total})")

        return {
            "items": formatted_docs,
            "total": total
        }

    except Exception as e:
        logger.error(f"Failed to list vector documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"벡터 문서 목록 조회 실패: {str(e)}"
        )
    finally:
        vector_store.close()


@router.get("/{document_id}")
async def get_vector_document(
    document_id: str,
    vector_store: VectorStoreService = Depends(get_vector_store)
):
    """
    벡터 문서 상세 조회

    Args:
        document_id: 문서 ID (file_id)
        vector_store: VectorStoreService 인스턴스

    Returns:
        문서 상세 정보
    """
    try:
        # Qdrant에서 해당 file_id를 가진 첫 번째 포인트 조회
        result = vector_store.client.scroll(
            collection_name=QDRANT_COLLECTION,
            scroll_filter={
                "must": [
                    {
                        "key": "metadata.file_id",
                        "match": {"value": document_id}
                    }
                ]
            },
            limit=1,
            with_payload=True,
            with_vectors=False
        )

        points, _ = result
        if not points:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

        point = points[0]
        metadata = point.payload.get("metadata", {})

        return {
            "id": document_id,
            "title": metadata.get("file_path", ["제목 없음"])[0],
            "file_path": metadata.get("file_path", []),
            "metadata_uri": metadata.get("metadata_uri", ""),
            "doctype": metadata.get("doctype", ""),
            "token_count": metadata.get("token_count", 0),
            "is_active": metadata.get("migrated", True),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get vector document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"벡터 문서 조회 실패: {str(e)}"
        )
    finally:
        vector_store.close()


# TODO: 벡터 문서 생성/수정/삭제는 별도의 문서 업로드 파이프라인을 통해 처리
# @router.post("")
# @router.put("/{document_id}")
# @router.delete("/{document_id}")
