"""
Fine-tuning MLOps 관련 데이터베이스 모델
"""
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    TIMESTAMP, ForeignKey, ARRAY
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.models.base import Base


class TrainingDataset(Base):
    """학습 데이터셋"""
    __tablename__ = "training_datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    description = Column(Text)
    format = Column(String(50), default='jsonl')  # jsonl, json, parquet, csv
    file_path = Column(Text, nullable=False)  # /data/datasets/dataset_v1.jsonl
    preprocessed_path = Column(Text)  # 전처리된 파일 경로 (Axolotl 형식)
    total_samples = Column(Integer)
    train_samples = Column(Integer)
    val_samples = Column(Integer)
    test_samples = Column(Integer)
    avg_instruction_length = Column(Float)  # 평균 instruction 길이
    avg_output_length = Column(Float)  # 평균 output 길이
    dataset_metadata = Column(JSONB)  # 통계 정보
    quality_score = Column(Float)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, onupdate=func.now())  # 업데이트 시간
    status = Column(String(50), default='active')  # active, deprecated, archived

    __table_args__ = (
        {"comment": "Fine-tuning용 학습 데이터셋"}
    )


class DatasetQualityLog(Base):
    """데이터셋 품질 검증 로그"""
    __tablename__ = "dataset_quality_logs"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("training_datasets.id", ondelete="CASCADE"))
    check_type = Column(String(100))  # pii_detection, duplicate_check, quality_score
    passed = Column(Boolean)
    issues = Column(JSONB)  # 발견된 문제점 목록
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        {"comment": "데이터셋 품질 검증 로그"}
    )


class FinetuningJob(Base):
    """Fine-tuning 작업"""
    __tablename__ = "finetuning_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String(255), unique=True, nullable=False, index=True)
    base_model = Column(String(255), nullable=False)  # Qwen/Qwen3-7B-Instruct
    dataset_id = Column(Integer, ForeignKey("training_datasets.id"))
    method = Column(String(50), nullable=False)  # full, lora, qlora
    hyperparameters = Column(JSONB, nullable=False)  # 모든 학습 설정
    mlflow_run_id = Column(String(255))  # MLflow 연동
    status = Column(String(50), default='pending', index=True)
        # pending, running, completed, failed
    start_time = Column(TIMESTAMP)
    end_time = Column(TIMESTAMP)
    output_dir = Column(Text)  # /data/models/finetuned/job_123
    checkpoint_dir = Column(Text)  # 체크포인트 저장 경로
    logs_path = Column(Text)  # 로그 파일 경로
    gpu_ids = Column(String(50))  # 0,1,2,3
    error_message = Column(Text)  # 실패 시 에러 메시지
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        {"comment": "Fine-tuning 작업"}
    )


class TrainingCheckpoint(Base):
    """학습 체크포인트"""
    __tablename__ = "training_checkpoints"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("finetuning_jobs.id", ondelete="CASCADE"))
    checkpoint_name = Column(String(255))  # checkpoint-1000, checkpoint-2000
    step = Column(Integer)
    epoch = Column(Float)
    metrics = Column(JSONB)  # {train_loss: 0.5, val_loss: 0.6}
    file_path = Column(Text)
    file_size_gb = Column(Float)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        {"comment": "Fine-tuning 체크포인트"}
    )


class ModelEvaluation(Base):
    """모델 평가 결과"""
    __tablename__ = "model_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("finetuning_jobs.id"))
    checkpoint_id = Column(Integer, ForeignKey("training_checkpoints.id"))
    eval_dataset_id = Column(Integer, ForeignKey("training_datasets.id"))
    metrics = Column(JSONB, nullable=False)
        # {accuracy: 0.92, f1: 0.89, perplexity: 5.2}
    test_cases = Column(JSONB)  # 개별 테스트 케이스 결과
    evaluated_at = Column(TIMESTAMP, server_default=func.now())
    evaluator = Column(Integer, ForeignKey("users.id"))

    __table_args__ = (
        {"comment": "모델 평가 결과"}
    )


class ModelRegistry(Base):
    """모델 레지스트리"""
    __tablename__ = "model_registry"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(255), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    base_model = Column(String(255))  # 원본 모델
    finetuning_job_id = Column(Integer, ForeignKey("finetuning_jobs.id"))
    model_path = Column(Text, nullable=False)  # /data/models/registered/model_v1
    model_format = Column(String(50), default='huggingface')
        # huggingface, gguf, awq
    model_size_gb = Column(Float)
    status = Column(String(50), default='staging', index=True)
        # staging, production, archived
    deployment_config = Column(JSONB)  # vLLM 설정
    mlflow_model_uri = Column(Text)
    description = Column(Text)
    tags = Column(ARRAY(String))  # {legal, korean, 7b}
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        {"comment": "Fine-tuned 모델 레지스트리"}
    )


class ModelBenchmark(Base):
    """모델 성능 벤치마크"""
    __tablename__ = "model_benchmarks"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("model_registry.id", ondelete="CASCADE"))
    benchmark_name = Column(String(255))
        # mmlu_kr, kobest, internal_test
    score = Column(Float)
    details = Column(JSONB)
    benchmark_date = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        {"comment": "모델 벤치마크 결과"}
    )
