"""
추천 질문 관리 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/v1/admin/recommended_questions", tags=["admin-recommended-questions"])


# Mock 데이터
MOCK_RECOMMENDED_QUESTIONS = [
    {
        "id": 1,
        "question": "하이패스는 어떻게 사용하나요?",
        "category": "하이패스",
        "description": "하이패스 이용 방법에 대한 기본 질문",
        "display_order": 1,
        "is_active": True,
        "created_at": "2025-01-15T10:30:00",
        "updated_at": "2025-01-15T10:30:00"
    },
    {
        "id": 2,
        "question": "통행료는 어떻게 계산되나요?",
        "category": "요금",
        "description": "고속도로 통행료 계산 방법",
        "display_order": 2,
        "is_active": True,
        "created_at": "2025-01-14T14:20:00",
        "updated_at": "2025-01-14T14:20:00"
    },
    {
        "id": 3,
        "question": "휴게소는 몇 km마다 있나요?",
        "category": "시설",
        "description": "휴게소 위치 및 간격에 대한 질문",
        "display_order": 3,
        "is_active": True,
        "created_at": "2025-01-10T09:15:00",
        "updated_at": "2025-01-10T09:15:00"
    },
    {
        "id": 4,
        "question": "교통사고가 났을 때 어떻게 하나요?",
        "category": "안전",
        "description": "고속도로 사고 발생 시 대처 방법",
        "display_order": 4,
        "is_active": False,
        "created_at": "2025-01-09T11:00:00",
        "updated_at": "2025-01-09T11:00:00"
    }
]


@router.get("")
async def list_recommended_questions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    category: Optional[str] = None,
    is_active: Optional[bool] = None
):
    """추천 질문 목록 조회"""
    items = MOCK_RECOMMENDED_QUESTIONS.copy()

    # 필터링
    if category:
        items = [item for item in items if item.get("category") == category]
    if is_active is not None:
        items = [item for item in items if item.get("is_active") == is_active]

    # 정렬 (display_order 순)
    items = sorted(items, key=lambda x: x.get("display_order", 999))

    # 페이징
    total = len(items)
    items = items[skip:skip + limit]

    return {"items": items, "total": total}


@router.get("/{question_id}")
async def get_recommended_question(question_id: int):
    """추천 질문 상세 조회"""
    for item in MOCK_RECOMMENDED_QUESTIONS:
        if item["id"] == question_id:
            return item

    raise HTTPException(status_code=404, detail="추천 질문을 찾을 수 없습니다")


@router.post("")
async def create_recommended_question(data: dict):
    """추천 질문 생성"""
    new_id = max([item["id"] for item in MOCK_RECOMMENDED_QUESTIONS]) + 1
    new_item = {
        "id": new_id,
        **data,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    MOCK_RECOMMENDED_QUESTIONS.append(new_item)
    return new_item


@router.put("/{question_id}")
async def update_recommended_question(question_id: int, data: dict):
    """추천 질문 수정"""
    for i, item in enumerate(MOCK_RECOMMENDED_QUESTIONS):
        if item["id"] == question_id:
            MOCK_RECOMMENDED_QUESTIONS[i] = {**item, **data, "updated_at": datetime.now().isoformat()}
            return MOCK_RECOMMENDED_QUESTIONS[i]

    raise HTTPException(status_code=404, detail="추천 질문을 찾을 수 없습니다")


@router.delete("/{question_id}")
async def delete_recommended_question(question_id: int):
    """추천 질문 삭제"""
    for i, item in enumerate(MOCK_RECOMMENDED_QUESTIONS):
        if item["id"] == question_id:
            MOCK_RECOMMENDED_QUESTIONS.pop(i)
            return {"message": "추천 질문이 삭제되었습니다", "id": question_id}

    raise HTTPException(status_code=404, detail="추천 질문을 찾을 수 없습니다")
