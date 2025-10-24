"""
사전 관리 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/v1/admin/dictionaries", tags=["admin-dictionaries"])


# Mock 데이터
MOCK_DICTIONARIES = [
    {
        "id": 1,
        "term": "하이패스",
        "definition": "High-pass, 고속도로 통행료 자동결제 시스템",
        "category": "시스템",
        "synonyms": "Hi-pass, 자동결제",
        "is_active": True,
        "created_at": "2025-01-15T10:30:00",
        "updated_at": "2025-01-15T10:30:00"
    },
    {
        "id": 2,
        "term": "톨게이트",
        "definition": "요금소, Toll gate",
        "category": "시설",
        "synonyms": "요금소, 통행료 징수소",
        "is_active": True,
        "created_at": "2025-01-14T14:20:00",
        "updated_at": "2025-01-14T14:20:00"
    },
    {
        "id": 3,
        "term": "휴게소",
        "definition": "고속도로 이용객을 위한 편의시설",
        "category": "시설",
        "synonyms": "서비스 에리어, SA",
        "is_active": True,
        "created_at": "2025-01-10T09:15:00",
        "updated_at": "2025-01-10T09:15:00"
    }
]


@router.get("")
async def list_dictionaries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    category: Optional[str] = None,
    is_active: Optional[bool] = None
):
    """사전 목록 조회"""
    items = MOCK_DICTIONARIES.copy()

    # 필터링
    if category:
        items = [item for item in items if item.get("category") == category]
    if is_active is not None:
        items = [item for item in items if item.get("is_active") == is_active]

    # 페이징
    total = len(items)
    items = items[skip:skip + limit]

    return {"items": items, "total": total}


@router.get("/{dictionary_id}")
async def get_dictionary(dictionary_id: int):
    """사전 상세 조회"""
    for item in MOCK_DICTIONARIES:
        if item["id"] == dictionary_id:
            return item

    raise HTTPException(status_code=404, detail="사전 항목을 찾을 수 없습니다")


@router.post("")
async def create_dictionary(data: dict):
    """사전 생성"""
    new_id = max([item["id"] for item in MOCK_DICTIONARIES]) + 1
    new_item = {
        "id": new_id,
        **data,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    MOCK_DICTIONARIES.append(new_item)
    return new_item


@router.put("/{dictionary_id}")
async def update_dictionary(dictionary_id: int, data: dict):
    """사전 수정"""
    for i, item in enumerate(MOCK_DICTIONARIES):
        if item["id"] == dictionary_id:
            MOCK_DICTIONARIES[i] = {**item, **data, "updated_at": datetime.now().isoformat()}
            return MOCK_DICTIONARIES[i]

    raise HTTPException(status_code=404, detail="사전 항목을 찾을 수 없습니다")


@router.delete("/{dictionary_id}")
async def delete_dictionary(dictionary_id: int):
    """사전 삭제"""
    for i, item in enumerate(MOCK_DICTIONARIES):
        if item["id"] == dictionary_id:
            MOCK_DICTIONARIES.pop(i)
            return {"message": "사전 항목이 삭제되었습니다", "id": dictionary_id}

    raise HTTPException(status_code=404, detail="사전 항목을 찾을 수 없습니다")
