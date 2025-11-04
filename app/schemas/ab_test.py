"""
Fine-tuning MLOps - A/B Testing Schemas
A/B 테스트 스키마
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ExperimentStatusEnum(str, Enum):
    """실험 상태"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VariantEnum(str, Enum):
    """실험 변형"""
    A = "a"
    B = "b"


class SuccessMetricEnum(str, Enum):
    """성공 메트릭"""
    USER_RATING = "user_rating"
    RESPONSE_TIME = "response_time"
    CLICK_THROUGH_RATE = "click_through_rate"
    TASK_COMPLETION = "task_completion"
    CUSTOM = "custom"


# ============================================================================
# A/B Experiment Schemas
# ============================================================================

class TrafficSplit(BaseModel):
    """트래픽 분할 설정"""
    a: float = Field(0.5, ge=0.0, le=1.0, description="모델 A 트래픽 비율")
    b: float = Field(0.5, ge=0.0, le=1.0, description="모델 B 트래픽 비율")

    @field_validator('a', 'b')
    @classmethod
    def validate_ratio(cls, v: float, info) -> float:
        """비율 검증"""
        if v < 0 or v > 1:
            raise ValueError('트래픽 비율은 0과 1 사이여야 합니다')
        return v


class ABTestRequest(BaseModel):
    """A/B 테스트 생성 요청"""
    experiment_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="실험 이름"
    )
    description: Optional[str] = Field(None, max_length=5000, description="실험 설명")
    model_a_id: int = Field(..., ge=1, description="모델 A ID (기준 모델)")
    model_b_id: int = Field(..., ge=1, description="모델 B ID (비교 모델)")
    traffic_split: TrafficSplit = Field(
        default_factory=lambda: TrafficSplit(a=0.5, b=0.5),
        description="트래픽 분할 비율"
    )
    target_samples: int = Field(
        200,
        ge=50,
        le=10000,
        description="목표 샘플 수"
    )
    success_metric: SuccessMetricEnum = Field(
        SuccessMetricEnum.USER_RATING,
        description="성공 메트릭"
    )
    min_confidence: float = Field(
        0.95,
        ge=0.9,
        le=0.99,
        description="최소 신뢰도"
    )
    expected_duration_days: Optional[int] = Field(
        None,
        ge=1,
        le=90,
        description="예상 실험 기간 (일)"
    )

    @field_validator('experiment_name')
    @classmethod
    def validate_experiment_name(cls, v: str) -> str:
        """실험 이름 검증"""
        if not v or not v.strip():
            raise ValueError('실험 이름은 필수입니다')

        # 알파벳, 숫자, 하이픈, 언더스코어만 허용
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('실험 이름은 영문, 숫자, 하이픈, 언더스코어만 허용됩니다')

        return v.strip()

    @field_validator('model_a_id', 'model_b_id')
    @classmethod
    def validate_model_ids(cls, v: int, info) -> int:
        """모델 ID 검증"""
        if v <= 0:
            raise ValueError('유효한 모델 ID를 입력해주세요')
        return v


class ABTestUpdateRequest(BaseModel):
    """A/B 테스트 업데이트 요청"""
    description: Optional[str] = Field(None, max_length=5000)
    traffic_split: Optional[TrafficSplit] = None
    target_samples: Optional[int] = Field(None, ge=50, le=10000)
    status: Optional[ExperimentStatusEnum] = None


class ABTestResponse(BaseModel):
    """A/B 테스트 응답"""
    id: int
    experiment_name: str
    description: Optional[str] = None
    model_a_id: int
    model_b_id: int
    model_a_name: Optional[str] = Field(None, description="모델 A 이름")
    model_b_name: Optional[str] = Field(None, description="모델 B 이름")
    traffic_split: Dict[str, float]
    status: ExperimentStatusEnum
    start_date: datetime
    end_date: Optional[datetime] = None
    target_samples: int
    current_samples: Optional[int] = Field(0, description="현재 수집된 샘플 수")
    success_metric: str
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


class ABTestListResponse(BaseModel):
    """A/B 테스트 목록 응답"""
    items: List[ABTestResponse]
    total: int
    page: int
    page_size: int


class ABTestDetailResponse(ABTestResponse):
    """A/B 테스트 상세 응답 (로그 통계 포함)"""
    total_logs: int = Field(0, description="총 로그 수")
    variant_a_count: int = Field(0, description="변형 A 샘플 수")
    variant_b_count: int = Field(0, description="변형 B 샘플 수")
    avg_rating_a: Optional[float] = Field(None, description="변형 A 평균 평점")
    avg_rating_b: Optional[float] = Field(None, description="변형 B 평균 평점")
    avg_response_time_a: Optional[float] = Field(None, description="변형 A 평균 응답시간")
    avg_response_time_b: Optional[float] = Field(None, description="변형 B 평균 응답시간")


# ============================================================================
# A/B Test Log Schemas
# ============================================================================

class ABTestLogCreate(BaseModel):
    """A/B 테스트 로그 생성 (사용자 인터랙션 기록)"""
    experiment_id: int = Field(..., ge=1, description="실험 ID")
    user_id: Optional[int] = Field(None, description="사용자 ID")
    session_id: str = Field(..., min_length=1, max_length=255, description="세션 ID")
    variant: VariantEnum = Field(..., description="변형 (a 또는 b)")
    model_id: int = Field(..., ge=1, description="사용된 모델 ID")
    query: str = Field(..., min_length=1, max_length=10000, description="사용자 쿼리")
    response: str = Field(..., min_length=1, max_length=50000, description="모델 응답")
    response_time_ms: int = Field(..., ge=0, description="응답 시간 (밀리초)")
    user_rating: Optional[int] = Field(None, ge=1, le=5, description="사용자 평점 (1-5)")
    user_feedback: Optional[str] = Field(None, max_length=5000, description="사용자 피드백")

    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """세션 ID 검증"""
        if not v or not v.strip():
            raise ValueError('세션 ID는 필수입니다')
        return v.strip()


class ABTestLogResponse(BaseModel):
    """A/B 테스트 로그 응답"""
    id: int
    experiment_id: int
    user_id: Optional[int] = None
    session_id: str
    variant: str
    model_id: int
    query: str
    response: str
    response_time_ms: int
    user_rating: Optional[int] = None
    user_feedback: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ABTestLogListResponse(BaseModel):
    """A/B 테스트 로그 목록 응답"""
    experiment_id: int
    logs: List[ABTestLogResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# A/B Test Result Schemas
# ============================================================================

class VariantStatistics(BaseModel):
    """변형별 통계"""
    variant: str
    total_samples: int
    avg_rating: Optional[float] = None
    avg_response_time_ms: Optional[float] = None
    rating_std_dev: Optional[float] = Field(None, description="평점 표준편차")
    response_time_std_dev: Optional[float] = Field(None, description="응답시간 표준편차")
    min_rating: Optional[int] = None
    max_rating: Optional[int] = None
    median_rating: Optional[float] = None


class StatisticalTest(BaseModel):
    """통계 검정 결과"""
    test_name: str = Field(..., description="검정 이름 (t-test, mann-whitney 등)")
    p_value: float = Field(..., description="p-value")
    statistic: float = Field(..., description="검정 통계량")
    significant: bool = Field(..., description="통계적 유의성 (p < 0.05)")
    confidence_level: float = Field(0.95, description="신뢰 수준")


class ABTestResultResponse(BaseModel):
    """A/B 테스트 결과 응답"""
    id: int
    experiment_id: int
    experiment_name: Optional[str] = None
    variant_a_stats: VariantStatistics
    variant_b_stats: VariantStatistics
    statistical_tests: List[StatisticalTest] = Field(
        ...,
        description="통계 검정 결과 목록"
    )
    winner: Optional[str] = Field(None, description="승리 변형 (a, b, 또는 null)")
    confidence_interval: Optional[Dict[str, Any]] = Field(
        None,
        description="신뢰 구간"
    )
    effect_size: Optional[float] = Field(None, description="효과 크기 (Cohen's d 등)")
    recommendation: str = Field(..., description="권장사항")
    calculated_at: datetime

    class Config:
        from_attributes = True


class ABTestResultListResponse(BaseModel):
    """A/B 테스트 결과 목록 응답"""
    items: List[ABTestResultResponse]
    total: int


# ============================================================================
# A/B Test Control Schemas
# ============================================================================

class ABTestStopRequest(BaseModel):
    """A/B 테스트 중단 요청"""
    reason: Optional[str] = Field(None, max_length=1000, description="중단 사유")


class ABTestConcludeRequest(BaseModel):
    """A/B 테스트 종료 및 결론 요청"""
    winner: Optional[VariantEnum] = Field(None, description="승리 변형 선택")
    reason: str = Field(..., min_length=1, max_length=5000, description="결론 사유")
    apply_winner: bool = Field(
        False,
        description="승리 모델을 프로덕션에 자동 배포할지 여부"
    )

    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v: str) -> str:
        """사유 검증"""
        if not v or not v.strip():
            raise ValueError('결론 사유는 필수입니다')
        return v.strip()


class ABTestConcludeResponse(BaseModel):
    """A/B 테스트 종료 응답"""
    experiment_id: int
    experiment_name: str
    winner: Optional[str] = None
    winner_model_id: Optional[int] = None
    final_status: ExperimentStatusEnum
    concluded_at: datetime
    message: str


# ============================================================================
# Real-time Monitoring Schemas
# ============================================================================

class ABTestMonitoringResponse(BaseModel):
    """A/B 테스트 실시간 모니터링 응답"""
    experiment_id: int
    experiment_name: str
    status: ExperimentStatusEnum
    progress_percent: float = Field(..., ge=0.0, le=100.0, description="진행률")
    current_samples: int
    target_samples: int
    variant_a_samples: int
    variant_b_samples: int
    current_leader: Optional[str] = Field(None, description="현재 우세 변형")
    is_statistically_significant: bool = Field(
        False,
        description="통계적 유의성 도달 여부"
    )
    estimated_completion_date: Optional[datetime] = Field(
        None,
        description="예상 완료일"
    )
    live_metrics: Dict[str, Any] = Field(..., description="실시간 메트릭")
