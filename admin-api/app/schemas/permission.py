from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class PermissionBase(BaseModel):
    """권한 기본 스키마"""
    resource: str = Field(..., min_length=1, max_length=100, description="리소스 (document, notice, user 등)")
    action: str = Field(..., min_length=1, max_length=50, description="작업 (read, write, delete 등)")
    description: Optional[str] = Field(None, max_length=255, description="권한 설명")


class PermissionCreate(PermissionBase):
    """권한 생성 스키마"""
    pass


class PermissionUpdate(BaseModel):
    """권한 수정 스키마"""
    resource: Optional[str] = Field(None, min_length=1, max_length=100)
    action: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)


class PermissionResponse(PermissionBase):
    """권한 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
