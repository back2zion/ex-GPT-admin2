from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class NoticeBase(BaseModel):
    """공지사항 기본 스키마"""
    title: str = Field(..., min_length=1, max_length=255, description="공지사항 제목")
    content: str = Field(..., min_length=1, description="공지사항 내용")
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$", description="우선순위")
    is_active: bool = Field(default=True, description="활성화 여부")


class NoticeCreate(NoticeBase):
    """공지사항 생성 스키마"""
    pass


class NoticeUpdate(BaseModel):
    """공지사항 수정 스키마"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    priority: Optional[str] = Field(None, pattern="^(low|normal|high|urgent)$")
    is_active: Optional[bool] = None


class NoticeResponse(NoticeBase):
    """공지사항 응답 스키마"""
    id: int
    view_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Pydantic v2: orm_mode 대체
