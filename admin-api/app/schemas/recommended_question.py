"""추천 질문 스키마

API 요청/응답을 위한 Pydantic 스키마
- XSS 방지를 위한 HTML 이스케이프 포함
- 입력 검증 및 데이터 변환
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
import html


class RecommendedQuestionBase(BaseModel):
    """추천 질문 기본 스키마"""
    question: str = Field(..., min_length=1, max_length=500, description="추천 질문 텍스트")
    category: Optional[str] = Field(None, max_length=100, description="카테고리")
    description: Optional[str] = Field(None, description="설명")
    display_order: int = Field(default=999, ge=0, description="표시 순서")
    is_active: bool = Field(default=True, description="활성화 여부")


class RecommendedQuestionCreate(RecommendedQuestionBase):
    """추천 질문 생성 스키마"""

    @field_validator('question', 'category', 'description')
    @classmethod
    def sanitize_html(cls, v: Optional[str]) -> Optional[str]:
        """XSS 방지: HTML 태그 이스케이프"""
        if v:
            return html.escape(v)
        return v


class RecommendedQuestionUpdate(BaseModel):
    """추천 질문 수정 스키마 (부분 업데이트 지원)"""
    question: Optional[str] = Field(None, min_length=1, max_length=500)
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    display_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

    @field_validator('question', 'category', 'description')
    @classmethod
    def sanitize_html(cls, v: Optional[str]) -> Optional[str]:
        """XSS 방지: HTML 태그 이스케이프"""
        if v:
            return html.escape(v)
        return v


class RecommendedQuestionResponse(BaseModel):
    """추천 질문 응답 스키마 (React Admin용 필드명 매핑)"""
    id: int = Field(description="추천 질문 ID")
    question: str = Field(description="질문 텍스트")
    category: Optional[str] = Field(None, description="카테고리")
    description: Optional[str] = Field(None, description="설명")
    display_order: int = Field(description="표시 순서")
    is_active: bool = Field(description="활성화 여부")
    created_at: datetime = Field(description="생성일시")
    updated_at: Optional[datetime] = Field(None, description="수정일시")

    class Config:
        from_attributes = True
        # ORM 필드명 -> API 필드명 매핑
        populate_by_name = True


class RecommendedQuestionListResponse(BaseModel):
    """추천 질문 목록 응답 스키마"""
    items: List[RecommendedQuestionResponse]
    total: int
