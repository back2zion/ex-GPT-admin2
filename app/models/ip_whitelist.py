"""
IP 접근 권한 모델
adminpage.txt: 8. 설정 > 1) 관리자관리>IP접근권한 관리
"""
from sqlalchemy import Column, Integer, String, Boolean
from app.models.base import Base, TimestampMixin


class IPWhitelist(Base, TimestampMixin):
    """IP 화이트리스트"""
    __tablename__ = "ip_whitelist"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), unique=True, nullable=False, index=True, comment="IP 주소 (IPv4/IPv6)")
    description = Column(String(255), comment="설명")
    is_allowed = Column(Boolean, default=True, comment="액세스 허용 여부")
    created_by = Column(Integer, comment="등록한 관리자 ID")
