from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class RoleBase(BaseModel):
    """역할 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=50, description="역할명")
    description: Optional[str] = Field(None, max_length=255, description="역할 설명")
    is_active: bool = Field(True, description="활성화 여부")


class RoleCreate(RoleBase):
    """역할 생성 스키마"""
    permission_ids: List[int] = Field(default=[], description="권한 ID 목록")


class RoleUpdate(BaseModel):
    """역할 수정 스키마"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    permission_ids: Optional[List[int]] = None


class PermissionInfo(BaseModel):
    """권한 정보 (역할 응답 시 사용)"""
    id: int
    resource: str
    action: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class RoleResponse(RoleBase):
    """역할 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    permissions: List[PermissionInfo] = []

    class Config:
        from_attributes = True
