"""
MLflow Service for Training Job Tracking
MLflow를 사용한 학습 작업 추적 및 관리

유지보수 용이성:
- 단일 책임 원칙 (SRP): MLflow 연동만 담당
- 명확한 에러 처리: 커스텀 예외 사용
- 의존성 주입 지원

주요 기능:
- Experiment 관리
- Run 생성 및 종료
- 하이퍼파라미터 로깅
- 메트릭 로깅
- 모델 아티팩트 등록
"""
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

import mlflow
from mlflow.tracking import MlflowClient
from mlflow.exceptions import MlflowException

logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exceptions
# ============================================================================

class MLflowConnectionError(Exception):
    """MLflow 서버 연결 실패"""
    pass


class MLflowExperimentError(Exception):
    """Experiment 관련 오류"""
    pass


class MLflowRunError(Exception):
    """Run 관련 오류"""
    pass


# ============================================================================
# MLflow Service
# ============================================================================

class MLflowService:
    """
    MLflow 연동 서비스

    책임:
    - MLflow Tracking Server 연동
    - Experiment 생성 및 관리
    - Run 생성, 시작, 종료
    - 하이퍼파라미터 로깅
    - 메트릭 로깅
    - 모델 아티팩트 등록
    """

    def __init__(self, tracking_uri: Optional[str] = None):
        """
        생성자

        Args:
            tracking_uri: MLflow Tracking Server URI
                         (기본값: 환경변수 MLFLOW_TRACKING_URI 또는 "http://mlflow:5000")
        """
        self.tracking_uri = tracking_uri or os.getenv(
            "MLFLOW_TRACKING_URI",
            "http://mlflow:5000"
        )
        mlflow.set_tracking_uri(self.tracking_uri)
        self.client = MlflowClient(tracking_uri=self.tracking_uri)

        logger.info(f"MLflow 서비스 초기화: tracking_uri={self.tracking_uri}")

    # ========================================================================
    # Connection Management
    # ========================================================================

    def check_connection(self) -> bool:
        """
        MLflow 서버 연결 확인

        Returns:
            연결 성공 여부

        Raises:
            MLflowConnectionError: 연결 실패
        """
        try:
            # 간단한 API 호출로 연결 확인
            self.client.search_experiments()
            logger.info("MLflow 서버 연결 성공")
            return True
        except Exception as e:
            logger.error(f"MLflow 서버 연결 실패: {e}")
            raise MLflowConnectionError(f"MLflow 서버 연결 실패: {str(e)}")

    # ========================================================================
    # Experiment Management
    # ========================================================================

    def create_experiment(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None,
        artifact_location: Optional[str] = None
    ) -> str:
        """
        새 Experiment 생성

        Args:
            name: Experiment 이름
            tags: Experiment 태그
            artifact_location: 아티팩트 저장 위치

        Returns:
            Experiment ID

        Raises:
            MLflowExperimentError: Experiment 생성 실패
        """
        try:
            experiment_id = self.client.create_experiment(
                name=name,
                tags=tags or {},
                artifact_location=artifact_location
            )
            logger.info(f"Experiment 생성 성공: {name} (ID: {experiment_id})")
            return experiment_id
        except Exception as e:
            logger.error(f"Experiment 생성 실패: {e}")
            raise MLflowExperimentError(f"Experiment 생성 실패: {str(e)}")

    def get_or_create_experiment(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Experiment 가져오기 (없으면 생성)

        Args:
            name: Experiment 이름
            tags: Experiment 태그 (생성 시)

        Returns:
            Experiment ID
        """
        try:
            # 기존 Experiment 확인
            experiment = self.client.get_experiment_by_name(name)
            if experiment:
                logger.info(f"기존 Experiment 사용: {name} (ID: {experiment.experiment_id})")
                return experiment.experiment_id

            # 없으면 생성
            return self.create_experiment(name, tags)

        except MlflowException as e:
            # Experiment가 없는 경우 생성
            if "does not exist" in str(e).lower():
                return self.create_experiment(name, tags)
            raise MLflowExperimentError(f"Experiment 조회 실패: {str(e)}")

    # ========================================================================
    # Run Management
    # ========================================================================

    def start_run(
        self,
        experiment_id: str,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Run 시작

        Args:
            experiment_id: Experiment ID
            run_name: Run 이름
            tags: Run 태그

        Returns:
            Run ID

        Raises:
            MLflowRunError: Run 시작 실패
        """
        try:
            run = self.client.create_run(
                experiment_id=experiment_id,
                run_name=run_name,
                tags=tags or {}
            )
            run_id = run.info.run_id
            logger.info(f"Run 시작: {run_name} (ID: {run_id})")
            return run_id

        except Exception as e:
            logger.error(f"Run 시작 실패: {e}")
            raise MLflowRunError(f"Run 시작 실패: {str(e)}")

    def end_run(
        self,
        run_id: str,
        status: str = "FINISHED"
    ) -> None:
        """
        Run 종료

        Args:
            run_id: Run ID
            status: Run 상태 (FINISHED, FAILED, KILLED)

        Raises:
            MLflowRunError: Run 종료 실패
        """
        try:
            self.client.set_terminated(run_id, status)
            logger.info(f"Run 종료: {run_id} (status: {status})")

        except Exception as e:
            logger.error(f"Run 종료 실패: {e}")
            raise MLflowRunError(f"Run 종료 실패: {str(e)}")

    # ========================================================================
    # Parameter Logging
    # ========================================================================

    def log_parameters(
        self,
        run_id: str,
        params: Dict[str, Any],
        flatten: bool = False
    ) -> None:
        """
        하이퍼파라미터 로깅

        Args:
            run_id: Run ID
            params: 파라미터 딕셔너리
            flatten: 중첩 딕셔너리를 평탄화할지 여부

        Raises:
            MLflowRunError: 파라미터 로깅 실패
        """
        try:
            if flatten:
                params = self._flatten_dict(params)

            for key, value in params.items():
                # MLflow는 문자열만 지원
                self.client.log_param(run_id, key, str(value))

            logger.info(f"파라미터 로깅 완료: {len(params)}개")

        except Exception as e:
            logger.error(f"파라미터 로깅 실패: {e}")
            raise MLflowRunError(f"파라미터 로깅 실패: {str(e)}")

    def _flatten_dict(
        self,
        d: Dict[str, Any],
        parent_key: str = "",
        sep: str = "."
    ) -> Dict[str, Any]:
        """
        중첩 딕셔너리를 평탄화

        Args:
            d: 원본 딕셔너리
            parent_key: 부모 키
            sep: 구분자

        Returns:
            평탄화된 딕셔너리
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    # ========================================================================
    # Metric Logging
    # ========================================================================

    def log_metric(
        self,
        run_id: str,
        key: str,
        value: float,
        step: Optional[int] = None,
        timestamp: Optional[int] = None
    ) -> None:
        """
        단일 메트릭 로깅

        Args:
            run_id: Run ID
            key: 메트릭 이름
            value: 메트릭 값
            step: 스텝 번호
            timestamp: 타임스탬프 (밀리초)

        Raises:
            MLflowRunError: 메트릭 로깅 실패
        """
        try:
            kwargs = {"step": step} if step is not None else {}
            if timestamp is not None:
                kwargs["timestamp"] = timestamp

            self.client.log_metric(run_id, key, value, **kwargs)

        except Exception as e:
            logger.error(f"메트릭 로깅 실패: {e}")
            raise MLflowRunError(f"메트릭 로깅 실패: {str(e)}")

    def log_metrics(
        self,
        run_id: str,
        metrics: Dict[str, float],
        step: Optional[int] = None
    ) -> None:
        """
        여러 메트릭 로깅

        Args:
            run_id: Run ID
            metrics: 메트릭 딕셔너리
            step: 스텝 번호

        Raises:
            MLflowRunError: 메트릭 로깅 실패
        """
        try:
            for key, value in metrics.items():
                self.log_metric(run_id, key, value, step=step)

            logger.info(f"메트릭 로깅 완료: {len(metrics)}개 (step: {step})")

        except Exception as e:
            logger.error(f"메트릭 로깅 실패: {e}")
            raise MLflowRunError(f"메트릭 로깅 실패: {str(e)}")

    # ========================================================================
    # Model Registration
    # ========================================================================

    def register_model(
        self,
        run_id: str,
        model_name: str,
        model_path: str,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """
        모델 등록

        Args:
            run_id: Run ID
            model_name: 모델 이름
            model_path: 모델 경로 (Run 내부 경로)
            tags: 모델 태그

        Returns:
            모델 버전

        Raises:
            MLflowRunError: 모델 등록 실패
        """
        try:
            # 모델 레지스트리에 등록
            try:
                self.client.create_registered_model(model_name, tags=tags or {})
                logger.info(f"새 모델 등록: {model_name}")
            except Exception as e:
                if "RESOURCE_ALREADY_EXISTS" in str(e):
                    logger.info(f"기존 모델 사용: {model_name}")
                else:
                    raise

            # 모델 버전 생성
            model_uri = f"runs:/{run_id}/{model_path}"
            version = self.client.create_model_version(
                name=model_name,
                source=model_uri,
                run_id=run_id
            )

            logger.info(f"모델 버전 생성: {model_name} v{version.version}")
            return version.version

        except Exception as e:
            logger.error(f"모델 등록 실패: {e}")
            raise MLflowRunError(f"모델 등록 실패: {str(e)}")

    # ========================================================================
    # Artifact Logging
    # ========================================================================

    def log_artifact(
        self,
        run_id: str,
        local_path: str,
        artifact_path: Optional[str] = None
    ) -> None:
        """
        파일 아티팩트 로깅

        Args:
            run_id: Run ID
            local_path: 로컬 파일 경로
            artifact_path: MLflow 내부 경로

        Raises:
            MLflowRunError: 아티팩트 로깅 실패
        """
        try:
            self.client.log_artifact(run_id, local_path, artifact_path)
            logger.info(f"아티팩트 로깅 완료: {local_path}")

        except Exception as e:
            logger.error(f"아티팩트 로깅 실패: {e}")
            raise MLflowRunError(f"아티팩트 로깅 실패: {str(e)}")

    def log_artifacts(
        self,
        run_id: str,
        local_dir: str,
        artifact_path: Optional[str] = None
    ) -> None:
        """
        디렉토리 아티팩트 로깅

        Args:
            run_id: Run ID
            local_dir: 로컬 디렉토리 경로
            artifact_path: MLflow 내부 경로

        Raises:
            MLflowRunError: 아티팩트 로깅 실패
        """
        try:
            self.client.log_artifacts(run_id, local_dir, artifact_path)
            logger.info(f"아티팩트 디렉토리 로깅 완료: {local_dir}")

        except Exception as e:
            logger.error(f"아티팩트 로깅 실패: {e}")
            raise MLflowRunError(f"아티팩트 로깅 실패: {str(e)}")
