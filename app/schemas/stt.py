"""
STT 시스템 Pydantic 스키마
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================
# STT Batch 스키마
# ============================================

class STTBatchCreate(BaseModel):
    """STT 배치 생성 요청"""
    name: str = Field(..., min_length=1, max_length=255, description="배치 작업 이름")
    description: Optional[str] = Field(None, description="배치 작업 설명")
    source_path: str = Field(..., min_length=1, max_length=500, description="음성파일 경로")
    file_pattern: str = Field(default="*.mp3", max_length=100, description="파일 패턴")
    priority: str = Field(default="normal", description="우선순위")
    notify_emails: Optional[List[str]] = Field(None, description="알림 이메일 목록")

    @validator('priority')
    def validate_priority(cls, v):
        valid = ["low", "normal", "high", "urgent"]
        if v not in valid:
            raise ValueError(f"priority must be one of {valid}")
        return v


class STTBatchUpdate(BaseModel):
    """STT 배치 수정 요청"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    notify_emails: Optional[List[str]] = None

    @validator('status')
    def validate_status(cls, v):
        if v is None:
            return v
        valid = ["pending", "processing", "completed", "failed", "paused"]
        if v not in valid:
            raise ValueError(f"status must be one of {valid}")
        return v

    @validator('priority')
    def validate_priority(cls, v):
        if v is None:
            return v
        valid = ["low", "normal", "high", "urgent"]
        if v not in valid:
            raise ValueError(f"priority must be one of {valid}")
        return v


class STTBatchResponse(BaseModel):
    """STT 배치 응답"""
    id: int
    name: str
    description: Optional[str]
    source_path: str
    file_pattern: str
    total_files: int
    status: str
    priority: str
    completed_files: int
    failed_files: int
    avg_processing_time: Optional[float]
    estimated_duration: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: str
    notify_emails: Optional[List[str]]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class STTBatchProgressResponse(BaseModel):
    """배치 진행 상황 응답"""
    batch_id: int
    status: str
    total_files: int
    completed: int
    failed: int
    pending: int
    progress_percentage: float
    avg_processing_time: Optional[float]
    estimated_completion: Optional[datetime]


# ============================================
# STT Transcription 스키마
# ============================================

class STTTranscriptionResponse(BaseModel):
    """전사 결과 응답"""
    id: int
    batch_id: int
    audio_file_path: str
    audio_file_size: Optional[int]
    audio_duration: Optional[float]
    transcription_text: str
    transcription_confidence: Optional[float]
    language_code: str
    speaker_labels: Optional[Dict[str, str]]
    segments: Optional[List[Dict[str, Any]]]
    processing_duration: Optional[float]
    stt_engine: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================
# STT Summary 스키마
# ============================================

class STTSummaryResponse(BaseModel):
    """요약 응답"""
    id: int
    transcription_id: int
    summary_text: str
    summary_level: str
    keywords: Optional[List[str]]
    action_items: Optional[List[Dict[str, Any]]]
    meeting_title: Optional[str]
    meeting_date: Optional[datetime]
    attendees: Optional[List[str]]
    llm_model: Optional[str]
    tokens_used: Optional[int]
    generation_duration: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================
# STT Email Log 스키마
# ============================================

class STTEmailLogResponse(BaseModel):
    """이메일 로그 응답"""
    id: int
    summary_id: int
    recipient_email: str
    recipient_name: Optional[str]
    cc_emails: Optional[List[str]]
    subject: Optional[str]
    status: str
    sent_at: Optional[datetime]
    delivery_status: Optional[str]
    error_message: Optional[str]
    retry_count: int
    email_provider: Optional[str]
    message_id: Optional[str]
    attachments: Optional[List[Dict[str, str]]]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
