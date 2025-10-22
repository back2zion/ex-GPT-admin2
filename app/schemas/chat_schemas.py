"""
Chat Schemas
채팅 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    """채팅 요청 스키마"""
    cnvs_idt_id: str = Field(
        default="",
        description="대화방 ID (빈 스트링 = 새 대화, 기존 ID = 이어가기)"
    )
    message: str = Field(..., description="사용자 질문", min_length=1)
    stream: bool = Field(default=True, description="스트리밍 여부")
    history: List[Dict[str, str]] = Field(default=[], description="대화 이력")
    search_documents: bool = Field(default=False, description="RAG 문서 검색 활성화")
    department: Optional[str] = Field(default=None, description="부서 코드 (문서 필터링)")
    search_scope: Optional[List[str]] = Field(default=None, description="검색 범위 (manual, faq 등)")
    max_context_tokens: int = Field(default=4000, description="최대 컨텍스트 토큰 수")
    temperature: float = Field(default=0.7, description="샘플링 온도", ge=0.0, le=2.0)
    suggest_questions: bool = Field(default=False, description="추천 질문 생성")
    think_mode: bool = Field(default=False, description="추론 모드 (DeepSeek-R1 등)")


class ConversationSummary(BaseModel):
    """대화 요약 (목록용)"""
    cnvs_idt_id: str
    cnvs_smry_txt: str
    reg_dt: Optional[str]


class ConversationListResponse(BaseModel):
    """대화 목록 응답"""
    conversations: List[ConversationSummary]
    total: int


class MessageReference(BaseModel):
    """참조 문서"""
    ref_seq: int
    doc_name: str
    chunk_text: str
    similarity: float


class MessageMetadata(BaseModel):
    """메시지 메타데이터"""
    tokens: int
    search_time_ms: int
    response_time_ms: Optional[int] = None


class ChatMessage(BaseModel):
    """채팅 메시지"""
    cnvs_id: int
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str]
    metadata: MessageMetadata
    references: Optional[List[MessageReference]] = None
    suggested_questions: Optional[List[str]] = None


class HistoryDetailResponse(BaseModel):
    """히스토리 상세 응답"""
    cnvs_idt_id: str
    messages: List[ChatMessage]
    total_messages: int


class RoomNameUpdateRequest(BaseModel):
    """대화명 변경 요청"""
    name: str = Field(..., description="새 대화명", min_length=1, max_length=500)


class FileUploadResponse(BaseModel):
    """파일 업로드 응답"""
    success: bool
    file_uid: str
    filename: str
    size: int
    download_url: str
