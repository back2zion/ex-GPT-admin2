from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class DocumentPermissionBase(BaseModel):
    """문서 권한 기본 스키마"""
    document_id: int = Field(..., description="문서 ID")
    department_id: Optional[int] = Field(None, description="부서 ID (부서별 권한)")
    approval_line_id: Optional[int] = Field(None, description="결재라인 ID (결재라인별 권한)")
    can_read: bool = Field(True, description="읽기 권한")
    can_write: bool = Field(False, description="쓰기 권한")
    can_delete: bool = Field(False, description="삭제 권한")


class DocumentPermissionCreate(DocumentPermissionBase):
    """문서 권한 생성 스키마"""
    pass


class DocumentPermissionUpdate(BaseModel):
    """문서 권한 수정 스키마"""
    department_id: Optional[int] = None
    approval_line_id: Optional[int] = None
    can_read: Optional[bool] = None
    can_write: Optional[bool] = None
    can_delete: Optional[bool] = None


class DepartmentInfo(BaseModel):
    """부서 정보 (문서 권한 응답 시 사용)"""
    id: int
    name: str
    code: str

    class Config:
        from_attributes = True


class ApprovalLineInfo(BaseModel):
    """결재라인 정보 (문서 권한 응답 시 사용)"""
    id: int
    name: str

    class Config:
        from_attributes = True


class DocumentInfo(BaseModel):
    """문서 정보 (문서 권한 응답 시 사용)"""
    id: int
    title: str
    document_id: str
    document_type: str
    status: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentPermissionResponse(DocumentPermissionBase):
    """문서 권한 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    document: Optional[DocumentInfo] = None
    department: Optional[DepartmentInfo] = None
    approval_line: Optional[ApprovalLineInfo] = None

    class Config:
        from_attributes = True
