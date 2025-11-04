"""
알림 모델
PRD FUN-002: 제·개정 문서 알림
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class Notification(Base, TimestampMixin):
    """알림 모델"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    # 알림 유형
    type = Column(
        String(20),
        nullable=False,
        comment="알림 유형: success, error, info, warning"
    )

    # 알림 카테고리
    category = Column(
        String(50),
        nullable=False,
        comment="알림 카테고리: document_update, system, deployment, stt_batch"
    )

    # 알림 내용
    title = Column(String(200), nullable=False, comment="알림 제목")
    message = Column(Text, nullable=False, comment="알림 메시지")
    link = Column(String(500), nullable=True, comment="관련 페이지 링크")

    # 읽음 상태
    is_read = Column(Boolean, default=False, comment="읽음 여부")
    read_at = Column(DateTime(timezone=True), nullable=True, comment="읽은 시간")

    # 대상 사용자 (NULL이면 전체 관리자)
    user_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=True,
        comment="특정 사용자 ID (NULL이면 전체)"
    )

    # 관련 엔티티
    related_entity_type = Column(
        String(50),
        nullable=True,
        comment="관련 엔티티 타입 (document, batch 등)"
    )
    related_entity_id = Column(
        Integer,
        nullable=True,
        comment="관련 엔티티 ID"
    )

    # 관계
    user = relationship("User", foreign_keys=[user_id])
