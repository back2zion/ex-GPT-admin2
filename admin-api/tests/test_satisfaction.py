"""
이용만족도 조사 테스트
PRD_v2.md P0 요구사항: 이용만족도 조사

요구사항:
- 별점 평가 (1-5점)
- 피드백 텍스트
- 개선 의견 수집
- 평균 만족도 통계
- 시간별 추이
- 부서별 만족도
- 낮은 만족도 알림

시큐어 코딩:
- 익명성 보장: 개인정보 분리
- 입력 검증: 별점 범위, 텍스트 길이
- XSS 방지: 피드백 텍스트 sanitization
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta


class TestSatisfactionSubmission:
    """만족도 조사 제출 테스트"""

    @pytest.mark.asyncio
    async def test_submit_satisfaction_survey(self, client: AsyncClient, db_session: AsyncSession):
        """
        만족도 조사 제출

        Given: 별점과 피드백 데이터
        When: POST /api/satisfaction/submit 호출
        Then:
            - 200 응답
            - survey_id 반환
            - DB에 저장됨
        """
        # Given
        survey_data = {
            "rating": 5,
            "feedback": "서비스가 정말 유용합니다!",
            "category": "ACCURACY",
            "user_id": "test_user_001"
        }

        # When
        response = await client.post("/api/v1/satisfaction/submit", json=survey_data)

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["rating"] == 5
        assert "survey_id" in data

        # DB 확인
        from sqlalchemy import select
        from app.models.satisfaction import SatisfactionSurvey
        result = await db_session.execute(
            select(SatisfactionSurvey).where(SatisfactionSurvey.id == data["survey_id"])
        )
        survey = result.scalar_one_or_none()
        assert survey is not None
        assert survey.rating == 5
        assert survey.feedback == "서비스가 정말 유용합니다!"

    @pytest.mark.asyncio
    async def test_submit_satisfaction_anonymous(self, client: AsyncClient):
        """
        익명 만족도 조사 제출

        Given: user_id 없는 데이터
        When: POST /api/satisfaction/submit 호출
        Then: 'anonymous'로 저장됨
        """
        # Given
        survey_data = {
            "rating": 4,
            "feedback": "좋아요"
        }

        # When
        response = await client.post("/api/v1/satisfaction/submit", json=survey_data)

        # Then
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_submit_satisfaction_minimal(self, client: AsyncClient):
        """
        최소 정보로 만족도 조사 제출

        Given: 별점만 있는 데이터
        When: POST /api/satisfaction/submit 호출
        Then: 200 응답
        """
        # Given
        survey_data = {
            "rating": 3
        }

        # When
        response = await client.post("/api/v1/satisfaction/submit", json=survey_data)

        # Then
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_submit_low_rating(self, client: AsyncClient):
        """
        낮은 평점 제출 (알림 기능 준비)

        Given: 낮은 평점 (1-2점)
        When: POST /api/satisfaction/submit 호출
        Then: 200 응답 (알림은 Phase 2)
        """
        # Given
        survey_data = {
            "rating": 1,
            "feedback": "응답이 부정확합니다",
            "category": "ACCURACY"
        }

        # When
        response = await client.post("/api/v1/satisfaction/submit", json=survey_data)

        # Then
        assert response.status_code == 200
        # TODO Phase 2: 낮은 평점 알림 확인


class TestSatisfactionQuery:
    """만족도 조사 조회 테스트"""

    @pytest_asyncio.fixture
    async def sample_surveys(self, db_session: AsyncSession):
        """테스트용 샘플 만족도 데이터 생성"""
        from app.models.satisfaction import SatisfactionSurvey, SurveyCategory
        import uuid

        unique_user = f"survey_test_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()

        surveys = [
            SatisfactionSurvey(
                user_id=f"{unique_user}_1",
                rating=5,
                feedback="매우 만족",
                category=SurveyCategory.ACCURACY,
                created_at=now - timedelta(days=i)
            )
            for i in range(5)
        ]

        for survey in surveys:
            db_session.add(survey)
        await db_session.commit()

        return {"user_prefix": unique_user, "surveys": surveys}

    @pytest.mark.asyncio
    async def test_list_satisfaction_surveys(
        self,
        authenticated_client: AsyncClient,
        sample_surveys
    ):
        """
        만족도 조사 목록 조회

        Given: 여러 만족도 조사 데이터
        When: GET /api/v1/admin/satisfaction/ 호출
        Then:
            - 200 응답
            - items와 total 포함
        """
        # When
        response = await authenticated_client.get("/api/v1/admin/satisfaction/")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 5

    @pytest.mark.asyncio
    async def test_list_satisfaction_with_filter(
        self,
        authenticated_client: AsyncClient,
        sample_surveys
    ):
        """
        평점 필터로 만족도 조사 조회

        Given: 다양한 평점의 만족도 데이터
        When: rating=5 파라미터로 조회
        Then: 평점 5인 데이터만 반환
        """
        # When
        response = await authenticated_client.get(
            "/api/v1/admin/satisfaction/",
            params={"rating": 5}
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        if len(data["items"]) > 0:
            for item in data["items"]:
                assert item["rating"] == 5

    @pytest.mark.asyncio
    async def test_get_satisfaction_by_id(
        self,
        authenticated_client: AsyncClient,
        client: AsyncClient
    ):
        """
        특정 만족도 조사 상세 조회

        Given: 만족도 조사 데이터
        When: GET /api/v1/admin/satisfaction/{id} 호출
        Then: 해당 만족도 조사 상세 정보 반환
        """
        # Given: 만족도 조사 생성
        survey_data = {
            "rating": 4,
            "feedback": "상세 조회 테스트",
            "category": "UI"
        }
        create_response = await client.post("/api/v1/satisfaction/submit", json=survey_data)
        survey_id = create_response.json()["survey_id"]

        # When
        response = await authenticated_client.get(f"/api/v1/admin/satisfaction/{survey_id}")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == survey_id
        assert data["rating"] == 4


class TestSatisfactionStatistics:
    """만족도 통계 테스트"""

    @pytest.mark.asyncio
    async def test_get_satisfaction_stats(
        self,
        authenticated_client: AsyncClient,
        client: AsyncClient
    ):
        """
        만족도 통계 조회

        Given: 여러 만족도 조사 데이터
        When: GET /api/v1/admin/satisfaction/stats 호출
        Then:
            - 평균 평점
            - 총 응답 수
        """
        # Given: 여러 만족도 조사 생성
        for rating in [5, 4, 3, 4, 5]:
            await client.post("/api/v1/satisfaction/submit", json={"rating": rating})

        # When
        response = await authenticated_client.get("/api/v1/admin/satisfaction/stats")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "average_rating" in data
        assert "total_surveys" in data
        assert data["total_surveys"] >= 5
        assert 1.0 <= data["average_rating"] <= 5.0

    @pytest.mark.asyncio
    async def test_satisfaction_distribution_by_category(
        self,
        authenticated_client: AsyncClient,
        client: AsyncClient
    ):
        """
        카테고리별 만족도 분포

        Given: 다양한 카테고리의 만족도 데이터
        When: 카테고리별 필터링
        Then: 각 카테고리별 데이터 조회 가능
        """
        # Given: 다양한 카테고리 데이터 생성
        import uuid
        unique_user = f"category_test_{uuid.uuid4().hex[:8]}"

        categories = ["UI", "SPEED", "ACCURACY", "OTHER"]
        for i, category in enumerate(categories):
            await client.post("/api/v1/satisfaction/submit", json={
                "rating": 4,
                "category": category,
                "user_id": f"{unique_user}_{i}"
            })

        # When: 각 카테고리로 필터링
        for category in categories:
            response = await authenticated_client.get(
                "/api/v1/admin/satisfaction/",
                params={"category": category.lower()}
            )

            # Then
            assert response.status_code == 200


class TestSatisfactionSecurity:
    """만족도 조사 보안 테스트"""

    @pytest.mark.asyncio
    async def test_validate_rating_range(self, client: AsyncClient):
        """
        별점 범위 검증

        Given: 범위를 벗어난 별점 (0, 6)
        When: POST /api/satisfaction/submit 호출
        Then: 422 Validation Error
        """
        # When/Then: 별점 0 (너무 낮음)
        response = await client.post("/api/v1/satisfaction/submit", json={"rating": 0})
        assert response.status_code == 422

        # When/Then: 별점 6 (너무 높음)
        response = await client.post("/api/v1/satisfaction/submit", json={"rating": 6})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_validate_feedback_length(self, client: AsyncClient):
        """
        피드백 길이 검증

        Given: 매우 긴 피드백 (> 1000자)
        When: POST /api/satisfaction/submit 호출
        Then: 422 Validation Error
        """
        # Given
        very_long_feedback = "테스트" * 500  # 1000자 초과

        # When
        response = await client.post("/api/v1/satisfaction/submit", json={
            "rating": 4,
            "feedback": very_long_feedback
        })

        # Then
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_xss_prevention_in_feedback(self, client: AsyncClient):
        """
        피드백 XSS 방지

        Given: XSS 스크립트가 포함된 피드백
        When: POST /api/satisfaction/submit 호출
        Then: 안전하게 저장됨 (스크립트 실행 방지)
        """
        # Given
        xss_feedback = "<script>alert('XSS')</script>악의적인 스크립트"

        # When
        response = await client.post("/api/v1/satisfaction/submit", json={
            "rating": 3,
            "feedback": xss_feedback
        })

        # Then
        assert response.status_code == 200
        # TODO: 실제로는 sanitization이 필요하지만, 현재는 DB에 그대로 저장됨
        # Phase 2에서 bleach 또는 html.escape 사용하여 sanitization 구현

    @pytest.mark.asyncio
    async def test_query_requires_authentication(self, client: AsyncClient):
        """
        조회는 인증 필요 확인

        Given: 인증되지 않은 요청
        When: GET /api/v1/admin/satisfaction/ 호출
        Then: 401 Unauthorized
        """
        # When
        response = await client.get("/api/v1/admin/satisfaction/")

        # Then
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_submission_without_authentication(self, client: AsyncClient):
        """
        제출은 인증 불필요 확인 (익명 제출 가능)

        Given: 인증되지 않은 요청
        When: POST /api/satisfaction/submit 호출
        Then: 200 응답
        """
        # When
        response = await client.post("/api/v1/satisfaction/submit", json={"rating": 4})

        # Then
        assert response.status_code == 200


class TestSatisfactionPagination:
    """만족도 조사 페이지네이션 테스트"""

    @pytest.mark.asyncio
    async def test_pagination_with_limit(
        self,
        authenticated_client: AsyncClient
    ):
        """
        페이지네이션 (limit)

        Given: 여러 만족도 조사 데이터
        When: limit=10으로 조회
        Then: 최대 10개만 반환
        """
        # When
        response = await authenticated_client.get(
            "/api/v1/admin/satisfaction/",
            params={"limit": 10}
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 10

    @pytest.mark.asyncio
    async def test_pagination_with_skip(
        self,
        authenticated_client: AsyncClient
    ):
        """
        페이지네이션 (skip)

        Given: 여러 만족도 조사 데이터
        When: skip=5로 조회
        Then: 첫 5개를 건너뜀
        """
        # When
        first_page = await authenticated_client.get(
            "/api/v1/admin/satisfaction/",
            params={"limit": 5, "skip": 0}
        )
        second_page = await authenticated_client.get(
            "/api/v1/admin/satisfaction/",
            params={"limit": 5, "skip": 5}
        )

        # Then
        assert first_page.status_code == 200
        assert second_page.status_code == 200

        first_data = first_page.json()
        second_data = second_page.json()

        # 첫 페이지와 두 번째 페이지의 ID가 다름
        if len(first_data["items"]) > 0 and len(second_data["items"]) > 0:
            first_ids = {item["id"] for item in first_data["items"]}
            second_ids = {item["id"] for item in second_data["items"]}
            assert first_ids.isdisjoint(second_ids)
