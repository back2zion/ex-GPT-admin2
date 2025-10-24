from sqlalchemy import Column, Integer, String, Text, Float, JSON, Boolean, DateTime
from app.models.base import Base, TimestampMixin


class UsageHistory(Base, TimestampMixin):
    """
    대화 이력 모델

    사용자와 AI 간의 모든 대화를 저장하는 메인 테이블

    Attributes:
        id: 기본 키 (자동 증가)
        user_id: 사용자 식별자 (최대 100자)
        session_id: 대화 세션 ID (여러 대화를 그룹화)
        conversation_title: 대화 제목 (사이드바 표시용, 최대 200자)
        question: 사용자 질문 (TEXT)
        answer: AI 응답 (TEXT)
        thinking_content: AI 사고 과정 (TEXT, <think> 태그 내용)
        response_time: 응답 시간 (밀리초)
        referenced_documents: 참조 문서 JSON (문서 ID 배열)
        model_name: 사용된 AI 모델명 (예: "ex-GPT")
        usage_metadata: 추가 메타데이터 JSON
        ip_address: 사용자 IP 주소 (IPv6 지원, 최대 45자)
        main_category: 대분류 (경영/기술/기타)
        sub_category: 소분류 (세부 카테고리)
        is_deleted: 소프트 딜리트 플래그 (기본값: False)
        deleted_at: 삭제 시간 (소프트 딜리트 시 기록)
        created_at: 레코드 생성 시간 (TimestampMixin)
        updated_at: 레코드 수정 시간 (TimestampMixin)

    Indexes:
        - user_id (사용자별 조회 최적화)
        - session_id (세션별 조회 최적화)
        - main_category, sub_category (카테고리별 통계)
        - is_deleted (삭제되지 않은 레코드 필터링)

    Notes:
        - 삭제 시 하드 딜리트하지 않고 is_deleted=True로 표시
        - 제목 생성용 세션(title_gen_*)은 별도 처리
        - thinking_content는 사용자에게 보이지 않는 AI 내부 사고 과정
    """
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

    # 소프트 딜리트
    is_deleted = Column(Boolean, nullable=False, server_default='false', comment="소프트 딜리트 플래그")
    deleted_at = Column(DateTime(timezone=True), nullable=True, comment="삭제 시간")
