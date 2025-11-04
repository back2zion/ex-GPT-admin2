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


class AccessChangeAction(str, enum.Enum):
    """권한 변경 액션"""
    GRANT = "grant"  # 권한 부여
    REVOKE = "revoke"  # 권한 회수
    MODEL_CHANGE = "model_change"  # 모델 변경
    APPROVE = "approve"  # 신청 승인
    REJECT = "reject"  # 신청 거부


class AccessChangeHistory(Base, TimestampMixin):
    """GPT 접근 권한 변경 이력 (감사 로그)"""
    __tablename__ = "access_change_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment="대상 사용자")
    action = Column(
        SQLEnum(AccessChangeAction, create_constraint=False, native_enum=False, length=50),
        nullable=False,
        comment="수행 액션"
    )
    changed_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment="변경 수행자 (관리자)")
    changed_at = Column(DateTime(timezone=True), nullable=False, comment="변경 일시")

    # 변경 내용 상세
    old_value = Column(String(200), nullable=True, comment="이전 값 (모델명 등)")
    new_value = Column(String(200), nullable=True, comment="새 값 (모델명 등)")
    reason = Column(String(500), nullable=True, comment="변경 사유")

    # 관계
    user = relationship("User", foreign_keys=[user_id])
    admin = relationship("User", foreign_keys=[changed_by])
