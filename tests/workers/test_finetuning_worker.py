"""
Test cases for Fine-tuning Worker
TDD: Red-Green-Refactor 방식으로 작성

Fine-tuning 작업 큐 테스트:
- Celery task 등록
- 작업 상태 업데이트
- MLflow 메트릭 로깅
- 에러 처리
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

# Celery task 테스트를 위한 mock
pytest_plugins = ('celery.contrib.pytest',)


class TestFinetuningTaskRegistration:
    """Fine-tuning task 등록 테스트"""

    def test_finetuning_task_exists(self):
        """정상: Fine-tuning task가 Celery app에 등록됨"""
        from app.workers.finetuning_worker import celery_app, start_finetuning_job

        # Task가 등록되었는지 확인
        assert 'app.workers.finetuning_worker.start_finetuning_job' in celery_app.tasks
        assert callable(start_finetuning_job)

    def test_celery_app_configuration(self):
        """정상: Celery app 설정 확인"""
        from app.workers.finetuning_worker import celery_app

        # Redis broker 설정 확인
        assert celery_app.conf.broker_url is not None
        assert 'redis' in celery_app.conf.broker_url.lower()


class TestJobStatusUpdates:
    """작업 상태 업데이트 테스트"""

    @pytest.mark.asyncio
    async def test_update_job_status_to_running(self):
        """정상: 작업 상태를 running으로 업데이트"""
        from app.workers.finetuning_worker import update_job_status

        mock_db = AsyncMock()
        job_id = 1

        await update_job_status(mock_db, job_id, "running")

        # DB commit이 호출되었는지 확인
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_job_status_to_completed(self):
        """정상: 작업 상태를 completed로 업데이트"""
        from app.workers.finetuning_worker import update_job_status

        mock_db = AsyncMock()
        job_id = 1

        await update_job_status(mock_db, job_id, "completed")

        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_job_status_to_failed(self):
        """정상: 작업 상태를 failed로 업데이트 (에러 메시지 포함)"""
        from app.workers.finetuning_worker import update_job_status

        mock_db = AsyncMock()
        job_id = 1
        error_message = "GPU out of memory"

        await update_job_status(
            mock_db,
            job_id,
            "failed",
            error_message=error_message
        )

        mock_db.commit.assert_called_once()


class TestFinetuningJobExecution:
    """Fine-tuning 작업 실행 테스트"""

    @pytest.mark.asyncio
    async def test_start_finetuning_job_success(self):
        """정상: Fine-tuning 작업 시작"""
        from app.workers.finetuning_worker import start_finetuning_job

        job_id = 1

        # Mock dependencies
        with patch('app.workers.finetuning_worker.get_async_db') as mock_get_db:
            with patch('app.workers.finetuning_worker.execute_training') as mock_execute:
                mock_db = AsyncMock()
                mock_get_db.return_value.__aenter__.return_value = mock_db
                mock_execute.return_value = {"status": "success"}

                # Execute task
                result = await start_finetuning_job(job_id)

                assert result["status"] == "success"
                mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_finetuning_job_with_invalid_id(self):
        """실패: 존재하지 않는 job_id"""
        from app.workers.finetuning_worker import start_finetuning_job

        job_id = 99999

        with patch('app.workers.finetuning_worker.get_async_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db

            # Mock job not found
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            with pytest.raises(ValueError) as exc_info:
                await start_finetuning_job(job_id)

            assert "not found" in str(exc_info.value).lower()


class TestTrainingExecution:
    """학습 실행 테스트"""

    @pytest.mark.asyncio
    async def test_execute_training_with_lora(self):
        """정상: LoRA 방식 학습 실행"""
        from app.workers.finetuning_worker import execute_training

        job = Mock()
        job.id = 1
        job.method = "lora"
        job.base_model = "Qwen/Qwen2.5-7B-Instruct"
        job.hyperparameters = {
            "lora_rank": 16,
            "learning_rate": 2e-4,
            "num_epochs": 3
        }
        job.output_dir = "/data/models/test"

        mock_db = AsyncMock()

        with patch('app.workers.finetuning_worker.run_axolotl_training') as mock_axolotl:
            mock_axolotl.return_value = {"exit_code": 0, "output_path": "/data/models/test"}

            result = await execute_training(mock_db, job)

            assert result["exit_code"] == 0
            mock_axolotl.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_training_failure(self):
        """실패: 학습 실행 중 에러 발생"""
        from app.workers.finetuning_worker import execute_training

        job = Mock()
        job.id = 1
        job.method = "lora"

        mock_db = AsyncMock()

        with patch('app.workers.finetuning_worker.run_axolotl_training') as mock_axolotl:
            mock_axolotl.side_effect = Exception("Training failed")

            with pytest.raises(Exception) as exc_info:
                await execute_training(mock_db, job)

            assert "Training failed" in str(exc_info.value)


class TestMLflowIntegration:
    """MLflow 연동 테스트"""

    @pytest.mark.asyncio
    async def test_log_training_metrics_during_execution(self):
        """정상: 학습 중 메트릭 로깅"""
        from app.workers.finetuning_worker import log_training_metrics

        mlflow_run_id = "run123"
        metrics = {
            "train_loss": 1.234,
            "eval_loss": 1.456,
            "learning_rate": 2e-4
        }
        step = 100

        with patch('app.workers.finetuning_worker.mlflow_service') as mock_mlflow:
            await log_training_metrics(mlflow_run_id, metrics, step)

            mock_mlflow.log_metrics.assert_called_once_with(
                mlflow_run_id,
                metrics,
                step=step
            )

    @pytest.mark.asyncio
    async def test_end_mlflow_run_on_completion(self):
        """정상: 작업 완료 시 MLflow Run 종료"""
        from app.workers.finetuning_worker import finalize_mlflow_run

        mlflow_run_id = "run123"
        status = "FINISHED"

        with patch('app.workers.finetuning_worker.mlflow_service') as mock_mlflow:
            await finalize_mlflow_run(mlflow_run_id, status)

            mock_mlflow.end_run.assert_called_once_with(mlflow_run_id, status)

    @pytest.mark.asyncio
    async def test_end_mlflow_run_on_failure(self):
        """정상: 작업 실패 시 MLflow Run 종료"""
        from app.workers.finetuning_worker import finalize_mlflow_run

        mlflow_run_id = "run123"
        status = "FAILED"

        with patch('app.workers.finetuning_worker.mlflow_service') as mock_mlflow:
            await finalize_mlflow_run(mlflow_run_id, status)

            mock_mlflow.end_run.assert_called_once_with(mlflow_run_id, status)


class TestCheckpointManagement:
    """체크포인트 관리 테스트"""

    @pytest.mark.asyncio
    async def test_save_checkpoint_to_db(self):
        """정상: 체크포인트를 DB에 저장"""
        from app.workers.finetuning_worker import save_checkpoint

        mock_db = AsyncMock()
        job_id = 1
        checkpoint_path = "/data/models/checkpoint-1000"
        step = 1000
        metrics = {"loss": 1.234}

        await save_checkpoint(mock_db, job_id, checkpoint_path, step, metrics)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_checkpoints_for_job(self):
        """정상: 특정 작업의 체크포인트 목록 조회"""
        from app.workers.finetuning_worker import list_checkpoints

        mock_db = AsyncMock()
        job_id = 1

        mock_checkpoints = [
            Mock(id=1, step=1000, checkpoint_path="/path1"),
            Mock(id=2, step=2000, checkpoint_path="/path2")
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_checkpoints
        mock_db.execute.return_value = mock_result

        checkpoints = await list_checkpoints(mock_db, job_id)

        assert len(checkpoints) == 2
        assert checkpoints[0].step == 1000


class TestErrorHandling:
    """에러 처리 테스트"""

    @pytest.mark.asyncio
    async def test_handle_gpu_out_of_memory(self):
        """실패: GPU 메모리 부족 에러 처리"""
        from app.workers.finetuning_worker import handle_training_error

        error = Exception("CUDA out of memory")
        mock_db = AsyncMock()
        job_id = 1

        await handle_training_error(mock_db, job_id, error)

        # Job status가 failed로 업데이트되었는지 확인
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_handle_dataset_loading_error(self):
        """실패: 데이터셋 로딩 에러 처리"""
        from app.workers.finetuning_worker import handle_training_error

        error = Exception("Dataset not found")
        mock_db = AsyncMock()
        job_id = 1

        await handle_training_error(mock_db, job_id, error)

        mock_db.commit.assert_called()


class TestProgressTracking:
    """진행 상황 추적 테스트"""

    @pytest.mark.asyncio
    async def test_update_training_progress(self):
        """정상: 학습 진행률 업데이트"""
        from app.workers.finetuning_worker import update_progress

        mock_db = AsyncMock()
        job_id = 1
        progress = 0.5  # 50%
        current_step = 500
        total_steps = 1000

        await update_progress(mock_db, job_id, progress, current_step, total_steps)

        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_eta(self):
        """정상: 예상 완료 시간 계산"""
        from app.workers.finetuning_worker import calculate_eta

        start_time = datetime(2025, 1, 1, 10, 0, 0)
        current_time = datetime(2025, 1, 1, 10, 30, 0)  # 30분 경과
        progress = 0.5  # 50% 완료

        eta = calculate_eta(start_time, current_time, progress)

        # 30분 경과했고 50% 완료이므로, 남은 시간은 약 30분
        assert eta.total_seconds() > 1500  # 25분 이상
        assert eta.total_seconds() < 2100  # 35분 이하
