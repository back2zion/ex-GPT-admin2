"""
STT 음성 전사 시스템 데이터베이스 모델
"""
from sqlalchemy import Column, Integer, String, Text, Float, BigInteger, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class STTBatch(Base):
    """
    STT 배치 작업 테이블
    - 500만건의 음성파일을 배치 단위로 관리
    - 진행 상황 추적
    """
    __tablename__ = "stt_batches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="배치 작업 이름")
    description = Column(Text, comment="배치 작업 설명")

    # 소스 파일 정보
    source_path = Column(String(500), nullable=False, comment="음성파일 경로 (S3/MinIO/로컬)")
    file_pattern = Column(String(100), default="*.mp3", comment="파일 패턴 (예: *.mp3, *.wav)")
    total_files = Column(Integer, default=0, comment="총 파일 개수")

    # 배치 상태
    status = Column(
        String(20),
        default="pending",
        nullable=False,
        comment="배치 상태: pending, processing, completed, failed, paused"
    )
    priority = Column(String(10), default="normal", comment="우선순위: low, normal, high, urgent")

    # 진행 상황
    completed_files = Column(Integer, default=0, comment="완료된 파일 수")
    failed_files = Column(Integer, default=0, comment="실패한 파일 수")
    avg_processing_time = Column(Float, comment="평균 처리 시간 (초)")

    # 예상 시간
    estimated_duration = Column(Integer, comment="예상 소요 시간 (초)")
    started_at = Column(DateTime, comment="시작 시간")
    completed_at = Column(DateTime, comment="완료 시간")

    # 메타데이터
    created_by = Column(String(100), nullable=False, comment="생성자 (user_id)")
    notify_emails = Column(ARRAY(String), comment="알림 받을 이메일 목록")
    config = Column(JSONB, comment="배치 설정 (JSON)")

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    transcriptions = relationship("STTTranscription", back_populates="batch", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<STTBatch(id={self.id}, name='{self.name}', status='{self.status}', progress={self.progress_percentage}%)>"

    @property
    def progress_percentage(self) -> float:
        """진행률 계산 (0.0 ~ 100.0)"""
        if self.total_files == 0:
            return 0.0
        return (self.completed_files / self.total_files) * 100.0


class STTTranscription(Base):
    """
    STT 전사 결과 테이블
    - 개별 음성파일의 전사 결과 저장
    - 화자 분리, 타임스탬프 지원
    """
    __tablename__ = "stt_transcriptions"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("stt_batches.id", ondelete="CASCADE"), nullable=False, index=True)

    # 원본 음성파일 정보
    audio_file_path = Column(String(500), nullable=False, unique=True, index=True, comment="음성파일 경로")
    audio_file_size = Column(BigInteger, comment="파일 크기 (bytes)")
    audio_duration = Column(Float, comment="음성 길이 (초)")

    # 전사 결과
    transcription_text = Column(Text, nullable=False, comment="전사된 텍스트")
    transcription_confidence = Column(Float, comment="전사 신뢰도 (0.0 ~ 1.0)")
    language_code = Column(String(10), default="ko-KR", comment="언어 코드")

    # 화자 분리 (Speaker Diarization)
    speaker_labels = Column(JSONB, comment='화자 레이블 매핑 (예: {"speaker_1": "홍길동"})')
    segments = Column(
        JSONB,
        comment='타임스탬프 세그먼트 (예: [{"start": 0.0, "end": 5.2, "speaker": "speaker_1", "text": "..."}])'
    )

    # 처리 정보
    processing_duration = Column(Float, comment="처리 소요 시간 (초)")
    stt_engine = Column(String(50), comment="STT 엔진 (예: whisper-large-v3, google-stt)")
    status = Column(String(20), default="pending", comment="상태: pending, processing, success, failed, partial")
    error_message = Column(Text, comment="에러 메시지")

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    batch = relationship("STTBatch", back_populates="transcriptions")
    summaries = relationship("STTSummary", back_populates="transcription", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<STTTranscription(id={self.id}, file='{self.audio_file_path}', status='{self.status}')>"


class STTSummary(Base):
    """
    STT 요약 테이블
    - 전사된 텍스트를 LLM으로 요약
    - 회의록 생성
    """
    __tablename__ = "stt_summaries"

    id = Column(Integer, primary_key=True, index=True)
    transcription_id = Column(
        Integer,
        ForeignKey("stt_transcriptions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # 요약 내용
    summary_text = Column(Text, nullable=False, comment="요약 텍스트")
    summary_level = Column(String(20), default="normal", comment="요약 레벨: brief, normal, detailed")
    keywords = Column(ARRAY(String), comment="핵심 키워드 배열")
    action_items = Column(
        JSONB,
        comment='액션 아이템 (예: [{"task": "...", "assignee": "홍길동", "due_date": "2025-11-01"}])'
    )

    # 회의록 정보
    meeting_title = Column(String(255), comment="회의 제목")
    meeting_date = Column(DateTime, comment="회의 날짜")
    attendees = Column(ARRAY(String), comment="참석자 목록")

    # LLM 생성 정보
    llm_model = Column(String(50), comment="사용된 LLM 모델 (예: gpt-4-turbo, claude-3-opus)")
    tokens_used = Column(Integer, comment="사용된 토큰 수")
    generation_duration = Column(Float, comment="요약 생성 소요 시간 (초)")

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    transcription = relationship("STTTranscription", back_populates="summaries")
    email_logs = relationship("STTEmailLog", back_populates="summary", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<STTSummary(id={self.id}, transcription_id={self.transcription_id}, level='{self.summary_level}')>"


class STTEmailLog(Base):
    """
    STT 이메일 송출 로그 테이블
    - 회의록 이메일 발송 내역 추적
    - 누구에게 보냈는지 기록
    """
    __tablename__ = "stt_email_logs"

    id = Column(Integer, primary_key=True, index=True)
    summary_id = Column(Integer, ForeignKey("stt_summaries.id", ondelete="CASCADE"), nullable=False, index=True)

    # 수신자 정보
    recipient_email = Column(String(255), nullable=False, index=True, comment="수신자 이메일")
    recipient_name = Column(String(100), comment="수신자 이름")
    cc_emails = Column(ARRAY(String), comment="참조(CC) 이메일 목록")
    subject = Column(String(500), comment="이메일 제목")

    # 발송 상태
    status = Column(
        String(20),
        default="pending",
        nullable=False,
        comment="상태: pending, sent, failed, bounced"
    )
    sent_at = Column(DateTime, comment="발송 시간")
    delivery_status = Column(String(50), comment="배달 상태: delivered, opened, clicked, bounced")
    error_message = Column(Text, comment="에러 메시지")
    retry_count = Column(Integer, default=0, comment="재시도 횟수")

    # 이메일 제공자 정보
    email_provider = Column(String(50), comment="이메일 제공자 (smtp, sendgrid, aws-ses)")
    message_id = Column(String(255), comment="이메일 서비스 제공자 Message ID")

    # 첨부파일
    attachments = Column(JSONB, comment='첨부파일 정보 (예: [{"filename": "회의록.pdf", "path": "s3://..."}])')

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    summary = relationship("STTSummary", back_populates="email_logs")

    def __repr__(self):
        return f"<STTEmailLog(id={self.id}, recipient='{self.recipient_email}', status='{self.status}')>"
