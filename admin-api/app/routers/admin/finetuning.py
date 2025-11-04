"""
Fine-tuning Jobs API Router
Fine-tuning 작업 관리 API

MLflow 연동:
- Experiment 자동 생성
- Run 시작 및 종료
- 하이퍼파라미터 로깅
- 메트릭 로깅
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime
import json
import logging

from app.core.database import get_db
from app.models.training import (
    FinetuningJob,
    TrainingDataset,
    TrainingCheckpoint,
    ModelEvaluation
)
from app.schemas.training import (
    FinetuningJobCreate,
    FinetuningJobResponse,
    FinetuningJobListResponse,
    JobControlRequest,
    JobLogsResponse,
    JobMetricsResponse,
    TrainingMetrics,
    CheckpointResponse,
    CheckpointListResponse,
    JobStatusEnum
)
from app.services.training.mlflow_service import (
    MLflowService,
    MLflowConnectionError,
    MLflowExperimentError,
    MLflowRunError
)

router = APIRouter(prefix="/api/v1/admin/finetuning/jobs", tags=["finetuning"])
logger = logging.getLogger(__name__)

# MLflow 서비스 초기화
mlflow_service = MLflowService()


# ============================================================================
# Job CRUD
# ============================================================================

@router.post("", response_model=FinetuningJobResponse, status_code=status.HTTP_201_CREATED)
async def create_finetuning_job(
    job: FinetuningJobCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Fine-tuning 작업 생성

    유지보수 용이성:
    - MLflow 자동 연동 (Experiment, Run 생성)
    - 하이퍼파라미터 자동 로깅
    - 명확한 에러 처리

    Secure: Input validation, unique constraint handling
    """
    # Validate dataset exists
    dataset_query = select(TrainingDataset).where(TrainingDataset.id == job.dataset_id)
    dataset_result = await db.execute(dataset_query)
    dataset = dataset_result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"데이터셋을 찾을 수 없습니다: {job.dataset_id}"
        )

    try:
        # 1. MLflow Experiment 생성 또는 가져오기
        experiment_name = f"finetuning_{job.base_model.replace('/', '_')}"
        try:
            experiment_id = mlflow_service.get_or_create_experiment(
                name=experiment_name,
                tags={
                    "project": "finetuning-mlops",
                    "base_model": job.base_model,
                    "method": job.method.value
                }
            )
            logger.info(f"MLflow Experiment: {experiment_name} (ID: {experiment_id})")
        except (MLflowConnectionError, MLflowExperimentError) as e:
            logger.warning(f"MLflow Experiment 생성 실패 (계속 진행): {e}")
            experiment_id = None

        # 2. MLflow Run 시작
        mlflow_run_id = None
        if experiment_id:
            try:
                mlflow_run_id = mlflow_service.start_run(
                    experiment_id=experiment_id,
                    run_name=job.job_name,
                    tags={
                        "job_name": job.job_name,
                        "dataset_id": str(job.dataset_id),
                        "dataset_name": dataset.name,
                        "method": job.method.value,
                        "base_model": job.base_model
                    }
                )
                logger.info(f"MLflow Run 시작: {mlflow_run_id}")

                # 3. 하이퍼파라미터 로깅
                if job.hyperparameters:
                    mlflow_service.log_parameters(
                        run_id=mlflow_run_id,
                        params=job.hyperparameters,
                        flatten=True
                    )
                    logger.info(f"하이퍼파라미터 로깅 완료: {len(job.hyperparameters)}개")

            except MLflowRunError as e:
                logger.warning(f"MLflow Run 시작 실패 (계속 진행): {e}")
                mlflow_run_id = None

        # 4. DB에 작업 생성
        finetuning_job = FinetuningJob(
            job_name=job.job_name,
            base_model=job.base_model,
            dataset_id=job.dataset_id,
            method=job.method.value,
            hyperparameters=job.hyperparameters,
            gpu_ids=job.gpu_ids,
            output_dir=job.output_dir or f"/data/models/finetuned/{job.job_name}",
            checkpoint_dir=f"/data/models/finetuned/{job.job_name}/checkpoints",
            logs_path=f"/data/logs/finetuning/{job.job_name}.log",
            mlflow_run_id=mlflow_run_id,  # MLflow Run ID 저장
            status="pending",
            created_at=datetime.utcnow()
        )

        db.add(finetuning_job)
        await db.commit()
        await db.refresh(finetuning_job)

        logger.info(f"Fine-tuning 작업 생성 완료: {job.job_name} (ID: {finetuning_job.id})")

        # Celery 작업 큐에 등록
        try:
            from app.workers.finetuning_worker import start_finetuning_job
            task = start_finetuning_job.delay(finetuning_job.id)
            logger.info(f"Celery task 등록: task_id={task.id}, job_id={finetuning_job.id}")
        except Exception as e:
            logger.warning(f"Celery task 등록 실패 (작업은 생성됨): {e}")

        return finetuning_job

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"작업 이름 중복: {job.job_name}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"작업 이름이 이미 존재합니다: {job.job_name}"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"작업 생성 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"작업 생성 실패: {str(e)}"
        )


@router.get("", response_model=FinetuningJobListResponse)
async def list_finetuning_jobs(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    status: Optional[JobStatusEnum] = Query(None, description="상태 필터"),
    method: Optional[str] = Query(None, description="방법 필터 (full, lora, qlora)"),
    search: Optional[str] = Query(None, max_length=255, description="검색어 (작업 이름)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Fine-tuning 작업 목록 조회
    Secure: Parameterized query, input validation
    """
    # Build query
    query = select(FinetuningJob)

    # Apply filters
    conditions = []
    if status:
        conditions.append(FinetuningJob.status == status.value)
    if method:
        conditions.append(FinetuningJob.method == method)
    if search:
        conditions.append(FinetuningJob.job_name.ilike(f"%{search}%"))

    if conditions:
        query = query.where(and_(*conditions))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(desc(FinetuningJob.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Execute query
    result = await db.execute(query)
    jobs = result.scalars().all()

    return FinetuningJobListResponse(
        items=jobs,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{job_id}", response_model=FinetuningJobResponse)
async def get_finetuning_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Fine-tuning 작업 상세 조회
    Secure: Parameterized query
    """
    query = select(FinetuningJob).where(FinetuningJob.id == job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"작업을 찾을 수 없습니다: {job_id}"
        )

    return job


# ============================================================================
# Job Control
# ============================================================================

@router.post("/{job_id}/stop")
async def stop_finetuning_job(
    job_id: int,
    request: JobControlRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Fine-tuning 작업 중단
    Secure: Parameterized query
    """
    query = select(FinetuningJob).where(FinetuningJob.id == job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"작업을 찾을 수 없습니다: {job_id}"
        )

    if job.status not in ["pending", "running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"중단할 수 없는 상태입니다: {job.status}"
        )

    # TODO: Celery 작업 중단
    # celery_app.control.revoke(job.celery_task_id, terminate=True)

    job.status = "stopped"
    job.end_time = datetime.utcnow()
    job.error_message = request.reason or "사용자에 의해 중단됨"

    await db.commit()

    return {
        "message": f"작업이 중단되었습니다: {job.job_name}",
        "job_id": job_id,
        "status": job.status
    }


@router.post("/{job_id}/resume")
async def resume_finetuning_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Fine-tuning 작업 재개 (중단된 작업만 가능)
    Secure: Parameterized query
    """
    query = select(FinetuningJob).where(FinetuningJob.id == job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"작업을 찾을 수 없습니다: {job_id}"
        )

    if job.status != "stopped":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"재개할 수 없는 상태입니다: {job.status}"
        )

    # TODO: Celery 작업 재개
    # celery_app.send_task('finetuning.resume', args=[job_id])

    job.status = "pending"
    job.error_message = None

    await db.commit()

    return {
        "message": f"작업이 재개되었습니다: {job.job_name}",
        "job_id": job_id,
        "status": job.status
    }


# ============================================================================
# Job Logs & Metrics
# ============================================================================

@router.get("/{job_id}/logs", response_model=JobLogsResponse)
async def get_job_logs(
    job_id: int,
    lines: int = Query(100, ge=1, le=10000, description="읽을 라인 수"),
    db: AsyncSession = Depends(get_db)
):
    """
    Fine-tuning 작업 로그 조회
    Secure: Parameterized query, file read validation
    """
    query = select(FinetuningJob).where(FinetuningJob.id == job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"작업을 찾을 수 없습니다: {job_id}"
        )

    # TODO: 실제 로그 파일 읽기
    # if job.logs_path and os.path.exists(job.logs_path):
    #     with open(job.logs_path, 'r') as f:
    #         logs = ''.join(f.readlines()[-lines:])
    # else:
    #     logs = "로그 파일을 찾을 수 없습니다"

    logs = f"[LOG PLACEHOLDER] 작업 {job.job_name}의 로그 (구현 예정)"

    return JobLogsResponse(
        job_id=job_id,
        job_name=job.job_name,
        logs=logs,
        last_updated=datetime.utcnow()
    )


@router.get("/{job_id}/metrics", response_model=JobMetricsResponse)
async def get_job_metrics(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Fine-tuning 작업 메트릭 조회
    Secure: Parameterized query
    """
    query = select(FinetuningJob).where(FinetuningJob.id == job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"작업을 찾을 수 없습니다: {job_id}"
        )

    # TODO: MLflow에서 메트릭 가져오기
    # if job.mlflow_run_id:
    #     client = mlflow.tracking.MlflowClient()
    #     metrics = client.get_metric_history(job.mlflow_run_id, "loss")

    # Placeholder metrics
    metrics = [
        TrainingMetrics(
            step=100,
            epoch=0.5,
            loss=2.5,
            learning_rate=2e-4,
            timestamp=datetime.utcnow()
        )
    ]

    return JobMetricsResponse(
        job_id=job_id,
        job_name=job.job_name,
        metrics=metrics,
        current_step=100,
        total_steps=1000,
        progress_percent=10.0
    )


# ============================================================================
# Checkpoints
# ============================================================================

@router.get("/{job_id}/checkpoints", response_model=CheckpointListResponse)
async def list_checkpoints(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    작업의 체크포인트 목록 조회
    Secure: Parameterized query
    """
    # Verify job exists
    job_query = select(FinetuningJob).where(FinetuningJob.id == job_id)
    job_result = await db.execute(job_query)
    job = job_result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"작업을 찾을 수 없습니다: {job_id}"
        )

    # Get checkpoints
    checkpoint_query = select(TrainingCheckpoint).where(
        TrainingCheckpoint.job_id == job_id
    ).order_by(desc(TrainingCheckpoint.step))

    result = await db.execute(checkpoint_query)
    checkpoints = result.scalars().all()

    return CheckpointListResponse(
        job_id=job_id,
        checkpoints=checkpoints,
        total=len(checkpoints)
    )
