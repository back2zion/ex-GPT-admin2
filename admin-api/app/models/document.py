from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import enum


class DocumentType(str, enum.Enum):
    """문서 타입"""
    LAW = "law"  # 법령
    REGULATION = "regulation"  # 사규
    STANDARD = "standard"  # 업무기준
    MANUAL = "manual"  # 매뉴얼
    OTHER = "other"  # 기타


class DocumentStatus(str, enum.Enum):
    """문서 상태"""
    ACTIVE = "active"  # 활성
    PENDING = "pending"  # 승인 대기
    ARCHIVED = "archived"  # 보관
    DELETED = "deleted"  # 삭제


class Document(Base, TimestampMixin):
    """문서 모델"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING)

    # 레거시 시스템 정보
    legacy_id = Column(String(100), index=True)
    legacy_updated_at = Column(String(50))

    # 문서 내용
    content = Column(Text)
    summary = Column(Text)
    doc_metadata = Column(JSON)  # 'metadata'는 SQLAlchemy 예약어

    # 버전 관리
    current_version = Column(String(20), default="1.0")

    # 파일 정보 (MinIO)
    file_path = Column(String(500))  # MinIO 객체 경로
    file_name = Column(String(500))  # 원본 파일명
    file_size = Column(Integer)  # 파일 크기 (bytes)
    mime_type = Column(String(200))  # MIME 타입

    # 카테고리 (학습데이터 관리)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True, index=True)

    # 관계
    category = relationship("Category", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document")
    changes = relationship("DocumentChange", back_populates="document")
    permissions = relationship("DocumentPermission", back_populates="document")
    pii_detections = relationship("PIIDetectionResult", back_populates="document")
    vectors = relationship("DocumentVector", back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(Base, TimestampMixin):
    """문서 버전 모델"""
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    version = Column(String(20), nullable=False)
    content = Column(Text)
    change_summary = Column(Text)
    changed_by = Column(String(100))

    # 관계
    document = relationship("Document", back_populates="versions")


class DocumentChange(Base, TimestampMixin):
    """문서 변경 이력 모델"""
    __tablename__ = "document_changes"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    change_type = Column(String(50))  # created, updated, deleted
    old_content = Column(Text)
    new_content = Column(Text)
    diff = Column(Text)  # 변경 차이점
    approved = Column(Boolean, default=False)
    approved_by = Column(String(100))
    approved_at = Column(String(50))

    # 관계
    document = relationship("Document", back_populates="changes")
