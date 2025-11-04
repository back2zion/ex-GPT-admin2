"""
A/B Test Service
A/B 테스트 생성, 변형 할당, 통계 분석 등을 관리하는 서비스

TDD + 시큐어 코딩 + 유지보수 용이성을 적용한 구현
"""
import re
import random
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import joinedload
import numpy as np
from scipy import stats

from app.models.ab_test import ABExperiment, ABTestLog, ABTestResult
from app.models.training import ModelRegistry

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """A/B 테스트 검증 오류"""
    pass


class ExperimentError(Exception):
    """실험 관련 오류"""
    pass


class StatisticalTestError(Exception):
    """통계 테스트 오류"""
    pass


class ABTestService:
    """A/B 테스트 관리 서비스"""

    # 보안: 실험 이름 패턴 (영문, 숫자, 하이픈, 언더스코어만 허용)
    EXPERIMENT_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    MAX_EXPERIMENT_NAME_LENGTH = 255

    # 통계 테스트 최소 샘플 수 (통계적 유의성을 위한 최소 샘플)
    MIN_SAMPLES_FOR_STATISTICS = 30

    # 변형(Variant) 허용 값
    VALID_VARIANTS = {"a", "b"}

    # 평점 범위
    MIN_RATING = 1
    MAX_RATING = 5

    async def create_experiment(
        self,
        db: AsyncSession,
        experiment_name: str,
        model_a_id: int,
        model_b_id: int,
        traffic_split: Dict[str, float] = None,
        target_samples: int = 200,
        success_metric: str = "user_rating",
        description: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> ABExperiment:
        """
        A/B 테스트 실험 생성

        Args:
            db: 데이터베이스 세션
            experiment_name: 실험 이름 (고유해야 함)
            model_a_id: 모델 A ID
            model_b_id: 모델 B ID
            traffic_split: 트래픽 분할 비율 (예: {"a": 0.5, "b": 0.5})
            target_samples: 목표 샘플 수
            success_metric: 성공 지표 (user_rating, response_time 등)
            description: 실험 설명
            created_by: 생성자 사용자 ID

        Returns:
            생성된 ABExperiment 객체

        Raises:
            ValidationError: 검증 실패 시
        """
        # 보안: 실험 이름 검증
        self._validate_experiment_name(experiment_name)

        # 검증: 동일한 모델 사용 불가
        if model_a_id == model_b_id:
            raise ValidationError("Model A and Model B cannot be the same")

        # 검증: 모델 존재 확인
        await self._validate_models_exist(db, model_a_id, model_b_id)

        # 기본 트래픽 분할 설정
        if traffic_split is None:
            traffic_split = {"a": 0.5, "b": 0.5}

        # 보안: 트래픽 분할 검증
        self._validate_traffic_split(traffic_split)

        # 보안: 목표 샘플 수 검증
        self._validate_target_samples(target_samples)

        # 중복 이름 확인
        existing = await db.execute(
            select(ABExperiment).where(ABExperiment.experiment_name == experiment_name)
        )
        if existing.scalar_one_or_none():
            raise ValidationError(f"Experiment with name '{experiment_name}' already exists")

        # 실험 생성
        experiment = ABExperiment(
            experiment_name=experiment_name,
            model_a_id=model_a_id,
            model_b_id=model_b_id,
            traffic_split=traffic_split,
            status="running",
            target_samples=target_samples,
            success_metric=success_metric,
            description=description,
            created_by=created_by
        )

        db.add(experiment)
        await db.commit()
        await db.refresh(experiment)

        logger.info(f"A/B 테스트 실험 생성: {experiment_name} (ID: {experiment.id})")
        return experiment

    async def assign_variant(
        self,
        db: AsyncSession,
        experiment_id: int,
        user_id: int,
        session_id: str
    ) -> str:
        """
        사용자에게 변형(Variant) 할당

        Sticky Session: 동일한 사용자는 항상 동일한 변형을 받음

        Args:
            db: 데이터베이스 세션
            experiment_id: 실험 ID
            user_id: 사용자 ID
            session_id: 세션 ID

        Returns:
            할당된 변형 ("a" 또는 "b")

        Raises:
            ValidationError: 실험이 존재하지 않거나 실행 중이 아닌 경우
        """
        # 실험 조회
        experiment = await self._get_experiment(db, experiment_id)

        # 검증: 실험이 실행 중인지 확인
        if experiment.status != "running":
            raise ValidationError(f"Experiment {experiment_id} is not running")

        # Sticky Session: 기존 로그 확인
        existing_log = await db.execute(
            select(ABTestLog)
            .where(
                and_(
                    ABTestLog.experiment_id == experiment_id,
                    ABTestLog.user_id == user_id
                )
            )
            .order_by(ABTestLog.created_at.desc())
            .limit(1)
        )
        existing = existing_log.scalar_one_or_none()

        if existing:
            # 기존 사용자는 동일한 변형 유지
            logger.debug(f"사용자 {user_id}에게 기존 변형 '{existing.variant}' 할당 (Sticky Session)")
            return existing.variant

        # 새 사용자: 트래픽 분할에 따라 변형 할당
        variant = self._assign_variant_by_traffic_split(experiment.traffic_split)

        logger.debug(f"사용자 {user_id}에게 새 변형 '{variant}' 할당")
        return variant

    async def log_interaction(
        self,
        db: AsyncSession,
        experiment_id: int,
        user_id: int,
        session_id: str,
        variant: str,
        model_id: int,
        query: str,
        response: str,
        response_time_ms: int,
        user_rating: Optional[int] = None,
        user_feedback: Optional[str] = None
    ) -> ABTestLog:
        """
        사용자 상호작용 로그 기록

        Args:
            db: 데이터베이스 세션
            experiment_id: 실험 ID
            user_id: 사용자 ID
            session_id: 세션 ID
            variant: 변형 ("a" 또는 "b")
            model_id: 사용된 모델 ID
            query: 사용자 질의
            response: 모델 응답
            response_time_ms: 응답 시간 (밀리초)
            user_rating: 사용자 평점 (1-5)
            user_feedback: 사용자 피드백 텍스트

        Returns:
            생성된 ABTestLog 객체

        Raises:
            ValidationError: 검증 실패 시
        """
        # 보안: 변형 검증
        self._validate_variant(variant)

        # 보안: 평점 검증 (제공된 경우)
        if user_rating is not None:
            self._validate_rating(user_rating)

        # 실험 존재 확인
        await self._get_experiment(db, experiment_id)

        # 로그 생성
        log = ABTestLog(
            experiment_id=experiment_id,
            user_id=user_id,
            session_id=session_id,
            variant=variant,
            model_id=model_id,
            query=query,
            response=response,
            response_time_ms=response_time_ms,
            user_rating=user_rating,
            user_feedback=user_feedback
        )

        db.add(log)
        await db.commit()
        await db.refresh(log)

        logger.debug(f"A/B 테스트 로그 기록: 실험 {experiment_id}, 사용자 {user_id}, 변형 {variant}")
        return log

    async def calculate_results(
        self,
        db: AsyncSession,
        experiment_id: int
    ) -> Dict[str, Dict[str, Any]]:
        """
        A/B 테스트 결과 계산

        Args:
            db: 데이터베이스 세션
            experiment_id: 실험 ID

        Returns:
            변형별 결과 딕셔너리
            예: {
                "a": {"total_samples": 100, "avg_rating": 4.5, "avg_response_time": 250},
                "b": {"total_samples": 100, "avg_rating": 4.2, "avg_response_time": 300}
            }
        """
        # 실험 조회
        await self._get_experiment(db, experiment_id)

        # 변형 A 통계
        result_a = await db.execute(
            select(
                func.count(ABTestLog.id).label("total_samples"),
                func.avg(ABTestLog.user_rating).label("avg_rating"),
                func.avg(ABTestLog.response_time_ms).label("avg_response_time")
            )
            .where(
                and_(
                    ABTestLog.experiment_id == experiment_id,
                    ABTestLog.variant == "a",
                    ABTestLog.user_rating.isnot(None)
                )
            )
        )
        stats_a = result_a.one()

        # 변형 B 통계
        result_b = await db.execute(
            select(
                func.count(ABTestLog.id).label("total_samples"),
                func.avg(ABTestLog.user_rating).label("avg_rating"),
                func.avg(ABTestLog.response_time_ms).label("avg_response_time")
            )
            .where(
                and_(
                    ABTestLog.experiment_id == experiment_id,
                    ABTestLog.variant == "b",
                    ABTestLog.user_rating.isnot(None)
                )
            )
        )
        stats_b = result_b.one()

        results = {
            "a": {
                "total_samples": stats_a.total_samples,
                "avg_rating": float(stats_a.avg_rating) if stats_a.avg_rating else 0.0,
                "avg_response_time": float(stats_a.avg_response_time) if stats_a.avg_response_time else 0.0
            },
            "b": {
                "total_samples": stats_b.total_samples,
                "avg_rating": float(stats_b.avg_rating) if stats_b.avg_rating else 0.0,
                "avg_response_time": float(stats_b.avg_response_time) if stats_b.avg_response_time else 0.0
            }
        }

        logger.info(f"A/B 테스트 결과 계산 완료: 실험 {experiment_id}")
        return results

    def check_statistical_significance(
        self,
        ratings_a: List[float],
        ratings_b: List[float],
        alpha: float = 0.05
    ) -> Tuple[bool, float]:
        """
        통계적 유의성 검정 (T-test)

        Args:
            ratings_a: 변형 A의 평점 리스트
            ratings_b: 변형 B의 평점 리스트
            alpha: 유의 수준 (기본값: 0.05)

        Returns:
            (is_significant, p_value) 튜플

        Raises:
            StatisticalTestError: 샘플 수 부족 시
        """
        # 검증: 최소 샘플 수 확인
        if len(ratings_a) < self.MIN_SAMPLES_FOR_STATISTICS:
            raise StatisticalTestError(
                f"Insufficient samples for variant A: {len(ratings_a)} < {self.MIN_SAMPLES_FOR_STATISTICS}"
            )

        if len(ratings_b) < self.MIN_SAMPLES_FOR_STATISTICS:
            raise StatisticalTestError(
                f"Insufficient samples for variant B: {len(ratings_b)} < {self.MIN_SAMPLES_FOR_STATISTICS}"
            )

        # T-test 수행
        t_statistic, p_value = stats.ttest_ind(ratings_a, ratings_b)

        # 유의성 판단 (numpy bool을 Python bool로 변환)
        is_significant = bool(p_value < alpha)

        logger.info(
            f"통계적 유의성 검정: t={t_statistic:.4f}, p={p_value:.4f}, "
            f"유의함={is_significant} (alpha={alpha})"
        )

        return is_significant, float(p_value)

    def calculate_confidence_interval(
        self,
        data: List[float],
        confidence: float = 0.95
    ) -> Dict[str, float]:
        """
        신뢰 구간 계산

        Args:
            data: 데이터 리스트
            confidence: 신뢰 수준 (기본값: 0.95)

        Returns:
            {"lower": float, "upper": float, "mean": float}
        """
        if len(data) == 0:
            return {"lower": 0.0, "upper": 0.0, "mean": 0.0}

        data_array = np.array(data)
        mean = float(np.mean(data_array))
        sem = float(stats.sem(data_array))  # Standard Error of Mean

        # T-분포를 사용한 신뢰 구간 계산
        interval = stats.t.interval(
            confidence,
            len(data) - 1,
            loc=mean,
            scale=sem
        )

        return {
            "lower": float(interval[0]),
            "upper": float(interval[1]),
            "mean": mean
        }

    async def conclude_experiment(
        self,
        db: AsyncSession,
        experiment_id: int,
        winner_variant: str,
        reason: Optional[str] = None,
        concluded_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        A/B 테스트 실험 종료 (승자 선정)

        Args:
            db: 데이터베이스 세션
            experiment_id: 실험 ID
            winner_variant: 승자 변형 ("a" 또는 "b")
            reason: 종료 사유
            concluded_by: 종료한 사용자 ID

        Returns:
            종료 결과 딕셔너리

        Raises:
            ValidationError: 검증 실패 시
        """
        # 보안: 변형 검증
        if winner_variant not in self.VALID_VARIANTS:
            raise ValidationError(f"Winner must be 'a' or 'b'")

        # 실험 조회
        experiment = await self._get_experiment(db, experiment_id)

        # 결과 계산
        results = await self.calculate_results(db, experiment_id)

        # 실험 상태 업데이트
        experiment.status = "completed"
        experiment.end_date = datetime.utcnow()

        # ABTestResult 생성 (변형 A)
        result_a = ABTestResult(
            experiment_id=experiment_id,
            variant="a",
            total_samples=results["a"]["total_samples"],
            avg_rating=results["a"]["avg_rating"],
            avg_response_time_ms=results["a"]["avg_response_time"],
            winner=(winner_variant == "a")
        )

        # ABTestResult 생성 (변형 B)
        result_b = ABTestResult(
            experiment_id=experiment_id,
            variant="b",
            total_samples=results["b"]["total_samples"],
            avg_rating=results["b"]["avg_rating"],
            avg_response_time_ms=results["b"]["avg_response_time"],
            winner=(winner_variant == "b")
        )

        db.add(result_a)
        db.add(result_b)
        await db.commit()

        logger.info(
            f"A/B 테스트 실험 종료: {experiment.experiment_name} (승자: {winner_variant})"
        )

        return {
            "experiment_id": experiment_id,
            "experiment_status": "completed",
            "winner": winner_variant,
            "reason": reason,
            "results": results
        }

    async def stop_experiment(
        self,
        db: AsyncSession,
        experiment_id: int,
        reason: Optional[str] = None,
        stopped_by: Optional[int] = None
    ) -> ABExperiment:
        """
        A/B 테스트 실험 중단 (승자 선정 없이)

        Args:
            db: 데이터베이스 세션
            experiment_id: 실험 ID
            reason: 중단 사유
            stopped_by: 중단한 사용자 ID

        Returns:
            업데이트된 ABExperiment 객체
        """
        # 실험 조회
        experiment = await self._get_experiment(db, experiment_id)

        # 실험 상태 업데이트
        experiment.status = "stopped"
        experiment.end_date = datetime.utcnow()

        await db.commit()
        await db.refresh(experiment)

        logger.info(f"A/B 테스트 실험 중단: {experiment.experiment_name}")
        return experiment

    # ==================== 내부 헬퍼 메서드 ====================

    async def _get_experiment(
        self,
        db: AsyncSession,
        experiment_id: int
    ) -> ABExperiment:
        """실험 조회 (존재하지 않으면 예외 발생)"""
        result = await db.execute(
            select(ABExperiment).where(ABExperiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            raise ValidationError(f"Experiment {experiment_id} not found")

        return experiment

    async def _validate_models_exist(
        self,
        db: AsyncSession,
        model_a_id: int,
        model_b_id: int
    ) -> None:
        """모델 존재 여부 검증"""
        result = await db.execute(
            select(ModelRegistry).where(
                ModelRegistry.id.in_([model_a_id, model_b_id])
            )
        )
        models = result.scalars().all()

        if len(models) != 2:
            missing = []
            found_ids = {m.id for m in models}
            if model_a_id not in found_ids:
                missing.append(model_a_id)
            if model_b_id not in found_ids:
                missing.append(model_b_id)
            raise ValidationError(f"Models not found: {missing}")

    def _validate_experiment_name(self, experiment_name: str) -> None:
        """
        보안: 실험 이름 검증
        - Path Traversal 방지
        - 특수 문자 제한
        """
        if not experiment_name or len(experiment_name) > self.MAX_EXPERIMENT_NAME_LENGTH:
            raise ValidationError(
                f"Experiment name must be between 1 and {self.MAX_EXPERIMENT_NAME_LENGTH} characters"
            )

        # Path Traversal 방지
        if ".." in experiment_name or "/" in experiment_name or "\\" in experiment_name:
            raise ValidationError(f"Invalid experiment name: {experiment_name}")

        # 허용된 문자만 사용
        if not self.EXPERIMENT_NAME_PATTERN.match(experiment_name):
            raise ValidationError(
                "Experiment name can only contain alphanumeric characters, hyphens, and underscores"
            )

    def _validate_traffic_split(self, traffic_split: Dict[str, float]) -> None:
        """
        보안: 트래픽 분할 비율 검증
        - 비율 합이 1.0인지 확인
        - 비율이 0~1 범위 내인지 확인
        """
        if not traffic_split or "a" not in traffic_split or "b" not in traffic_split:
            raise ValidationError("Traffic split must include both 'a' and 'b' variants")

        # 범위 검증
        for variant, ratio in traffic_split.items():
            if not (0.0 <= ratio <= 1.0):
                raise ValidationError(
                    f"Traffic split ratio for '{variant}' must be between 0 and 1"
                )

        # 합계 검증 (부동소수점 오차 허용)
        total = traffic_split["a"] + traffic_split["b"]
        if not (0.99 <= total <= 1.01):
            raise ValidationError(
                f"Traffic split must sum to 1.0"
            )

    def _validate_target_samples(self, target_samples: int) -> None:
        """
        보안: 목표 샘플 수 검증
        - 통계적 유의성을 위한 최소 샘플 수 확인
        """
        if target_samples < self.MIN_SAMPLES_FOR_STATISTICS:
            raise ValidationError(
                f"Target samples must be at least {self.MIN_SAMPLES_FOR_STATISTICS} for statistical significance"
            )

    def _validate_rating(self, rating: int) -> None:
        """
        보안: 평점 범위 검증
        """
        if not (self.MIN_RATING <= rating <= self.MAX_RATING):
            raise ValidationError(
                f"User rating must be between {self.MIN_RATING} and {self.MAX_RATING}"
            )

    def _validate_variant(self, variant: str) -> None:
        """
        보안: 변형 값 검증
        """
        if variant not in self.VALID_VARIANTS:
            raise ValidationError(f"Variant must be 'a' or 'b', got '{variant}'")

    def _assign_variant_by_traffic_split(
        self,
        traffic_split: Dict[str, float]
    ) -> str:
        """
        트래픽 분할 비율에 따라 변형 할당

        예: {"a": 0.7, "b": 0.3} -> 70% 확률로 "a", 30% 확률로 "b"
        """
        rand = random.random()

        if rand < traffic_split["a"]:
            return "a"
        else:
            return "b"
