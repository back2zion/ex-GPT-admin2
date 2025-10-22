from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

# 사용자-역할 다대다 관계 테이블
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)


class User(Base, TimestampMixin):
    """사용자 모델"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # 부서 정보
    department_id = Column(Integer, ForeignKey('departments.id'))
    department = relationship("Department", back_populates="users")

    # 역할 (다대다 관계)
    roles = relationship("Role", secondary=user_roles, back_populates="users")

    # GPT 접근 권한 관련
    gpt_access_granted = Column(Boolean, default=False, comment="GPT 접근 허용 여부")
    allowed_model = Column(String(100), nullable=True, comment="허용된 모델명")
    last_login_at = Column(DateTime(timezone=True), nullable=True, comment="마지막 로그인 시간")

    # 조직 및 인사 정보
    employee_number = Column(String(50), unique=True, index=True, comment="사번")
    position = Column(String(50), comment="직급 (예: 사원, 대리, 과장, 차장, 부장)")
    rank = Column(String(50), comment="직위 (예: 팀원, 팀장, 본부장)")
    job_category = Column(String(50), comment="직종 (예: 사무, 기술, 관리)")
    team = Column(String(100), comment="팀명/부서명")
    join_year = Column(Integer, comment="입사년도")

    # 관계 (역참조)
    access_requests = relationship("AccessRequest", foreign_keys="AccessRequest.user_id", back_populates="user")
    document_permissions = relationship("UserDocumentPermission", back_populates="user")
