"""
Model Registry Service
모델 레지스트리 관리 서비스

책임:
- Fine-tuned 모델 등록 및 버전 관리
- 모델 상태 관리 (staging → production → archived)
- 모델 메타데이터 및 태그 관리
- 벤치마크 결과 관리
- 모델 검색 및 비교
"""
import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.training import (
    ModelRegistry,
    ModelBenchmark,
    FinetuningJob
)

logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exceptions
# ============================================================================

class RegistrationError(Exception):
    """모델 등록 중 발생하는 에러"""
    pass


class PromotionError(Exception):
    """모델 승격 중 발생하는 에러"""
    pass


class ValidationError(Exception):
    """입력 검증 에러"""
    pass


# ============================================================================
# ModelRegistryService
# ============================================================================

class ModelRegistryService:
    """
    모델 레지스트리 관리 서비스

    주요 기능:
    1. 모델 등록 (Fine-tuning 작업 → 레지스트리)
    2. 모델 상태 관리 (staging, production, archived)
    3. 벤치마크 관리
    4. 모델 검색 및 비교
    """

    # 허용된 모델 상태
    VALID_STATUSES = {"staging", "production", "archived"}

    # 허용된 모델 포맷
    VALID_FORMATS = {"huggingface", "gguf", "awq"}

    # 태그 검증 패턴 (영문, 숫자, 하이픈, 언더스코어만)
    TAG_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    MAX_TAG_LENGTH = 50

    # 버전 패턴 (semantic versioning)
    VERSION_PATTERN = re.compile(r'^\d+\.\d+\.\d+$')

    def __init__(self):
        """초기화"""
        pass

    # ========================================================================
    # 모델 등록
    # ========================================================================

    async def register_model_from_job(
        self,
        db: AsyncSession,
        job: FinetuningJob,
        model_name: str,
        version: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        deployment_config: Optional[Dict[str, Any]] = None,
        created_by: int = None
    ) -> ModelRegistry:
        """
        Fine-tuning 작업에서 모델 등록

        Args:
            db: DB 세션
            job: Fine-tuning 작업
            model_name: 모델 이름
            version: 모델 버전
            description: 설명
            tags: 태그 리스트
            deployment_config: 배포 설정
            created_by: 등록자 ID

        Returns:
            등록된 모델

        Raises:
            RegistrationError: 등록 실패
            ValidationError: 검증 실패
        """
        try:
            # 1. 작업 상태 검증
            if job.status != "completed":
                raise RegistrationError(f"Job must be completed. Current status: {job.status}")

            # 2. 입력 검증
            self._validate_model_name(model_name)
            self._validate_version(version)

            if tags:
                if not self.validate_tags(tags):
                    raise ValidationError("Invalid tag format")

            # 3. 모델 경로 생성
            model_path = self._generate_model_path(model_name, version)

            # 4. 모델 크기 계산
            model_size_gb = self._calculate_model_size(job.output_dir)

            # 5. ModelRegistry 생성
            model = ModelRegistry(
                model_name=model_name,
                version=version,
                base_model=job.base_model,
                finetuning_job_id=job.id,
                model_path=model_path,
                model_format="huggingface",  # 기본값
                model_size_gb=model_size_gb,
                status="staging",  # 새 모델은 staging으로 시작
                deployment_config=deployment_config,
                mlflow_model_uri=f"runs:/{job.mlflow_run_id}/model" if job.mlflow_run_id else None,
                description=description,
                tags=tags or [],
                created_by=created_by,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            db.add(model)
            await db.commit()
            await db.refresh(model)

            logger.info(f"모델 등록 완료: {model_name} v{version} (ID: {model.id})")

            return model

        except (RegistrationError, ValidationError):
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"모델 등록 실패: {e}")
            raise RegistrationError(f"Failed to register model: {e}")

    def _validate_model_name(self, model_name: str) -> None:
        """모델 이름 검증"""
        if not model_name or len(model_name) > 255:
            raise ValidationError("Model name must be between 1 and 255 characters")

        # 경로 조작 방지
        if ".." in model_name or "/" in model_name or "\\" in model_name:
            raise ValidationError(f"Invalid model name: {model_name}")

        # 특수문자 제한 (영문, 숫자, 하이픈, 언더스코어만)
        if not re.match(r'^[a-zA-Z0-9_-]+$', model_name):
            raise ValidationError(f"Model name contains invalid characters: {model_name}")

    def _validate_version(self, version: str) -> None:
        """버전 형식 검증 (semantic versioning)"""
        if not self.VERSION_PATTERN.match(version):
            raise ValidationError(
                f"Invalid version format: {version}. Expected format: X.Y.Z (e.g., 1.0.0)"
            )

    def validate_tags(self, tags: List[str]) -> bool:
        """
        태그 형식 검증

        Args:
            tags: 태그 리스트

        Returns:
            검증 통과 여부
        """
        if not tags:
            return True

        for tag in tags:
            # 빈 태그
            if not tag:
                return False

            # 길이 검증
            if len(tag) > self.MAX_TAG_LENGTH:
                return False

            # 패턴 검증
            if not self.TAG_PATTERN.match(tag):
                return False

        return True

    def _generate_model_path(self, model_name: str, version: str) -> str:
        """모델 저장 경로 생성"""
        return f"/data/models/registered/{model_name}/v{version}"

    def _calculate_model_size(self, model_dir: str) -> float:
        """
        모델 크기 계산 (GB)

        Args:
            model_dir: 모델 디렉토리

        Returns:
            모델 크기 (GB)
        """
        try:
            model_path = Path(model_dir)
            if not model_path.exists():
                logger.warning(f"Model directory not found: {model_dir}")
                return 0.0

            total_size = 0
            for file_path in model_path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size

            # Bytes → GB
            size_gb = total_size / (1024 ** 3)
            return round(size_gb, 2)

        except Exception as e:
            logger.warning(f"Failed to calculate model size: {e}")
            return 0.0

    # ========================================================================
    # 모델 상태 관리
    # ========================================================================

    async def promote_to_production(
        self,
        db: AsyncSession,
        model_id: int,
        promoted_by: int
    ) -> ModelRegistry:
        """
        모델을 Production으로 승격

        Args:
            db: DB 세션
            model_id: 모델 ID
            promoted_by: 승격자 ID

        Returns:
            승격된 모델

        Raises:
            PromotionError: 승격 실패
        """
        try:
            # 1. 모델 조회
            model = await self.get_model_by_id(db, model_id)

            if not model:
                raise PromotionError(f"Model {model_id} not found")

            # 2. 상태 검증 (staging만 production으로 승격 가능)
            if model.status != "staging":
                raise PromotionError(
                    f"Cannot promote model with status '{model.status}'. "
                    "Only 'staging' models can be promoted."
                )

            # 3. 같은 이름의 기존 production 모델을 archived로 변경
            await self._demote_existing_production_model(db, model.model_name)

            # 4. 모델 승격
            model.status = "production"
            model.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(model)

            logger.info(f"모델 승격: {model.model_name} v{model.version} → production")

            return model

        except PromotionError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"모델 승격 실패: {e}")
            raise PromotionError(f"Failed to promote model: {e}")

    async def _demote_existing_production_model(
        self,
        db: AsyncSession,
        model_name: str
    ) -> None:
        """같은 이름의 기존 production 모델을 archived로 변경"""
        try:
            stmt = (
                select(ModelRegistry)
                .where(
                    and_(
                        ModelRegistry.model_name == model_name,
                        ModelRegistry.status == "production"
                    )
                )
            )

            result = await db.execute(stmt)
            existing_model = result.scalar_one_or_none()

            if existing_model:
                existing_model.status = "archived"
                existing_model.updated_at = datetime.utcnow()
                logger.info(
                    f"기존 production 모델 archived: {existing_model.model_name} "
                    f"v{existing_model.version}"
                )

        except Exception as e:
            logger.error(f"기존 모델 archived 실패: {e}")
            raise

    async def archive_model(
        self,
        db: AsyncSession,
        model_id: int
    ) -> ModelRegistry:
        """
        모델 아카이브

        Args:
            db: DB 세션
            model_id: 모델 ID

        Returns:
            아카이브된 모델
        """
        try:
            model = await self.get_model_by_id(db, model_id)

            if not model:
                raise PromotionError(f"Model {model_id} not found")

            model.status = "archived"
            model.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(model)

            logger.info(f"모델 archived: {model.model_name} v{model.version}")

            return model

        except Exception as e:
            await db.rollback()
            logger.error(f"모델 archived 실패: {e}")
            raise PromotionError(f"Failed to archive model: {e}")

    # ========================================================================
    # 모델 조회
    # ========================================================================

    async def get_model_by_id(
        self,
        db: AsyncSession,
        model_id: int
    ) -> Optional[ModelRegistry]:
        """
        ID로 모델 조회

        Args:
            db: DB 세션
            model_id: 모델 ID

        Returns:
            모델 (없으면 None)
        """
        stmt = select(ModelRegistry).where(ModelRegistry.id == model_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_models(
        self,
        db: AsyncSession,
        status: Optional[str] = None,
        base_model: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[ModelRegistry]:
        """
        모델 목록 조회

        Args:
            db: DB 세션
            status: 상태 필터
            base_model: 베이스 모델 필터
            limit: 최대 개수
            offset: 오프셋

        Returns:
            모델 리스트
        """
        stmt = select(ModelRegistry)

        # 필터 적용
        conditions = []
        if status:
            conditions.append(ModelRegistry.status == status)
        if base_model:
            conditions.append(ModelRegistry.base_model == base_model)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # 정렬 및 페이징
        stmt = stmt.order_by(ModelRegistry.created_at.desc())
        stmt = stmt.limit(limit).offset(offset)

        result = await db.execute(stmt)
        return result.scalars().all()

    async def search_by_tags(
        self,
        db: AsyncSession,
        tags: List[str],
        match_all: bool = False
    ) -> List[ModelRegistry]:
        """
        태그로 모델 검색

        Args:
            db: DB 세션
            tags: 검색할 태그 리스트
            match_all: True면 모든 태그 포함, False면 하나라도 포함

        Returns:
            모델 리스트
        """
        stmt = select(ModelRegistry)

        if match_all:
            # 모든 태그 포함 (PostgreSQL @> 연산자)
            stmt = stmt.where(ModelRegistry.tags.contains(tags))
        else:
            # 하나라도 포함 (OR 조건)
            tag_conditions = [ModelRegistry.tags.any(tag) for tag in tags]
            if tag_conditions:
                stmt = stmt.where(or_(*tag_conditions))

        result = await db.execute(stmt)
        return result.scalars().all()

    # ========================================================================
    # 벤치마크 관리
    # ========================================================================

    async def add_benchmark(
        self,
        db: AsyncSession,
        model_id: int,
        benchmark_name: str,
        score: float,
        details: Optional[Dict[str, Any]] = None
    ) -> ModelBenchmark:
        """
        벤치마크 결과 추가

        Args:
            db: DB 세션
            model_id: 모델 ID
            benchmark_name: 벤치마크 이름
            score: 점수 (0.0 ~ 1.0)
            details: 상세 결과

        Returns:
            벤치마크 결과

        Raises:
            ValidationError: 검증 실패
        """
        try:
            # 1. 모델 존재 확인
            model = await self.get_model_by_id(db, model_id)
            if not model:
                raise ValidationError(f"Model {model_id} not found")

            # 2. 점수 검증 (0.0 ~ 1.0)
            if not (0.0 <= score <= 1.0):
                raise ValidationError(f"Score must be between 0 and 1, got {score}")

            # 3. 벤치마크 생성
            benchmark = ModelBenchmark(
                model_id=model_id,
                benchmark_name=benchmark_name,
                score=score,
                details=details or {},
                benchmark_date=datetime.utcnow()
            )

            db.add(benchmark)
            await db.commit()
            await db.refresh(benchmark)

            logger.info(
                f"벤치마크 추가: model_id={model_id}, "
                f"{benchmark_name}={score:.4f}"
            )

            return benchmark

        except ValidationError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"벤치마크 추가 실패: {e}")
            raise ValidationError(f"Failed to add benchmark: {e}")

    async def get_benchmarks_for_model(
        self,
        db: AsyncSession,
        model_id: int
    ) -> List[ModelBenchmark]:
        """
        모델의 벤치마크 조회

        Args:
            db: DB 세션
            model_id: 모델 ID

        Returns:
            벤치마크 리스트
        """
        stmt = (
            select(ModelBenchmark)
            .where(ModelBenchmark.model_id == model_id)
            .order_by(ModelBenchmark.benchmark_date.desc())
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    async def compare_models(
        self,
        db: AsyncSession,
        model_ids: List[int],
        benchmark_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        여러 모델 비교

        Args:
            db: DB 세션
            model_ids: 비교할 모델 ID 리스트
            benchmark_name: 특정 벤치마크로 필터링 (선택)

        Returns:
            비교 결과 리스트
        """
        stmt = select(ModelBenchmark).where(
            ModelBenchmark.model_id.in_(model_ids)
        )

        if benchmark_name:
            stmt = stmt.where(ModelBenchmark.benchmark_name == benchmark_name)

        result = await db.execute(stmt)
        benchmarks = result.scalars().all()

        # 모델별로 그룹화
        comparison = []
        for benchmark in benchmarks:
            comparison.append({
                "model_id": benchmark.model_id,
                "benchmark_name": benchmark.benchmark_name,
                "score": benchmark.score,
                "benchmark_date": benchmark.benchmark_date,
                "details": benchmark.details
            })

        return comparison
