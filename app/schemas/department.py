from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class DepartmentBase(BaseModel):
    """부서 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=100, description="부서명")
    code: str = Field(..., min_length=1, max_length=50, description="부서 코드")
    description: Optional[str] = Field(None, max_length=255, description="부서 설명")
    parent_id: Optional[int] = Field(None, description="상위 부서 ID")


class DepartmentCreate(DepartmentBase):
    """부서 생성 스키마"""
    pass


class DepartmentUpdate(BaseModel):
    """부서 수정 스키마"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    parent_id: Optional[int] = None


class DepartmentResponse(DepartmentBase):
    """부서 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DepartmentTreeResponse(DepartmentResponse):
    """부서 트리 구조 응답 스키마"""
    children: List['DepartmentTreeResponse'] = []

    class Config:
        from_attributes = True


# 순환 참조 문제 해결
DepartmentTreeResponse.model_rebuild()
