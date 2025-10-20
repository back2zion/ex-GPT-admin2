"""
P0-2: 통계 페이지 테스트
TDD 기반 개발 - PRD_v2.md 요구사항 준수

요구사항:
- 전체 요약 통계 (총 질문 수, 일평균, 응답시간, 사용자 수)
- 시간별/일별/주별/월별 통계
- 부서별 통계
- 모델별 통계
- 날짜 범위 필터링

시큐어 코딩:
- 권한 검증: Cerbos 기반 RBAC
- SQL Injection 방지: SQLAlchemy ORM
- 입력 검증: 날짜 형식 검증
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.models.usage import UsageHistory


class TestStatisticsSummary:
    """전체 요약 통계 테스트"""

    @pytest_asyncio.fixture
    async def sample_statistics_data(self, db_session: AsyncSession):
        """테스트용 통계 데이터 생성"""
        now = datetime.utcnow()
        unique_user_id = f"stats_user_{uuid.uuid4().hex[:8]}"

        # 다양한 시간대의 데이터 생성
        histories = []
        for i in range(24):  # 24시간 데이터
            for j in range(3):  # 각 시간당 3개 레코드
                histories.append(
                    UsageHistory(
                        user_id=f"{unique_user_id}_{i % 5}",  # 5명의 사용자
                        question=f"시간별 질문 {i}:{j}",
                        answer=f"답변 {i}:{j}",
                        response_time=1000.0 + (i * 100) + (j * 10),
                        model_name="gpt-4" if i % 2 == 0 else "gpt-3.5-turbo",
                        created_at=now - timedelta(hours=i, minutes=j*10)
                    )
                )

        for history in histories:
            db_session.add(history)
        await db_session.commit()

        return {"user_id_prefix": unique_user_id, "histories": histories}

    @pytest.mark.asyncio
    async def test_get_summary_statistics(
        self,
        authenticated_client: AsyncClient,
        sample_statistics_data
    ):
        """
        전체 요약 통계 조회

        Given: 24시간 동안의 사용 이력 데이터 (72개 레코드, 5명 사용자)
        When: GET /api/v1/admin/statistics/summary 호출
        Then:
            - 총 질문 수
            - 평균 응답시간
            - 고유 사용자 수
            - 평균 일일 사용량
        """
        # When
        response = await authenticated_client.get("/api/v1/admin/statistics/summary")

        # Then
        assert response.status_code == 200
        data = response.json()

        # 기본 통계 필드 확인
        assert "total_questions" in data
        assert "average_response_time" in data
        assert "unique_users" in data
        assert "daily_average" in data
        assert data["total_questions"] >= 72
        assert data["unique_users"] >= 5

    @pytest.mark.asyncio
    async def test_get_summary_statistics_with_date_filter(
        self,
        authenticated_client: AsyncClient,
        sample_statistics_data
    ):
        """
        날짜 필터링된 요약 통계

        Given: 24시간 데이터
        When: 최근 12시간으로 필터링
        Then: 해당 기간의 통계만 반환
        """
        # Given
        today = datetime.utcnow().date()
        yesterday = (datetime.utcnow() - timedelta(days=1)).date()

        # When
        response = await authenticated_client.get(
            "/api/v1/admin/statistics/summary",
            params={
                "start_date": yesterday.isoformat(),
                "end_date": today.isoformat()
            }
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "total_questions" in data
        assert data["total_questions"] >= 0


class TestStatisticsHourly:
    """시간별 통계 테스트"""

    @pytest.mark.asyncio
    async def test_get_hourly_statistics(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        시간별 통계 조회

        Given: 여러 시간대의 사용 이력
        When: GET /api/v1/admin/statistics/hourly 호출
        Then: 시간별 집계 데이터 반환 (0-23시)
        """
        # Given - 테스트 데이터 생성
        unique_user_id = f"hourly_user_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()

        for hour in range(24):
            history = UsageHistory(
                user_id=unique_user_id,
                question=f"시간 {hour}시 질문",
                answer="답변",
                response_time=1000.0 + hour * 50,
                created_at=now.replace(hour=hour, minute=0, second=0, microsecond=0)
            )
            db_session.add(history)
        await db_session.commit()

        # When
        response = await authenticated_client.get(
            "/api/v1/admin/statistics/hourly",
            params={
                "start_date": now.date().isoformat(),
                "end_date": now.date().isoformat()
            }
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 24  # 최대 24시간

        # 각 시간대 데이터 구조 확인
        if len(data) > 0:
            first_entry = data[0]
            assert "hour" in first_entry
            assert "count" in first_entry
            assert "average_response_time" in first_entry
            assert 0 <= first_entry["hour"] <= 23


class TestStatisticsDaily:
    """일별 통계 테스트"""

    @pytest.mark.asyncio
    async def test_get_daily_statistics(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        일별 통계 조회

        Given: 최근 7일간의 사용 이력
        When: GET /api/v1/admin/statistics/daily 호출
        Then: 일별 집계 데이터 반환
        """
        # Given
        unique_user_id = f"daily_user_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()

        for day in range(7):
            for i in range(5):  # 각 날짜당 5개 레코드
                history = UsageHistory(
                    user_id=f"{unique_user_id}_{i}",
                    question=f"일별 질문 {day}-{i}",
                    answer="답변",
                    response_time=1000.0 + day * 100,
                    created_at=now - timedelta(days=day)
                )
                db_session.add(history)
        await db_session.commit()

        # When
        start_date = (now - timedelta(days=7)).date()
        end_date = now.date()

        response = await authenticated_client.get(
            "/api/v1/admin/statistics/daily",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 8  # 최대 8일

        # 데이터 구조 확인
        if len(data) > 0:
            first_entry = data[0]
            assert "date" in first_entry
            assert "count" in first_entry
            assert "average_response_time" in first_entry
            assert "unique_users" in first_entry


class TestStatisticsByDepartment:
    """부서별 통계 테스트"""

    @pytest.mark.asyncio
    async def test_get_statistics_by_department(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        부서별 통계 조회

        Given: 여러 부서의 사용 이력
        When: GET /api/v1/admin/statistics/by-department 호출
        Then: 부서별 집계 데이터 반환

        Note: 부서 정보는 사용자 메타데이터 또는 별도 테이블에서 조인
        """
        # When
        response = await authenticated_client.get(
            "/api/v1/admin/statistics/by-department"
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # 부서별 데이터 구조 확인
        if len(data) > 0:
            first_entry = data[0]
            assert "department" in first_entry or "department_name" in first_entry
            assert "count" in first_entry
            assert "average_response_time" in first_entry


class TestStatisticsByModel:
    """모델별 통계 테스트"""

    @pytest.mark.asyncio
    async def test_get_statistics_by_model(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        모델별 통계 조회

        Given: 다양한 모델의 사용 이력
        When: GET /api/v1/admin/statistics/by-model 호출
        Then: 모델별 집계 데이터 반환
        """
        # Given
        unique_user_id = f"model_user_{uuid.uuid4().hex[:8]}"
        models = ["gpt-4", "gpt-3.5-turbo", "claude-3-opus"]

        for model in models:
            for i in range(10):
                history = UsageHistory(
                    user_id=unique_user_id,
                    question=f"{model} 질문 {i}",
                    answer="답변",
                    response_time=1000.0 + i * 10,
                    model_name=model
                )
                db_session.add(history)
        await db_session.commit()

        # When
        response = await authenticated_client.get(
            "/api/v1/admin/statistics/by-model"
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3  # 최소 3개 모델

        # 모델별 데이터 구조 확인
        first_entry = data[0]
        assert "model_name" in first_entry
        assert "count" in first_entry
        assert "average_response_time" in first_entry
        assert "total_response_time" in first_entry


class TestStatisticsWeeklyMonthly:
    """주별/월별 통계 테스트"""

    @pytest.mark.asyncio
    async def test_get_weekly_statistics(
        self,
        authenticated_client: AsyncClient
    ):
        """
        주별 통계 조회

        Given: 최근 4주간의 데이터
        When: GET /api/v1/admin/statistics/weekly 호출
        Then: 주별 집계 데이터 반환
        """
        # When
        response = await authenticated_client.get(
            "/api/v1/admin/statistics/weekly",
            params={
                "weeks": 4
            }
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        if len(data) > 0:
            first_entry = data[0]
            assert "week_start" in first_entry
            assert "week_end" in first_entry
            assert "count" in first_entry
            assert "average_response_time" in first_entry

    @pytest.mark.asyncio
    async def test_get_monthly_statistics(
        self,
        authenticated_client: AsyncClient
    ):
        """
        월별 통계 조회

        Given: 최근 12개월 데이터
        When: GET /api/v1/admin/statistics/monthly 호출
        Then: 월별 집계 데이터 반환
        """
        # When
        response = await authenticated_client.get(
            "/api/v1/admin/statistics/monthly",
            params={
                "months": 12
            }
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        if len(data) > 0:
            first_entry = data[0]
            assert "year" in first_entry
            assert "month" in first_entry
            assert "count" in first_entry
            assert "average_response_time" in first_entry
            assert 1 <= first_entry["month"] <= 12


class TestStatisticsPermissions:
    """통계 API 권한 테스트"""

    @pytest.mark.asyncio
    async def test_statistics_require_authentication(
        self,
        client: AsyncClient
    ):
        """
        통계 API는 인증 필요

        Given: 인증되지 않은 요청
        When: 통계 엔드포인트 호출
        Then: 401 또는 307 (리다이렉트)
        """
        # When
        response = await client.get("/api/v1/admin/statistics/summary")

        # Then
        assert response.status_code in [307, 401, 403]

    @pytest.mark.asyncio
    async def test_statistics_require_read_permission(
        self,
        authenticated_client: AsyncClient
    ):
        """
        통계 조회 권한 필요

        Given: 인증된 사용자 (권한 있음)
        When: 통계 조회
        Then: 200 OK
        """
        # When
        response = await authenticated_client.get("/api/v1/admin/statistics/summary")

        # Then
        assert response.status_code == 200
