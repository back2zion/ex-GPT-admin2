"""
Model Registry Service Tests (TDD)
모델 레지스트리 서비스 테스트

책임:
- 모델 등록 (Fine-tuning 작업 → 레지스트리)
- 모델 상태 관리 (staging → production → archived)
- 벤치마크 결과 관리
- 모델 비교 및 검색

TDD Red Phase: 테스트 먼저 작성
"""
import pytest
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

# TDD: 구현 전 - import는 실패할 것으로 예상
from app.services.training.model_registry_service import (
    ModelRegistryService,
    RegistrationError,
    PromotionError,
    ValidationError
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock AsyncSession"""
    db = AsyncMock(spec=AsyncSession)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def registry_service():
    """ModelRegistryService 인스턴스"""
    return ModelRegistryService()


@pytest.fixture
def sample_finetuning_job():
    """샘플 Fine-tuning 작업"""
    job = MagicMock()
    job.id = 1
    job.job_name = "test-finetuning-job"
    job.base_model = "Qwen/Qwen3-7B-Instruct"
    job.method = "lora"
    job.output_dir = "/data/models/finetuned/job_1"
    job.status = "completed"
    job.mlflow_run_id = "mlflow-run-123"
    return job


@pytest.fixture
def sample_model():
    """샘플 모델 레지스트리"""
    model = MagicMock()
    model.id = 1
    model.model_name = "qwen-legal-v1"
    model.version = "1.0.0"
    model.base_model = "Qwen/Qwen3-7B-Instruct"
    model.finetuning_job_id = 1
    model.model_path = "/data/models/registered/qwen-legal-v1"
    model.model_format = "huggingface"
    model.model_size_gb = 14.5
    model.status = "staging"
    model.tags = ["legal", "korean", "7b"]
    model.created_by = 1
    model.created_at = datetime.utcnow()
    return model


# ============================================================================
# Test Class: 모델 등록
# ============================================================================

class TestModelRegistration:
    """모델 등록 테스트"""

    @pytest.mark.asyncio
    async def test_register_model_from_job_success(
        self, registry_service, mock_db, sample_finetuning_job
    ):
        """정상: Fine-tuning 작업에서 모델 등록"""
        # Mock execute 결과 설정
        mock_result = MagicMock()
        mock_db.execute.return_value = mock_result

        registered_model = await registry_service.register_model_from_job(
            db=mock_db,
            job=sample_finetuning_job,
            model_name="qwen-legal-v1",
            version="1.0.0",
            description="Legal domain fine-tuned model",
            tags=["legal", "korean", "7b"],
            created_by=1
        )

        assert registered_model is not None
        assert registered_model.model_name == "qwen-legal-v1"
        assert registered_model.version == "1.0.0"
        assert registered_model.base_model == "Qwen/Qwen3-7B-Instruct"
        assert registered_model.finetuning_job_id == 1
        assert registered_model.status == "staging"
        assert "legal" in registered_model.tags

        # DB 커밋 확인
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_model_job_not_completed(
        self, registry_service, mock_db, sample_finetuning_job
    ):
        """실패: 완료되지 않은 작업"""
        sample_finetuning_job.status = "running"

        with pytest.raises(RegistrationError, match="Job must be completed"):
            await registry_service.register_model_from_job(
                db=mock_db,
                job=sample_finetuning_job,
                model_name="qwen-legal-v1",
                version="1.0.0",
                created_by=1
            )

    @pytest.mark.asyncio
    async def test_register_model_invalid_model_name(
        self, registry_service, mock_db, sample_finetuning_job
    ):
        """실패: 잘못된 모델 이름"""
        with pytest.raises(ValidationError, match="Invalid model name"):
            await registry_service.register_model_from_job(
                db=mock_db,
                job=sample_finetuning_job,
                model_name="../../../etc/passwd",  # 경로 조작
                version="1.0.0",
                created_by=1
            )

    @pytest.mark.asyncio
    async def test_register_model_invalid_version(
        self, registry_service, mock_db, sample_finetuning_job
    ):
        """실패: 잘못된 버전 형식"""
        with pytest.raises(ValidationError, match="Invalid version format"):
            await registry_service.register_model_from_job(
                db=mock_db,
                job=sample_finetuning_job,
                model_name="qwen-legal-v1",
                version="invalid_version!@#",
                created_by=1
            )

    @pytest.mark.asyncio
    async def test_register_model_with_model_size_calculation(
        self, registry_service, mock_db, sample_finetuning_job
    ):
        """정상: 모델 크기 자동 계산"""
        mock_result = MagicMock()
        mock_db.execute.return_value = mock_result

        registered_model = await registry_service.register_model_from_job(
            db=mock_db,
            job=sample_finetuning_job,
            model_name="qwen-legal-v1",
            version="1.0.0",
            created_by=1
        )

        # 모델 크기가 계산되었는지 확인
        # 디렉토리가 없을 경우 0.0 반환
        assert registered_model.model_size_gb is not None
        assert registered_model.model_size_gb >= 0


# ============================================================================
# Test Class: 모델 상태 관리
# ============================================================================

class TestModelPromotion:
    """모델 승격 및 상태 관리 테스트"""

    @pytest.mark.asyncio
    async def test_promote_to_production_success(
        self, registry_service, mock_db, sample_model
    ):
        """정상: Staging → Production 승격"""
        # Mock 조회 결과
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_model
        mock_db.execute.return_value = mock_result

        promoted_model = await registry_service.promote_to_production(
            db=mock_db,
            model_id=1,
            promoted_by=1
        )

        assert promoted_model.status == "production"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_promote_invalid_status_transition(
        self, registry_service, mock_db, sample_model
    ):
        """실패: 잘못된 상태 전환 (archived → production)"""
        sample_model.status = "archived"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_model
        mock_db.execute.return_value = mock_result

        with pytest.raises(PromotionError, match="Cannot promote"):
            await registry_service.promote_to_production(
                db=mock_db,
                model_id=1,
                promoted_by=1
            )

    @pytest.mark.asyncio
    async def test_demote_current_production_model(
        self, registry_service, mock_db, sample_model
    ):
        """정상: 기존 Production 모델 자동 Archived"""
        # 새 모델
        sample_model.status = "staging"

        # 기존 production 모델
        old_production_model = MagicMock()
        old_production_model.id = 999
        old_production_model.model_name = "qwen-legal-v1"
        old_production_model.status = "production"

        # Mock: 같은 이름의 production 모델 조회
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = sample_model

        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = old_production_model

        mock_db.execute.side_effect = [mock_result1, mock_result2]

        promoted_model = await registry_service.promote_to_production(
            db=mock_db,
            model_id=1,
            promoted_by=1
        )

        # 새 모델은 production, 기존 모델은 archived
        assert promoted_model.status == "production"
        assert old_production_model.status == "archived"

    @pytest.mark.asyncio
    async def test_archive_model_success(
        self, registry_service, mock_db, sample_model
    ):
        """정상: 모델 Archived"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_model
        mock_db.execute.return_value = mock_result

        archived_model = await registry_service.archive_model(
            db=mock_db,
            model_id=1
        )

        assert archived_model.status == "archived"
        mock_db.commit.assert_called_once()


# ============================================================================
# Test Class: 모델 조회
# ============================================================================

class TestModelQuery:
    """모델 조회 테스트"""

    @pytest.mark.asyncio
    async def test_list_models_with_filters(
        self, registry_service, mock_db
    ):
        """정상: 필터링된 모델 목록 조회"""
        # Mock 결과
        mock_result = MagicMock()
        mock_models = [MagicMock() for _ in range(3)]
        mock_result.scalars.return_value.all.return_value = mock_models
        mock_db.execute.return_value = mock_result

        models = await registry_service.list_models(
            db=mock_db,
            status="production",
            base_model="Qwen/Qwen3-7B-Instruct",
            limit=10,
            offset=0
        )

        assert len(models) == 3
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_model_by_id_success(
        self, registry_service, mock_db, sample_model
    ):
        """정상: ID로 모델 조회"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_model
        mock_db.execute.return_value = mock_result

        model = await registry_service.get_model_by_id(
            db=mock_db,
            model_id=1
        )

        assert model is not None
        assert model.id == 1
        assert model.model_name == "qwen-legal-v1"

    @pytest.mark.asyncio
    async def test_get_model_by_id_not_found(
        self, registry_service, mock_db
    ):
        """실패: 존재하지 않는 모델"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        model = await registry_service.get_model_by_id(
            db=mock_db,
            model_id=999
        )

        assert model is None

    @pytest.mark.asyncio
    async def test_search_models_by_tags(
        self, registry_service, mock_db
    ):
        """정상: 태그로 모델 검색"""
        mock_result = MagicMock()
        mock_models = [MagicMock() for _ in range(2)]
        mock_result.scalars.return_value.all.return_value = mock_models
        mock_db.execute.return_value = mock_result

        models = await registry_service.search_by_tags(
            db=mock_db,
            tags=["legal", "korean"]
        )

        assert len(models) == 2


# ============================================================================
# Test Class: 벤치마크 관리
# ============================================================================

class TestBenchmarkManagement:
    """벤치마크 관리 테스트"""

    @pytest.mark.asyncio
    async def test_add_benchmark_success(
        self, registry_service, mock_db, sample_model
    ):
        """정상: 벤치마크 결과 추가"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_model
        mock_db.execute.return_value = mock_result

        benchmark = await registry_service.add_benchmark(
            db=mock_db,
            model_id=1,
            benchmark_name="mmlu_kr",
            score=0.85,
            details={"accuracy": 0.85, "f1": 0.83}
        )

        assert benchmark is not None
        assert benchmark.benchmark_name == "mmlu_kr"
        assert benchmark.score == 0.85
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_benchmark_invalid_score(
        self, registry_service, mock_db, sample_model
    ):
        """실패: 잘못된 점수 (범위 초과)"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_model
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValidationError, match="Score must be between 0 and 1"):
            await registry_service.add_benchmark(
                db=mock_db,
                model_id=1,
                benchmark_name="mmlu_kr",
                score=1.5,  # 범위 초과
                details={}
            )

    @pytest.mark.asyncio
    async def test_get_benchmarks_for_model(
        self, registry_service, mock_db
    ):
        """정상: 모델별 벤치마크 조회"""
        mock_result = MagicMock()
        mock_benchmarks = [MagicMock() for _ in range(3)]
        mock_result.scalars.return_value.all.return_value = mock_benchmarks
        mock_db.execute.return_value = mock_result

        benchmarks = await registry_service.get_benchmarks_for_model(
            db=mock_db,
            model_id=1
        )

        assert len(benchmarks) == 3

    @pytest.mark.asyncio
    async def test_compare_models_by_benchmark(
        self, registry_service, mock_db
    ):
        """정상: 벤치마크 기준 모델 비교"""
        # Mock 여러 모델의 벤치마크 (필터링된 결과)
        mock_result = MagicMock()

        # benchmark_name="mmlu_kr"로 필터링된 결과만
        filtered_benchmarks = [
            MagicMock(model_id=1, benchmark_name="mmlu_kr", score=0.85,
                     benchmark_date=MagicMock(), details={}),
            MagicMock(model_id=2, benchmark_name="mmlu_kr", score=0.82,
                     benchmark_date=MagicMock(), details={})
        ]

        mock_result.scalars.return_value.all.return_value = filtered_benchmarks
        mock_db.execute.return_value = mock_result

        comparison = await registry_service.compare_models(
            db=mock_db,
            model_ids=[1, 2],
            benchmark_name="mmlu_kr"
        )

        assert len(comparison) == 2
        assert comparison[0]["model_id"] == 1
        assert comparison[0]["score"] == 0.85
        assert comparison[1]["model_id"] == 2
        assert comparison[1]["score"] == 0.82


# ============================================================================
# Test Class: 시큐어 코딩
# ============================================================================

class TestSecurityValidation:
    """시큐어 코딩: 입력 검증 및 보안"""

    @pytest.mark.asyncio
    async def test_prevent_path_traversal_in_model_name(
        self, registry_service, mock_db, sample_finetuning_job
    ):
        """시큐어: 모델 이름 경로 조작 방지"""
        with pytest.raises(ValidationError, match="Invalid model name"):
            await registry_service.register_model_from_job(
                db=mock_db,
                job=sample_finetuning_job,
                model_name="../../malicious",
                version="1.0.0",
                created_by=1
            )

    @pytest.mark.asyncio
    async def test_validate_tag_format(
        self, registry_service
    ):
        """시큐어: 태그 형식 검증"""
        # 정상 태그
        assert registry_service.validate_tags(["legal", "korean", "7b"]) is True

        # 잘못된 태그 (특수문자)
        assert registry_service.validate_tags(["legal@#$", "korean"]) is False

        # 너무 긴 태그
        assert registry_service.validate_tags(["a" * 100]) is False

        # 빈 태그
        assert registry_service.validate_tags([""]) is False

    @pytest.mark.asyncio
    async def test_prevent_sql_injection_in_search(
        self, registry_service, mock_db
    ):
        """시큐어: SQL Injection 방지"""
        # SQLAlchemy는 기본적으로 파라미터화 쿼리 사용
        # 하지만 명시적 검증도 추가
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        # 악의적인 입력
        models = await registry_service.search_by_tags(
            db=mock_db,
            tags=["'; DROP TABLE model_registry; --"]
        )

        # 쿼리는 실행되지만 안전하게 처리됨
        assert models == []


# ============================================================================
# Test Class: 통합 시나리오
# ============================================================================

class TestModelLifecycle:
    """모델 생명주기 통합 테스트"""

    @pytest.mark.asyncio
    async def test_full_model_lifecycle(
        self, registry_service, mock_db, sample_finetuning_job
    ):
        """정상: 모델 등록 → 벤치마크 → 승격 → 아카이브"""
        # Step 1: 모델 등록
        registered_model = MagicMock()
        registered_model.id = 1
        registered_model.status = "staging"
        registered_model.model_name = "qwen-legal-v1"

        model = await registry_service.register_model_from_job(
            db=mock_db,
            job=sample_finetuning_job,
            model_name="qwen-legal-v1",
            version="1.0.0",
            created_by=1
        )
        assert model.status == "staging"

        # Step 2: 벤치마크 추가
        # Mock 모델 조회 (벤치마크 추가 시)
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = registered_model
        mock_db.execute.return_value = mock_result2

        benchmark = await registry_service.add_benchmark(
            db=mock_db,
            model_id=model.id,
            benchmark_name="mmlu_kr",
            score=0.90,
            details={}
        )
        assert benchmark.score == 0.90

        # Step 3: Production 승격
        # Mock: 첫 번째 조회 (모델 조회), 두 번째 조회 (기존 production 모델 없음)
        mock_result3 = MagicMock()
        mock_result3.scalar_one_or_none.return_value = registered_model

        mock_result4 = MagicMock()
        mock_result4.scalar_one_or_none.return_value = None  # 기존 production 모델 없음

        mock_db.execute.side_effect = [mock_result3, mock_result4]

        promoted_model = await registry_service.promote_to_production(
            db=mock_db,
            model_id=model.id,
            promoted_by=1
        )
        # 승격 후 상태 변경 확인
        assert promoted_model.status == "production"

        # Step 4: 아카이브
        mock_result5 = MagicMock()
        mock_result5.scalar_one_or_none.return_value = promoted_model
        mock_db.execute.side_effect = None
        mock_db.execute.return_value = mock_result5

        archived_model = await registry_service.archive_model(
            db=mock_db,
            model_id=model.id
        )
        assert archived_model.status == "archived"
