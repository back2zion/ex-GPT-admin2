"""
Fine-tuning Worker
Celery를 사용한 Fine-tuning 작업 처리

책임:
- Fine-tuning 작업 실행
- 작업 상태 업데이트
- MLflow 메트릭 로깅
- 체크포인트 저장
- 에러 처리
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery_app import celery_app
from app.core.database import get_async_db
from app.models.training import FinetuningJob, TrainingCheckpoint, TrainingDataset
from app.services.training.mlflow_service import MLflowService
from app.services.training.training_executor import TrainingExecutor

logger = logging.getLogger(__name__)

# MLflow 서비스 초기화
mlflow_service = MLflowService()

# TrainingExecutor 초기화
training_executor = TrainingExecutor(data_mount_path="/data")


# ============================================================================
# Helper Functions
# ============================================================================

async def get_async_db():
    """비동기 DB 세션 생성"""
    from app.core.database import async_session_maker
    async with async_session_maker() as session:
        yield session


async def update_job_status(
    db: AsyncSession,
    job_id: int,
    status: str,
    error_message: Optional[str] = None
) -> None:
    """
    작업 상태 업데이트

    Args:
        db: DB 세션
        job_id: 작업 ID
        status: 새로운 상태
        error_message: 에러 메시지 (실패 시)
    """
    try:
        stmt = (
            update(FinetuningJob)
            .where(FinetuningJob.id == job_id)
            .values(status=status)
        )

        if status == "running":
            stmt = stmt.values(started_at=datetime.utcnow())
        elif status in ["completed", "failed"]:
            stmt = stmt.values(
                completed_at=datetime.utcnow(),
                error_message=error_message
            )

        await db.execute(stmt)
        await db.commit()

        logger.info(f"작업 상태 업데이트: job_id={job_id}, status={status}")

    except Exception as e:
        logger.error(f"작업 상태 업데이트 실패: {e}")
        await db.rollback()
        raise


async def update_progress(
    db: AsyncSession,
    job_id: int,
    progress: float,
    current_step: int,
    total_steps: int
) -> None:
    """
    학습 진행률 업데이트

    Args:
        db: DB 세션
        job_id: 작업 ID
        progress: 진행률 (0.0 ~ 1.0)
        current_step: 현재 스텝
        total_steps: 전체 스텝
    """
    try:
        stmt = (
            update(FinetuningJob)
            .where(FinetuningJob.id == job_id)
            .values(
                progress=progress,
                training_logs={"current_step": current_step, "total_steps": total_steps}
            )
        )

        await db.execute(stmt)
        await db.commit()

        logger.debug(f"진행률 업데이트: job_id={job_id}, progress={progress:.2%}")

    except Exception as e:
        logger.error(f"진행률 업데이트 실패: {e}")


def calculate_eta(
    start_time: datetime,
    current_time: datetime,
    progress: float
) -> timedelta:
    """
    예상 완료 시간 계산

    Args:
        start_time: 시작 시간
        current_time: 현재 시간
        progress: 진행률 (0.0 ~ 1.0)

    Returns:
        남은 시간 (timedelta)
    """
    if progress <= 0:
        return timedelta(seconds=0)

    elapsed = current_time - start_time
    total_time = elapsed / progress
    remaining = total_time - elapsed

    return remaining


async def save_checkpoint(
    db: AsyncSession,
    job_id: int,
    checkpoint_path: str,
    step: int,
    metrics: Dict[str, float]
) -> None:
    """
    체크포인트 저장

    Args:
        db: DB 세션
        job_id: 작업 ID
        checkpoint_path: 체크포인트 경로
        step: 스텝 번호
        metrics: 메트릭
    """
    try:
        checkpoint = TrainingCheckpoint(
            job_id=job_id,
            checkpoint_path=checkpoint_path,
            step=step,
            metrics=metrics,
            created_at=datetime.utcnow()
        )

        db.add(checkpoint)
        await db.commit()

        logger.info(f"체크포인트 저장: job_id={job_id}, step={step}, path={checkpoint_path}")

    except Exception as e:
        logger.error(f"체크포인트 저장 실패: {e}")
        await db.rollback()


async def list_checkpoints(
    db: AsyncSession,
    job_id: int
) -> List[TrainingCheckpoint]:
    """
    작업의 체크포인트 목록 조회

    Args:
        db: DB 세션
        job_id: 작업 ID

    Returns:
        체크포인트 리스트
    """
    query = (
        select(TrainingCheckpoint)
        .where(TrainingCheckpoint.job_id == job_id)
        .order_by(TrainingCheckpoint.step.desc())
    )

    result = await db.execute(query)
    checkpoints = result.scalars().all()

    return list(checkpoints)


async def log_training_metrics(
    mlflow_run_id: str,
    metrics: Dict[str, float],
    step: int
) -> None:
    """
    학습 메트릭을 MLflow에 로깅

    Args:
        mlflow_run_id: MLflow Run ID
        metrics: 메트릭 딕셔너리
        step: 스텝 번호
    """
    try:
        mlflow_service.log_metrics(mlflow_run_id, metrics, step=step)
        logger.debug(f"메트릭 로깅: run_id={mlflow_run_id}, step={step}")

    except Exception as e:
        logger.warning(f"메트릭 로깅 실패 (계속 진행): {e}")


async def finalize_mlflow_run(
    mlflow_run_id: str,
    status: str
) -> None:
    """
    MLflow Run 종료

    Args:
        mlflow_run_id: MLflow Run ID
        status: Run 상태 (FINISHED/FAILED)
    """
    try:
        mlflow_service.end_run(mlflow_run_id, status)
        logger.info(f"MLflow Run 종료: run_id={mlflow_run_id}, status={status}")

    except Exception as e:
        logger.warning(f"MLflow Run 종료 실패 (무시): {e}")


async def handle_training_error(
    db: AsyncSession,
    job_id: int,
    error: Exception
) -> None:
    """
    학습 에러 처리

    Args:
        db: DB 세션
        job_id: 작업 ID
        error: 에러 객체
    """
    error_message = str(error)
    logger.error(f"학습 실패: job_id={job_id}, error={error_message}", exc_info=True)

    # 에러 유형 분류
    if "cuda" in error_message.lower() or "out of memory" in error_message.lower():
        error_type = "GPU_ERROR"
    elif "dataset" in error_message.lower():
        error_type = "DATASET_ERROR"
    else:
        error_type = "UNKNOWN_ERROR"

    # 상태 업데이트
    await update_job_status(
        db,
        job_id,
        "failed",
        error_message=f"[{error_type}] {error_message}"
    )


# ============================================================================
# Training Execution
# ============================================================================

async def run_axolotl_training(
    db: AsyncSession,
    job: FinetuningJob
) -> Dict[str, Any]:
    """
    Axolotl을 사용한 학습 실행

    Args:
        db: DB 세션
        job: Fine-tuning 작업

    Returns:
        실행 결과
    """
    logger.info(f"Axolotl 학습 시작: job_id={job.id}, model={job.base_model}")

    try:
        # 1. 데이터셋 정보 조회
        dataset_result = await db.execute(
            select(TrainingDataset).where(TrainingDataset.id == job.dataset_id)
        )
        dataset = dataset_result.scalar_one_or_none()

        if not dataset:
            raise Exception(f"Dataset {job.dataset_id} not found")

        # 2. Axolotl 설정 파일 생성
        config_dir = Path(job.output_dir) / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "axolotl_config.yaml"

        job_config = {
            "job_id": job.id,
            "job_name": job.job_name,
            "base_model": job.base_model,
            "dataset_path": dataset.preprocessed_path or dataset.file_path,
            "output_dir": job.output_dir,
            "method": job.method,
            "hyperparameters": job.hyperparameters or {},
            "gpu_ids": job.gpu_ids or "0"
        }

        # 체크포인트 재개 설정
        if job.checkpoint_dir:
            job_config["resume_from_checkpoint"] = job.checkpoint_dir

        training_executor.generate_axolotl_config(
            job_config=job_config,
            output_path=str(config_path)
        )

        logger.info(f"Axolotl config 생성: {config_path}")

        # 3. 진행률 콜백 함수 정의
        async def progress_callback(step: int, total_steps: int, metrics: Dict[str, float]):
            """학습 진행률 업데이트"""
            try:
                progress = step / total_steps if total_steps > 0 else 0
                await update_progress(db, job.id, progress, step, total_steps)

                # MLflow에 메트릭 로깅
                if job.mlflow_run_id and metrics:
                    await log_training_metrics(job.mlflow_run_id, metrics, step)

                # 체크포인트 저장
                if step % 500 == 0 and "loss" in metrics:
                    checkpoint_path = f"{job.output_dir}/checkpoint-{step}"
                    await save_checkpoint(db, job.id, checkpoint_path, step, metrics)

            except Exception as e:
                logger.warning(f"진행률 콜백 실패: {e}")

        # 4. 학습 실행
        result = await training_executor.execute_training(
            config_path=str(config_path),
            job_id=job.id,
            gpu_ids=job.gpu_ids or "0",
            progress_callback=progress_callback
        )

        logger.info(f"Axolotl 학습 완료: job_id={job.id}")

        return {
            "exit_code": result["exit_code"],
            "output_path": result["output_dir"],
            "logs": result.get("logs", "")
        }

    except Exception as e:
        logger.error(f"Axolotl 학습 실패: {e}")
        raise


async def execute_training(
    db: AsyncSession,
    job: FinetuningJob
) -> Dict[str, Any]:
    """
    Fine-tuning 실행

    Args:
        db: DB 세션
        job: Fine-tuning 작업

    Returns:
        실행 결과
    """
    try:
        logger.info(f"학습 실행: job_id={job.id}, method={job.method}")

        # 학습 실행 (Axolotl)
        result = await run_axolotl_training(db, job)

        if result["exit_code"] != 0:
            raise Exception(f"Training failed with exit code {result['exit_code']}")

        return result

    except Exception as e:
        logger.error(f"학습 실행 실패: {e}")
        raise


# ============================================================================
# Celery Tasks
# ============================================================================

@celery_app.task(bind=True, name='app.workers.finetuning_worker.start_finetuning_job')
def start_finetuning_job(self, job_id: int) -> Dict[str, Any]:
    """
    Fine-tuning 작업 시작 (Celery Task)

    Args:
        job_id: 작업 ID

    Returns:
        실행 결과
    """
    async def _run():
        async for db in get_async_db():
            try:
                # 1. 작업 조회
                result = await db.execute(
                    select(FinetuningJob).where(FinetuningJob.id == job_id)
                )
                job = result.scalar_one_or_none()

                if not job:
                    raise ValueError(f"Job {job_id} not found")

                # 2. 상태 업데이트: running
                await update_job_status(db, job_id, "running")

                # 3. 학습 실행
                training_result = await execute_training(db, job)

                # 4. 상태 업데이트: completed
                await update_job_status(db, job_id, "completed")

                # 5. MLflow Run 종료
                if job.mlflow_run_id:
                    await finalize_mlflow_run(job.mlflow_run_id, "FINISHED")

                logger.info(f"작업 완료: job_id={job_id}")

                return {
                    "status": "success",
                    "job_id": job_id,
                    "result": training_result
                }

            except Exception as e:
                # 에러 처리
                await handle_training_error(db, job_id, e)

                # MLflow Run 종료 (실패)
                if job and job.mlflow_run_id:
                    await finalize_mlflow_run(job.mlflow_run_id, "FAILED")

                return {
                    "status": "failed",
                    "job_id": job_id,
                    "error": str(e)
                }

    # asyncio 이벤트 루프 실행
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_run())
