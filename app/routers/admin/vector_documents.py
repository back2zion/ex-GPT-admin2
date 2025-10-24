"""
벡터 문서 관리 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/v1/admin/vector_documents", tags=["admin-vector-documents"])


# Mock 데이터
MOCK_DOCUMENTS = [
    {
        "id": 1,
        "title": "도로교통법 제1조 - 법의 목적",
        "category": "법규",
        "chunk_count": 15,
        "is_active": True,
        "created_at": "2025-01-15T10:30:00",
        "updated_at": "2025-01-15T10:30:00"
    },
    {
        "id": 2,
        "title": "고속도로 안전운행 지침",
        "category": "지침",
        "chunk_count": 32,
        "is_active": True,
        "created_at": "2025-01-14T14:20:00",
        "updated_at": "2025-01-14T14:20:00"
    },
    {
        "id": 3,
        "title": "톨게이트 요금 정산 매뉴얼",
        "category": "매뉴얼",
        "chunk_count": 28,
        "is_active": False,
        "created_at": "2025-01-10T09:15:00",
        "updated_at": "2025-01-10T09:15:00"
    }
]


@router.get("")
async def list_vector_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    category: Optional[str] = None,
    is_active: Optional[bool] = None
):
    """벡터 문서 목록 조회"""
    items = MOCK_DOCUMENTS.copy()

    # 필터링
    if category:
        items = [doc for doc in items if doc.get("category") == category]
    if is_active is not None:
        items = [doc for doc in items if doc.get("is_active") == is_active]

    # 페이징
    total = len(items)
    items = items[skip:skip + limit]

    return {"items": items, "total": total}


@router.get("/{document_id}")
async def get_vector_document(
    document_id: int
):
    """벡터 문서 상세 조회"""
    for doc in MOCK_DOCUMENTS:
        if doc["id"] == document_id:
            return doc

    raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")


@router.post("")
async def create_vector_document(
    data: dict
):
    """벡터 문서 생성"""
    new_id = max([doc["id"] for doc in MOCK_DOCUMENTS]) + 1
    new_doc = {
        "id": new_id,
        **data,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    MOCK_DOCUMENTS.append(new_doc)
    return new_doc


@router.put("/{document_id}")
async def update_vector_document(
    document_id: int,
    data: dict
):
    """벡터 문서 수정"""
    for i, doc in enumerate(MOCK_DOCUMENTS):
        if doc["id"] == document_id:
            MOCK_DOCUMENTS[i] = {**doc, **data, "updated_at": datetime.now().isoformat()}
            return MOCK_DOCUMENTS[i]

    raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")


@router.delete("/{document_id}")
async def delete_vector_document(
    document_id: int
):
    """벡터 문서 삭제"""
    for i, doc in enumerate(MOCK_DOCUMENTS):
        if doc["id"] == document_id:
            MOCK_DOCUMENTS.pop(i)
            return {"message": "문서가 삭제되었습니다", "id": document_id}

    raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
