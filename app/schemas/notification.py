"""
알림 스키마
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class NotificationBase(BaseModel):
    """알림 기본 스키마"""
    type: str = Field(..., description="알림 유형: success, error, info, warning")
    category: str = Field(..., description="알림 카테고리")
    title: str = Field(..., max_length=200, description="알림 제목")
    message: str = Field(..., description="알림 메시지")
    link: Optional[str] = Field(None, max_length=500, description="관련 페이지 링크")
    related_entity_type: Optional[str] = Field(None, description="관련 엔티티 타입")
    related_entity_id: Optional[int] = Field(None, description="관련 엔티티 ID")


class NotificationCreate(NotificationBase):
    """알림 생성 스키마"""
    user_id: Optional[int] = Field(None, description="특정 사용자 ID (NULL이면 전체)")


class NotificationUpdate(BaseModel):
    """알림 업데이트 스키마"""
    is_read: bool = Field(..., description="읽음 여부")


class NotificationResponse(NotificationBase):
    """알림 응답 스키마"""
    id: int
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    user_id: Optional[int]

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """알림 목록 응답"""
    items: list[NotificationResponse]
    total: int
    unread_count: int
