"""
문서 변경 요청 스키마
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class DocumentChangeRequestCreate(BaseModel):
    """문서 변경 요청 생성"""
    document_id: int = Field(..., description="문서 ID")
    legacy_id: Optional[str] = Field(None, max_length=100, description="레거시 시스템 문서 ID")
    change_type: str = Field(..., pattern="^(new|modified|deleted)$", description="변경 유형")
    old_data: Optional[Dict[str, Any]] = Field(None, description="변경 전 데이터")
    new_data: Dict[str, Any] = Field(..., description="변경 후 데이터")
    diff_summary: Optional[str] = Field(None, description="변경 요약")


class DocumentChangeRequestResponse(BaseModel):
    """문서 변경 요청 응답"""
    id: int
    document_id: int
    legacy_id: Optional[str] = None
    change_type: str
    old_data: Optional[Dict[str, Any]] = None
    new_data: Optional[Dict[str, Any]] = None
    diff_summary: Optional[str] = None
    status: str
    requester_id: Optional[int] = None
    approved_at: Optional[str] = None
    applied_at: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentChangeRequestListResponse(BaseModel):
    """문서 변경 요청 목록 응답"""
    items: list[DocumentChangeRequestResponse]
    total: int


class ApproveChangeRequest(BaseModel):
    """변경 요청 승인"""
    apply_immediately: bool = Field(True, description="즉시 적용 여부")


class RejectChangeRequest(BaseModel):
    """변경 요청 반려"""
    reason: str = Field(..., max_length=500, description="반려 사유")


class DetectChangesResponse(BaseModel):
    """변경 감지 응답"""
    changes: int = Field(..., description="감지된 변경 수")
    total: int = Field(..., description="전체 문서 수")
