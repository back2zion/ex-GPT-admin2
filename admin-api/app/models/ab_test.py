"""
A/B 테스트 관련 데이터베이스 모델
"""
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    TIMESTAMP, ForeignKey
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.models.base import Base


class ABExperiment(Base):
    """A/B 테스트 실험"""
    __tablename__ = "ab_experiments"

    id = Column(Integer, primary_key=True, index=True)
    experiment_name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)
    model_a_id = Column(Integer, ForeignKey("model_registry.id"))
    model_b_id = Column(Integer, ForeignKey("model_registry.id"))
    traffic_split = Column(JSONB, default={"a": 0.5, "b": 0.5})
    status = Column(String(50), default='running', index=True)
        # running, completed, stopped
    start_date = Column(TIMESTAMP, server_default=func.now())
    end_date = Column(TIMESTAMP)
    target_samples = Column(Integer, default=200)  # 최소 샘플 수
    success_metric = Column(String(100), default='user_rating')
    created_by = Column(Integer, ForeignKey("users.id"))

    __table_args__ = (
        {"comment": "A/B 테스트 실험"}
    )


class ABTestLog(Base):
    """A/B 테스트 로그"""
    __tablename__ = "ab_test_logs"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("ab_experiments.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(String(255), index=True)
    variant = Column(String(10))  # 'a' or 'b'
    model_id = Column(Integer, ForeignKey("model_registry.id"))
    query = Column(Text)
    response = Column(Text)
    response_time_ms = Column(Integer)
    user_rating = Column(Integer)  # 1-5
    user_feedback = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)

    __table_args__ = (
        {"comment": "A/B 테스트 로그"}
    )


class ABTestResult(Base):
    """A/B 테스트 결과"""
    __tablename__ = "ab_test_results"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("ab_experiments.id", ondelete="CASCADE"))
    variant = Column(String(10))  # 'a' or 'b'
    total_samples = Column(Integer)
    avg_rating = Column(Float)
    avg_response_time_ms = Column(Float)
    confidence_interval = Column(JSONB)  # {lower: 4.1, upper: 4.5}
    statistical_significance = Column(Boolean)
    winner = Column(Boolean)
    calculated_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        {"comment": "A/B 테스트 결과 (통계)"}
    )
