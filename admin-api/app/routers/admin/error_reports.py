"""
오류 보고 관리 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/v1/admin/error_reports", tags=["admin-error-reports"])


# Mock 데이터
MOCK_ERROR_REPORTS = [
    {
        "id": 1,
        "error_type": "시스템 오류",
        "error_message": "채팅 응답 생성 실패",
        "stack_trace": "Traceback (most recent call last):\n  File \"chat.py\", line 42, in generate_response\n    ...",
        "user_id": "user001",
        "session_id": "session-2025-01-15-001",
        "severity": "high",
        "resolution_notes": "",
        "is_resolved": False,
        "created_at": "2025-01-15T10:30:00",
        "resolved_at": None
    },
    {
        "id": 2,
        "error_type": "네트워크 오류",
        "error_message": "API 서버 연결 실패",
        "stack_trace": "Connection refused: 503 Service Unavailable",
        "user_id": "user002",
        "session_id": "session-2025-01-14-002",
        "severity": "medium",
        "resolution_notes": "서버 재시작으로 해결",
        "is_resolved": True,
        "created_at": "2025-01-14T14:20:00",
        "resolved_at": "2025-01-14T15:00:00"
    },
    {
        "id": 3,
        "error_type": "데이터 오류",
        "error_message": "잘못된 문서 형식",
        "stack_trace": "ValueError: Invalid document format: expected PDF, got HWP",
        "user_id": "user003",
        "session_id": "session-2025-01-10-003",
        "severity": "low",
        "resolution_notes": "문서 변환 로직 추가",
        "is_resolved": True,
        "created_at": "2025-01-10T09:15:00",
        "resolved_at": "2025-01-11T10:00:00"
    }
]


@router.get("")
async def list_error_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    severity: Optional[str] = None,
    is_resolved: Optional[bool] = None
):
    """오류 보고 목록 조회"""
    items = MOCK_ERROR_REPORTS.copy()

    # 필터링
    if severity:
        items = [item for item in items if item.get("severity") == severity]
    if is_resolved is not None:
        items = [item for item in items if item.get("is_resolved") == is_resolved]

    # 페이징
    total = len(items)
    items = items[skip:skip + limit]

    return {"items": items, "total": total}


@router.get("/{error_id}")
async def get_error_report(error_id: int):
    """오류 보고 상세 조회"""
    for item in MOCK_ERROR_REPORTS:
        if item["id"] == error_id:
            return item

    raise HTTPException(status_code=404, detail="오류 보고를 찾을 수 없습니다")


@router.post("")
async def create_error_report(data: dict):
    """오류 보고 생성"""
    new_id = max([item["id"] for item in MOCK_ERROR_REPORTS]) + 1
    new_item = {
        "id": new_id,
        **data,
        "created_at": datetime.now().isoformat()
    }
    MOCK_ERROR_REPORTS.append(new_item)
    return new_item


@router.put("/{error_id}")
async def update_error_report(error_id: int, data: dict):
    """오류 보고 수정"""
    for i, item in enumerate(MOCK_ERROR_REPORTS):
        if item["id"] == error_id:
            MOCK_ERROR_REPORTS[i] = {**item, **data}
            if data.get("is_resolved"):
                MOCK_ERROR_REPORTS[i]["resolved_at"] = datetime.now().isoformat()
            return MOCK_ERROR_REPORTS[i]

    raise HTTPException(status_code=404, detail="오류 보고를 찾을 수 없습니다")


@router.delete("/{error_id}")
async def delete_error_report(error_id: int):
    """오류 보고 삭제"""
    for i, item in enumerate(MOCK_ERROR_REPORTS):
        if item["id"] == error_id:
            MOCK_ERROR_REPORTS.pop(i)
            return {"message": "오류 보고가 삭제되었습니다", "id": error_id}

    raise HTTPException(status_code=404, detail="오류 보고를 찾을 수 없습니다")
