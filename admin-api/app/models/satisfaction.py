from sqlalchemy import Column, Integer, String, Text, Enum, JSON
from app.models.base import Base, TimestampMixin
import enum


class SurveyCategory(str, enum.Enum):
    """만족도 조사 카테고리"""
    UI = "ui"
    SPEED = "speed"
    ACCURACY = "accuracy"
    OTHER = "other"


class SatisfactionSurvey(Base, TimestampMixin):
    """만족도 조사 모델"""
    __tablename__ = "satisfaction_surveys"

    id = Column(Integer, primary_key=True, index=True)

    # 사용자 정보 (MVP: String으로 단순화)
    user_id = Column(String(100), nullable=False, index=True)

    # 평가 점수 (1-5)
    rating = Column(Integer, nullable=False)

    # 피드백
    feedback = Column(Text)

    # 카테고리
    category = Column(Enum(SurveyCategory), nullable=True)

    # 관련 질문 ID (선택사항, String으로 저장)
    related_question_id = Column(String(100), nullable=True)

    # 추가 메타데이터
    survey_metadata = Column(JSON)  # 'metadata'는 SQLAlchemy 예약어

    # IP 주소
    ip_address = Column(String(45))
