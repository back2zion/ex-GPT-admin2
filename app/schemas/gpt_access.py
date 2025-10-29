"""
GPT 접근 권한 관리 스키마
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class GPTModel(str, Enum):
    """사용 가능한 GPT 모델 (실제 vLLM에서 사용 중인 모델)"""
    QWEN3_32B = "Qwen3-32B"
    QWEN3_235B_GPTQ = "Qwen3-235B-A22B-GPTQ-Int4"


class AccessRequestStatusEnum(str, Enum):
    """접근 신청 상태"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class UserGPTAccessResponse(BaseModel):
    """사용자 GPT 접근 정보 응답"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    department_name: Optional[str] = None
    gpt_access_granted: bool
    allowed_model: Optional[str] = None
    last_login_at: Optional[datetime] = None
    is_active: bool

    # 도로공사 조직 정보
    employee_number: Optional[str] = None
    position: Optional[str] = None
    rank: Optional[str] = None
    team: Optional[str] = None
    job_category: Optional[str] = None

    class Config:
        from_attributes = True


class UsersListResponse(BaseModel):
    """사용자 목록 응답"""
    users: List[UserGPTAccessResponse]
    total: int


class GrantAccessRequest(BaseModel):
    """GPT 접근 권한 부여 요청"""
    user_ids: List[int] = Field(..., description="권한을 부여할 사용자 ID 목록")
    model: str = Field(..., description="할당할 모델명 (Qwen235B, Qwen32B, 70B 등)")


class RevokeAccessRequest(BaseModel):
    """GPT 접근 권한 회수 요청"""
    user_ids: List[int] = Field(..., description="권한을 회수할 사용자 ID 목록")


class GrantAccessResponse(BaseModel):
    """GPT 접근 권한 부여 응답"""
    granted_count: int
    message: str


class RevokeAccessResponse(BaseModel):
    """GPT 접근 권한 회수 응답"""
    revoked_count: int
    message: str


class AccessRequestResponse(BaseModel):
    """접근 신청 응답"""
    id: int
    user_id: int
    username: str
    full_name: Optional[str] = None
    department_name: Optional[str] = None
    status: str
    requested_at: datetime
    processed_at: Optional[datetime] = None
    processor_name: Optional[str] = None
    reject_reason: Optional[str] = None

    class Config:
        from_attributes = True


class AccessRequestsListResponse(BaseModel):
    """접근 신청 목록 응답"""
    requests: List[AccessRequestResponse]
    total: int


class ApproveRequestRequest(BaseModel):
    """접근 신청 승인 요청"""
    model: str = Field(..., description="할당할 모델명")
    processor_id: int = Field(..., description="처리자 ID")


class RejectRequestRequest(BaseModel):
    """접근 신청 거부 요청"""
    reason: str = Field(..., description="거부 사유")
    processor_id: int = Field(..., description="처리자 ID")


class ProcessRequestResponse(BaseModel):
    """접근 신청 처리 응답"""
    id: int
    status: str
    message: str


class AccessChangeHistoryResponse(BaseModel):
    """권한 변경 이력 응답"""
    id: int
    user_id: int
    username: Optional[str] = None
    full_name: Optional[str] = None
    employee_number: Optional[str] = None
    department_name: Optional[str] = None
    action: str  # grant, revoke, model_change, approve, reject
    changed_by: int
    admin_name: Optional[str] = None
    changed_at: datetime
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    reason: Optional[str] = None

    class Config:
        from_attributes = True


class AccessChangeHistoryListResponse(BaseModel):
    """권한 변경 이력 목록 응답"""
    history: List[AccessChangeHistoryResponse]
    total: int
