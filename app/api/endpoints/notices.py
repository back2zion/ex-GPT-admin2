from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()


@router.get("/")
async def list_notices(
    active_only: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000)
):
    """공지사항 목록 조회"""
    # TODO: 공지사항 목록 반환
    return {
        "total": 0,
        "items": [],
        "skip": skip,
        "limit": limit
    }


@router.post("/")
async def create_notice(
    title: str,
    content: str,
    priority: str = "normal",
    target_users: Optional[list] = None
):
    """공지사항 생성"""
    # TODO: 공지사항 생성 로직
    return {
        "id": "notice_id",
        "title": title,
        "status": "created"
    }


@router.put("/{notice_id}")
async def update_notice(
    notice_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    active: Optional[bool] = None
):
    """공지사항 수정"""
    # TODO: 공지사항 수정 로직
    return {
        "id": notice_id,
        "status": "updated"
    }


@router.delete("/{notice_id}")
async def delete_notice(notice_id: str):
    """공지사항 삭제"""
    # TODO: 공지사항 삭제 로직
    return {
        "id": notice_id,
        "status": "deleted"
    }


@router.get("/active")
async def get_active_notices():
    """활성 공지사항 조회 (사용자용)"""
    # TODO: 현재 활성화된 공지사항만 반환
    return {
        "notices": []
    }
