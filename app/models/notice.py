from sqlalchemy import Column, Integer, String, Text, Boolean, Enum, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import enum


class NoticePriority(str, enum.Enum):
    """공지사항 우선순위"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notice(Base, TimestampMixin):
    """공지사항 모델"""
    __tablename__ = "notices"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    priority = Column(Enum(NoticePriority), default=NoticePriority.NORMAL)

    # 활성화 상태
    is_active = Column(Boolean, default=True)
    is_important = Column(Boolean, default=False)  # 중요 공지 여부
    is_popup = Column(Boolean, default=False)  # 팝업 표시 여부

    # 대상 사용자 (null이면 전체)
    target_users = Column(JSON)  # 사용자 ID 리스트
    target_departments = Column(JSON)  # 부서 ID 리스트

    # 표시 기간
    start_date = Column(String(50))
    end_date = Column(String(50))

    # 작성자
    created_by = Column(String(100))

    # 조회 수
    view_count = Column(Integer, default=0)
