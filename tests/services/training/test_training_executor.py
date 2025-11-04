"""
Training Executor Service Tests (TDD)
학습 실행 서비스 테스트

책임:
- Axolotl 설정 파일 생성
- 학습 실행 및 모니터링
- 체크포인트 관리
- 에러 처리

TDD Red Phase: 테스트 먼저 작성
"""
import pytest
import yaml
import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# TDD: 구현 전 - import는 실패할 것으로 예상
from app.services.training.training_executor import (
    TrainingExecutor,
    TrainingError,
    ConfigurationError,
    CheckpointError
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def executor():
    """TrainingExecutor 인스턴스"""
    return TrainingExecutor()


@pytest.fixture
def sample_job_config():
    """샘플 Fine-tuning 작업 설정"""
    return {
        "job_id": 1,
        "job_name": "test-finetuning-job",
        "base_model": "Qwen/Qwen3-7B-Instruct",
        "dataset_path": "/data/datasets/test_dataset.jsonl",
        "output_dir": "/data/models/finetuned/job_1",
        "method": "lora",
        "hyperparameters": {
            "learning_rate": 2e-4,
            "num_epochs": 3,
            "batch_size": 4,
            "gradient_accumulation_steps": 8,
            "lora_rank": 16,
            "lora_alpha": 32,
            "lora_dropout": 0.05
        },
        "gpu_ids": "0,1"
    }


@pytest.fixture
def mock_subprocess():
    """subprocess.run을 모킹"""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="Training completed", stderr="")
        yield mock_run


@pytest.fixture
def mock_docker():
    """Docker client를 모킹"""
    with patch("docker.from_env") as mock_docker:
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_container.logs.return_value = b"Training logs..."
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_client.containers.run.return_value = mock_container
        mock_docker.return_value = mock_client
        yield mock_client


# ============================================================================
# Test Class: Axolotl Config 생성
# ============================================================================

class TestAxolotlConfigGeneration:
    """Axolotl 설정 파일 생성 테스트"""

    def test_generate_lora_config(self, executor, sample_job_config, tmp_path):
        """정상: LoRA 설정 생성"""
        config_path = tmp_path / "axolotl_config.yaml"

        result = executor.generate_axolotl_config(
            job_config=sample_job_config,
            output_path=str(config_path)
        )

        assert Path(result).exists()

        # YAML 파일 검증
        with open(result, 'r') as f:
            config = yaml.safe_load(f)

        # 필수 필드 검증
        assert config["base_model"] == "Qwen/Qwen3-7B-Instruct"
        assert config["adapter"] == "lora"
        assert config["lora_r"] == 16
        assert config["lora_alpha"] == 32
        assert config["lora_dropout"] == 0.05
        assert config["learning_rate"] == 2e-4
        assert config["num_epochs"] == 3
        assert config["micro_batch_size"] == 4
        assert config["gradient_accumulation_steps"] == 8
        assert config["output_dir"] == "/data/models/finetuned/job_1"

        # 데이터셋 설정
        assert "datasets" in config
        assert config["datasets"][0]["path"] == "/data/datasets/test_dataset.jsonl"
        assert config["datasets"][0]["type"] == "alpaca"

    def test_generate_qlora_config(self, executor, sample_job_config, tmp_path):
        """정상: QLoRA 설정 생성"""
        sample_job_config["method"] = "qlora"
        config_path = tmp_path / "axolotl_config.yaml"

        result = executor.generate_axolotl_config(
            job_config=sample_job_config,
            output_path=str(config_path)
        )

        with open(result, 'r') as f:
            config = yaml.safe_load(f)

        # QLoRA 특화 설정
        assert config["adapter"] == "qlora"
        assert config["load_in_4bit"] is True
        assert config["bnb_4bit_compute_dtype"] == "bfloat16"
        assert config["bnb_4bit_use_double_quant"] is True

    def test_generate_full_finetuning_config(self, executor, sample_job_config, tmp_path):
        """정상: Full Fine-tuning 설정 생성"""
        sample_job_config["method"] = "full"
        config_path = tmp_path / "axolotl_config.yaml"

        result = executor.generate_axolotl_config(
            job_config=sample_job_config,
            output_path=str(config_path)
        )

        with open(result, 'r') as f:
            config = yaml.safe_load(f)

        # Full Fine-tuning: adapter 설정 없음
        assert "adapter" not in config or config["adapter"] is None
        assert "lora_r" not in config

    def test_generate_config_invalid_method(self, executor, sample_job_config, tmp_path):
        """실패: 지원하지 않는 학습 방법"""
        sample_job_config["method"] = "unknown_method"

        with pytest.raises(ConfigurationError, match="Unsupported training method"):
            executor.generate_axolotl_config(
                job_config=sample_job_config,
                output_path=str(tmp_path / "config.yaml")
            )

    def test_generate_config_missing_required_params(self, executor, tmp_path):
        """실패: 필수 파라미터 누락"""
        incomplete_config = {
            "job_id": 1,
            "base_model": "Qwen/Qwen3-7B-Instruct"
            # dataset_path, output_dir 누락
        }

        with pytest.raises(ConfigurationError, match="Missing required"):
            executor.generate_axolotl_config(
                job_config=incomplete_config,
                output_path=str(tmp_path / "config.yaml")
            )

    def test_generate_config_with_custom_hyperparameters(self, executor, sample_job_config, tmp_path):
        """정상: 커스텀 하이퍼파라미터"""
        sample_job_config["hyperparameters"].update({
            "warmup_steps": 100,
            "weight_decay": 0.01,
            "max_grad_norm": 1.0,
            "save_steps": 500
        })

        config_path = tmp_path / "axolotl_config.yaml"
        result = executor.generate_axolotl_config(
            job_config=sample_job_config,
            output_path=str(config_path)
        )

        with open(result, 'r') as f:
            config = yaml.safe_load(f)

        assert config["warmup_steps"] == 100
        assert config["weight_decay"] == 0.01
        assert config["max_grad_norm"] == 1.0
        assert config["save_steps"] == 500


# ============================================================================
# Test Class: 학습 실행
# ============================================================================

class TestTrainingExecution:
    """학습 실행 테스트"""

    @pytest.mark.asyncio
    async def test_execute_training_success(self, executor, sample_job_config, mock_docker, tmp_path):
        """정상: 학습 성공"""
        # 설정 파일 생성
        config_path = tmp_path / "config.yaml"
        executor.generate_axolotl_config(sample_job_config, str(config_path))

        # 학습 실행
        result = await executor.execute_training(
            config_path=str(config_path),
            job_id=sample_job_config["job_id"],
            gpu_ids="0,1"
        )

        assert result["status"] == "success"
        assert result["exit_code"] == 0
        assert "output_dir" in result

    @pytest.mark.asyncio
    async def test_execute_training_with_progress_callback(
        self, executor, sample_job_config, tmp_path
    ):
        """정상: 진행률 콜백"""
        config_path = tmp_path / "config.yaml"
        executor.generate_axolotl_config(sample_job_config, str(config_path))

        progress_updates = []

        async def progress_callback(step: int, total_steps: int, metrics: Dict[str, float]):
            progress_updates.append({
                "step": step,
                "total_steps": total_steps,
                "metrics": metrics
            })

        # Mock Docker with streaming logs
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_container = MagicMock()

            # Mock logs() to handle both streaming and non-streaming
            def mock_logs(stream=False):
                if stream:
                    return iter([
                        b"[INFO] Step 100/1000, Loss: 2.345, LR: 0.0002\n",
                        b"[INFO] Step 200/1000, Loss: 1.987, LR: 0.00018\n",
                        b"[INFO] Step 300/1000, Loss: 1.654, LR: 0.00016\n"
                    ])
                else:
                    return b"Training completed successfully"

            mock_container.logs = mock_logs
            mock_container.wait.return_value = {"StatusCode": 0}
            mock_client.containers.run.return_value = mock_container
            mock_docker.return_value = mock_client

            result = await executor.execute_training(
                config_path=str(config_path),
                job_id=sample_job_config["job_id"],
                gpu_ids="0,1",
                progress_callback=progress_callback
            )

        assert result["status"] == "success"
        # 진행률 콜백이 호출되었는지 확인
        assert len(progress_updates) > 0

    @pytest.mark.asyncio
    async def test_execute_training_failure(self, executor, sample_job_config, tmp_path):
        """실패: 학습 실패"""
        config_path = tmp_path / "config.yaml"
        executor.generate_axolotl_config(sample_job_config, str(config_path))

        # Docker 실행 실패 모킹
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_client.containers.run.side_effect = Exception("CUDA out of memory")
            mock_docker.return_value = mock_client

            with pytest.raises(TrainingError, match="CUDA out of memory"):
                await executor.execute_training(
                    config_path=str(config_path),
                    job_id=sample_job_config["job_id"],
                    gpu_ids="0,1"
                )

    @pytest.mark.asyncio
    async def test_execute_training_invalid_gpu_ids(self, executor, sample_job_config, tmp_path):
        """실패: 잘못된 GPU ID"""
        config_path = tmp_path / "config.yaml"
        executor.generate_axolotl_config(sample_job_config, str(config_path))

        with pytest.raises(ConfigurationError, match="Invalid GPU IDs"):
            await executor.execute_training(
                config_path=str(config_path),
                job_id=sample_job_config["job_id"],
                gpu_ids="abc"  # 잘못된 형식
            )

    @pytest.mark.asyncio
    async def test_parse_training_logs(self, executor):
        """정상: 학습 로그 파싱"""
        sample_logs = """
        [INFO] Step 100/1000, Loss: 2.345, LR: 0.0002
        [INFO] Step 200/1000, Loss: 1.987, LR: 0.00018
        [INFO] Step 300/1000, Loss: 1.654, LR: 0.00016
        """

        metrics = executor.parse_training_logs(sample_logs)

        assert metrics["current_step"] == 300
        assert metrics["total_steps"] == 1000
        assert metrics["loss"] == 1.654
        assert metrics["learning_rate"] == 0.00016


# ============================================================================
# Test Class: 체크포인트 관리
# ============================================================================

class TestCheckpointManagement:
    """체크포인트 관리 테스트"""

    def test_list_checkpoints(self, executor, tmp_path):
        """정상: 체크포인트 목록 조회"""
        # 가짜 체크포인트 생성
        checkpoint_dir = tmp_path / "checkpoints"
        checkpoint_dir.mkdir()

        (checkpoint_dir / "checkpoint-100").mkdir()
        (checkpoint_dir / "checkpoint-200").mkdir()
        (checkpoint_dir / "checkpoint-300").mkdir()

        checkpoints = executor.list_checkpoints(str(checkpoint_dir))

        assert len(checkpoints) == 3
        assert "checkpoint-300" in checkpoints
        assert "checkpoint-200" in checkpoints
        assert "checkpoint-100" in checkpoints

    def test_get_best_checkpoint(self, executor, tmp_path):
        """정상: 최적 체크포인트 선택"""
        checkpoint_dir = tmp_path / "checkpoints"
        checkpoint_dir.mkdir()

        # 메트릭 파일 생성
        (checkpoint_dir / "checkpoint-100").mkdir()
        (checkpoint_dir / "checkpoint-100" / "trainer_state.json").write_text(
            '{"log_history": [{"loss": 2.5}]}'
        )

        (checkpoint_dir / "checkpoint-200").mkdir()
        (checkpoint_dir / "checkpoint-200" / "trainer_state.json").write_text(
            '{"log_history": [{"loss": 1.8}]}'
        )

        (checkpoint_dir / "checkpoint-300").mkdir()
        (checkpoint_dir / "checkpoint-300" / "trainer_state.json").write_text(
            '{"log_history": [{"loss": 1.5}]}'
        )

        best_checkpoint = executor.get_best_checkpoint(
            str(checkpoint_dir),
            metric="loss",
            mode="min"
        )

        assert "checkpoint-300" in best_checkpoint

    def test_cleanup_old_checkpoints(self, executor, tmp_path):
        """정상: 오래된 체크포인트 삭제"""
        checkpoint_dir = tmp_path / "checkpoints"
        checkpoint_dir.mkdir()

        # 5개 체크포인트 생성
        for i in range(1, 6):
            (checkpoint_dir / f"checkpoint-{i*100}").mkdir()

        # 최근 3개만 유지
        executor.cleanup_old_checkpoints(
            str(checkpoint_dir),
            keep_last_n=3
        )

        checkpoints = executor.list_checkpoints(str(checkpoint_dir))
        assert len(checkpoints) == 3

    def test_verify_checkpoint_integrity(self, executor, tmp_path):
        """정상: 체크포인트 무결성 검증"""
        checkpoint_dir = tmp_path / "checkpoint-100"
        checkpoint_dir.mkdir()

        # 필수 파일 생성
        (checkpoint_dir / "pytorch_model.bin").write_text("model weights")
        (checkpoint_dir / "config.json").write_text('{"model_type": "qwen"}')
        (checkpoint_dir / "trainer_state.json").write_text('{"step": 100}')

        is_valid = executor.verify_checkpoint_integrity(str(checkpoint_dir))
        assert is_valid is True

    def test_verify_checkpoint_corrupted(self, executor, tmp_path):
        """실패: 손상된 체크포인트"""
        checkpoint_dir = tmp_path / "checkpoint-100"
        checkpoint_dir.mkdir()

        # 일부 파일만 존재
        (checkpoint_dir / "config.json").write_text('{"model_type": "qwen"}')

        is_valid = executor.verify_checkpoint_integrity(str(checkpoint_dir))
        assert is_valid is False


# ============================================================================
# Test Class: 시큐어 코딩
# ============================================================================

class TestSecurityValidation:
    """시큐어 코딩: 입력 검증 및 보안"""

    def test_prevent_path_traversal_in_config(self, executor, sample_job_config, tmp_path):
        """시큐어: 경로 조작 공격 방지"""
        sample_job_config["output_dir"] = "../../../etc/passwd"

        with pytest.raises(ConfigurationError, match="Invalid path"):
            executor.generate_axolotl_config(
                job_config=sample_job_config,
                output_path=str(tmp_path / "config.yaml")
            )

    def test_validate_model_name(self, executor, sample_job_config, tmp_path):
        """시큐어: 모델 이름 검증"""
        # 잘못된 문자 포함
        sample_job_config["base_model"] = "Qwen/../../malicious"

        with pytest.raises(ConfigurationError, match="Invalid model name"):
            executor.generate_axolotl_config(
                job_config=sample_job_config,
                output_path=str(tmp_path / "config.yaml")
            )

    def test_validate_gpu_allocation(self, executor):
        """시큐어: GPU 할당 검증"""
        # 시스템에 없는 GPU ID
        is_valid = executor.validate_gpu_ids("0,1,2,3,4,5,6,7,8,9")
        assert is_valid is False

        # 유효한 GPU ID
        is_valid = executor.validate_gpu_ids("0,1")
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_handle_oom_error_gracefully(self, executor, sample_job_config, tmp_path):
        """정상: OOM 에러 처리"""
        config_path = tmp_path / "config.yaml"
        executor.generate_axolotl_config(sample_job_config, str(config_path))

        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_client.containers.run.side_effect = Exception(
                "CUDA out of memory. Tried to allocate 20.00 GiB"
            )
            mock_docker.return_value = mock_client

            with pytest.raises(TrainingError) as exc_info:
                await executor.execute_training(
                    config_path=str(config_path),
                    job_id=sample_job_config["job_id"],
                    gpu_ids="0,1"
                )

            # 에러 메시지에 OOM 정보 포함
            assert "out of memory" in str(exc_info.value).lower()


# ============================================================================
# Test Class: 통합 파이프라인
# ============================================================================

class TestTrainingPipeline:
    """전체 학습 파이프라인 통합 테스트"""

    @pytest.mark.asyncio
    async def test_full_training_pipeline(self, executor, sample_job_config, mock_docker, tmp_path):
        """정상: 전체 파이프라인 실행"""
        # Step 1: 설정 생성
        config_path = tmp_path / "config.yaml"
        executor.generate_axolotl_config(sample_job_config, str(config_path))

        # Step 2: 학습 실행
        result = await executor.execute_training(
            config_path=str(config_path),
            job_id=sample_job_config["job_id"],
            gpu_ids="0,1"
        )

        # Step 3: 체크포인트 검증
        assert result["status"] == "success"
        assert Path(sample_job_config["output_dir"]).exists() or result["exit_code"] == 0

    @pytest.mark.asyncio
    async def test_resume_from_checkpoint(self, executor, sample_job_config, mock_docker, tmp_path):
        """정상: 체크포인트에서 재개"""
        config_path = tmp_path / "config.yaml"

        # 기존 체크포인트 경로 추가
        sample_job_config["resume_from_checkpoint"] = "/data/models/checkpoint-500"

        executor.generate_axolotl_config(sample_job_config, str(config_path))

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        assert config["resume_from_checkpoint"] == "/data/models/checkpoint-500"
