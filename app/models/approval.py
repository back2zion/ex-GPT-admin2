"""
Approval Models
승인 워크플로우 모델
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.models.base import Base, TimestampMixin


class ChangeType(str, enum.Enum):
    """변경 유형"""
    NEW = "new"  # 신규
    MODIFIED = "modified"  # 수정
    DELETED = "deleted"  # 삭제


class RequestStatus(str, enum.Enum):
    """요청 상태"""
    PENDING = "pending"  # 승인 대기
    APPROVED = "approved"  # 승인됨
    REJECTED = "rejected"  # 반려됨
    COMPLETED = "completed"  # 적용 완료


class ApprovalStatus(str, enum.Enum):
    """승인 단계 상태"""
    PENDING = "pending"  # 대기
    APPROVED = "approved"  # 승인
    REJECTED = "rejected"  # 반려
    SKIPPED = "skipped"  # 건너뜀


class DocumentChangeRequest(Base, TimestampMixin):
    """문서 변경 요청 모델"""
    __tablename__ = "document_change_requests"

    id = Column(Integer, primary_key=True, index=True)

    # 문서 정보
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    legacy_id = Column(String(100))  # 레거시 DB 문서 ID

    # 변경 유형
    change_type = Column(String(20), nullable=False)

    # 변경 데이터
    old_data = Column(JSON)  # 기존 데이터
    new_data = Column(JSON)  # 새 데이터
    diff_summary = Column(Text)  # Diff 요약

    # 상태
    status = Column(String(20), default="pending")

    # 요청자 (시스템 자동 생성 시 NULL)
    requester_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    # 승인 완료 시각
    approved_at = Column(String(50), nullable=True)
    applied_at = Column(String(50), nullable=True)  # 실제 적용 시각

    # 관계
    document = relationship("Document", backref="change_requests")
    requester = relationship("User", backref="change_requests", foreign_keys=[requester_id])
    approval_steps = relationship("ApprovalStep", back_populates="change_request", cascade="all, delete-orphan")


class ApprovalStep(Base, TimestampMixin):
    """승인 단계 모델"""
    __tablename__ = "approval_steps"

    id = Column(Integer, primary_key=True, index=True)

    # 변경 요청
    change_request_id = Column(Integer, ForeignKey('document_change_requests.id'), nullable=False)

    # 승인 단계
    level = Column(Integer, nullable=False)  # 1, 2, 3...

    # 승인자
    approver_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    approver_name = Column(String(100))  # 승인자 이름 (캐시)

    # 상태
    status = Column(String(20), default="pending")

    # 승인/반려 정보
    approved_at = Column(String(50), nullable=True)
    comment = Column(Text, nullable=True)

    # 관계
    change_request = relationship("DocumentChangeRequest", back_populates="approval_steps")
    approver = relationship("User", foreign_keys=[approver_id])
