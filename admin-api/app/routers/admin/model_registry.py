"""
Model Registry API Router
모델 레지스트리 관리 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime
import logging

from app.core.database import get_db
from app.models.training import (
    ModelRegistry,
    FinetuningJob,
    ModelBenchmark,
    ModelEvaluation,
    TrainingDataset
)
from app.schemas.model_registry import (
    ModelRegisterRequest,
    ModelUpdateRequest,
    ModelResponse,
    ModelListResponse,
    ModelDetailResponse,
    ModelEvaluationRequest,
    ModelEvaluationResponse,
    ModelPromoteRequest,
    ModelPromoteResponse,
    ModelDeployRequest,
    ModelDeployResponse,
    BenchmarkRequest,
    BenchmarkResponse,
    BenchmarkListResponse,
    BenchmarkCompareRequest,
    BenchmarkCompareResponse,
    ModelStatusEnum
)
from app.services.training.model_registry_service import (
    ModelRegistryService,
    RegistrationError,
    PromotionError,
    ValidationError
)

router = APIRouter(prefix="/api/v1/admin/models", tags=["model-registry"])
logger = logging.getLogger(__name__)

# 서비스 초기화
model_registry_service = ModelRegistryService()


# ============================================================================
# Model Registry CRUD
# ============================================================================

@router.post("/register", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def register_model(
    model: ModelRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    모델 등록

    Fine-tuning 작업에서 모델을 레지스트리에 등록합니다.

    Secure: Input validation, path sanitization
    """
    try:
        # 1. Fine-tuning 작업 조회
        if not model.finetuning_job_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="finetuning_job_id is required"
            )

        job_query = select(FinetuningJob).where(FinetuningJob.id == model.finetuning_job_id)
        job_result = await db.execute(job_query)
        job = job_result.scalar_one_or_none()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fine-tuning 작업을 찾을 수 없습니다: {model.finetuning_job_id}"
            )

        # 2. ModelRegistryService를 사용하여 등록
        registered_model = await model_registry_service.register_model_from_job(
            db=db,
            job=job,
            model_name=model.model_name,
            version=model.version,
            description=model.description,
            tags=model.tags,
            deployment_config=model.deployment_config,
            created_by=1  # TODO: 현재 사용자 ID 가져오기
        )

        logger.info(f"모델 등록 성공: {registered_model.model_name} v{registered_model.version}")

        return registered_model

    except (RegistrationError, ValidationError) as e:
        logger.error(f"모델 등록 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모델 등록 중 예상치 못한 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"모델 등록 실패: {str(e)}"
        )


@router.get("", response_model=ModelListResponse)
async def list_models(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    status: Optional[ModelStatusEnum] = Query(None, description="상태 필터"),
    search: Optional[str] = Query(None, max_length=255, description="검색어 (모델 이름)"),
    tags: Optional[str] = Query(None, description="태그 필터 (쉼표 구분)"),
    db: AsyncSession = Depends(get_db)
):
    """
    모델 목록 조회

    페이징, 필터링, 태그 검색을 지원합니다.

    Secure: Parameterized query, input validation
    """
    try:
        # 오프셋 계산
        offset = (page - 1) * page_size

        # 태그 검색
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
            models = await model_registry_service.search_by_tags(
                db=db,
                tags=tag_list,
                match_all=False
            )
            # 추가 필터링 (status, search)
            if status:
                models = [m for m in models if m.status == status.value]
            if search:
                models = [m for m in models if search.lower() in m.model_name.lower()]

            total = len(models)
            models = models[offset:offset + page_size]

        else:
            # 일반 목록 조회
            models = await model_registry_service.list_models(
                db=db,
                status=status.value if status else None,
                limit=page_size,
                offset=offset
            )

            # 검색 필터 적용
            if search:
                query = select(ModelRegistry)
                conditions = []
                if status:
                    conditions.append(ModelRegistry.status == status.value)
                conditions.append(ModelRegistry.model_name.ilike(f"%{search}%"))
                query = query.where(and_(*conditions))

                count_result = await db.execute(select(func.count()).select_from(query.subquery()))
                total = count_result.scalar() or 0
            else:
                # 전체 카운트
                count_query = select(func.count()).select_from(ModelRegistry)
                if status:
                    count_query = count_query.where(ModelRegistry.status == status.value)
                count_result = await db.execute(count_query)
                total = count_result.scalar() or 0

        return ModelListResponse(
            items=models,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"모델 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"모델 목록 조회 실패: {str(e)}"
        )


@router.get("/{model_id}", response_model=ModelDetailResponse)
async def get_model(
    model_id: int,
    include_benchmarks: bool = Query(False, description="벤치마크 포함 여부"),
    include_evaluations: bool = Query(False, description="평가 결과 포함 여부"),
    db: AsyncSession = Depends(get_db)
):
    """
    모델 상세 조회
    Secure: Parameterized query
    """
    query = select(ModelRegistry).where(ModelRegistry.id == model_id)
    result = await db.execute(query)
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"모델을 찾을 수 없습니다: {model_id}"
        )

    # Convert to dict for response
    model_dict = {
        "id": model.id,
        "model_name": model.model_name,
        "version": model.version,
        "base_model": model.base_model,
        "finetuning_job_id": model.finetuning_job_id,
        "model_path": model.model_path,
        "model_format": model.model_format,
        "model_size_gb": model.model_size_gb,
        "status": model.status,
        "deployment_config": model.deployment_config,
        "mlflow_model_uri": model.mlflow_model_uri,
        "description": model.description,
        "tags": model.tags,
        "created_by": model.created_by,
        "created_at": model.created_at,
        "updated_at": model.updated_at
    }

    # Add benchmarks if requested
    if include_benchmarks:
        benchmark_query = select(ModelBenchmark).where(ModelBenchmark.model_id == model_id)
        benchmark_result = await db.execute(benchmark_query)
        benchmarks = benchmark_result.scalars().all()
        model_dict["benchmarks"] = [
            {
                "id": b.id,
                "benchmark_name": b.benchmark_name,
                "score": b.score,
                "details": b.details,
                "benchmark_date": b.benchmark_date
            }
            for b in benchmarks
        ]

    # Add evaluations if requested
    if include_evaluations:
        eval_query = select(ModelEvaluation).where(
            ModelEvaluation.job_id == model.finetuning_job_id
        )
        eval_result = await db.execute(eval_query)
        evaluations = eval_result.scalars().all()
        model_dict["evaluations"] = [
            {
                "id": e.id,
                "metrics": e.metrics,
                "evaluated_at": e.evaluated_at
            }
            for e in evaluations
        ]

    return model_dict


@router.patch("/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: int,
    update: ModelUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    모델 정보 업데이트
    Secure: Parameterized query
    """
    query = select(ModelRegistry).where(ModelRegistry.id == model_id)
    result = await db.execute(query)
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"모델을 찾을 수 없습니다: {model_id}"
        )

    # Update fields
    if update.description is not None:
        model.description = update.description
    if update.tags is not None:
        model.tags = update.tags
    if update.status is not None:
        model.status = update.status.value
    if update.deployment_config is not None:
        model.deployment_config = update.deployment_config

    model.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(model)

    return model


# ============================================================================
# Model Evaluation
# ============================================================================

@router.post("/{model_id}/evaluate", response_model=ModelEvaluationResponse)
async def evaluate_model(
    model_id: int,
    request: ModelEvaluationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    모델 평가 실행
    Secure: Parameterized query
    """
    query = select(ModelRegistry).where(ModelRegistry.id == model_id)
    result = await db.execute(query)
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"모델을 찾을 수 없습니다: {model_id}"
        )

    # Validate eval dataset exists
    dataset_query = select(TrainingDataset).where(TrainingDataset.id == request.eval_dataset_id)
    dataset_result = await db.execute(dataset_query)
    dataset = dataset_result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"평가 데이터셋을 찾을 수 없습니다: {request.eval_dataset_id}"
        )

    # TODO: 실제 평가 실행
    # 1. 모델 로드
    # 2. 데이터셋으로 평가
    # 3. 메트릭 계산

    metrics = {
        "accuracy": 0.92,
        "f1": 0.89,
        "perplexity": 5.2
    }

    return ModelEvaluationResponse(
        model_id=model_id,
        model_name=model.model_name,
        eval_dataset_id=request.eval_dataset_id,
        metrics=metrics,
        test_results=None,
        evaluated_at=datetime.utcnow()
    )


# ============================================================================
# Model Promotion
# ============================================================================

@router.post("/{model_id}/promote", response_model=ModelPromoteResponse)
async def promote_model(
    model_id: int,
    request: ModelPromoteRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    모델 승격 (staging → production)

    기존 production 모델은 자동으로 archived 처리됩니다.

    Secure: Parameterized query
    """
    try:
        # Production으로 승격
        if request.target_status == ModelStatusEnum.PRODUCTION:
            promoted_model = await model_registry_service.promote_to_production(
                db=db,
                model_id=model_id,
                promoted_by=1  # TODO: 현재 사용자 ID
            )

            logger.info(f"모델 승격 성공: {promoted_model.model_name} → production")

            return ModelPromoteResponse(
                model_id=model_id,
                model_name=promoted_model.model_name,
                previous_status="staging",
                current_status=promoted_model.status,
                promoted_at=datetime.utcnow(),
                message=f"모델이 production으로 승격되었습니다"
            )

        # Archived로 변경
        elif request.target_status == ModelStatusEnum.ARCHIVED:
            archived_model = await model_registry_service.archive_model(
                db=db,
                model_id=model_id
            )

            logger.info(f"모델 아카이브: {archived_model.model_name}")

            return ModelPromoteResponse(
                model_id=model_id,
                model_name=archived_model.model_name,
                previous_status=archived_model.status,
                current_status="archived",
                promoted_at=datetime.utcnow(),
                message=f"모델이 archived로 변경되었습니다"
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"지원하지 않는 상태 전환: {request.target_status}"
            )

    except PromotionError as e:
        logger.error(f"모델 승격 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모델 승격 중 예상치 못한 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"모델 승격 실패: {str(e)}"
        )


# ============================================================================
# Model Deployment
# ============================================================================

@router.post("/{model_id}/deploy", response_model=ModelDeployResponse)
async def deploy_model(
    model_id: int,
    request: ModelDeployRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    모델 배포 (vLLM)
    Secure: Parameterized query
    """
    query = select(ModelRegistry).where(ModelRegistry.id == model_id)
    result = await db.execute(query)
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"모델을 찾을 수 없습니다: {model_id}"
        )

    if model.status != "production":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"프로덕션 상태의 모델만 배포할 수 있습니다. 현재 상태: {model.status}"
        )

    # TODO: vLLM 서버에 배포
    # 1. vLLM 설정 생성
    # 2. Docker 컨테이너 시작
    # 3. Health check

    endpoint_url = f"http://model-server:8000/v1/models/{request.deployment_name}"

    return ModelDeployResponse(
        model_id=model_id,
        model_name=model.model_name,
        deployment_name=request.deployment_name,
        endpoint_url=endpoint_url,
        status="deployed",
        deployed_at=datetime.utcnow(),
        message=f"모델이 배포되었습니다: {endpoint_url} (구현 예정)"
    )


# ============================================================================
# Model Benchmarks
# ============================================================================

@router.post("/{model_id}/benchmark", response_model=BenchmarkResponse)
async def run_benchmark(
    model_id: int,
    request: BenchmarkRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    모델 벤치마크 실행
    Secure: Parameterized query
    """
    query = select(ModelRegistry).where(ModelRegistry.id == model_id)
    result = await db.execute(query)
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"모델을 찾을 수 없습니다: {model_id}"
        )

    # TODO: 실제 벤치마크 실행

    benchmark = ModelBenchmark(
        model_id=model_id,
        benchmark_name=request.benchmark_name.value,
        score=0.85,  # Placeholder
        details={"placeholder": "구현 예정"},
        benchmark_date=datetime.utcnow()
    )

    db.add(benchmark)
    await db.commit()
    await db.refresh(benchmark)

    benchmark_dict = {
        "id": benchmark.id,
        "model_id": model_id,
        "model_name": model.model_name,
        "benchmark_name": benchmark.benchmark_name,
        "score": benchmark.score,
        "details": benchmark.details,
        "benchmark_date": benchmark.benchmark_date
    }

    return benchmark_dict


@router.get("/{model_id}/benchmarks", response_model=BenchmarkListResponse)
async def list_benchmarks(
    model_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    모델의 벤치마크 목록 조회
    Secure: Parameterized query
    """
    # Verify model exists
    model_query = select(ModelRegistry).where(ModelRegistry.id == model_id)
    model_result = await db.execute(model_query)
    model = model_result.scalar_one_or_none()

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"모델을 찾을 수 없습니다: {model_id}"
        )

    # Get benchmarks
    benchmark_query = select(ModelBenchmark).where(
        ModelBenchmark.model_id == model_id
    ).order_by(desc(ModelBenchmark.benchmark_date))

    result = await db.execute(benchmark_query)
    benchmarks = result.scalars().all()

    return BenchmarkListResponse(
        model_id=model_id,
        benchmarks=benchmarks,
        total=len(benchmarks)
    )


@router.post("/benchmarks/compare", response_model=BenchmarkCompareResponse)
async def compare_benchmarks(
    request: BenchmarkCompareRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    여러 모델의 벤치마크 비교
    Secure: Parameterized query
    """
    # Get benchmarks for all models
    models_data = []

    for model_id in request.model_ids:
        model_query = select(ModelRegistry).where(ModelRegistry.id == model_id)
        model_result = await db.execute(model_query)
        model = model_result.scalar_one_or_none()

        if not model:
            continue

        benchmark_query = select(ModelBenchmark).where(ModelBenchmark.model_id == model_id)
        if request.benchmark_names:
            benchmark_query = benchmark_query.where(
                ModelBenchmark.benchmark_name.in_(request.benchmark_names)
            )

        benchmark_result = await db.execute(benchmark_query)
        benchmarks = benchmark_result.scalars().all()

        models_data.append({
            "model_id": model_id,
            "model_name": model.model_name,
            "benchmarks": [
                {
                    "benchmark_name": b.benchmark_name,
                    "score": b.score
                }
                for b in benchmarks
            ]
        })

    comparison = {
        "summary": "벤치마크 비교 분석 (구현 예정)",
        "best_overall": None  # TODO: 계산
    }

    return BenchmarkCompareResponse(
        models=models_data,
        comparison=comparison
    )
