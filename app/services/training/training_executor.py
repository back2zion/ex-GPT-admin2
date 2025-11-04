"""
Training Executor Service
Axolotl 기반 Fine-tuning 실행 서비스

책임:
- Axolotl 설정 파일 생성 (LoRA, QLoRA, Full Fine-tuning)
- Docker를 통한 학습 실행
- 학습 진행률 모니터링
- 체크포인트 관리
- 에러 처리 및 로깅
"""
import os
import re
import json
import yaml
import logging
import asyncio
import docker
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exceptions
# ============================================================================

class TrainingError(Exception):
    """학습 실행 중 발생하는 에러"""
    pass


class ConfigurationError(Exception):
    """설정 생성 중 발생하는 에러"""
    pass


class CheckpointError(Exception):
    """체크포인트 관리 중 발생하는 에러"""
    pass


# ============================================================================
# TrainingExecutor Service
# ============================================================================

class TrainingExecutor:
    """
    Axolotl 기반 Fine-tuning 실행 서비스

    주요 기능:
    1. Axolotl 설정 파일 생성
    2. Docker를 통한 학습 실행
    3. 진행률 모니터링
    4. 체크포인트 관리
    """

    # 지원하는 학습 방법
    SUPPORTED_METHODS = {"lora", "qlora", "full"}

    # 필수 설정 파라미터
    REQUIRED_CONFIG_PARAMS = {
        "job_id", "base_model", "dataset_path", "output_dir"
    }

    # Axolotl Docker 이미지
    AXOLOTL_IMAGE = "winglian/axolotl:main-py3.11-cu121-2.2.1"

    # 최대 GPU 개수 (시스템 한계)
    MAX_GPU_COUNT = 8

    def __init__(self, data_mount_path: str = "/data"):
        """
        Args:
            data_mount_path: Docker 마운트 경로
        """
        self.data_mount_path = data_mount_path

    # ========================================================================
    # Axolotl Config 생성
    # ========================================================================

    def generate_axolotl_config(
        self,
        job_config: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Axolotl 설정 파일 생성

        Args:
            job_config: Fine-tuning 작업 설정
            output_path: 설정 파일 저장 경로

        Returns:
            생성된 설정 파일 경로

        Raises:
            ConfigurationError: 설정 오류
        """
        try:
            # 1. 필수 파라미터 검증
            self._validate_required_params(job_config)

            # 2. 보안 검증
            self._validate_security(job_config)

            # 3. 학습 방법에 따라 설정 생성
            method = job_config.get("method", "lora").lower()

            if method not in self.SUPPORTED_METHODS:
                raise ConfigurationError(
                    f"Unsupported training method: {method}. "
                    f"Supported: {self.SUPPORTED_METHODS}"
                )

            # 4. 기본 설정 구성
            axolotl_config = self._build_base_config(job_config)

            # 5. 방법별 설정 추가
            if method == "lora":
                axolotl_config.update(self._build_lora_config(job_config))
            elif method == "qlora":
                axolotl_config.update(self._build_qlora_config(job_config))
            elif method == "full":
                axolotl_config.update(self._build_full_config(job_config))

            # 6. 커스텀 하이퍼파라미터 추가
            if "hyperparameters" in job_config:
                axolotl_config.update(
                    self._process_hyperparameters(job_config["hyperparameters"])
                )

            # 7. 체크포인트 재개 설정
            if "resume_from_checkpoint" in job_config:
                axolotl_config["resume_from_checkpoint"] = job_config["resume_from_checkpoint"]

            # 8. YAML 파일 저장
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(axolotl_config, f, default_flow_style=False, allow_unicode=True)

            logger.info(f"Axolotl config 생성 완료: {output_path}")
            return output_path

        except ConfigurationError:
            raise
        except Exception as e:
            logger.error(f"Axolotl config 생성 실패: {e}")
            raise ConfigurationError(f"Failed to generate config: {e}")

    def _validate_required_params(self, job_config: Dict[str, Any]) -> None:
        """필수 파라미터 검증"""
        missing = self.REQUIRED_CONFIG_PARAMS - set(job_config.keys())
        if missing:
            raise ConfigurationError(f"Missing required parameters: {missing}")

    def _validate_security(self, job_config: Dict[str, Any]) -> None:
        """보안 검증: 경로 조작, 모델 이름 등"""
        # 경로 조작 방지
        for key in ["output_dir", "dataset_path"]:
            if key in job_config:
                path = job_config[key]
                if ".." in path or path.startswith("/etc"):
                    raise ConfigurationError(f"Invalid path detected: {path}")

        # 모델 이름 검증
        model_name = job_config.get("base_model", "")
        if ".." in model_name or "/" * 3 in model_name:
            raise ConfigurationError(f"Invalid model name: {model_name}")

    def _build_base_config(self, job_config: Dict[str, Any]) -> Dict[str, Any]:
        """기본 Axolotl 설정"""
        hyperparams = job_config.get("hyperparameters", {})

        return {
            # 모델 설정
            "base_model": job_config["base_model"],
            "model_type": "AutoModelForCausalLM",
            "tokenizer_type": "AutoTokenizer",

            # 데이터셋 설정
            "datasets": [
                {
                    "path": job_config["dataset_path"],
                    "type": "alpaca"
                }
            ],

            # 출력 디렉토리
            "output_dir": job_config["output_dir"],

            # 학습 하이퍼파라미터
            "learning_rate": hyperparams.get("learning_rate", 2e-4),
            "num_epochs": hyperparams.get("num_epochs", 3),
            "micro_batch_size": hyperparams.get("batch_size", 4),
            "gradient_accumulation_steps": hyperparams.get("gradient_accumulation_steps", 8),

            # 최적화 설정
            "optimizer": "adamw_torch",
            "lr_scheduler": "cosine",
            "warmup_ratio": 0.05,

            # 정밀도 설정
            "bf16": True,
            "fp16": False,
            "tf32": True,

            # 로깅 설정
            "logging_steps": 10,
            "save_steps": hyperparams.get("save_steps", 500),
            "eval_steps": hyperparams.get("eval_steps", 500),

            # 기타 설정
            "max_seq_length": 2048,
            "pad_to_sequence_len": True,
            "gradient_checkpointing": True,
            "flash_attention": True,
        }

    def _build_lora_config(self, job_config: Dict[str, Any]) -> Dict[str, Any]:
        """LoRA 설정"""
        hyperparams = job_config.get("hyperparameters", {})

        return {
            "adapter": "lora",
            "lora_r": hyperparams.get("lora_rank", 16),
            "lora_alpha": hyperparams.get("lora_alpha", 32),
            "lora_dropout": hyperparams.get("lora_dropout", 0.05),
            "lora_target_modules": [
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj",
                "gate_proj",
                "up_proj",
                "down_proj"
            ],
            "lora_fan_in_fan_out": False,
        }

    def _build_qlora_config(self, job_config: Dict[str, Any]) -> Dict[str, Any]:
        """QLoRA 설정 (4-bit 양자화 + LoRA)"""
        lora_config = self._build_lora_config(job_config)

        lora_config.update({
            "adapter": "qlora",
            "load_in_4bit": True,
            "bnb_4bit_compute_dtype": "bfloat16",
            "bnb_4bit_use_double_quant": True,
            "bnb_4bit_quant_type": "nf4",
        })

        return lora_config

    def _build_full_config(self, job_config: Dict[str, Any]) -> Dict[str, Any]:
        """Full Fine-tuning 설정"""
        return {
            # Full Fine-tuning은 adapter 없음
            "adapter": None,
        }

    def _process_hyperparameters(self, hyperparams: Dict[str, Any]) -> Dict[str, Any]:
        """커스텀 하이퍼파라미터 처리"""
        processed = {}

        # 허용된 커스텀 파라미터만 추가
        allowed_params = {
            "warmup_steps", "weight_decay", "max_grad_norm",
            "save_steps", "eval_steps", "max_steps",
            "seed", "gradient_checkpointing_kwargs"
        }

        for key, value in hyperparams.items():
            if key in allowed_params:
                processed[key] = value

        return processed

    # ========================================================================
    # 학습 실행
    # ========================================================================

    async def execute_training(
        self,
        config_path: str,
        job_id: int,
        gpu_ids: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Axolotl 학습 실행

        Args:
            config_path: Axolotl 설정 파일 경로
            job_id: 작업 ID
            gpu_ids: GPU IDs (예: "0,1")
            progress_callback: 진행률 콜백 함수

        Returns:
            실행 결과

        Raises:
            TrainingError: 학습 실행 오류
        """
        try:
            # 1. GPU 검증
            if not self.validate_gpu_ids(gpu_ids):
                raise ConfigurationError(f"Invalid GPU IDs: {gpu_ids}")

            # 2. Docker 클라이언트 생성
            client = docker.from_env()

            # 3. 컨테이너 실행 설정
            container_config = {
                "image": self.AXOLOTL_IMAGE,
                "command": f"accelerate launch -m axolotl.cli.train {config_path}",
                "environment": {
                    "CUDA_VISIBLE_DEVICES": gpu_ids,
                    "WANDB_DISABLED": "true",  # WandB 비활성화
                },
                "volumes": {
                    self.data_mount_path: {"bind": "/workspace/data", "mode": "rw"}
                },
                "device_requests": [
                    docker.types.DeviceRequest(
                        device_ids=gpu_ids.split(","),
                        capabilities=[["gpu"]]
                    )
                ],
                "detach": True,
                "remove": False,  # 로그 수집을 위해 유지
            }

            logger.info(f"학습 시작: job_id={job_id}, GPUs={gpu_ids}")

            # 4. 컨테이너 실행
            container = client.containers.run(**container_config)

            # 5. 로그 스트리밍 및 진행률 모니터링
            if progress_callback:
                await self._monitor_progress(container, progress_callback)

            # 6. 완료 대기
            result = container.wait()
            exit_code = result["StatusCode"]

            # 7. 로그 수집
            logs = container.logs().decode("utf-8")

            # 8. 컨테이너 제거
            container.remove()

            if exit_code != 0:
                logger.error(f"학습 실패: exit_code={exit_code}")
                raise TrainingError(f"Training failed with exit code {exit_code}\n{logs}")

            logger.info(f"학습 완료: job_id={job_id}")

            # 9. 설정에서 output_dir 추출
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            return {
                "status": "success",
                "exit_code": exit_code,
                "output_dir": config.get("output_dir"),
                "logs": logs
            }

        except ConfigurationError:
            # ConfigurationError는 그대로 전파
            raise
        except docker.errors.DockerException as e:
            logger.error(f"Docker 실행 실패: {e}")
            raise TrainingError(f"Docker execution failed: {e}")
        except Exception as e:
            logger.error(f"학습 실행 실패: {e}")
            raise TrainingError(f"Training execution failed: {e}")

    async def _monitor_progress(
        self,
        container,
        progress_callback: Callable
    ) -> None:
        """
        학습 진행률 모니터링

        Args:
            container: Docker 컨테이너
            progress_callback: 콜백 함수 (step, total_steps, metrics)
        """
        try:
            for log_line in container.logs(stream=True):
                # bytes 또는 str 타입 처리
                if isinstance(log_line, bytes):
                    log_str = log_line.decode("utf-8").strip()
                else:
                    log_str = str(log_line).strip()

                # 로그 파싱
                metrics = self.parse_training_logs(log_str)

                if metrics and "current_step" in metrics:
                    await progress_callback(
                        step=metrics["current_step"],
                        total_steps=metrics.get("total_steps", 0),
                        metrics=metrics
                    )

        except Exception as e:
            logger.warning(f"진행률 모니터링 실패: {e}")

    def parse_training_logs(self, logs: str) -> Dict[str, Any]:
        """
        학습 로그 파싱

        Args:
            logs: 로그 문자열

        Returns:
            파싱된 메트릭
        """
        metrics = {}

        # 패턴: [INFO] Step 100/1000, Loss: 2.345, LR: 0.0002
        step_pattern = r"Step (\d+)/(\d+)"
        loss_pattern = r"Loss:\s*([\d.]+)"
        lr_pattern = r"LR:\s*([\d.eE-]+)"

        # findall을 사용하여 모든 매칭을 찾고 마지막 값 사용
        step_matches = re.findall(step_pattern, logs)
        if step_matches:
            last_match = step_matches[-1]
            metrics["current_step"] = int(last_match[0])
            metrics["total_steps"] = int(last_match[1])

        loss_matches = re.findall(loss_pattern, logs)
        if loss_matches:
            metrics["loss"] = float(loss_matches[-1])

        lr_matches = re.findall(lr_pattern, logs)
        if lr_matches:
            metrics["learning_rate"] = float(lr_matches[-1])

        return metrics

    def validate_gpu_ids(self, gpu_ids: str) -> bool:
        """
        GPU IDs 검증

        Args:
            gpu_ids: GPU IDs (예: "0,1,2")

        Returns:
            유효 여부
        """
        try:
            # 형식 검증
            gpu_list = [int(gpu_id.strip()) for gpu_id in gpu_ids.split(",")]

            # 범위 검증
            if any(gpu_id < 0 or gpu_id >= self.MAX_GPU_COUNT for gpu_id in gpu_list):
                return False

            # 중복 검증
            if len(gpu_list) != len(set(gpu_list)):
                return False

            return True

        except (ValueError, AttributeError):
            return False

    # ========================================================================
    # 체크포인트 관리
    # ========================================================================

    def list_checkpoints(self, checkpoint_dir: str) -> List[str]:
        """
        체크포인트 목록 조회

        Args:
            checkpoint_dir: 체크포인트 디렉토리

        Returns:
            체크포인트 이름 리스트
        """
        try:
            checkpoint_path = Path(checkpoint_dir)

            if not checkpoint_path.exists():
                return []

            checkpoints = [
                d.name for d in checkpoint_path.iterdir()
                if d.is_dir() and d.name.startswith("checkpoint-")
            ]

            # 스텝 번호로 정렬
            checkpoints.sort(key=lambda x: int(x.split("-")[1]) if "-" in x else 0)

            return checkpoints

        except Exception as e:
            logger.error(f"체크포인트 목록 조회 실패: {e}")
            return []

    def get_best_checkpoint(
        self,
        checkpoint_dir: str,
        metric: str = "loss",
        mode: str = "min"
    ) -> Optional[str]:
        """
        최적 체크포인트 선택

        Args:
            checkpoint_dir: 체크포인트 디렉토리
            metric: 평가 메트릭 (loss, accuracy 등)
            mode: 최적화 방향 (min 또는 max)

        Returns:
            최적 체크포인트 경로
        """
        try:
            checkpoints = self.list_checkpoints(checkpoint_dir)

            if not checkpoints:
                return None

            best_checkpoint = None
            best_value = float('inf') if mode == "min" else float('-inf')

            for checkpoint_name in checkpoints:
                checkpoint_path = Path(checkpoint_dir) / checkpoint_name
                trainer_state_path = checkpoint_path / "trainer_state.json"

                if not trainer_state_path.exists():
                    continue

                with open(trainer_state_path, 'r') as f:
                    trainer_state = json.load(f)

                # 마지막 로그에서 메트릭 추출
                log_history = trainer_state.get("log_history", [])
                if not log_history:
                    continue

                last_log = log_history[-1]
                metric_value = last_log.get(metric)

                if metric_value is None:
                    continue

                # 최적값 비교
                if mode == "min" and metric_value < best_value:
                    best_value = metric_value
                    best_checkpoint = str(checkpoint_path)
                elif mode == "max" and metric_value > best_value:
                    best_value = metric_value
                    best_checkpoint = str(checkpoint_path)

            return best_checkpoint

        except Exception as e:
            logger.error(f"최적 체크포인트 선택 실패: {e}")
            return None

    def cleanup_old_checkpoints(
        self,
        checkpoint_dir: str,
        keep_last_n: int = 3
    ) -> None:
        """
        오래된 체크포인트 삭제

        Args:
            checkpoint_dir: 체크포인트 디렉토리
            keep_last_n: 유지할 최근 체크포인트 개수
        """
        try:
            checkpoints = self.list_checkpoints(checkpoint_dir)

            if len(checkpoints) <= keep_last_n:
                return

            # 오래된 체크포인트 삭제
            checkpoints_to_delete = checkpoints[:-keep_last_n]

            for checkpoint_name in checkpoints_to_delete:
                checkpoint_path = Path(checkpoint_dir) / checkpoint_name

                # 디렉토리 삭제
                import shutil
                shutil.rmtree(checkpoint_path)

                logger.info(f"체크포인트 삭제: {checkpoint_name}")

        except Exception as e:
            logger.error(f"체크포인트 정리 실패: {e}")

    def verify_checkpoint_integrity(self, checkpoint_path: str) -> bool:
        """
        체크포인트 무결성 검증

        Args:
            checkpoint_path: 체크포인트 경로

        Returns:
            무결성 여부
        """
        try:
            checkpoint_dir = Path(checkpoint_path)

            # 필수 파일 확인
            required_files = [
                "pytorch_model.bin",  # 또는 model.safetensors
                "config.json",
                "trainer_state.json"
            ]

            for file_name in required_files:
                file_path = checkpoint_dir / file_name

                # safetensors 대안 확인
                if file_name == "pytorch_model.bin":
                    if not file_path.exists():
                        alt_path = checkpoint_dir / "model.safetensors"
                        if not alt_path.exists():
                            return False
                elif not file_path.exists():
                    return False

            return True

        except Exception as e:
            logger.error(f"체크포인트 무결성 검증 실패: {e}")
            return False
