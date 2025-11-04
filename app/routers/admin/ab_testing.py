"""
A/B Testing API Router
A/B 테스트 관리 API

ABTestService 통합 (TDD + 시큐어 코딩 + 유지보수 용이성)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime
import logging

from app.core.database import get_db
from app.models.ab_test import ABExperiment, ABTestLog, ABTestResult
from app.models.training import ModelRegistry
from app.schemas.ab_test import (
    ABTestRequest,
    ABTestUpdateRequest,
    ABTestResponse,
    ABTestListResponse,
    ABTestDetailResponse,
    ABTestLogCreate,
    ABTestLogResponse,
    ABTestLogListResponse,
    ABTestResultResponse,
    ABTestResultListResponse,
    ABTestStopRequest,
    ABTestConcludeRequest,
    ABTestConcludeResponse,
    ABTestMonitoringResponse,
    VariantStatistics,
    StatisticalTest,
    ExperimentStatusEnum
)
from app.services.training.ab_test_service import (
    ABTestService,
    ValidationError,
    ExperimentError,
    StatisticalTestError
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin/ab-tests", tags=["ab-testing"])

# ABTestService 인스턴스
ab_test_service = ABTestService()


# ============================================================================
# A/B Experiment CRUD
# ============================================================================

@router.post("", response_model=ABTestResponse, status_code=status.HTTP_201_CREATED)
async def create_ab_test(
    test: ABTestRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    A/B 테스트 생성

    ABTestService 사용 - TDD + 시큐어 코딩 적용:
    - Path Traversal 방지 (실험 이름)
    - 트래픽 분할 검증 (합계 1.0, 범위 0-1)
    - 최소 샘플 수 검증 (30+)
    - 모델 존재 여부 검증
    """
    try:
        # ABTestService를 통해 실험 생성 (자동 검증 포함)
        traffic_dict = {
            "a": test.traffic_split.a,
            "b": test.traffic_split.b
        }

        experiment = await ab_test_service.create_experiment(
            db=db,
            experiment_name=test.experiment_name,
            model_a_id=test.model_a_id,
            model_b_id=test.model_b_id,
            traffic_split=traffic_dict,
            target_samples=test.target_samples,
            success_metric=test.success_metric.value,
            description=test.description,
            created_by=1  # TODO: 현재 사용자 ID 가져오기
        )

        # 모델 이름 조회 (응답용)
        model_a_query = select(ModelRegistry).where(ModelRegistry.id == test.model_a_id)
        model_a_result = await db.execute(model_a_query)
        model_a = model_a_result.scalar_one_or_none()

        model_b_query = select(ModelRegistry).where(ModelRegistry.id == test.model_b_id)
        model_b_result = await db.execute(model_b_query)
        model_b = model_b_result.scalar_one_or_none()

        logger.info(f"A/B 테스트 생성 성공: {experiment.experiment_name} (ID: {experiment.id})")

        return {
            "id": experiment.id,
            "experiment_name": experiment.experiment_name,
            "description": experiment.description,
            "model_a_id": experiment.model_a_id,
            "model_b_id": experiment.model_b_id,
            "model_a_name": model_a.model_name if model_a else None,
            "model_b_name": model_b.model_name if model_b else None,
            "traffic_split": experiment.traffic_split,
            "status": experiment.status,
            "start_date": experiment.start_date,
            "end_date": experiment.end_date,
            "target_samples": experiment.target_samples,
            "current_samples": 0,
            "success_metric": experiment.success_metric,
            "created_by": experiment.created_by
        }

    except ValidationError as e:
        logger.warning(f"A/B 테스트 생성 검증 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"A/B 테스트 생성 실패: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"A/B 테스트 생성 실패: {str(e)}"
        )


@router.get("", response_model=ABTestListResponse)
async def list_ab_tests(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    status: Optional[ExperimentStatusEnum] = Query(None, description="상태 필터"),
    search: Optional[str] = Query(None, max_length=255, description="검색어 (실험 이름)"),
    db: AsyncSession = Depends(get_db)
):
    """
    A/B 테스트 목록 조회
    Secure: Parameterized query, input validation
    """
    # Build query
    query = select(ABExperiment)

    # Apply filters
    conditions = []
    if status:
        conditions.append(ABExperiment.status == status.value)
    if search:
        conditions.append(ABExperiment.experiment_name.ilike(f"%{search}%"))

    if conditions:
        query = query.where(and_(*conditions))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(desc(ABExperiment.start_date))
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Execute query
    result = await db.execute(query)
    experiments = result.scalars().all()

    # Enrich with model names and current samples
    items = []
    for exp in experiments:
        # Get model names
        model_a_query = select(ModelRegistry).where(ModelRegistry.id == exp.model_a_id)
        model_a_result = await db.execute(model_a_query)
        model_a = model_a_result.scalar_one_or_none()

        model_b_query = select(ModelRegistry).where(ModelRegistry.id == exp.model_b_id)
        model_b_result = await db.execute(model_b_query)
        model_b = model_b_result.scalar_one_or_none()

        # Count current samples
        log_count_query = select(func.count()).where(ABTestLog.experiment_id == exp.id)
        log_count_result = await db.execute(log_count_query)
        current_samples = log_count_result.scalar() or 0

        items.append({
            "id": exp.id,
            "experiment_name": exp.experiment_name,
            "description": exp.description,
            "model_a_id": exp.model_a_id,
            "model_b_id": exp.model_b_id,
            "model_a_name": model_a.model_name if model_a else None,
            "model_b_name": model_b.model_name if model_b else None,
            "traffic_split": exp.traffic_split,
            "status": exp.status,
            "start_date": exp.start_date,
            "end_date": exp.end_date,
            "target_samples": exp.target_samples,
            "current_samples": current_samples,
            "success_metric": exp.success_metric,
            "created_by": exp.created_by
        })

    return ABTestListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{experiment_id}", response_model=ABTestDetailResponse)
async def get_ab_test(
    experiment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    A/B 테스트 상세 조회 (통계 포함)
    Secure: Parameterized query
    """
    query = select(ABExperiment).where(ABExperiment.id == experiment_id)
    result = await db.execute(query)
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"실험을 찾을 수 없습니다: {experiment_id}"
        )

    # Get model names
    model_a_query = select(ModelRegistry).where(ModelRegistry.id == experiment.model_a_id)
    model_a_result = await db.execute(model_a_query)
    model_a = model_a_result.scalar_one_or_none()

    model_b_query = select(ModelRegistry).where(ModelRegistry.id == experiment.model_b_id)
    model_b_result = await db.execute(model_b_query)
    model_b = model_b_result.scalar_one_or_none()

    # Get statistics
    log_query = select(ABTestLog).where(ABTestLog.experiment_id == experiment_id)
    log_result = await db.execute(log_query)
    logs = log_result.scalars().all()

    total_logs = len(logs)
    variant_a_logs = [log for log in logs if log.variant == "a"]
    variant_b_logs = [log for log in logs if log.variant == "b"]

    # Calculate averages
    avg_rating_a = (
        sum(log.user_rating for log in variant_a_logs if log.user_rating) / len(variant_a_logs)
        if variant_a_logs else None
    )
    avg_rating_b = (
        sum(log.user_rating for log in variant_b_logs if log.user_rating) / len(variant_b_logs)
        if variant_b_logs else None
    )
    avg_response_time_a = (
        sum(log.response_time_ms for log in variant_a_logs) / len(variant_a_logs)
        if variant_a_logs else None
    )
    avg_response_time_b = (
        sum(log.response_time_ms for log in variant_b_logs) / len(variant_b_logs)
        if variant_b_logs else None
    )

    return {
        "id": experiment.id,
        "experiment_name": experiment.experiment_name,
        "description": experiment.description,
        "model_a_id": experiment.model_a_id,
        "model_b_id": experiment.model_b_id,
        "model_a_name": model_a.model_name if model_a else None,
        "model_b_name": model_b.model_name if model_b else None,
        "traffic_split": experiment.traffic_split,
        "status": experiment.status,
        "start_date": experiment.start_date,
        "end_date": experiment.end_date,
        "target_samples": experiment.target_samples,
        "current_samples": total_logs,
        "success_metric": experiment.success_metric,
        "created_by": experiment.created_by,
        "total_logs": total_logs,
        "variant_a_count": len(variant_a_logs),
        "variant_b_count": len(variant_b_logs),
        "avg_rating_a": avg_rating_a,
        "avg_rating_b": avg_rating_b,
        "avg_response_time_a": avg_response_time_a,
        "avg_response_time_b": avg_response_time_b
    }


@router.patch("/{experiment_id}", response_model=ABTestResponse)
async def update_ab_test(
    experiment_id: int,
    update: ABTestUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    A/B 테스트 업데이트
    Secure: Parameterized query
    """
    query = select(ABExperiment).where(ABExperiment.id == experiment_id)
    result = await db.execute(query)
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"실험을 찾을 수 없습니다: {experiment_id}"
        )

    # Update fields
    if update.description is not None:
        experiment.description = update.description
    if update.traffic_split is not None:
        traffic_dict = {
            "a": update.traffic_split.a,
            "b": update.traffic_split.b
        }
        experiment.traffic_split = traffic_dict
    if update.target_samples is not None:
        experiment.target_samples = update.target_samples
    if update.status is not None:
        experiment.status = update.status.value

    await db.commit()
    await db.refresh(experiment)

    # Get model names for response
    model_a_query = select(ModelRegistry).where(ModelRegistry.id == experiment.model_a_id)
    model_a_result = await db.execute(model_a_query)
    model_a = model_a_result.scalar_one_or_none()

    model_b_query = select(ModelRegistry).where(ModelRegistry.id == experiment.model_b_id)
    model_b_result = await db.execute(model_b_query)
    model_b = model_b_result.scalar_one_or_none()

    return {
        "id": experiment.id,
        "experiment_name": experiment.experiment_name,
        "description": experiment.description,
        "model_a_id": experiment.model_a_id,
        "model_b_id": experiment.model_b_id,
        "model_a_name": model_a.model_name if model_a else None,
        "model_b_name": model_b.model_name if model_b else None,
        "traffic_split": experiment.traffic_split,
        "status": experiment.status,
        "start_date": experiment.start_date,
        "end_date": experiment.end_date,
        "target_samples": experiment.target_samples,
        "current_samples": 0,
        "success_metric": experiment.success_metric,
        "created_by": experiment.created_by
    }


# ============================================================================
# A/B Test Variant Assignment
# ============================================================================

@router.post("/{experiment_id}/assign-variant")
async def assign_variant(
    experiment_id: int,
    user_id: int = Query(..., description="사용자 ID"),
    session_id: str = Query(..., description="세션 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Variant 할당 (Sticky Session)

    ABTestService 사용 - 동일 사용자는 항상 동일한 변형 할당
    """
    try:
        variant = await ab_test_service.assign_variant(
            db=db,
            experiment_id=experiment_id,
            user_id=user_id,
            session_id=session_id
        )

        logger.info(f"Variant 할당: 실험 {experiment_id}, 사용자 {user_id} -> {variant}")

        return {
            "experiment_id": experiment_id,
            "user_id": user_id,
            "session_id": session_id,
            "variant": variant
        }

    except ValidationError as e:
        logger.warning(f"Variant 할당 검증 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Variant 할당 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Variant 할당 실패: {str(e)}"
        )


# ============================================================================
# A/B Test Logs
# ============================================================================

@router.post("/{experiment_id}/logs", response_model=ABTestLogResponse, status_code=status.HTTP_201_CREATED)
async def create_ab_test_log(
    experiment_id: int,
    log: ABTestLogCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    A/B 테스트 로그 생성 (사용자 인터랙션 기록)

    ABTestService 사용 - 시큐어 코딩 적용:
    - 평점 범위 검증 (1-5)
    - Variant 검증 ('a' 또는 'b')
    - SQL Injection 방지 (파라미터화 쿼리)
    """
    try:
        test_log = await ab_test_service.log_interaction(
            db=db,
            experiment_id=experiment_id,
            user_id=log.user_id,
            session_id=log.session_id,
            variant=log.variant.value,
            model_id=log.model_id,
            query=log.query,
            response=log.response,
            response_time_ms=log.response_time_ms,
            user_rating=log.user_rating,
            user_feedback=log.user_feedback
        )

        logger.info(f"A/B 테스트 로그 기록: 실험 {experiment_id}, 변형 {log.variant.value}")
        return test_log

    except ValidationError as e:
        logger.warning(f"A/B 테스트 로그 검증 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"A/B 테스트 로그 기록 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"로그 기록 실패: {str(e)}"
        )


@router.get("/{experiment_id}/logs", response_model=ABTestLogListResponse)
async def list_ab_test_logs(
    experiment_id: int,
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(50, ge=1, le=200, description="페이지 크기"),
    variant: Optional[str] = Query(None, description="변형 필터 (a 또는 b)"),
    db: AsyncSession = Depends(get_db)
):
    """
    A/B 테스트 로그 목록 조회
    Secure: Parameterized query
    """
    # Verify experiment exists
    exp_query = select(ABExperiment).where(ABExperiment.id == experiment_id)
    exp_result = await db.execute(exp_query)
    experiment = exp_result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"실험을 찾을 수 없습니다: {experiment_id}"
        )

    # Build query
    query = select(ABTestLog).where(ABTestLog.experiment_id == experiment_id)

    if variant:
        query = query.where(ABTestLog.variant == variant)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(desc(ABTestLog.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Execute query
    result = await db.execute(query)
    logs = result.scalars().all()

    return ABTestLogListResponse(
        experiment_id=experiment_id,
        logs=logs,
        total=total,
        page=page,
        page_size=page_size
    )


# ============================================================================
# A/B Test Results
# ============================================================================

@router.get("/{experiment_id}/results", response_model=ABTestResultResponse)
async def get_ab_test_results(
    experiment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    A/B 테스트 결과 조회 (통계 분석)

    ABTestService 사용 - 실제 통계 검정 적용:
    - T-test (통계적 유의성)
    - 95% 신뢰 구간
    - 평균 비교 및 승자 판정
    """
    try:
        # 실험 정보 조회
        exp_query = select(ABExperiment).where(ABExperiment.id == experiment_id)
        exp_result = await db.execute(exp_query)
        experiment = exp_result.scalar_one_or_none()

        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"실험을 찾을 수 없습니다: {experiment_id}"
            )

        # ABTestService를 통한 통계 계산
        results = await ab_test_service.calculate_results(db=db, experiment_id=experiment_id)

        # 로그 데이터 조회 (통계 검정용)
        log_query = select(ABTestLog).where(ABTestLog.experiment_id == experiment_id)
        log_result = await db.execute(log_query)
        logs = log_result.scalars().all()

        if not logs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="분석할 데이터가 충분하지 않습니다"
            )

        ratings_a = [log.user_rating for log in logs if log.variant == "a" and log.user_rating]
        ratings_b = [log.user_rating for log in logs if log.variant == "b" and log.user_rating]

        # 통계적 유의성 검정 (충분한 샘플이 있는 경우)
        statistical_tests = []
        is_significant = False
        p_value = None

        if len(ratings_a) >= 30 and len(ratings_b) >= 30:
            try:
                is_significant, p_value = ab_test_service.check_statistical_significance(
                    ratings_a=ratings_a,
                    ratings_b=ratings_b,
                    alpha=0.05
                )

                statistical_tests.append(
                    StatisticalTest(
                        test_name="t-test (user rating)",
                        p_value=p_value,
                        statistic=None,  # t_statistic는 내부에서 계산됨
                        significant=is_significant,
                        confidence_level=0.95
                    )
                )
            except StatisticalTestError as e:
                logger.warning(f"통계 검정 실패: {str(e)}")

        # 신뢰 구간 계산
        ci_a = ab_test_service.calculate_confidence_interval(ratings_a) if ratings_a else None
        ci_b = ab_test_service.calculate_confidence_interval(ratings_b) if ratings_b else None

        # Variant 통계
        variant_a_stats = VariantStatistics(
            variant="a",
            total_samples=results["a"]["total_samples"],
            avg_rating=results["a"]["avg_rating"],
            avg_response_time_ms=results["a"]["avg_response_time"]
        )

        variant_b_stats = VariantStatistics(
            variant="b",
            total_samples=results["b"]["total_samples"],
            avg_rating=results["b"]["avg_rating"],
            avg_response_time_ms=results["b"]["avg_response_time"]
        )

        # 승자 판정
        winner = None
        recommendation = "충분한 데이터가 없습니다"

        if results["a"]["avg_rating"] and results["b"]["avg_rating"]:
            if results["a"]["avg_rating"] > results["b"]["avg_rating"]:
                winner = "a"
                if is_significant:
                    recommendation = f"변형 A가 통계적으로 유의미한 성능 향상을 보입니다 (p={p_value:.4f})"
                else:
                    recommendation = "변형 A가 더 나은 성능을 보이지만 통계적으로 유의하지 않습니다"
            elif results["b"]["avg_rating"] > results["a"]["avg_rating"]:
                winner = "b"
                if is_significant:
                    recommendation = f"변형 B가 통계적으로 유의미한 성능 향상을 보입니다 (p={p_value:.4f})"
                else:
                    recommendation = "변형 B가 더 나은 성능을 보이지만 통계적으로 유의하지 않습니다"

        logger.info(f"A/B 테스트 결과 분석 완료: 실험 {experiment_id}, 승자: {winner}, 유의성: {is_significant}")

        return ABTestResultResponse(
            id=experiment_id,  # Placeholder
            experiment_id=experiment_id,
            experiment_name=experiment.experiment_name,
            variant_a_stats=variant_a_stats,
            variant_b_stats=variant_b_stats,
            statistical_tests=statistical_tests,
            winner=winner,
            confidence_interval={"a": ci_a, "b": ci_b} if ci_a and ci_b else None,
            effect_size=None,  # TODO: Cohen's d 계산
            recommendation=recommendation,
            calculated_at=datetime.utcnow()
        )

    except ValidationError as e:
        logger.warning(f"A/B 테스트 결과 조회 검증 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"A/B 테스트 결과 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"결과 조회 실패: {str(e)}"
        )


# ============================================================================
# A/B Test Control
# ============================================================================

@router.post("/{experiment_id}/stop")
async def stop_ab_test(
    experiment_id: int,
    request: ABTestStopRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    A/B 테스트 중단 (승자 선정 없이)

    ABTestService 사용
    """
    try:
        experiment = await ab_test_service.stop_experiment(
            db=db,
            experiment_id=experiment_id,
            reason=request.reason,
            stopped_by=1  # TODO: 현재 사용자 ID
        )

        logger.info(f"A/B 테스트 중단: {experiment.experiment_name} (ID: {experiment_id})")

        return {
            "message": f"실험이 중단되었습니다: {experiment.experiment_name}",
            "experiment_id": experiment_id,
            "status": experiment.status,
            "reason": request.reason
        }

    except ValidationError as e:
        logger.warning(f"A/B 테스트 중단 검증 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"A/B 테스트 중단 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"실험 중단 실패: {str(e)}"
        )


@router.post("/{experiment_id}/conclude", response_model=ABTestConcludeResponse)
async def conclude_ab_test(
    experiment_id: int,
    request: ABTestConcludeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    A/B 테스트 종료 및 결론 (승자 선정)

    ABTestService 사용 - 통계 결과와 함께 종료
    """
    try:
        if not request.winner:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="승자를 지정해야 합니다"
            )

        conclusion = await ab_test_service.conclude_experiment(
            db=db,
            experiment_id=experiment_id,
            winner_variant=request.winner.value,
            reason=f"관리자 종료: apply_winner={request.apply_winner}",
            concluded_by=1  # TODO: 현재 사용자 ID
        )

        # Determine winner model
        query = select(ABExperiment).where(ABExperiment.id == experiment_id)
        result = await db.execute(query)
        experiment = result.scalar_one_or_none()

        winner_model_id = None
        if request.winner.value == "a":
            winner_model_id = experiment.model_a_id
        elif request.winner.value == "b":
            winner_model_id = experiment.model_b_id

        # TODO: 승리 모델을 프로덕션에 자동 배포
        if request.apply_winner and winner_model_id:
            logger.info(f"승리 모델 배포 예정: {winner_model_id}")

        logger.info(f"A/B 테스트 종료: {experiment.experiment_name}, 승자: {request.winner.value}")

        return ABTestConcludeResponse(
            experiment_id=experiment_id,
            experiment_name=experiment.experiment_name,
            winner=request.winner.value,
            winner_model_id=winner_model_id,
            final_status=ExperimentStatusEnum.COMPLETED,
            concluded_at=datetime.utcnow(),
            message=conclusion.get("reason", f"실험 종료 - 승자: {request.winner.value}")
        )

    except ValidationError as e:
        logger.warning(f"A/B 테스트 종료 검증 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"A/B 테스트 종료 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"실험 종료 실패: {str(e)}"
        )


# ============================================================================
# Real-time Monitoring
# ============================================================================

@router.get("/{experiment_id}/monitoring", response_model=ABTestMonitoringResponse)
async def monitor_ab_test(
    experiment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    A/B 테스트 실시간 모니터링
    Secure: Parameterized query
    """
    query = select(ABExperiment).where(ABExperiment.id == experiment_id)
    result = await db.execute(query)
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"실험을 찾을 수 없습니다: {experiment_id}"
        )

    # Count samples
    log_query = select(ABTestLog).where(ABTestLog.experiment_id == experiment_id)
    log_result = await db.execute(log_query)
    logs = log_result.scalars().all()

    current_samples = len(logs)
    variant_a_samples = len([log for log in logs if log.variant == "a"])
    variant_b_samples = len([log for log in logs if log.variant == "b"])

    progress_percent = (current_samples / experiment.target_samples * 100.0
                       if experiment.target_samples > 0 else 0.0)

    # TODO: 실제 통계 분석으로 현재 우세 변형 계산
    current_leader = None

    return ABTestMonitoringResponse(
        experiment_id=experiment_id,
        experiment_name=experiment.experiment_name,
        status=experiment.status,
        progress_percent=min(progress_percent, 100.0),
        current_samples=current_samples,
        target_samples=experiment.target_samples,
        variant_a_samples=variant_a_samples,
        variant_b_samples=variant_b_samples,
        current_leader=current_leader,
        is_statistically_significant=False,
        estimated_completion_date=None,
        live_metrics={"placeholder": "구현 예정"}
    )
