"""
사전 관리 스키마
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.dictionary import DictType


# ========== Dictionary Base Schemas ==========

class DictionaryBase(BaseModel):
    """사전 기본 스키마"""
    dict_type: DictType = Field(..., description="사전 종류")
    dict_name: str = Field(..., max_length=200, description="사전명")
    dict_desc: Optional[str] = Field(None, description="사전 설명")
    case_sensitive: bool = Field(False, description="대소문자 구분 여부")
    use_yn: bool = Field(True, description="사용 여부")


class DictionaryCreate(DictionaryBase):
    """사전 생성 스키마"""
    pass


class DictionaryUpdate(BaseModel):
    """사전 수정 스키마"""
    dict_name: Optional[str] = Field(None, max_length=200, description="사전명")
    dict_desc: Optional[str] = Field(None, description="사전 설명")
    case_sensitive: Optional[bool] = Field(None, description="대소문자 구분 여부")
    use_yn: Optional[bool] = Field(None, description="사용 여부")


class DictionaryResponse(DictionaryBase):
    """사전 응답 스키마"""
    dict_id: int
    word_count: int = Field(0, description="용어 개수")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== DictionaryTerm Base Schemas ==========

class DictionaryTermBase(BaseModel):
    """사전 용어 기본 스키마"""
    main_term: str = Field(..., max_length=200, description="정식명칭")
    main_alias: Optional[str] = Field(None, max_length=200, description="주요약칭")
    alias_1: Optional[str] = Field(None, max_length=200, description="추가약칭1")
    alias_2: Optional[str] = Field(None, max_length=200, description="추가약칭2")
    alias_3: Optional[str] = Field(None, max_length=200, description="추가약칭3")
    english_name: Optional[str] = Field(None, max_length=500, description="영문명")
    english_alias: Optional[str] = Field(None, max_length=100, description="영문약칭")
    category: Optional[str] = Field(None, max_length=100, description="분류")
    definition: Optional[str] = Field(None, description="정의/설명")
    use_yn: bool = Field(True, description="사용 여부")


class DictionaryTermCreate(DictionaryTermBase):
    """사전 용어 생성 스키마"""
    dict_id: int = Field(..., description="사전 ID")


class DictionaryTermUpdate(BaseModel):
    """사전 용어 수정 스키마"""
    main_term: Optional[str] = Field(None, max_length=200, description="정식명칭")
    main_alias: Optional[str] = Field(None, max_length=200, description="주요약칭")
    alias_1: Optional[str] = Field(None, max_length=200, description="추가약칭1")
    alias_2: Optional[str] = Field(None, max_length=200, description="추가약칭2")
    alias_3: Optional[str] = Field(None, max_length=200, description="추가약칭3")
    english_name: Optional[str] = Field(None, max_length=500, description="영문명")
    english_alias: Optional[str] = Field(None, max_length=100, description="영문약칭")
    category: Optional[str] = Field(None, max_length=100, description="분류")
    definition: Optional[str] = Field(None, description="정의/설명")
    use_yn: Optional[bool] = Field(None, description="사용 여부")


class DictionaryTermResponse(DictionaryTermBase):
    """사전 용어 응답 스키마"""
    term_id: int
    dict_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== Combined Response (with terms) ==========

class DictionaryWithTermsResponse(DictionaryResponse):
    """사전 + 용어 목록 응답 스키마"""
    terms: list[DictionaryTermResponse] = []

    class Config:
        from_attributes = True


# ========== List Response ==========

class DictionaryListResponse(BaseModel):
    """사전 목록 응답"""
    items: list[DictionaryResponse]
    total: int


class DictionaryTermListResponse(BaseModel):
    """사전 용어 목록 응답"""
    items: list[DictionaryTermResponse]
    total: int
