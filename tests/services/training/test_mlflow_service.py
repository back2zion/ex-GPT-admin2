"""
Test cases for MLflow Service
TDD: Red-Green-Refactor 방식으로 작성

MLflow 연동 테스트:
- Experiment 생성
- Run 생성 및 관리
- 하이퍼파라미터 로깅
- 메트릭 로깅
- 모델 아티팩트 등록

유지보수 용이성:
- Mock을 사용한 외부 의존성 격리
- 명확한 에러 처리
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime

from app.services.training.mlflow_service import (
    MLflowService,
    MLflowConnectionError,
    MLflowExperimentError,
    MLflowRunError
)


class TestMLflowConnection:
    """MLflow 연결 테스트"""

    def test_mlflow_service_initialization(self):
        """정상: MLflow 서비스 초기화"""
        tracking_uri = "http://mlflow:5000"
        service = MLflowService(tracking_uri=tracking_uri)

        assert service.tracking_uri == tracking_uri
        assert service.client is not None

    def test_mlflow_connection_check(self):
        """정상: MLflow 서버 연결 확인"""
        service = MLflowService()

        # Mock MLflow client
        with patch.object(service.client, 'search_experiments') as mock_search:
            mock_search.return_value = []

            result = service.check_connection()

            assert result is True
            mock_search.assert_called_once()

    def test_mlflow_connection_failure(self):
        """실패: MLflow 서버 연결 실패"""
        service = MLflowService()

        with patch.object(service.client, 'search_experiments') as mock_search:
            mock_search.side_effect = Exception("Connection refused")

            with pytest.raises(MLflowConnectionError) as exc_info:
                service.check_connection()

            assert "Connection refused" in str(exc_info.value)


class TestExperimentManagement:
    """Experiment 관리 테스트"""

    @pytest.fixture
    def mlflow_service(self):
        return MLflowService()

    def test_create_experiment_success(self, mlflow_service):
        """정상: Experiment 생성"""
        experiment_name = "finetuning_qwen_v1"

        with patch.object(mlflow_service.client, 'create_experiment') as mock_create:
            mock_create.return_value = "exp123"

            exp_id = mlflow_service.create_experiment(
                name=experiment_name,
                tags={"project": "legal-ai", "model": "qwen"}
            )

            assert exp_id == "exp123"
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            assert call_args[1]["name"] == experiment_name
            assert "project" in call_args[1]["tags"]

    def test_get_or_create_experiment_exists(self, mlflow_service):
        """정상: 기존 Experiment 가져오기"""
        experiment_name = "finetuning_qwen_v1"
        mock_experiment = Mock(experiment_id="exp123")

        with patch.object(mlflow_service.client, 'get_experiment_by_name') as mock_get:
            mock_get.return_value = mock_experiment

            exp_id = mlflow_service.get_or_create_experiment(experiment_name)

            assert exp_id == "exp123"
            mock_get.assert_called_once_with(experiment_name)

    def test_get_or_create_experiment_new(self, mlflow_service):
        """정상: 새 Experiment 생성 (존재하지 않는 경우)"""
        experiment_name = "finetuning_new_model"

        with patch.object(mlflow_service.client, 'get_experiment_by_name') as mock_get:
            with patch.object(mlflow_service.client, 'create_experiment') as mock_create:
                mock_get.return_value = None
                mock_create.return_value = "exp456"

                exp_id = mlflow_service.get_or_create_experiment(experiment_name)

                assert exp_id == "exp456"
                mock_get.assert_called_once()
                mock_create.assert_called_once()

    def test_create_experiment_with_invalid_name(self, mlflow_service):
        """실패: 잘못된 Experiment 이름"""
        with patch.object(mlflow_service.client, 'create_experiment') as mock_create:
            mock_create.side_effect = Exception("Invalid experiment name")

            with pytest.raises(MLflowExperimentError):
                mlflow_service.create_experiment(name="")


class TestRunManagement:
    """Run 관리 테스트"""

    @pytest.fixture
    def mlflow_service(self):
        return MLflowService()

    def test_start_run_success(self, mlflow_service):
        """정상: Run 시작"""
        experiment_id = "exp123"
        run_name = "qwen_training_run_001"

        mock_run = Mock()
        mock_run.info.run_id = "run123"

        with patch.object(mlflow_service.client, 'create_run') as mock_create:
            mock_create.return_value = mock_run

            run_id = mlflow_service.start_run(
                experiment_id=experiment_id,
                run_name=run_name,
                tags={"job_id": "1", "method": "lora"}
            )

            assert run_id == "run123"
            mock_create.assert_called_once()

    def test_end_run_success(self, mlflow_service):
        """정상: Run 종료"""
        run_id = "run123"

        with patch.object(mlflow_service.client, 'set_terminated') as mock_terminate:
            mlflow_service.end_run(run_id, status="FINISHED")

            mock_terminate.assert_called_once_with(run_id, "FINISHED")

    def test_end_run_with_failure(self, mlflow_service):
        """정상: Run 실패로 종료"""
        run_id = "run123"

        with patch.object(mlflow_service.client, 'set_terminated') as mock_terminate:
            mlflow_service.end_run(run_id, status="FAILED")

            mock_terminate.assert_called_once_with(run_id, "FAILED")


class TestParameterLogging:
    """하이퍼파라미터 로깅 테스트"""

    @pytest.fixture
    def mlflow_service(self):
        return MLflowService()

    def test_log_parameters_success(self, mlflow_service):
        """정상: 하이퍼파라미터 로깅"""
        run_id = "run123"
        params = {
            "learning_rate": 2e-4,
            "batch_size": 4,
            "lora_rank": 16,
            "lora_alpha": 32,
            "num_epochs": 3
        }

        with patch.object(mlflow_service.client, 'log_param') as mock_log:
            mlflow_service.log_parameters(run_id, params)

            assert mock_log.call_count == len(params)
            # 각 파라미터가 로깅되었는지 확인
            logged_params = {call[0][1]: call[0][2] for call in mock_log.call_args_list}
            assert logged_params["learning_rate"] == "0.0002"
            assert logged_params["batch_size"] == "4"

    def test_log_parameters_with_nested_dict(self, mlflow_service):
        """정상: 중첩된 딕셔너리 파라미터 로깅"""
        run_id = "run123"
        params = {
            "model_config": {
                "hidden_size": 4096,
                "num_layers": 32
            },
            "training_config": {
                "optimizer": "adamw",
                "scheduler": "cosine"
            }
        }

        with patch.object(mlflow_service.client, 'log_param') as mock_log:
            mlflow_service.log_parameters(run_id, params, flatten=True)

            # 중첩된 딕셔너리가 flatten되어 로깅되었는지 확인
            assert mock_log.call_count == 4
            logged_keys = [call[0][1] for call in mock_log.call_args_list]
            assert "model_config.hidden_size" in logged_keys
            assert "training_config.optimizer" in logged_keys


class TestMetricLogging:
    """메트릭 로깅 테스트"""

    @pytest.fixture
    def mlflow_service(self):
        return MLflowService()

    def test_log_single_metric(self, mlflow_service):
        """정상: 단일 메트릭 로깅"""
        run_id = "run123"

        with patch.object(mlflow_service.client, 'log_metric') as mock_log:
            mlflow_service.log_metric(run_id, "loss", 1.234, step=100)

            mock_log.assert_called_once_with(run_id, "loss", 1.234, step=100)

    def test_log_multiple_metrics(self, mlflow_service):
        """정상: 여러 메트릭 로깅"""
        run_id = "run123"
        metrics = {
            "train_loss": 1.234,
            "eval_loss": 1.456,
            "accuracy": 0.87,
            "perplexity": 3.45
        }

        with patch.object(mlflow_service.client, 'log_metric') as mock_log:
            mlflow_service.log_metrics(run_id, metrics, step=100)

            assert mock_log.call_count == len(metrics)
            for metric_name in metrics:
                assert any(call[0][1] == metric_name for call in mock_log.call_args_list)

    def test_log_metric_with_timestamp(self, mlflow_service):
        """정상: 타임스탬프와 함께 메트릭 로깅"""
        run_id = "run123"
        timestamp = int(datetime.now().timestamp() * 1000)

        with patch.object(mlflow_service.client, 'log_metric') as mock_log:
            mlflow_service.log_metric(
                run_id, "loss", 1.234,
                step=100,
                timestamp=timestamp
            )

            call_args = mock_log.call_args
            assert call_args[1].get("timestamp") == timestamp


class TestModelRegistration:
    """모델 아티팩트 등록 테스트"""

    @pytest.fixture
    def mlflow_service(self):
        return MLflowService()

    def test_register_model_success(self, mlflow_service):
        """정상: 모델 등록"""
        run_id = "run123"
        model_name = "qwen-legal-v1"
        model_path = "/models/checkpoint-1000"

        mock_version = Mock()
        mock_version.version = "1"

        with patch.object(mlflow_service.client, 'create_registered_model') as mock_create:
            with patch.object(mlflow_service.client, 'create_model_version') as mock_version_create:
                mock_create.return_value = Mock(name=model_name)
                mock_version_create.return_value = mock_version

                version = mlflow_service.register_model(
                    run_id=run_id,
                    model_name=model_name,
                    model_path=model_path
                )

                assert version == "1"

    def test_register_model_already_exists(self, mlflow_service):
        """정상: 기존 모델에 새 버전 추가"""
        run_id = "run123"
        model_name = "qwen-legal-v1"
        model_path = "/models/checkpoint-1000"

        mock_version = Mock()
        mock_version.version = "2"

        with patch.object(mlflow_service.client, 'create_registered_model') as mock_create:
            with patch.object(mlflow_service.client, 'create_model_version') as mock_version_create:
                # 모델이 이미 존재하는 경우
                mock_create.side_effect = Exception("RESOURCE_ALREADY_EXISTS")
                mock_version_create.return_value = mock_version

                version = mlflow_service.register_model(
                    run_id=run_id,
                    model_name=model_name,
                    model_path=model_path
                )

                assert version == "2"
                mock_version_create.assert_called_once()


class TestArtifactLogging:
    """아티팩트 로깅 테스트"""

    @pytest.fixture
    def mlflow_service(self):
        return MLflowService()

    def test_log_artifact_file(self, mlflow_service):
        """정상: 파일 아티팩트 로깅"""
        run_id = "run123"
        file_path = "/tmp/training_config.json"

        with patch.object(mlflow_service.client, 'log_artifact') as mock_log:
            mlflow_service.log_artifact(run_id, file_path, artifact_path="config")

            mock_log.assert_called_once_with(run_id, file_path, "config")

    def test_log_artifact_directory(self, mlflow_service):
        """정상: 디렉토리 아티팩트 로깅"""
        run_id = "run123"
        dir_path = "/tmp/checkpoints"

        with patch.object(mlflow_service.client, 'log_artifacts') as mock_log:
            mlflow_service.log_artifacts(run_id, dir_path, artifact_path="checkpoints")

            mock_log.assert_called_once_with(run_id, dir_path, "checkpoints")


class TestIntegration:
    """통합 테스트 (전체 워크플로우)"""

    @pytest.fixture
    def mlflow_service(self):
        return MLflowService()

    def test_full_training_workflow(self, mlflow_service):
        """정상: 전체 학습 워크플로우"""
        # Mocking
        with patch.object(mlflow_service.client, 'get_experiment_by_name') as mock_get_exp:
            with patch.object(mlflow_service.client, 'create_experiment') as mock_create_exp:
                with patch.object(mlflow_service.client, 'create_run') as mock_create_run:
                    with patch.object(mlflow_service.client, 'log_param') as mock_log_param:
                        with patch.object(mlflow_service.client, 'log_metric') as mock_log_metric:
                            with patch.object(mlflow_service.client, 'set_terminated') as mock_terminate:

                                # Setup mocks
                                mock_get_exp.return_value = None
                                mock_create_exp.return_value = "exp123"
                                mock_run = Mock()
                                mock_run.info.run_id = "run123"
                                mock_create_run.return_value = mock_run

                                # 1. Experiment 생성
                                exp_id = mlflow_service.get_or_create_experiment("test_experiment")
                                assert exp_id == "exp123"

                                # 2. Run 시작
                                run_id = mlflow_service.start_run(exp_id, "test_run")
                                assert run_id == "run123"

                                # 3. 파라미터 로깅
                                mlflow_service.log_parameters(run_id, {"lr": 0.001, "batch": 32})
                                assert mock_log_param.call_count == 2

                                # 4. 메트릭 로깅
                                mlflow_service.log_metric(run_id, "loss", 1.5, step=1)
                                mock_log_metric.assert_called_once()

                                # 5. Run 종료
                                mlflow_service.end_run(run_id, "FINISHED")
                                mock_terminate.assert_called_once()
