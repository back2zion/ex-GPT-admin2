from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any


class ApprovalLineBase(BaseModel):
    """결재라인 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=100, description="결재라인명")
    description: Optional[str] = Field(None, max_length=255, description="결재라인 설명")
    departments: Any = Field(default=[], description="부서 ID 리스트 (JSON)")
    approvers: Any = Field(default=[], description="승인자 정보 (JSON)")


class ApprovalLineCreate(ApprovalLineBase):
    """결재라인 생성 스키마

    Example:
        {
            "name": "계약 관련 문서",
            "description": "계약 관련 문서 결재 라인",
            "departments": [1, 2, 5],
            "approvers": [
                {"step": 1, "user_id": "user1", "name": "담당자"},
                {"step": 2, "user_id": "user2", "name": "팀장"},
                {"step": 3, "user_id": "user3", "name": "부서장"}
            ]
        }
    """
    pass


class ApprovalLineUpdate(BaseModel):
    """결재라인 수정 스키마"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    departments: Optional[Any] = None
    approvers: Optional[Any] = None


class ApprovalLineResponse(ApprovalLineBase):
    """결재라인 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
