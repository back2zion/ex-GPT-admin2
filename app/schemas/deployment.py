"""
배포관리 Pydantic 스키마
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ModelRegisterRequest(BaseModel):
    """MLflow 모델 등록 요청"""
    model_name: str = Field(..., description="모델 이름 (예: qwen3-235b-v1)")
    model_uri: str = Field(..., description="모델 경로 (HuggingFace ID 또는 로컬 경로)")
    framework: str = Field(default="vllm", description="vllm 또는 transformers")
    description: Optional[str] = None


class BentoDeployRequest(BaseModel):
    """Bento 배포 요청"""
    model_name: str = Field(..., description="배포할 모델 이름")
    gpu_ids: List[int] = Field(default=[0], description="사용할 GPU ID 목록")
    port: int = Field(default=8000, ge=8000, le=9999, description="서비스 포트")
    vllm_config: Optional[Dict[str, Any]] = Field(
        default={
            "gpu_memory_utilization": 0.9,
            "max_model_len": 8192
        },
        description="vLLM 설정"
    )


class DeploymentResponse(BaseModel):
    """배포 정보 응답"""
    deployment_id: int
    model_name: str
    model_uri: Optional[str] = None
    framework: Optional[str] = "vllm"
    status: str = Field(
        ...,
        description="배포 상태: building, ready, serving, stopped, failed"
    )
    endpoint_url: Optional[str] = None
    gpu_ids: List[int]
    port: Optional[int] = None
    vllm_config: Optional[Dict[str, Any]] = None
    process_id: Optional[int] = None
    deployed_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeploymentListResponse(BaseModel):
    """배포 목록 응답"""
    deployments: List[DeploymentResponse]
    total: int


class GPUInfo(BaseModel):
    """GPU 정보"""
    id: int
    name: str
    utilization: int = Field(..., ge=0, le=100, description="GPU 사용률 (%)")
    memory_used: str = Field(..., description="메모리 사용량 (예: 72GB/80GB)")


class GPUStatusResponse(BaseModel):
    """GPU 상태 응답"""
    gpus: List[GPUInfo]


class HealthCheckResponse(BaseModel):
    """Health Check 응답"""
    deployment_id: int
    healthy: bool
    response_time_ms: Optional[int] = None
    status: Optional[str] = None
    error: Optional[str] = None


class BentoInfo(BaseModel):
    """Bento 정보"""
    name: str
    version: str
    tag: str = Field(..., description="Bento 태그 (name:version)")
    model: str = Field(..., description="포함된 모델")
    size: str = Field(..., description="Bento 크기")
    created_at: datetime
    port: int = Field(..., description="서비스 포트")
    endpoint_url: str = Field(..., description="서비스 엔드포인트 URL")
    status: str = Field(default="serving", description="서비스 상태")


class BentoListResponse(BaseModel):
    """Bento 목록 응답"""
    bentos: List[BentoInfo]
    total: int


class BentoBuildRequest(BaseModel):
    """Bento 빌드 요청"""
    model_name: str = Field(..., description="빌드할 모델 이름")
    version: str = Field(..., description="Bento 버전")
    python_version: str = Field(default="3.9", description="Python 버전")
    description: Optional[str] = None


class BentoDeploymentRequest(BaseModel):
    """Bento 배포 요청"""
    bento_tag: str = Field(..., description="배포할 Bento 태그 (name:version)")
    gpu_ids: List[int] = Field(default=[0], description="사용할 GPU ID 목록")
    port: int = Field(default=3000, ge=3000, le=3999, description="서비스 포트")
    replicas: int = Field(default=1, ge=1, le=4, description="레플리카 수")
