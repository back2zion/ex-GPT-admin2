"""
Document Schemas for Learning Data Management
학습데이터 관리 - 문서 스키마 (Secure Coding Applied)
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DocumentTypeEnum(str, Enum):
    """문서 타입"""
    LAW = "law"
    REGULATION = "regulation"
    STANDARD = "standard"
    MANUAL = "manual"
    OTHER = "other"


class DocumentStatusEnum(str, Enum):
    """문서 상태"""
    ACTIVE = "active"
    PENDING = "pending"
    ARCHIVED = "archived"
    DELETED = "deleted"


class VectorStatusEnum(str, Enum):
    """벡터화 상태"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DocumentVectorInfo(BaseModel):
    """문서 벡터 정보"""
    total_chunks: int = Field(0, description="총 청크 수")
    completed_chunks: int = Field(0, description="완료된 청크 수")
    failed_chunks: int = Field(0, description="실패한 청크 수")
    status: VectorStatusEnum = Field(VectorStatusEnum.PENDING, description="전체 벡터화 상태")
    vector_dimension: Optional[int] = Field(None, description="벡터 차원")
    embedding_model: Optional[str] = Field(None, description="임베딩 모델")


class DocumentBase(BaseModel):
    """문서 기본 스키마"""
    title: str = Field(..., min_length=1, max_length=500, description="문서 제목")
    document_type: DocumentTypeEnum = Field(..., description="문서 타입")
    status: DocumentStatusEnum = Field(DocumentStatusEnum.PENDING, description="문서 상태")
    category_id: Optional[int] = Field(None, description="카테고리 ID")
    content: Optional[str] = Field(None, max_length=1000000, description="문서 내용")
    summary: Optional[str] = Field(None, max_length=5000, description="문서 요약")

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """
        제목 검증 (Secure: XSS Prevention)
        """
        if not v or not v.strip():
            raise ValueError('문서 제목은 필수입니다')

        # Remove dangerous characters
        dangerous_chars = ['<script', '</script', '<iframe', 'javascript:', 'onerror=']
        v_lower = v.lower()
        for char in dangerous_chars:
            if char in v_lower:
                raise ValueError(f'제목에 허용되지 않는 패턴이 포함되어 있습니다: {char}')

        return v.strip()


class DocumentCreate(DocumentBase):
    """문서 생성 스키마 (메타데이터만, 업로드는 별도 엔드포인트)"""
    document_id: str = Field(..., min_length=1, max_length=100, description="문서 ID")

    @field_validator('document_id')
    @classmethod
    def validate_document_id(cls, v: str) -> str:
        """
        문서 ID 검증 (Secure: 특수문자 제한)
        """
        if not v or not v.strip():
            raise ValueError('문서 ID는 필수입니다')

        # Allow only alphanumeric, dash, underscore
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('문서 ID는 영문, 숫자, 하이픈, 언더스코어만 허용됩니다')

        return v.strip()


class DocumentUpdate(BaseModel):
    """문서 수정 스키마"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    document_type: Optional[DocumentTypeEnum] = None
    status: Optional[DocumentStatusEnum] = None
    category_id: Optional[int] = None
    content: Optional[str] = Field(None, max_length=1000000)
    summary: Optional[str] = Field(None, max_length=5000)


class DocumentResponse(DocumentBase):
    """문서 응답 스키마"""
    id: int
    document_id: str

    # 파일 정보
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None

    # 버전 정보
    current_version: Optional[str] = None

    # 카테고리 정보
    category_name: Optional[str] = Field(None, description="카테고리 이름")

    # 벡터 정보
    vector_info: Optional[DocumentVectorInfo] = Field(None, description="벡터화 정보")

    # 타임스탬프
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """문서 목록 응답 스키마"""
    items: List[DocumentResponse]
    total: int
    page: int
    limit: int


class DocumentUploadRequest(BaseModel):
    """문서 업로드 요청 스키마"""
    title: str = Field(..., min_length=1, max_length=500)
    document_type: DocumentTypeEnum
    category_id: Optional[int] = None
    status: DocumentStatusEnum = Field(DocumentStatusEnum.PENDING)

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """제목 검증"""
        if not v or not v.strip():
            raise ValueError('문서 제목은 필수입니다')
        return v.strip()


class DocumentUploadResponse(BaseModel):
    """문서 업로드 응답 스키마"""
    id: int
    document_id: str
    title: str
    file_name: str
    file_size: int
    mime_type: str
    status: DocumentStatusEnum
    vector_status: VectorStatusEnum
    message: str = Field(..., description="처리 결과 메시지")

    class Config:
        from_attributes = True
