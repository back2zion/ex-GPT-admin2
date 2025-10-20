"""
사용자별 문서 권한 스키마
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class UserDocumentPermissionCreate(BaseModel):
    """사용자 문서 권한 생성 요청"""
    user_id: int = Field(..., description="사용자 ID")
    department_ids: List[int] = Field(..., description="접근 가능한 부서 ID 목록")


class UserDocumentPermissionResponse(BaseModel):
    """사용자 문서 권한 응답"""
    id: int
    user_id: int
    department_id: int
    department_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserWithDocPermissionsResponse(BaseModel):
    """문서 권한 포함 사용자 응답"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    department_name: Optional[str] = None
    doc_permissions: List[str] = Field(default_factory=list, description="접근 가능한 부서 목록")

    class Config:
        from_attributes = True


class UsersListWithDocPermissionsResponse(BaseModel):
    """사용자 목록 응답 (문서 권한 포함)"""
    users: List[UserWithDocPermissionsResponse]
    total: int


class GrantDocPermissionRequest(BaseModel):
    """문서 권한 부여 요청"""
    user_id: int = Field(..., description="사용자 ID")
    department_ids: List[int] = Field(..., description="접근 가능한 부서 ID 목록")


class GrantDocPermissionResponse(BaseModel):
    """문서 권한 부여 응답"""
    granted_count: int
    message: str


class RevokeDocPermissionResponse(BaseModel):
    """문서 권한 회수 응답"""
    revoked_count: int
    message: str
