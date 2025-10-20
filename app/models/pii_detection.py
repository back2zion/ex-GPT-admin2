"""
개인정보 검출 결과 모델
PRD_v2.md P0 요구사항: FUN-003
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import enum


class PIIStatus(str, enum.Enum):
    """PII 검출 상태"""
    PENDING = "pending"  # 관리자 확인 대기
    APPROVED = "approved"  # 승인됨 (보관)
    MASKED = "masked"  # 마스킹 처리됨
    DELETED = "deleted"  # 삭제됨


class PIIDetectionResult(Base, TimestampMixin):
    """개인정보 검출 결과"""
    __tablename__ = "pii_detection_results"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False, comment="문서 ID")
    has_pii = Column(Boolean, default=False, comment="개인정보 포함 여부")
    pii_data = Column(Text, comment="검출된 개인정보 (JSON)")
    status = Column(SQLEnum(PIIStatus), default=PIIStatus.PENDING, comment="처리 상태")
    admin_note = Column(Text, comment="관리자 메모")
    processed_by = Column(Integer, ForeignKey('users.id'), comment="처리한 관리자 ID")

    # 관계
    document = relationship("Document", back_populates="pii_detections")
    admin = relationship("User", foreign_keys=[processed_by])
