"""
배포관리 SQLAlchemy 모델
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, ARRAY
from sqlalchemy.sql import func
from app.models.base import Base


class Deployment(Base):
    """배포 정보 테이블"""

    __tablename__ = "deployments"

    deployment_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_name = Column(String(200), nullable=False, index=True)
    model_uri = Column(String(500), nullable=True)
    framework = Column(String(50), nullable=True, default="vllm")
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
        comment="배포 상태: building, ready, serving, stopped, failed"
    )
    gpu_ids = Column(ARRAY(Integer), nullable=True)
    port = Column(Integer, nullable=True)
    endpoint_url = Column(String(500), nullable=True)
    vllm_config = Column(JSON, nullable=True)
    process_id = Column(Integer, nullable=True, comment="vLLM 서버 프로세스 ID")
    deployed_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Deployment(id={self.deployment_id}, name='{self.model_name}', status='{self.status}')>"
