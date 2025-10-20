from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List


class UserBase(BaseModel):
    """사용자 기본 스키마"""
    username: str = Field(..., min_length=3, max_length=50, description="사용자명")
    email: EmailStr = Field(..., description="이메일")
    full_name: Optional[str] = Field(None, max_length=100, description="전체 이름")
    department_id: Optional[int] = Field(None, description="부서 ID")
    is_active: bool = Field(True, description="활성화 여부")


class UserCreate(UserBase):
    """사용자 생성 스키마"""
    password: str = Field(..., min_length=8, description="비밀번호")
    role_ids: List[int] = Field(default=[], description="역할 ID 목록")


class UserUpdate(BaseModel):
    """사용자 수정 스키마"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    department_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class RoleInfo(BaseModel):
    """역할 정보 (사용자 응답 시 사용)"""
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class DepartmentInfo(BaseModel):
    """부서 정보 (사용자 응답 시 사용)"""
    id: int
    name: str
    code: str

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    """사용자 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    roles: List[RoleInfo] = []
    department: Optional[DepartmentInfo] = None

    class Config:
        from_attributes = True


class UserRoleAssignment(BaseModel):
    """사용자-역할 매핑 스키마"""
    role_ids: List[int] = Field(..., description="할당할 역할 ID 목록")
