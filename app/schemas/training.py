"""
Fine-tuning MLOps - Training Dataset & Job Schemas
학습 데이터셋 및 Fine-tuning 작업 스키마
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DatasetFormatEnum(str, Enum):
    """데이터셋 포맷"""
    JSONL = "jsonl"
    JSON = "json"
    PARQUET = "parquet"
    CSV = "csv"
    ZIP = "zip"


class DatasetStatusEnum(str, Enum):
    """데이터셋 상태"""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class FinetuningMethodEnum(str, Enum):
    """Fine-tuning 방법"""
    FULL = "full"
    LORA = "lora"
    QLORA = "qlora"


class JobStatusEnum(str, Enum):
    """작업 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class QualityCheckTypeEnum(str, Enum):
    """품질 검증 타입"""
    PII_DETECTION = "pii_detection"
    DUPLICATE_CHECK = "duplicate_check"
    FORMAT_CHECK = "format_check"
    QUALITY_SCORE = "quality_score"


# ============================================================================
# Dataset Schemas
# ============================================================================

class DatasetBase(BaseModel):
    """데이터셋 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=255, description="데이터셋 이름")
    version: str = Field(..., min_length=1, max_length=50, description="버전")
    description: Optional[str] = Field(None, max_length=5000, description="설명")
    format: DatasetFormatEnum = Field(DatasetFormatEnum.JSONL, description="파일 포맷")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """데이터셋 이름 검증"""
        if not v or not v.strip():
            raise ValueError('데이터셋 이름은 필수입니다')
        return v.strip()


class DatasetCreate(DatasetBase):
    """데이터셋 생성 요청"""
    pass


class DatasetUploadRequest(BaseModel):
    """데이터셋 파일 업로드 요청"""
    name: str = Field(..., min_length=1, max_length=255)
    version: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=5000)
    format: DatasetFormatEnum = Field(DatasetFormatEnum.JSONL)
    category_id: Optional[int] = Field(None, description="카테고리 ID")


class DatasetResponse(DatasetBase):
    """데이터셋 응답"""
    id: int
    file_path: str
    total_samples: Optional[int] = None
    train_samples: Optional[int] = None
    val_samples: Optional[int] = None
    test_samples: Optional[int] = None
    dataset_metadata: Optional[Dict[str, Any]] = Field(None, description="메타데이터")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="품질 점수")
    status: DatasetStatusEnum
    created_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetListResponse(BaseModel):
    """데이터셋 목록 응답"""
    items: List[DatasetResponse]
    total: int
    page: int
    page_size: int


class DatasetStatsResponse(BaseModel):
    """데이터셋 통계"""
    id: int
    name: str
    total_samples: int
    train_samples: int
    val_samples: int
    test_samples: int
    avg_input_length: Optional[float] = None
    avg_output_length: Optional[float] = None
    distribution: Optional[Dict[str, Any]] = Field(None, description="분포 정보")
    quality_score: Optional[float] = None


class DatasetSplitRequest(BaseModel):
    """데이터셋 분할 요청"""
    train_ratio: float = Field(0.8, ge=0.1, le=0.9, description="학습 데이터 비율")
    val_ratio: float = Field(0.1, ge=0.0, le=0.5, description="검증 데이터 비율")
    test_ratio: float = Field(0.1, ge=0.0, le=0.5, description="테스트 데이터 비율")
    random_seed: int = Field(42, description="랜덤 시드")

    @field_validator('train_ratio', 'val_ratio', 'test_ratio')
    @classmethod
    def validate_ratios(cls, v: float, info) -> float:
        """비율 검증"""
        if v < 0 or v > 1:
            raise ValueError('비율은 0과 1 사이여야 합니다')
        return v


class DatasetValidationRequest(BaseModel):
    """데이터셋 검증 요청"""
    check_pii: bool = Field(True, description="PII 검사 여부")
    check_duplicates: bool = Field(True, description="중복 검사 여부")
    check_format: bool = Field(True, description="포맷 검사 여부")


class QualityCheckResult(BaseModel):
    """품질 검증 결과"""
    check_type: QualityCheckTypeEnum
    passed: bool
    issues: Optional[List[Dict[str, Any]]] = Field(None, description="발견된 문제점")
    message: str


class DatasetValidationResponse(BaseModel):
    """데이터셋 검증 응답"""
    dataset_id: int
    checks: List[QualityCheckResult]
    overall_passed: bool
    quality_score: Optional[float] = None


# ============================================================================
# Fine-tuning Job Schemas
# ============================================================================

class HyperparametersBase(BaseModel):
    """하이퍼파라미터 기본 스키마"""
    learning_rate: float = Field(2e-4, gt=0, description="학습률")
    batch_size: int = Field(4, ge=1, description="배치 크기")
    num_epochs: int = Field(3, ge=1, description="에폭 수")
    max_seq_length: int = Field(2048, ge=128, le=8192, description="최대 시퀀스 길이")
    warmup_steps: int = Field(100, ge=0, description="워밍업 스텝")
    gradient_accumulation_steps: int = Field(1, ge=1, description="그래디언트 누적 스텝")
    save_steps: int = Field(500, ge=1, description="체크포인트 저장 간격")
    logging_steps: int = Field(10, ge=1, description="로깅 간격")

    # LoRA specific
    lora_rank: Optional[int] = Field(None, ge=1, le=128, description="LoRA 랭크")
    lora_alpha: Optional[int] = Field(None, ge=1, description="LoRA 알파")
    lora_dropout: Optional[float] = Field(None, ge=0.0, le=0.5, description="LoRA 드롭아웃")
    target_modules: Optional[List[str]] = Field(None, description="LoRA 타겟 모듈")


class FinetuningJobCreate(BaseModel):
    """Fine-tuning 작업 생성"""
    job_name: str = Field(..., min_length=1, max_length=255, description="작업 이름")
    base_model: str = Field(..., min_length=1, max_length=255, description="기본 모델")
    dataset_id: int = Field(..., ge=1, description="데이터셋 ID")
    method: FinetuningMethodEnum = Field(..., description="Fine-tuning 방법")
    hyperparameters: Dict[str, Any] = Field(..., description="하이퍼파라미터")
    gpu_ids: Optional[str] = Field(None, max_length=50, description="사용할 GPU ID (예: 0,1)")
    output_dir: Optional[str] = Field(None, description="출력 디렉토리")

    @field_validator('job_name')
    @classmethod
    def validate_job_name(cls, v: str) -> str:
        """작업 이름 검증"""
        if not v or not v.strip():
            raise ValueError('작업 이름은 필수입니다')

        # 알파벳, 숫자, 하이픈, 언더스코어만 허용
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('작업 이름은 영문, 숫자, 하이픈, 언더스코어만 허용됩니다')

        return v.strip()


class FinetuningJobResponse(BaseModel):
    """Fine-tuning 작업 응답"""
    id: int
    job_name: str
    base_model: str
    dataset_id: int
    method: FinetuningMethodEnum
    hyperparameters: Dict[str, Any]
    mlflow_run_id: Optional[str] = None
    status: JobStatusEnum
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    output_dir: Optional[str] = None
    checkpoint_dir: Optional[str] = None
    logs_path: Optional[str] = None
    gpu_ids: Optional[str] = None
    error_message: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FinetuningJobListResponse(BaseModel):
    """Fine-tuning 작업 목록 응답"""
    items: List[FinetuningJobResponse]
    total: int
    page: int
    page_size: int


class JobControlRequest(BaseModel):
    """작업 제어 요청 (stop, resume)"""
    reason: Optional[str] = Field(None, max_length=500, description="사유")


class JobLogsResponse(BaseModel):
    """작업 로그 응답"""
    job_id: int
    job_name: str
    logs: str = Field(..., description="로그 내용")
    last_updated: datetime


class TrainingMetrics(BaseModel):
    """학습 메트릭"""
    step: int
    epoch: float
    loss: float
    learning_rate: float
    grad_norm: Optional[float] = None
    timestamp: datetime


class JobMetricsResponse(BaseModel):
    """작업 메트릭 응답"""
    job_id: int
    job_name: str
    metrics: List[TrainingMetrics]
    current_step: int
    total_steps: int
    progress_percent: float


# ============================================================================
# Checkpoint Schemas
# ============================================================================

class CheckpointResponse(BaseModel):
    """체크포인트 응답"""
    id: int
    job_id: int
    checkpoint_name: str
    step: int
    epoch: float
    metrics: Dict[str, Any]
    file_path: str
    file_size_gb: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CheckpointListResponse(BaseModel):
    """체크포인트 목록 응답"""
    job_id: int
    checkpoints: List[CheckpointResponse]
    total: int


# ============================================================================
# Evaluation Schemas
# ============================================================================

class EvaluationRequest(BaseModel):
    """평가 요청"""
    job_id: Optional[int] = Field(None, description="작업 ID")
    checkpoint_id: Optional[int] = Field(None, description="체크포인트 ID")
    eval_dataset_id: int = Field(..., description="평가 데이터셋 ID")
    metrics: List[str] = Field(
        default=["accuracy", "f1", "perplexity"],
        description="평가할 메트릭 목록"
    )
    test_cases: Optional[List[Dict[str, Any]]] = Field(None, description="테스트 케이스")


class EvaluationResponse(BaseModel):
    """평가 응답"""
    id: int
    job_id: Optional[int] = None
    checkpoint_id: Optional[int] = None
    eval_dataset_id: int
    metrics: Dict[str, Any] = Field(..., description="평가 메트릭")
    test_cases: Optional[Dict[str, Any]] = Field(None, description="테스트 케이스 결과")
    evaluated_at: datetime
    evaluator: Optional[int] = None

    class Config:
        from_attributes = True


class EvaluationListResponse(BaseModel):
    """평가 목록 응답"""
    items: List[EvaluationResponse]
    total: int
