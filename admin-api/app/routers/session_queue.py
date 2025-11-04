"""
PER-002: 세션 및 대기열 관리 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

from app.services.session_queue_service import get_session_queue_service, SessionQueueService
from app.core.config import Settings

settings = Settings()

router = APIRouter(prefix="/session", tags=["Session & Queue Management"])


# Dependency to get session queue service
async def get_queue_service() -> SessionQueueService:
    """Get session queue service instance"""
    return await get_session_queue_service(settings.REDIS_URL)


class SessionCreateRequest(BaseModel):
    """세션 생성 요청"""
    user_id: str
    session_id: str


class SessionStatusResponse(BaseModel):
    """세션 상태 응답"""
    status: str  # "active" or "queued"
    session_id: Optional[str] = None
    created_at: Optional[str] = None
    position: Optional[int] = None
    estimated_wait_minutes: Optional[int] = None
    active_sessions: Optional[int] = None
    max_sessions: Optional[int] = None


class QueueStatusResponse(BaseModel):
    """대기열 상태 응답"""
    active_sessions: int
    max_sessions: int
    queue_length: int
    available_slots: int


@router.post("/create", response_model=SessionStatusResponse, summary="세션 생성")
async def create_session(
    request: SessionCreateRequest,
    queue_service: SessionQueueService = Depends(get_queue_service)
):
    """
    새 세션 생성 또는 대기열 추가

    PER-002 요구사항:
    - 최대 20개 세션 유지
    - 초과 시 대기열에 추가

    Returns:
        - status="active": 세션 생성 성공
        - status="queued": 대기열에 추가됨
    """
    result = await queue_service.create_session(request.user_id, request.session_id)
    return SessionStatusResponse(**result)


@router.delete("/close/{user_id}", summary="세션 종료")
async def close_session(
    user_id: str,
    queue_service: SessionQueueService = Depends(get_queue_service)
):
    """
    세션 종료 및 대기열 처리

    세션 종료 후 자동으로 대기열의 다음 사용자를 활성화합니다.
    """
    await queue_service.close_session(user_id)
    return {"message": "세션이 종료되었습니다", "user_id": user_id}


@router.get("/status", response_model=QueueStatusResponse, summary="대기열 상태 조회")
async def get_queue_status(
    queue_service: SessionQueueService = Depends(get_queue_service)
):
    """
    현재 대기열 및 세션 상태 조회

    Returns:
        - active_sessions: 현재 활성 세션 수
        - max_sessions: 최대 세션 수 (20)
        - queue_length: 대기열 길이
        - available_slots: 사용 가능한 슬롯 수
    """
    status = await queue_service.get_queue_status()
    return QueueStatusResponse(**status)


@router.get("/position/{user_id}", summary="사용자 대기열 위치 조회")
async def get_user_position(
    user_id: str,
    queue_service: SessionQueueService = Depends(get_queue_service)
):
    """
    특정 사용자의 대기열 위치 확인

    Returns:
        - position: 0이면 활성 세션, 1~N이면 대기열 순번, None이면 없음
    """
    position = await queue_service.get_user_queue_position(user_id)

    if position is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )

    return {
        "user_id": user_id,
        "position": position,
        "status": "active" if position == 0 else "queued"
    }


@router.post("/cleanup", summary="만료된 세션 정리 (관리자용)")
async def cleanup_expired_sessions(
    queue_service: SessionQueueService = Depends(get_queue_service)
):
    """
    만료된 세션 정리

    30분 이상 활동이 없는 세션을 자동으로 종료합니다.
    일반적으로 백그라운드 작업으로 실행되지만, 수동 실행도 가능합니다.
    """
    await queue_service.cleanup_expired_sessions()
    status = await queue_service.get_queue_status()
    return {
        "message": "만료된 세션이 정리되었습니다",
        "current_status": status
    }
