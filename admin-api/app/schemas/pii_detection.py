"""
PII 검출 스키마
PRD_v2.md P0 요구사항: FUN-003
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.models.pii_detection import PIIStatus


class PIIMatchSchema(BaseModel):
    """PII 매치 정보"""
    type: str = Field(..., description="PII 유형")
    value: str = Field(..., description="검출된 값 (마스킹됨)")
    start_pos: int = Field(..., description="시작 위치")
    end_pos: int = Field(..., description="종료 위치")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도")


class PIIDetectionResultResponse(BaseModel):
    """PII 검출 결과 응답"""
    id: int
    document_id: int
    has_pii: bool
    pii_matches: List[PIIMatchSchema]
    status: PIIStatus
    admin_note: Optional[str] = None
    processed_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PIIApprovalRequest(BaseModel):
    """PII 승인 요청"""
    action: str = Field(..., description="처리 작업 (approve, mask, delete)")
    admin_note: Optional[str] = Field(None, description="관리자 메모")


class PIIDetectionListResponse(BaseModel):
    """PII 검출 목록 응답"""
    total: int
    items: List[PIIDetectionResultResponse]
    page: int
    page_size: int
