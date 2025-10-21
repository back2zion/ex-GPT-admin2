"""
Category Schemas
학습데이터 관리 - 카테고리 스키마 (Secure: Input Validation)
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from app.models.category import ParsingPattern


class CategoryBase(BaseModel):
    """카테고리 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=255, description="카테고리 이름")
    description: Optional[str] = Field(None, max_length=5000, description="카테고리 설명")
    parsing_pattern: ParsingPattern = Field(default=ParsingPattern.PARAGRAPH, description="파싱 패턴")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """
        카테고리 이름 검증 (Secure: XSS/Injection Prevention)
        """
        if not v or not v.strip():
            raise ValueError('카테고리 이름은 필수입니다')

        # Remove dangerous characters
        dangerous_chars = ['<', '>', ';', '--', '/*', '*/', 'DROP', 'DELETE']
        for char in dangerous_chars:
            if char.lower() in v.lower():
                raise ValueError(f'카테고리 이름에 허용되지 않는 문자가 포함되어 있습니다: {char}')

        return v.strip()


class CategoryCreate(CategoryBase):
    """카테고리 생성 스키마"""
    pass


class CategoryUpdate(BaseModel):
    """카테고리 수정 스키마"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    parsing_pattern: Optional[ParsingPattern] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """이름 검증"""
        if v is None:
            return v

        if not v.strip():
            raise ValueError('카테고리 이름은 비어있을 수 없습니다')

        # Remove dangerous characters
        dangerous_chars = ['<', '>', ';', '--', '/*', '*/', 'DROP', 'DELETE']
        for char in dangerous_chars:
            if char.lower() in v.lower():
                raise ValueError(f'카테고리 이름에 허용되지 않는 문자가 포함되어 있습니다: {char}')

        return v.strip()


class CategoryResponse(CategoryBase):
    """카테고리 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Pydantic v2


class CategoryListResponse(BaseModel):
    """카테고리 목록 응답 스키마"""
    items: list[CategoryResponse]
    total: int
    page: int
    limit: int
