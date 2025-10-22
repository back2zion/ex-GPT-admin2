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

    # 대화 제목 (첫 질문으로 자동 생성 또는 사용자 지정)
    conversation_title = Column(String(200))

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

    # 질문 분류 (대분류/소분류)
    main_category = Column(String(50), index=True, comment="대분류: 경영분야, 기술분야, 경영/기술 외, 미분류")
    sub_category = Column(String(50), index=True, comment="소분류: 세부 카테고리")
