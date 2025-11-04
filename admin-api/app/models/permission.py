"""
역할 및 부서 관리 모델
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

# 역할-권한 다대다 관계 테이블
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)


class Role(Base, TimestampMixin):
    """역할 모델"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    is_active = Column(Boolean, default=True)

    # 사용자 (다대다 관계)
    users = relationship("User", secondary="user_roles", back_populates="roles")

    # 권한 (다대다 관계)
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")


class Permission(Base, TimestampMixin):
    """권한 모델"""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    resource = Column(String(100), nullable=False)  # document, user, notice 등
    action = Column(String(50), nullable=False)  # read, write, delete 등
    description = Column(String(255))

    # 역할 (다대다 관계)
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


class Department(Base, TimestampMixin):
    """부서 모델"""
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    parent_id = Column(Integer, ForeignKey('departments.id'), nullable=True)

    # 계층 구조
    parent = relationship("Department", remote_side=[id], backref="children")

    # 사용자
    users = relationship("User", back_populates="department")
