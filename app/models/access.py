"""
GPT 접근 권한 관련 모델
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import enum


class AccessRequestStatus(str, enum.Enum):
    """접근 신청 상태"""
    PENDING = "pending"  # 신청
    APPROVED = "approved"  # 승인
    REJECTED = "rejected"  # 거부


class AccessRequest(Base, TimestampMixin):
    """GPT 접근 신청 모델"""
    __tablename__ = "access_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment="신청 사용자")
    status = Column(
        SQLEnum(AccessRequestStatus),
        default=AccessRequestStatus.PENDING,
        nullable=False,
        comment="신청 상태"
    )
    requested_at = Column(DateTime(timezone=True), nullable=False, comment="신청 일시")
    processed_at = Column(DateTime(timezone=True), nullable=True, comment="처리 일시")
    processed_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment="처리자")
    reject_reason = Column(String(500), nullable=True, comment="거부 사유")

    # 관계
    user = relationship("User", foreign_keys=[user_id], back_populates="access_requests")
    processor = relationship("User", foreign_keys=[processed_by])
