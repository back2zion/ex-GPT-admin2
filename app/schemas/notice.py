from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
import html
import re


class NoticeBase(BaseModel):
    """공지사항 기본 스키마"""
    title: str = Field(..., min_length=1, max_length=200, description="공지사항 제목")
    content: str = Field(..., min_length=1, description="공지사항 내용")
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$", description="우선순위")
    is_active: bool = Field(default=True, description="활성화 여부")
    is_important: bool = Field(default=False, description="중요 공지 여부")
    is_popup: bool = Field(default=False, description="팝업 표시 여부")
    start_date: Optional[str] = Field(None, pattern="^\\d{4}-\\d{2}-\\d{2}$", description="게시 시작일 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, pattern="^\\d{4}-\\d{2}-\\d{2}$", description="게시 종료일 (YYYY-MM-DD)")


class NoticeCreate(NoticeBase):
    """공지사항 생성 스키마 (입력 검증 포함)"""

    @field_validator('title', 'content')
    @classmethod
    def sanitize_html(cls, v: str) -> str:
        """XSS 방지: HTML 태그 이스케이프"""
        if v:
            return html.escape(v)
        return v

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        """날짜 형식 및 유효성 검증"""
        if v is None:
            return v

        # 정규식 검증 (YYYY-MM-DD)
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError('날짜 형식은 YYYY-MM-DD 형식이어야 합니다')

        # 실제 날짜 유효성 검증
        try:
            year, month, day = map(int, v.split('-'))
            if not (1 <= month <= 12):
                raise ValueError('월은 1-12 사이여야 합니다')
            if not (1 <= day <= 31):
                raise ValueError('일은 1-31 사이여야 합니다')
            # 간단한 월별 일수 검증
            if month in [4, 6, 9, 11] and day > 30:
                raise ValueError(f'{month}월은 30일까지만 있습니다')
            if month == 2 and day > 29:
                raise ValueError('2월은 29일까지만 있습니다')
            datetime.strptime(v, '%Y-%m-%d')  # 최종 검증
        except ValueError as e:
            raise ValueError(f'유효하지 않은 날짜입니다: {e}')

        return v


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


class NoticeListResponse(BaseModel):
    """공지사항 목록 응답 스키마 (페이지네이션)"""
    items: List[NoticeResponse]
    total: int
