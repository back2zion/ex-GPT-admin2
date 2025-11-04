"""
A/B Test Service Tests (TDD)
A/B 테스트 서비스 테스트

책임:
- A/B 테스트 실험 생성 및 관리
- Variant 할당 (sticky session)
- 상호작용 로그 기록
- 통계 분석 및 유의성 검증
- 자동 승자 결정

TDD Red Phase: 테스트 먼저 작성
"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, MagicMock

# TDD: 구현 전 - import는 실패할 것으로 예상
from app.services.training.ab_test_service import (
    ABTestService,
    ExperimentError,
    StatisticalTestError,
    ValidationError
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock AsyncSession"""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()

    # Default mock for execute() - returns proper structure for scalars().all()
    default_result = MagicMock()
    default_scalars = MagicMock()
    default_scalars.all.return_value = [MagicMock(id=1), MagicMock(id=2)]  # Mock models
    default_result.scalars.return_value = default_scalars
    default_result.scalar_one_or_none.return_value = None
    db.execute.return_value = default_result

    return db


@pytest.fixture
def ab_test_service():
    """ABTestService 인스턴스"""
    return ABTestService()


@pytest.fixture
def sample_experiment():
    """샘플 A/B 테스트 실험"""
    experiment = MagicMock()
    experiment.id = 1
    experiment.experiment_name = "qwen-vs-llama-test"
    experiment.model_a_id = 1
    experiment.model_b_id = 2
    experiment.traffic_split = {"a": 0.5, "b": 0.5}
    experiment.status = "running"
    experiment.target_samples = 200
    experiment.success_metric = "user_rating"
    return experiment


# ============================================================================
# Test Class: 실험 생성
# ============================================================================

class TestExperimentCreation:
    """A/B 테스트 실험 생성 테스트"""

    @pytest.mark.asyncio
    async def test_create_experiment_success(self, ab_test_service, mock_db):
        """정상: A/B 테스트 실험 생성"""
        experiment = await ab_test_service.create_experiment(
            db=mock_db,
            experiment_name="qwen-vs-llama-test",
            model_a_id=1,
            model_b_id=2,
            description="Qwen vs Llama performance comparison",
            traffic_split={"a": 0.5, "b": 0.5},
            target_samples=200,
            success_metric="user_rating",
            created_by=1
        )

        assert experiment is not None
        assert experiment.experiment_name == "qwen-vs-llama-test"
        assert experiment.model_a_id == 1
        assert experiment.model_b_id == 2
        assert experiment.status == "running"
        assert experiment.traffic_split["a"] == 0.5

        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_experiment_same_models(self, ab_test_service, mock_db):
        """실패: 동일한 모델 A/B 테스트"""
        with pytest.raises(ValidationError, match="Model A and Model B cannot be the same"):
            await ab_test_service.create_experiment(
                db=mock_db,
                experiment_name="invalid-test",
                model_a_id=1,
                model_b_id=1,  # 동일한 모델
                created_by=1
            )

    @pytest.mark.asyncio
    async def test_create_experiment_invalid_traffic_split(self, ab_test_service, mock_db):
        """실패: 잘못된 트래픽 분할"""
        with pytest.raises(ValidationError, match="Traffic split must sum to 1.0"):
            await ab_test_service.create_experiment(
                db=mock_db,
                experiment_name="invalid-split",
                model_a_id=1,
                model_b_id=2,
                traffic_split={"a": 0.6, "b": 0.6},  # 합이 1.0이 아님
                created_by=1
            )

    @pytest.mark.asyncio
    async def test_create_experiment_invalid_target_samples(self, ab_test_service, mock_db):
        """실패: 너무 작은 샘플 수"""
        with pytest.raises(ValidationError, match="Target samples must be at least 30"):
            await ab_test_service.create_experiment(
                db=mock_db,
                experiment_name="small-sample",
                model_a_id=1,
                model_b_id=2,
                target_samples=10,  # 너무 작음
                created_by=1
            )


# ============================================================================
# Test Class: Variant 할당
# ============================================================================

class TestVariantAssignment:
    """Variant 할당 테스트"""

    @pytest.mark.asyncio
    async def test_assign_variant_new_user(self, ab_test_service, mock_db, sample_experiment):
        """정상: 새 사용자에게 variant 할당"""
        # Mock 1: 실험 조회 (성공)
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = sample_experiment

        # Mock 2: 기존 로그 조회 (없음)
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [mock_result1, mock_result2]

        variant = await ab_test_service.assign_variant(
            db=mock_db,
            experiment_id=1,
            user_id=100,
            session_id="session-123"
        )

        assert variant in ["a", "b"]

    @pytest.mark.asyncio
    async def test_assign_variant_sticky_session(self, ab_test_service, mock_db, sample_experiment):
        """정상: Sticky session (동일 사용자는 동일 variant)"""
        # 첫 번째 할당
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = sample_experiment

        # 기존 로그 없음
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [mock_result1, mock_result2]

        variant1 = await ab_test_service.assign_variant(
            db=mock_db,
            experiment_id=1,
            user_id=100,
            session_id="session-123"
        )

        # 두 번째 요청 (기존 로그 있음)
        existing_log = MagicMock()
        existing_log.variant = variant1

        mock_result3 = MagicMock()
        mock_result3.scalar_one_or_none.return_value = sample_experiment

        mock_result4 = MagicMock()
        mock_result4.scalar_one_or_none.return_value = existing_log

        mock_db.execute.side_effect = [mock_result3, mock_result4]

        variant2 = await ab_test_service.assign_variant(
            db=mock_db,
            experiment_id=1,
            user_id=100,
            session_id="session-123"
        )

        # 동일한 variant 할당
        assert variant1 == variant2

    @pytest.mark.asyncio
    async def test_assign_variant_respects_traffic_split(self, ab_test_service, mock_db, sample_experiment):
        """정상: 트래픽 분할 비율 준수"""
        # 90/10 split
        sample_experiment.traffic_split = {"a": 0.9, "b": 0.1}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_experiment

        # 로그 없음 (신규 사용자)
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [mock_result, mock_result2] * 100

        variants = []
        for i in range(100):
            variant = await ab_test_service.assign_variant(
                db=mock_db,
                experiment_id=1,
                user_id=1000 + i,
                session_id=f"session-{i}"
            )
            variants.append(variant)

        # 대략 90:10 비율 확인 (오차 허용)
        a_count = variants.count("a")
        assert 80 <= a_count <= 100  # 80~100% 범위


# ============================================================================
# Test Class: 로그 기록
# ============================================================================

class TestInteractionLogging:
    """상호작용 로그 기록 테스트"""

    @pytest.mark.asyncio
    async def test_log_interaction_success(self, ab_test_service, mock_db, sample_experiment):
        """정상: 상호작용 로그 기록"""
        # Mock: 실험 조회 (성공)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_experiment
        mock_db.execute.return_value = mock_result

        log = await ab_test_service.log_interaction(
            db=mock_db,
            experiment_id=1,
            user_id=100,
            session_id="session-123",
            variant="a",
            model_id=1,
            query="What is the capital of France?",
            response="The capital of France is Paris.",
            response_time_ms=250,
            user_rating=5,
            user_feedback="Very accurate!"
        )

        assert log is not None
        assert log.variant == "a"
        assert log.user_rating == 5
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_interaction_invalid_rating(self, ab_test_service, mock_db):
        """실패: 잘못된 평점"""
        with pytest.raises(ValidationError, match="User rating must be between 1 and 5"):
            await ab_test_service.log_interaction(
                db=mock_db,
                experiment_id=1,
                user_id=100,
                session_id="session-123",
                variant="a",
                model_id=1,
                query="Test",
                response="Response",
                response_time_ms=100,
                user_rating=10,  # 범위 초과
                user_feedback=None
            )

    @pytest.mark.asyncio
    async def test_log_interaction_invalid_variant(self, ab_test_service, mock_db):
        """실패: 잘못된 variant"""
        with pytest.raises(ValidationError, match="Variant must be 'a' or 'b'"):
            await ab_test_service.log_interaction(
                db=mock_db,
                experiment_id=1,
                user_id=100,
                session_id="session-123",
                variant="c",  # 잘못된 variant
                model_id=1,
                query="Test",
                response="Response",
                response_time_ms=100,
                user_rating=5,
                user_feedback=None
            )


# ============================================================================
# Test Class: 통계 분석
# ============================================================================

class TestStatisticalAnalysis:
    """통계 분석 테스트"""

    @pytest.mark.asyncio
    async def test_calculate_results_success(self, ab_test_service, mock_db, sample_experiment):
        """정상: 실험 결과 계산"""
        # Mock 1: 실험 조회
        mock_result_exp = MagicMock()
        mock_result_exp.scalar_one_or_none.return_value = sample_experiment

        # Mock 2: Variant A 통계 (count, avg_rating, avg_response_time)
        mock_result_a = MagicMock()
        mock_stats_a = MagicMock()
        mock_stats_a.total_samples = 3
        mock_stats_a.avg_rating = 4.67
        mock_stats_a.avg_response_time = 250.0
        mock_result_a.one.return_value = mock_stats_a

        # Mock 3: Variant B 통계
        mock_result_b = MagicMock()
        mock_stats_b = MagicMock()
        mock_stats_b.total_samples = 3
        mock_stats_b.avg_rating = 3.33
        mock_stats_b.avg_response_time = 300.0
        mock_result_b.one.return_value = mock_stats_b

        mock_db.execute.side_effect = [mock_result_exp, mock_result_a, mock_result_b]

        results = await ab_test_service.calculate_results(
            db=mock_db,
            experiment_id=1
        )

        assert "a" in results
        assert "b" in results
        assert results["a"]["avg_rating"] > results["b"]["avg_rating"]

    @pytest.mark.asyncio
    async def test_check_statistical_significance(self, ab_test_service):
        """정상: 통계적 유의성 검증"""
        # A가 B보다 명확히 좋은 경우 (30+ 샘플)
        ratings_a = [5, 5, 4, 5, 4, 5, 5, 4, 5, 5, 5, 4, 5, 4, 5, 5, 4, 5, 5, 5, 4, 5, 4, 5, 5, 4, 5, 5, 5, 4]
        ratings_b = [3, 3, 2, 3, 2, 3, 3, 2, 3, 3, 3, 2, 3, 2, 3, 3, 2, 3, 3, 3, 2, 3, 2, 3, 3, 2, 3, 3, 3, 2]

        is_significant, p_value = ab_test_service.check_statistical_significance(
            ratings_a=ratings_a,
            ratings_b=ratings_b,
            alpha=0.05
        )

        assert is_significant is True
        assert p_value < 0.05

    @pytest.mark.asyncio
    async def test_check_statistical_significance_insufficient_samples(self, ab_test_service):
        """실패: 샘플 수 부족"""
        ratings_a = [5, 4]
        ratings_b = [3, 2]

        with pytest.raises(StatisticalTestError, match="Insufficient samples"):
            ab_test_service.check_statistical_significance(
                ratings_a=ratings_a,
                ratings_b=ratings_b
            )

    @pytest.mark.asyncio
    async def test_calculate_confidence_interval(self, ab_test_service):
        """정상: 신뢰구간 계산"""
        ratings = [4, 5, 4, 5, 3, 4, 5, 4, 5, 4]

        ci = ab_test_service.calculate_confidence_interval(
            data=ratings,
            confidence=0.95
        )

        assert "lower" in ci
        assert "upper" in ci
        assert ci["lower"] < ci["upper"]
        assert 3.0 <= ci["lower"] <= 5.0
        assert 3.0 <= ci["upper"] <= 5.0


# ============================================================================
# Test Class: 실험 종료
# ============================================================================

class TestExperimentConclusion:
    """실험 종료 테스트"""

    @pytest.mark.asyncio
    async def test_conclude_experiment_with_winner(self, ab_test_service, mock_db, sample_experiment):
        """정상: 승자가 있는 실험 종료"""
        # Mock 실험 조회
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = sample_experiment
        mock_db.execute.return_value = mock_result1

        conclusion = await ab_test_service.conclude_experiment(
            db=mock_db,
            experiment_id=1,
            winner_variant="a",
            reason="Model A has statistically significant better performance"
        )

        assert conclusion["winner"] == "a"
        assert conclusion["experiment_status"] == "completed"
        assert sample_experiment.status == "completed"
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_conclude_experiment_invalid_variant(self, ab_test_service, mock_db, sample_experiment):
        """실패: 잘못된 승자 variant"""
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = sample_experiment
        mock_db.execute.return_value = mock_result1

        with pytest.raises(ValidationError, match="Winner must be 'a' or 'b'"):
            await ab_test_service.conclude_experiment(
                db=mock_db,
                experiment_id=1,
                winner_variant="c",
                reason="Test"
            )

    @pytest.mark.asyncio
    async def test_stop_experiment(self, ab_test_service, mock_db, sample_experiment):
        """정상: 실험 중단 (승자 없음)"""
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = sample_experiment
        mock_db.execute.return_value = mock_result1

        await ab_test_service.stop_experiment(
            db=mock_db,
            experiment_id=1,
            reason="Experiment stopped by admin"
        )

        assert sample_experiment.status == "stopped"
        mock_db.commit.assert_called()


# ============================================================================
# Test Class: 시큐어 코딩
# ============================================================================

class TestSecurityValidation:
    """시큐어 코딩: 입력 검증 및 보안"""

    @pytest.mark.asyncio
    async def test_prevent_sql_injection_in_query(self, ab_test_service, mock_db, sample_experiment):
        """시큐어: SQL Injection 방지"""
        # Mock: 실험 조회 (성공)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_experiment
        mock_db.execute.return_value = mock_result

        # SQLAlchemy parameterized query 사용
        log = await ab_test_service.log_interaction(
            db=mock_db,
            experiment_id=1,
            user_id=100,
            session_id="session-123",
            variant="a",
            model_id=1,
            query="'; DROP TABLE ab_test_logs; --",  # SQL Injection 시도
            response="Safe response",
            response_time_ms=100,
            user_rating=5,
            user_feedback=None
        )

        # 안전하게 처리됨
        assert log.query == "'; DROP TABLE ab_test_logs; --"

    @pytest.mark.asyncio
    async def test_validate_experiment_name(self, ab_test_service, mock_db):
        """시큐어: 실험 이름 검증"""
        with pytest.raises(ValidationError, match="Invalid experiment name"):
            await ab_test_service.create_experiment(
                db=mock_db,
                experiment_name="../../etc/passwd",  # 경로 조작
                model_a_id=1,
                model_b_id=2,
                created_by=1
            )

    @pytest.mark.asyncio
    async def test_validate_traffic_split_range(self, ab_test_service, mock_db):
        """시큐어: 트래픽 분할 범위 검증"""
        with pytest.raises(ValidationError, match="must be between 0 and 1"):
            await ab_test_service.create_experiment(
                db=mock_db,
                experiment_name="invalid-range",
                model_a_id=1,
                model_b_id=2,
                traffic_split={"a": 1.5, "b": -0.5},  # 범위 초과
                created_by=1
            )


# ============================================================================
# Test Class: 통합 시나리오
# ============================================================================

class TestABTestWorkflow:
    """A/B 테스트 전체 워크플로우 통합 테스트"""

    @pytest.mark.asyncio
    async def test_full_ab_test_workflow(self, ab_test_service, mock_db, sample_experiment):
        """정상: 전체 A/B 테스트 워크플로우"""
        # Step 1: 실험 생성 (mocked)
        # Create_experiment에서 필요한 모든 mocks 설정
        # Mock 1: 모델 존재 확인 (2개 모델)
        mock_models = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [MagicMock(id=1), MagicMock(id=2)]
        mock_models.scalars.return_value = mock_scalars

        # Mock 2: 기존 실험 없음 (중복 체크)
        mock_check = MagicMock()
        mock_check.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [mock_models, mock_check]

        experiment = await ab_test_service.create_experiment(
            db=mock_db,
            experiment_name="full-workflow-test",
            model_a_id=1,
            model_b_id=2,
            created_by=1
        )
        assert experiment.status == "running"

        # Step 2: Variant 할당
        # Mock: 실험 조회 + 기존 로그 없음
        mock_exp = MagicMock()
        mock_exp.scalar_one_or_none.return_value = experiment
        mock_no_log = MagicMock()
        mock_no_log.scalar_one_or_none.return_value = None

        mock_db.execute.reset_mock()
        mock_db.execute.side_effect = [mock_exp, mock_no_log]

        variant = await ab_test_service.assign_variant(
            db=mock_db,
            experiment_id=experiment.id,
            user_id=100,
            session_id="session-123"
        )
        assert variant in ["a", "b"]

        # Step 3: 로그 기록
        # Mock: 실험 조회
        mock_exp2 = MagicMock()
        mock_exp2.scalar_one_or_none.return_value = experiment

        mock_db.execute.reset_mock()
        mock_db.execute.side_effect = None
        mock_db.execute.return_value = mock_exp2

        log = await ab_test_service.log_interaction(
            db=mock_db,
            experiment_id=experiment.id,
            user_id=100,
            session_id="session-123",
            variant=variant,
            model_id=1,
            query="Test query",
            response="Test response",
            response_time_ms=150,
            user_rating=5,
            user_feedback="Great!"
        )
        assert log.user_rating == 5

        # Step 4: 실험 종료
        # Mock: conclude -> get_experiment, calculate_results -> get_experiment + stats A + stats B
        # Total: 4 execute calls needed
        mock_exp3a = MagicMock()
        mock_exp3a.scalar_one_or_none.return_value = experiment

        mock_exp3b = MagicMock()
        mock_exp3b.scalar_one_or_none.return_value = experiment

        mock_stats_a = MagicMock()
        mock_stats_a.total_samples = 10
        mock_stats_a.avg_rating = 4.5
        mock_stats_a.avg_response_time = 200.0
        mock_result_a = MagicMock()
        mock_result_a.one.return_value = mock_stats_a

        mock_stats_b = MagicMock()
        mock_stats_b.total_samples = 10
        mock_stats_b.avg_rating = 3.5
        mock_stats_b.avg_response_time = 250.0
        mock_result_b = MagicMock()
        mock_result_b.one.return_value = mock_stats_b

        mock_db.execute.reset_mock()
        mock_db.execute.side_effect = [mock_exp3a, mock_exp3b, mock_result_a, mock_result_b]

        conclusion = await ab_test_service.conclude_experiment(
            db=mock_db,
            experiment_id=experiment.id,
            winner_variant="a",
            reason="Model A wins"
        )
        assert conclusion["winner"] == "a"
        assert experiment.status == "completed"
