from sqlalchemy import Column, Integer, String, Text, Float, JSON
from app.models.base import Base, TimestampMixin


class UsageHistory(Base, TimestampMixin):
    """사용 이력 모델"""
    __tablename__ = "usage_history"

    id = Column(Integer, primary_key=True, index=True)

    # 사용자 정보 (MVP: String으로 단순화)
    user_id = Column(String(100), nullable=False, index=True)

    # 세션 정보
    session_id = Column(String(100), index=True)

    # 질문/답변
    question = Column(Text, nullable=False)
    answer = Column(Text)

    # 추론 내용 (Think 토큰)
    thinking_content = Column(Text)

    # 응답 시간 (밀리초)
    response_time = Column(Float)

    # 참조 문서
    referenced_documents = Column(JSON)  # 문서 ID 리스트

    # 모델 정보
    model_name = Column(String(100))

    # 추가 메타데이터
    usage_metadata = Column(JSON)  # 'metadata'는 SQLAlchemy 예약어

    # IP 주소
    ip_address = Column(String(45))
