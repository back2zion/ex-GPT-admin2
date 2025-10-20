"""
통계 API 테스트
TDD RED 단계: 실패하는 테스트 작성
"""
import pytest
from datetime import date, datetime, timedelta
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_dashboard_stats(client: AsyncClient):
    """
    대시보드 통계 조회 테스트
    - 기간별 총 질문 수
    - 평균 응답 시간
    - 총 사용자 수
    - 만족도 평균
    """
    # Given: 7일간의 통계를 조회
    end_date = date.today()
    start_date = end_date - timedelta(days=7)

    # When: 통계 API 호출
    response = await client.get(
        f"/api/v1/admin/stats/dashboard?start={start_date}&end={end_date}"
    )

    # Then: 200 응답과 통계 데이터 반환
    assert response.status_code == 200
    data = response.json()

    assert "total_questions" in data
    assert "average_response_time" in data
    assert "total_users" in data
    assert "average_satisfaction" in data
    assert data["total_questions"] >= 0
    assert data["average_response_time"] >= 0


@pytest.mark.asyncio
async def test_get_daily_trend(client: AsyncClient):
    """
    일자별 사용 추이 테스트
    - 날짜별 질문 수
    - 날짜별 평균 응답 시간
    """
    # Given: 7일간의 추이 조회
    end_date = date.today()
    start_date = end_date - timedelta(days=7)

    # When: 일자별 추이 API 호출
    response = await client.get(
        f"/api/v1/admin/stats/daily-trend?start={start_date}&end={end_date}"
    )

    # Then: 200 응답과 일자별 데이터 반환
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert isinstance(data["items"], list)
    if len(data["items"]) > 0:
        item = data["items"][0]
        assert "date" in item
        assert "question_count" in item
        assert "avg_response_time" in item


@pytest.mark.asyncio
async def test_get_hourly_pattern(client: AsyncClient):
    """
    시간대별 사용 패턴 테스트
    - 0~23시 각 시간대별 질문 수
    """
    # Given: 특정 날짜의 시간대별 패턴 조회
    target_date = date.today()

    # When: 시간대별 패턴 API 호출
    response = await client.get(
        f"/api/v1/admin/stats/hourly-pattern?date={target_date}"
    )

    # Then: 200 응답과 시간대별 데이터 반환
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert isinstance(data["items"], list)
    # 0~23시 총 24개 시간대
    assert len(data["items"]) == 24

    for item in data["items"]:
        assert "hour" in item
        assert "question_count" in item
        assert 0 <= item["hour"] <= 23


@pytest.mark.asyncio
async def test_get_top_questions(client: AsyncClient):
    """
    인기 질문 TOP 10 테스트
    """
    # Given: 최근 30일간의 인기 질문 조회
    # When: 인기 질문 API 호출
    response = await client.get("/api/v1/admin/stats/top-questions?limit=10")

    # Then: 200 응답과 TOP 10 질문 반환
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) <= 10

    if len(data["items"]) > 0:
        item = data["items"][0]
        assert "question" in item
        assert "count" in item
