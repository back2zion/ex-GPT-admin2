"""
문서 접근 권한 관련 모델
NOTE: This is a future model design. Current database uses simpler structure.
For now, we keep backward compatibility with existing schema.
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class ApprovalLine(Base, TimestampMixin):
    """결재라인 모델 (레거시 구조 유지)"""
    __tablename__ = "approval_lines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    departments = Column(JSON, nullable=True)  # 부서 ID 리스트
    approvers = Column(JSON, nullable=True)  # 승인자 정보

    # 관계
    document_permissions = relationship("DocumentPermission", back_populates="approval_line")


class DocumentPermission(Base, TimestampMixin):
    """문서별 접근 권한 모델 (레거시 구조 유지)"""
    __tablename__ = "document_permissions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)

    # 권한 대상
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=True)
    approval_line_id = Column(Integer, ForeignKey('approval_lines.id'), nullable=True)

    # 권한 설정
    can_read = Column(Boolean, default=True)
    can_write = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)

    # 관계
    document = relationship("Document", back_populates="permissions")
    department = relationship("Department")
    approval_line = relationship("ApprovalLine", back_populates="document_permissions")


class UserDocumentPermission(Base, TimestampMixin):
    """사용자별 부서 문서 권한 모델"""
    __tablename__ = "user_document_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment="사용자 ID")
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False, comment="접근 가능 부서 ID")

    # 관계
    user = relationship("User", back_populates="document_permissions")
    department = relationship("Department")
