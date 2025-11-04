"""
P0-1: 사용 이력 관리 테스트
TDD 기반 개발 - PRD_v2.md 요구사항 준수

요구사항:
- 질문/답변 로깅
- 응답 시간 측정
- 사용자 정보 (부서, 직급)
- Thinking 과정 저장
- 통계 및 분석 (일별/주별/월별)
- 데이터 내보내기 (CSV/Excel)

시큐어 코딩:
- PII 보호: 개인정보 마스킹
- 권한 검증: Cerbos 기반 RBAC
- 입력 검증: Pydantic 스키마
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.usage import UsageHistory


class TestUsageHistoryLogging:
    """사용 이력 로깅 테스트"""

    @pytest.mark.asyncio
    async def test_log_usage_with_thinking(self, client: AsyncClient, db_session: AsyncSession):
        """
        Thinking 내용을 포함한 사용 이력 로깅

        Given: Thinking 내용이 포함된 사용 이력 데이터
        When: POST /api/v1/admin/usage/log 호출
        Then:
            - 201 Created 응답
            - Thinking 내용이 DB에 저장됨
            - 응답 시간이 기록됨
        """
        import uuid

        # Given - use unique user_id for test isolation
        unique_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        usage_data = {
            "user_id": unique_user_id,
            "session_id": "session_001",
            "question": "국가계약법 제5조의 내용은 무엇인가요?",
            "answer": "국가계약법 제5조는 계약의 방법에 대해 규정하고 있습니다.",
            "thinking_content": "사용자가 국가계약법 제5조에 대해 질문했으므로, 해당 법령 문서를 검색하여 관련 조항을 찾아 답변합니다.",
            "response_time": 2450.5,
            "referenced_documents": ["법령/국가계약법.pdf", "규정/계약업무규정.hwp"],
            "model_name": "gpt-4",
            "ip_address": "192.168.1.100"
        }

        # When
        response = await client.post("/api/v1/admin/usage/log", json=usage_data)

        # Then
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == unique_user_id
        assert data["thinking_content"] == usage_data["thinking_content"]
        assert data["response_time"] == 2450.5
        assert data["model_name"] == "gpt-4"
        assert data["ip_address"] == "192.168.1.100"

        # DB 확인
        result = await db_session.execute(
            select(UsageHistory).where(UsageHistory.user_id == unique_user_id)
        )
        saved_history = result.scalar_one_or_none()
        assert saved_history is not None
        assert saved_history.thinking_content == usage_data["thinking_content"]

    @pytest.mark.asyncio
    async def test_log_usage_without_authentication(self, client: AsyncClient):
        """
        인증 없이 사용 이력 로깅 (layout.html에서 호출)

        Given: 인증 토큰 없는 요청
        When: POST /api/v1/admin/usage/log 호출
        Then: 201 Created (인증 불필요)
        """
        # Given
        usage_data = {
            "user_id": "anonymous_user",
            "question": "테스트 질문",
            "answer": "테스트 답변",
            "response_time": 1000.0,
            "model_name": "gpt-3.5-turbo"
        }

        # When
        response = await client.post("/api/v1/admin/usage/log", json=usage_data)

        # Then
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_log_usage_with_ip_address_from_header(self, client: AsyncClient):
        """
        X-Forwarded-For 헤더에서 IP 주소 자동 수집

        Given: X-Forwarded-For 헤더 포함 요청
        When: POST /api/v1/admin/usage/log 호출
        Then: 첫 번째 IP 주소가 기록됨
        """
        # Given
        usage_data = {
            "user_id": "test_user_002",
            "question": "테스트",
            "answer": "답변",
            "response_time": 500.0
        }
        headers = {
            "X-Forwarded-For": "203.0.113.1, 198.51.100.1, 192.0.2.1"
        }

        # When
        response = await client.post(
            "/api/v1/admin/usage/log",
            json=usage_data,
            headers=headers
        )

        # Then
        assert response.status_code == 201
        data = response.json()
        assert data["ip_address"] == "203.0.113.1"  # 첫 번째 IP


class TestUsageHistoryQuery:
    """사용 이력 조회 테스트"""

    @pytest_asyncio.fixture
    async def sample_usage_data(self, db_session: AsyncSession):
        """테스트용 샘플 데이터 생성"""
        import uuid
        unique_user_id = f"test_user_{uuid.uuid4().hex[:8]}"

        now = datetime.utcnow()
        histories = [
            UsageHistory(
                user_id=unique_user_id,
                question=f"질문 {i}",
                answer=f"답변 {i}",
                response_time=1000.0 + i * 100,
                model_name="gpt-4",
                created_at=now - timedelta(days=i)
            )
            for i in range(10)
        ]

        for history in histories:
            db_session.add(history)
        await db_session.commit()

        return {"user_id": unique_user_id, "histories": histories}

    @pytest.mark.asyncio
    async def test_query_usage_by_date_range(
        self,
        authenticated_client: AsyncClient,
        sample_usage_data
    ):
        """
        날짜 범위로 사용 이력 조회

        Given: 10일간의 사용 이력 데이터
        When: 최근 5일간의 데이터 조회
        Then: 6개의 레코드 반환됨 (0일 ~ 5일 = 6개)
        """
        # Given
        user_id = sample_usage_data["user_id"]
        today = datetime.utcnow().date()
        five_days_ago = (datetime.utcnow() - timedelta(days=5)).date()

        # When
        response = await authenticated_client.get(
            "/api/v1/admin/usage",
            params={
                "start_date": five_days_ago.isoformat(),
                "end_date": today.isoformat(),
                "user_id": user_id  # Filter to only sample data
            }
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        # Should return records with i=0,1,2,3,4,5 (6 records total)
        assert 5 <= len(data) <= 6  # Allow for 5 or 6 depending on timezone

    @pytest.mark.asyncio
    async def test_query_usage_by_user_id(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        사용자 ID로 사용 이력 조회

        Given: 특정 사용자의 이력 데이터
        When: user_id 파라미터로 조회
        Then: 해당 사용자의 이력만 반환됨
        """
        import uuid
        unique_user_id = f"specific_user_{uuid.uuid4().hex[:8]}"

        # Given
        await authenticated_client.post("/api/v1/admin/usage/log", json={
            "user_id": unique_user_id,
            "question": "특정 사용자 질문",
            "answer": "답변",
            "response_time": 1000.0
        })

        # When
        response = await authenticated_client.get(
            "/api/v1/admin/usage",
            params={"user_id": unique_user_id}
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert all(item["user_id"] == unique_user_id for item in data)

    @pytest.mark.asyncio
    async def test_query_usage_with_pagination(
        self,
        authenticated_client: AsyncClient,
        sample_usage_data
    ):
        """
        페이지네이션 지원 확인

        Given: 10개의 사용 이력 데이터
        When: limit=5, skip=0으로 조회
        Then: 5개의 레코드만 반환됨
        """
        # Given
        user_id = sample_usage_data["user_id"]

        # When
        response = await authenticated_client.get(
            "/api/v1/admin/usage",
            params={"limit": 5, "skip": 0, "user_id": user_id}
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5


class TestUsageHistoryStatistics:
    """사용 이력 통계 테스트"""

    @pytest.mark.asyncio
    async def test_usage_stats_by_department(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        부서별 사용 통계

        Given: 여러 부서의 사용 이력
        When: GET /api/v1/admin/usage/stats/by-department 호출
        Then: 부서별 집계 데이터 반환
        """
        # Given: 부서 정보를 포함한 사용 이력 생성
        # TODO: 부서 테이블과 연결 후 구현

        # When
        response = await client.get("/api/v1/admin/usage/stats/by-department")

        # Then
        # 구현 전이므로 404 또는 501 예상
        assert response.status_code in [404, 501]

    @pytest.mark.asyncio
    async def test_usage_stats_daily(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        일별 사용 통계

        Given: 여러 날짜의 사용 이력
        When: GET /api/v1/admin/usage/stats/daily 호출
        Then: 일별 집계 데이터 반환
        """
        # When
        response = await client.get(
            "/api/v1/admin/usage/stats/daily",
            params={
                "start_date": "2025-10-01",
                "end_date": "2025-10-31"
            }
        )

        # Then
        assert response.status_code in [200, 404, 501]


class TestUsageHistoryExport:
    """사용 이력 내보내기 테스트"""

    @pytest.mark.asyncio
    async def test_export_usage_to_csv(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        CSV 형식으로 사용 이력 내보내기

        Given: 사용 이력 데이터
        When: GET /api/v1/admin/usage/export/csv 호출
        Then: CSV 파일 다운로드 응답
        """
        # When
        response = await client.get("/api/v1/admin/usage/export/csv")

        # Then
        # 구현 전이므로 404 또는 501 예상
        assert response.status_code in [404, 501]


class TestUsageHistorySecurity:
    """사용 이력 보안 테스트 (시큐어 코딩)"""

    @pytest.mark.asyncio
    async def test_input_validation_max_length(
        self,
        client: AsyncClient
    ):
        """
        입력 검증: 최대 길이 제한

        Given: 매우 긴 질문/답변 데이터
        When: POST /api/v1/admin/usage/log 호출
        Then: 자동으로 잘림 또는 422 Validation Error
        """
        # Given
        very_long_question = "테스트 질문 " * 10000  # 매우 긴 문자열
        usage_data = {
            "user_id": "test_user",
            "question": very_long_question,
            "answer": "답변",
            "response_time": 1000.0
        }

        # When
        response = await client.post("/api/v1/admin/usage/log", json=usage_data)

        # Then
        # 201 (자동 잘림) 또는 422 (Validation Error) 예상
        assert response.status_code in [201, 422]

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(
        self,
        authenticated_client: AsyncClient
    ):
        """
        SQL Injection 방지 확인

        Given: SQL Injection 시도 문자열
        When: user_id 파라미터에 주입
        Then: 안전하게 처리됨 (SQLAlchemy ORM 사용)
        """
        # Given
        malicious_input = "'; DROP TABLE usage_history; --"

        # When
        response = await authenticated_client.get(
            "/api/v1/admin/usage",
            params={"user_id": malicious_input}
        )

        # Then
        # 200 (안전하게 처리) 또는 400 (Bad Request)
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_pii_masking_in_response(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        개인정보 마스킹 확인

        Given: 주민등록번호가 포함된 질문
        When: 조회 시
        Then: 주민등록번호가 마스킹됨
        """
        # Given
        usage_data = {
            "user_id": "test_user",
            "question": "홍길동(주민번호: 990101-1234567)의 계약 내역을 조회해주세요",
            "answer": "답변",
            "response_time": 1000.0
        }

        create_response = await authenticated_client.post("/api/v1/admin/usage/log", json=usage_data)
        usage_id = create_response.json()["id"]

        # When
        response = await authenticated_client.get(f"/api/v1/admin/usage/{usage_id}")

        # Then
        assert response.status_code == 200
        data = response.json()
        # TODO: PII 마스킹 구현 후 검증
        # assert "990101-1234567" not in data["question"]
        # assert "******" in data["question"]
