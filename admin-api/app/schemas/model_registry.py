"""
Fine-tuning MLOps - Model Registry Schemas
모델 레지스트리 스키마
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ModelFormatEnum(str, Enum):
    """모델 포맷"""
    HUGGINGFACE = "huggingface"
    GGUF = "gguf"
    AWQ = "awq"
    GPTQ = "gptq"


class ModelStatusEnum(str, Enum):
    """모델 상태"""
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class BenchmarkTypeEnum(str, Enum):
    """벤치마크 타입"""
    MMLU_KR = "mmlu_kr"
    KOBEST = "kobest"
    INTERNAL_TEST = "internal_test"
    LEGAL_QA = "legal_qa"
    CUSTOM = "custom"


# ============================================================================
# Model Registry Schemas
# ============================================================================

class ModelRegisterRequest(BaseModel):
    """모델 등록 요청"""
    model_name: str = Field(..., min_length=1, max_length=255, description="모델 이름")
    version: str = Field(..., min_length=1, max_length=50, description="버전")
    base_model: Optional[str] = Field(None, max_length=255, description="기반 모델")
    finetuning_job_id: Optional[int] = Field(None, description="Fine-tuning 작업 ID")
    model_path: str = Field(..., description="모델 저장 경로")
    model_format: ModelFormatEnum = Field(
        ModelFormatEnum.HUGGINGFACE,
        description="모델 포맷"
    )
    description: Optional[str] = Field(None, max_length=5000, description="모델 설명")
    tags: Optional[List[str]] = Field(None, description="태그 목록")
    deployment_config: Optional[Dict[str, Any]] = Field(
        None,
        description="배포 설정 (vLLM 등)"
    )

    @field_validator('model_name')
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        """모델 이름 검증"""
        if not v or not v.strip():
            raise ValueError('모델 이름은 필수입니다')

        # 알파벳, 숫자, 하이픈, 언더스코어, 슬래시만 허용
        import re
        if not re.match(r'^[a-zA-Z0-9_/-]+$', v):
            raise ValueError('모델 이름은 영문, 숫자, 하이픈, 언더스코어, 슬래시만 허용됩니다')

        return v.strip()

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """태그 검증"""
        if v is None:
            return v

        # 각 태그 검증
        validated = []
        for tag in v:
            if not tag or not tag.strip():
                continue
            if len(tag) > 50:
                raise ValueError('각 태그는 50자를 초과할 수 없습니다')
            validated.append(tag.strip().lower())

        return validated if validated else None


class ModelUpdateRequest(BaseModel):
    """모델 업데이트 요청"""
    description: Optional[str] = Field(None, max_length=5000)
    tags: Optional[List[str]] = None
    status: Optional[ModelStatusEnum] = None
    deployment_config: Optional[Dict[str, Any]] = None


class ModelResponse(BaseModel):
    """모델 응답"""
    id: int
    model_name: str
    version: str
    base_model: Optional[str] = None
    finetuning_job_id: Optional[int] = None
    model_path: str
    model_format: ModelFormatEnum
    model_size_gb: Optional[float] = None
    status: ModelStatusEnum
    deployment_config: Optional[Dict[str, Any]] = None
    mlflow_model_uri: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ModelListResponse(BaseModel):
    """모델 목록 응답"""
    items: List[ModelResponse]
    total: int
    page: int
    page_size: int


class ModelDetailResponse(ModelResponse):
    """모델 상세 응답 (벤치마크, 평가 정보 포함)"""
    benchmarks: Optional[List[Dict[str, Any]]] = Field(None, description="벤치마크 결과")
    evaluations: Optional[List[Dict[str, Any]]] = Field(None, description="평가 결과")
    deployment_history: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="배포 이력"
    )


# ============================================================================
# Model Evaluation Schemas
# ============================================================================

class ModelEvaluationRequest(BaseModel):
    """모델 평가 요청"""
    eval_dataset_id: int = Field(..., description="평가 데이터셋 ID")
    metrics: List[str] = Field(
        default=["accuracy", "f1", "perplexity", "latency"],
        description="평가할 메트릭"
    )
    test_cases: Optional[List[Dict[str, str]]] = Field(
        None,
        description="테스트 케이스 (input, expected_output)"
    )
    batch_size: int = Field(8, ge=1, le=64, description="배치 크기")


class ModelEvaluationResponse(BaseModel):
    """모델 평가 응답"""
    model_id: int
    model_name: str
    eval_dataset_id: int
    metrics: Dict[str, Any]
    test_results: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="개별 테스트 케이스 결과"
    )
    evaluated_at: datetime
    evaluator: Optional[int] = None


# ============================================================================
# Model Promotion Schemas
# ============================================================================

class ModelPromoteRequest(BaseModel):
    """모델 승격 요청 (staging → production)"""
    target_status: ModelStatusEnum = Field(
        ModelStatusEnum.PRODUCTION,
        description="목표 상태"
    )
    reason: Optional[str] = Field(None, max_length=1000, description="승격 사유")
    rollback_enabled: bool = Field(True, description="롤백 가능 여부")

    @field_validator('target_status')
    @classmethod
    def validate_target_status(cls, v: ModelStatusEnum) -> ModelStatusEnum:
        """승격 대상 상태 검증"""
        if v not in [ModelStatusEnum.PRODUCTION, ModelStatusEnum.ARCHIVED]:
            raise ValueError('승격은 production 또는 archived 상태로만 가능합니다')
        return v


class ModelPromoteResponse(BaseModel):
    """모델 승격 응답"""
    model_id: int
    model_name: str
    previous_status: ModelStatusEnum
    current_status: ModelStatusEnum
    promoted_at: datetime
    promoted_by: Optional[int] = None
    message: str


# ============================================================================
# Model Deployment Schemas
# ============================================================================

class DeploymentConfig(BaseModel):
    """배포 설정 (vLLM)"""
    gpu_memory_utilization: float = Field(
        0.9,
        ge=0.1,
        le=0.95,
        description="GPU 메모리 사용률"
    )
    max_model_len: int = Field(
        4096,
        ge=512,
        le=32768,
        description="최대 모델 길이"
    )
    tensor_parallel_size: int = Field(
        1,
        ge=1,
        le=8,
        description="텐서 병렬 크기"
    )
    dtype: str = Field("auto", description="데이터 타입 (auto, float16, bfloat16)")
    quantization: Optional[str] = Field(None, description="양자화 방법 (awq, gptq)")
    max_num_seqs: int = Field(256, ge=1, description="최대 동시 시퀀스 수")
    trust_remote_code: bool = Field(False, description="원격 코드 신뢰 여부")

    @field_validator('dtype')
    @classmethod
    def validate_dtype(cls, v: str) -> str:
        """데이터 타입 검증"""
        allowed_dtypes = ["auto", "float16", "bfloat16", "float32"]
        if v not in allowed_dtypes:
            raise ValueError(f'dtype은 {allowed_dtypes} 중 하나여야 합니다')
        return v


class ModelDeployRequest(BaseModel):
    """모델 배포 요청"""
    deployment_name: str = Field(..., min_length=1, max_length=100, description="배포 이름")
    endpoint_name: Optional[str] = Field(None, max_length=100, description="엔드포인트 이름")
    gpu_ids: Optional[str] = Field(None, max_length=50, description="사용할 GPU ID")
    config: DeploymentConfig = Field(..., description="배포 설정")
    auto_scaling: bool = Field(False, description="오토스케일링 활성화")
    min_replicas: int = Field(1, ge=1, le=10, description="최소 레플리카 수")
    max_replicas: int = Field(3, ge=1, le=10, description="최대 레플리카 수")

    @field_validator('deployment_name')
    @classmethod
    def validate_deployment_name(cls, v: str) -> str:
        """배포 이름 검증"""
        if not v or not v.strip():
            raise ValueError('배포 이름은 필수입니다')

        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('배포 이름은 영문, 숫자, 하이픈, 언더스코어만 허용됩니다')

        return v.strip()


class ModelDeployResponse(BaseModel):
    """모델 배포 응답"""
    model_id: int
    model_name: str
    deployment_name: str
    endpoint_url: str
    status: str  # deploying, deployed, failed
    deployed_at: Optional[datetime] = None
    deployed_by: Optional[int] = None
    message: str


# ============================================================================
# Model Benchmark Schemas
# ============================================================================

class BenchmarkRequest(BaseModel):
    """벤치마크 요청"""
    benchmark_name: BenchmarkTypeEnum = Field(..., description="벤치마크 이름")
    dataset_path: Optional[str] = Field(None, description="벤치마크 데이터셋 경로")
    custom_config: Optional[Dict[str, Any]] = Field(
        None,
        description="커스텀 벤치마크 설정"
    )


class BenchmarkResponse(BaseModel):
    """벤치마크 응답"""
    id: int
    model_id: int
    model_name: str
    benchmark_name: str
    score: float
    details: Optional[Dict[str, Any]] = Field(None, description="상세 결과")
    benchmark_date: datetime

    class Config:
        from_attributes = True


class BenchmarkListResponse(BaseModel):
    """벤치마크 목록 응답"""
    model_id: int
    benchmarks: List[BenchmarkResponse]
    total: int


class BenchmarkCompareRequest(BaseModel):
    """벤치마크 비교 요청"""
    model_ids: List[int] = Field(..., min_length=2, max_length=5, description="비교할 모델 ID 목록")
    benchmark_names: Optional[List[str]] = Field(None, description="비교할 벤치마크 이름")


class BenchmarkCompareResponse(BaseModel):
    """벤치마크 비교 응답"""
    models: List[Dict[str, Any]] = Field(..., description="모델별 벤치마크 결과")
    comparison: Dict[str, Any] = Field(..., description="비교 분석")
