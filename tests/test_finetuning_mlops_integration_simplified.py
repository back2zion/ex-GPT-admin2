"""
Fine-tuning MLOps Integration Tests (Simplified)
실제 구현된 서비스 API 기반 통합 테스트
"""
import pytest
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import List, Dict

from app.models.training import (
    TrainingDataset,
    FinetuningJob,
    TrainingCheckpoint,
    ModelEvaluation,
    ModelRegistry,
    ModelBenchmark
)
from app.models.ab_test import ABExperiment, ABTestLog, ABTestResult
from app.services.training.ab_test_service import ABTestService
from app.services.training.model_registry_service import ModelRegistryService

logger = logging.getLogger(__name__)


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def mock_db():
    """Mock AsyncSession"""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()

    # Default mock for execute()
    default_result = MagicMock()
    default_scalars = MagicMock()
    default_scalars.all.return_value = []
    default_scalars.first.return_value = None
    default_result.scalars.return_value = default_scalars
    default_result.scalar_one_or_none.return_value = None
    default_result.one_or_none.return_value = None
    db.execute.return_value = default_result

    return db


@pytest.fixture
def sample_model():
    """샘플 모델 레지스트리"""
    return ModelRegistry(
        id=1,
        model_name="test_model_a",
        version="v1.0",
        base_model="Qwen/Qwen2.5-7B-Instruct",
        finetuning_job_id=1,
        model_path="/data/models/test_model_a",
        model_format="huggingface",
        model_size_gb=14.5,
        status="staging",
        deployment_config={
            "gpu_memory_utilization": 0.9,
            "max_model_len": 8192,
            "tensor_parallel_size": 2
        },
        description="테스트 모델 A",
        tags=["legal", "korean", "7b"],
        created_at=datetime.utcnow()
    )


@pytest.fixture
def sample_model_b():
    """샘플 모델 B"""
    return ModelRegistry(
        id=2,
        model_name="test_model_b",
        version="v2.0",
        base_model="Qwen/Qwen2.5-7B-Instruct",
        finetuning_job_id=2,
        model_path="/data/models/test_model_b",
        model_format="huggingface",
        model_size_gb=14.5,
        status="staging",
        description="테스트 모델 B",
        tags=["legal", "korean", "7b"],
        created_at=datetime.utcnow()
    )


# ========================================
# Model Registry Integration Tests
# ========================================

@pytest.mark.integration
class TestModelRegistryIntegration:
    """Model Registry Service 통합 테스트"""

    async def test_list_models_integration(self, mock_db, sample_model, sample_model_b):
        """모델 목록 조회 통합 테스트"""

        # Mock DB 설정
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_model, sample_model_b]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        # ModelRegistryService
        registry_service = ModelRegistryService()

        models = await registry_service.list_models(
            db=mock_db,
            status=None,
            limit=10,
            offset=0
        )

        # 검증
        assert len(models) == 2
        assert models[0].model_name == "test_model_a"
        assert models[1].model_name == "test_model_b"

    async def test_get_model_by_id_integration(self, mock_db, sample_model):
        """모델 ID로 조회 통합 테스트"""

        # Mock DB 설정
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_model
        mock_db.execute.return_value = mock_result

        # ModelRegistryService
        registry_service = ModelRegistryService()

        model = await registry_service.get_model_by_id(db=mock_db, model_id=1)

        # 검증
        assert model.id == 1
        assert model.model_name == "test_model_a"
        assert model.version == "v1.0"

    async def test_add_model_benchmark_integration(self, mock_db, sample_model):
        """모델 벤치마크 추가 통합 테스트"""

        # Mock DB 설정
        mock_model_result = MagicMock()
        mock_model_result.scalar_one_or_none.return_value = sample_model
        mock_db.execute.return_value = mock_model_result

        # ModelRegistryService
        registry_service = ModelRegistryService()

        benchmark = await registry_service.add_benchmark(
            db=mock_db,
            model_id=sample_model.id,
            benchmark_name="mmlu_kr",
            score=0.78,
            details={
                "accuracy": 0.78,
                "f1_score": 0.76,
                "categories": {"law": 0.82, "general": 0.74}
            }
        )

        # 검증
        assert benchmark.model_id == sample_model.id
        assert benchmark.benchmark_name == "mmlu_kr"
        assert benchmark.score == 0.78
        assert benchmark.details["categories"]["law"] == 0.82
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    async def test_archive_model_integration(self, mock_db, sample_model):
        """모델 아카이브 통합 테스트"""

        # Mock DB 설정
        # archive_model calls get_model_by_id internally, so we need 2 mocks
        mock_get_result = MagicMock()
        mock_get_result.scalar_one_or_none.return_value = sample_model

        # Set the model status to staging first, then it will be archived
        sample_model.status = "staging"

        mock_db.execute.return_value = mock_get_result

        # ModelRegistryService
        registry_service = ModelRegistryService()

        archived_model = await registry_service.archive_model(
            db=mock_db,
            model_id=sample_model.id
        )

        # 검증
        assert archived_model.status == "archived"
        mock_db.commit.assert_called()


# ========================================
# A/B Test Service Integration Tests
# ========================================

@pytest.mark.integration
class TestABTestServiceIntegration:
    """A/B Test Service 통합 테스트"""

    async def test_create_experiment_integration(self, mock_db, sample_model, sample_model_b):
        """A/B 실험 생성 통합 테스트"""

        # Mock DB 설정 - 모델 2개 조회
        mock_models = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_model, sample_model_b]
        mock_models.scalars.return_value = mock_scalars

        # Mock: 중복 실험 검사 (없음)
        mock_exp_check = MagicMock()
        mock_exp_check.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [mock_models, mock_exp_check]

        # ABTestService
        ab_test_service = ABTestService()

        experiment = await ab_test_service.create_experiment(
            db=mock_db,
            experiment_name="integration_test_exp",
            model_a_id=sample_model.id,
            model_b_id=sample_model_b.id,
            traffic_split={"a": 0.5, "b": 0.5},
            target_samples=200,
            success_metric="user_rating",
            description="통합 테스트 실험",
            created_by=1
        )

        # 검증
        assert experiment.experiment_name == "integration_test_exp"
        assert experiment.model_a_id == sample_model.id
        assert experiment.model_b_id == sample_model_b.id
        assert experiment.status == "running"
        assert experiment.traffic_split == {"a": 0.5, "b": 0.5}
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    async def test_variant_assignment_sticky_session_integration(self, mock_db):
        """Sticky session 변형 할당 통합 테스트"""

        # 실험 생성
        experiment = ABExperiment(
            id=1,
            experiment_name="sticky_test",
            model_a_id=1,
            model_b_id=2,
            traffic_split={"a": 0.5, "b": 0.5},
            target_samples=100,
            success_metric="user_rating",
            status="running",
            start_date=datetime.utcnow()
        )

        # 기존 로그 (사용자가 이미 변형 A 할당받음)
        existing_log = ABTestLog(
            id=1,
            experiment_id=1,
            user_id=1001,
            session_id="session_123",
            variant="a",
            model_id=1,
            query="테스트 질문",
            response="테스트 응답",
            response_time_ms=200
        )

        # Mock DB 설정
        mock_exp_result = MagicMock()
        mock_exp_result.scalar_one_or_none.return_value = experiment

        mock_log_result = MagicMock()
        mock_log_result.scalar_one_or_none.return_value = existing_log

        mock_db.execute.side_effect = [mock_exp_result, mock_log_result]

        # ABTestService
        ab_test_service = ABTestService()

        variant = await ab_test_service.assign_variant(
            db=mock_db,
            experiment_id=1,
            user_id=1001,
            session_id="session_123"
        )

        # 검증 - Sticky session이므로 동일한 변형 반환
        assert variant == "a"

    async def test_log_interaction_integration(self, mock_db):
        """상호작용 로깅 통합 테스트"""

        # 실험 생성
        experiment = ABExperiment(
            id=1,
            experiment_name="log_test",
            model_a_id=1,
            model_b_id=2,
            traffic_split={"a": 0.5, "b": 0.5},
            target_samples=100,
            success_metric="user_rating",
            status="running",
            start_date=datetime.utcnow()
        )

        # Mock DB 설정
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = experiment
        mock_db.execute.return_value = mock_result

        # ABTestService
        ab_test_service = ABTestService()

        log = await ab_test_service.log_interaction(
            db=mock_db,
            experiment_id=1,
            user_id=1001,
            session_id="session_456",
            variant="a",
            model_id=1,
            query="테스트 질문",
            response="테스트 응답",
            response_time_ms=250,
            user_rating=5,
            user_feedback="매우 좋습니다"
        )

        # 검증
        assert log.experiment_id == 1
        assert log.user_id == 1001
        assert log.variant == "a"
        assert log.user_rating == 5
        assert log.user_feedback == "매우 좋습니다"
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    async def test_calculate_results_integration(self, mock_db):
        """결과 계산 통합 테스트"""

        # 실험 생성
        experiment = ABExperiment(
            id=1,
            experiment_name="results_test",
            model_a_id=1,
            model_b_id=2,
            traffic_split={"a": 0.5, "b": 0.5},
            target_samples=100,
            success_metric="user_rating",
            status="running",
            start_date=datetime.utcnow()
        )

        # Mock DB 설정
        mock_exp_result = MagicMock()
        mock_exp_result.scalar_one_or_none.return_value = experiment

        # Variant A 통계
        mock_stats_a = MagicMock()
        mock_stats_a.total_samples = 50
        mock_stats_a.avg_rating = 4.5
        mock_stats_a.avg_response_time = 250.0
        mock_result_a = MagicMock()
        mock_result_a.one.return_value = mock_stats_a

        # Variant B 통계
        mock_stats_b = MagicMock()
        mock_stats_b.total_samples = 50
        mock_stats_b.avg_rating = 3.8
        mock_stats_b.avg_response_time = 300.0
        mock_result_b = MagicMock()
        mock_result_b.one.return_value = mock_stats_b

        mock_db.execute.side_effect = [mock_exp_result, mock_result_a, mock_result_b]

        # ABTestService
        ab_test_service = ABTestService()

        results = await ab_test_service.calculate_results(
            db=mock_db,
            experiment_id=1
        )

        # 검증
        assert results["a"]["total_samples"] == 50
        assert results["a"]["avg_rating"] == 4.5
        assert results["a"]["avg_response_time"] == 250.0
        assert results["b"]["total_samples"] == 50
        assert results["b"]["avg_rating"] == 3.8
        assert results["b"]["avg_response_time"] == 300.0

    async def test_statistical_significance_integration(self):
        """통계적 유의성 검증 통합 테스트"""

        # ABTestService
        ab_test_service = ABTestService()

        # 충분한 샘플 (30+)과 명확한 차이
        ratings_a = [5.0, 5.0, 4.0, 5.0, 4.0] * 6  # 30 samples, avg ~4.67
        ratings_b = [3.0, 3.0, 2.0, 3.0, 2.0] * 6  # 30 samples, avg ~2.67

        is_significant, p_value = ab_test_service.check_statistical_significance(
            ratings_a=ratings_a,
            ratings_b=ratings_b,
            alpha=0.05
        )

        # 검증 - 명확한 차이이므로 유의미해야 함
        assert is_significant is True
        assert p_value < 0.05
        assert isinstance(p_value, float)

    async def test_confidence_interval_integration(self):
        """신뢰 구간 계산 통합 테스트"""

        # ABTestService
        ab_test_service = ABTestService()

        ratings = [4.0, 5.0, 4.0, 5.0, 4.0, 5.0, 4.0, 5.0] * 3  # 24 samples

        ci = ab_test_service.calculate_confidence_interval(
            data=ratings,
            confidence=0.95
        )

        # 검증
        assert "mean" in ci
        assert "lower" in ci
        assert "upper" in ci
        assert ci["mean"] == 4.5
        assert ci["lower"] < ci["mean"]
        assert ci["upper"] > ci["mean"]


# ========================================
# Cross-Service Integration Tests
# ========================================

@pytest.mark.integration
class TestCrossServiceIntegration:
    """서비스 간 통합 테스트"""

    async def test_model_registry_to_ab_test_integration(
        self, mock_db, sample_model, sample_model_b
    ):
        """ModelRegistry → ABTest 통합 워크플로우"""

        # 1. Mock DB 설정 - 모델 목록 조회
        mock_models = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_model, sample_model_b]
        mock_models.scalars.return_value = mock_scalars

        mock_exp_check = MagicMock()
        mock_exp_check.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [mock_models, mock_exp_check]

        # 2. ModelRegistryService로 모델 확인
        registry_service = ModelRegistryService()

        # (실제로는 list_models를 먼저 호출하지만 여기서는 직접 모델 사용)

        # 3. ABTestService로 실험 생성
        ab_test_service = ABTestService()

        experiment = await ab_test_service.create_experiment(
            db=mock_db,
            experiment_name="cross_service_test",
            model_a_id=sample_model.id,
            model_b_id=sample_model_b.id,
            traffic_split={"a": 0.6, "b": 0.4},
            target_samples=150,
            success_metric="user_rating",
            description="모델 레지스트리 → A/B 테스트 통합",
            created_by=1
        )

        # 4. 검증
        assert experiment.model_a_id == sample_model.id
        assert experiment.model_b_id == sample_model_b.id
        assert experiment.status == "running"
        assert experiment.traffic_split["a"] == 0.6
        assert experiment.traffic_split["b"] == 0.4

    async def test_ab_test_complete_lifecycle_integration(self, mock_db):
        """A/B 테스트 전체 라이프사이클 통합 테스트"""

        # 1. 실험 생성
        model_a = ModelRegistry(id=1, model_name="m1", model_path="/m1", base_model="q1", status="staging")
        model_b = ModelRegistry(id=2, model_name="m2", model_path="/m2", base_model="q2", status="staging")

        mock_models = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [model_a, model_b]
        mock_models.scalars.return_value = mock_scalars

        mock_exp_check = MagicMock()
        mock_exp_check.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [mock_models, mock_exp_check]

        ab_test_service = ABTestService()

        experiment = await ab_test_service.create_experiment(
            db=mock_db,
            experiment_name="lifecycle_test",
            model_a_id=1,
            model_b_id=2,
            traffic_split={"a": 0.5, "b": 0.5},
            target_samples=100,
            success_metric="user_rating",
            created_by=1
        )

        # 2. 실험 중단 테스트
        mock_db.execute.reset_mock()
        mock_db.execute.side_effect = None  # Reset side_effect
        experiment.status = "running"
        mock_stop_result = MagicMock()
        mock_stop_result.scalar_one_or_none.return_value = experiment
        mock_db.execute.return_value = mock_stop_result

        stopped = await ab_test_service.stop_experiment(
            db=mock_db,
            experiment_id=experiment.id,
            reason="테스트 완료",
            stopped_by=1
        )

        # 3. 검증
        assert stopped.status == "stopped"
        mock_db.commit.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
