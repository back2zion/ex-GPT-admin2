"""
Health Check Tests - Day 20
프로덕션 배포용 Health Check 엔드포인트 검증 (TDD)

Health Check Requirements:
- /health - Basic health status
- /health/db - Database connection check
- /health/ready - Readiness probe (K8s)
- /health/live - Liveness probe (K8s)

Methodology: TDD (Test-Driven Development)
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.core.database import get_db


# ============================================================================
# Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """Health check test용 클라이언트 (인증 불필요)"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=True
    ) as ac:
        yield ac


# ============================================================================
# Basic Health Check Tests
# ============================================================================

class TestBasicHealthCheck:
    """
    기본 Health Check 테스트

    Requirements:
    - /health 엔드포인트 존재
    - 200 OK 응답
    - JSON 형식 응답
    - status 필드 포함
    """

    @pytest.mark.asyncio
    async def test_health_endpoint_exists(self, client: AsyncClient):
        """
        Test: /health endpoint should exist

        Expected: 200 OK
        """
        # Act
        response = await client.get("/health")

        # Assert
        assert response.status_code == 200, \
            f"Health endpoint not found or returned error: {response.status_code}"

    @pytest.mark.asyncio
    async def test_health_returns_json(self, client: AsyncClient):
        """
        Test: /health should return JSON

        Expected: Content-Type: application/json
        """
        # Act
        response = await client.get("/health")

        # Assert
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json"), \
            f"Expected JSON response, got {response.headers['content-type']}"

    @pytest.mark.asyncio
    async def test_health_has_status_field(self, client: AsyncClient):
        """
        Test: /health should include status field

        Expected: {"status": "ok"} or {"status": "healthy"}
        """
        # Act
        response = await client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "status" in data, \
            f"Response missing 'status' field: {data}"

        assert data["status"] in ["ok", "healthy", "up"], \
            f"Unexpected status value: {data['status']}"

    @pytest.mark.asyncio
    async def test_health_includes_timestamp(self, client: AsyncClient):
        """
        Test: /health should include timestamp

        Expected: {"timestamp": "2025-10-22T..."}
        """
        # Act
        response = await client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "timestamp" in data, \
            f"Response missing 'timestamp' field: {data}"

        # Timestamp should be ISO format string
        assert isinstance(data["timestamp"], str)
        assert len(data["timestamp"]) > 0


# ============================================================================
# Database Health Check Tests
# ============================================================================

class TestDatabaseHealthCheck:
    """
    Database Health Check 테스트

    Requirements:
    - /health/db 엔드포인트 존재
    - Database 연결 상태 확인
    - 연결 실패 시 적절한 에러 응답
    """

    @pytest.mark.asyncio
    async def test_db_health_endpoint_exists(self, client: AsyncClient):
        """
        Test: /health/db endpoint should exist

        Expected: 200 OK when DB is connected
        """
        # Act
        response = await client.get("/health/db")

        # Assert
        assert response.status_code == 200, \
            f"Database health endpoint error: {response.status_code}"

    @pytest.mark.asyncio
    async def test_db_health_checks_connection(self, client: AsyncClient):
        """
        Test: /health/db should verify database connection

        Expected: {"status": "ok", "database": "connected"}
        """
        # Act
        response = await client.get("/health/db")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "database" in data

        assert data["database"] in ["connected", "ok", "healthy"], \
            f"Database not connected: {data['database']}"

    @pytest.mark.asyncio
    async def test_db_health_includes_db_info(self, client: AsyncClient):
        """
        Test: /health/db should include database info

        Expected: Database name or connection info
        """
        # Act
        response = await client.get("/health/db")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Should have either db_name or connection info
        has_db_info = any(key in data for key in ["db_name", "database", "connection"])

        assert has_db_info, \
            f"Missing database info in response: {data}"


# ============================================================================
# Kubernetes Readiness Probe Tests
# ============================================================================

class TestReadinessProbe:
    """
    Kubernetes Readiness Probe 테스트

    Requirements:
    - /health/ready 엔드포인트
    - 모든 의존성 준비 상태 확인
    - 준비되지 않으면 503 반환
    """

    @pytest.mark.asyncio
    async def test_readiness_endpoint_exists(self, client: AsyncClient):
        """
        Test: /health/ready endpoint should exist

        Expected: 200 OK when ready, 503 when not ready
        """
        # Act
        response = await client.get("/health/ready")

        # Assert
        assert response.status_code in [200, 503], \
            f"Unexpected status code: {response.status_code}"

    @pytest.mark.asyncio
    async def test_readiness_checks_dependencies(self, client: AsyncClient):
        """
        Test: /health/ready should check all dependencies

        Expected: {"status": "ready", "checks": {...}}
        """
        # Act
        response = await client.get("/health/ready")

        # Assert
        # Should return 200 if ready or 503 if not ready
        assert response.status_code in [200, 503]

        data = response.json()
        assert "status" in data

        # If 200, status should be "ready"
        if response.status_code == 200:
            assert data["status"] in ["ready", "ok"], \
                f"Expected 'ready' status, got {data['status']}"

    @pytest.mark.asyncio
    async def test_readiness_includes_checks(self, client: AsyncClient):
        """
        Test: /health/ready should include dependency checks

        Expected: {"checks": {"database": "ok", ...}}
        """
        # Act
        response = await client.get("/health/ready")

        # Assert
        data = response.json()

        # Should include checks object
        assert "checks" in data or "components" in data or "database" in data, \
            f"Missing dependency check info: {data}"


# ============================================================================
# Kubernetes Liveness Probe Tests
# ============================================================================

class TestLivenessProbe:
    """
    Kubernetes Liveness Probe 테스트

    Requirements:
    - /health/live 엔드포인트
    - 애플리케이션 생존 여부 확인
    - 항상 200 OK (죽지 않은 이상)
    """

    @pytest.mark.asyncio
    async def test_liveness_endpoint_exists(self, client: AsyncClient):
        """
        Test: /health/live endpoint should exist

        Expected: Always 200 OK if app is running
        """
        # Act
        response = await client.get("/health/live")

        # Assert
        assert response.status_code == 200, \
            f"Liveness probe failed: {response.status_code}"

    @pytest.mark.asyncio
    async def test_liveness_always_returns_ok(self, client: AsyncClient):
        """
        Test: /health/live should always return OK if app is running

        Expected: {"status": "alive"} with 200 OK
        """
        # Act
        response = await client.get("/health/live")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] in ["alive", "ok", "healthy"], \
            f"Unexpected liveness status: {data['status']}"

    @pytest.mark.asyncio
    async def test_liveness_is_lightweight(self, client: AsyncClient):
        """
        Test: /health/live should be fast (no DB checks)

        Expected: Response time < 100ms
        """
        import time

        # Act
        start_time = time.time()
        response = await client.get("/health/live")
        elapsed_ms = (time.time() - start_time) * 1000

        # Assert
        assert response.status_code == 200
        assert elapsed_ms < 100, \
            f"Liveness probe too slow: {elapsed_ms:.2f}ms (should be < 100ms)"


# ============================================================================
# Health Check Response Format Tests
# ============================================================================

class TestHealthCheckFormat:
    """
    Health Check 응답 형식 테스트

    Requirements:
    - 일관된 JSON 형식
    - 표준 필드명
    - 에러 시 적절한 상태 코드
    """

    @pytest.mark.asyncio
    async def test_health_response_format(self, client: AsyncClient):
        """
        Test: Health check responses should follow consistent format

        Expected Format:
        {
            "status": "ok",
            "timestamp": "2025-10-22T...",
            "version": "1.0.0",
            "checks": {...}
        }
        """
        # Act
        response = await client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Required fields
        assert "status" in data, "Missing 'status' field"
        assert "timestamp" in data, "Missing 'timestamp' field"

        # Status should be string
        assert isinstance(data["status"], str)

    @pytest.mark.asyncio
    async def test_health_no_authentication_required(self, client: AsyncClient):
        """
        Test: Health checks should not require authentication

        Expected: Accessible without credentials
        """
        # Act - No authentication headers
        response = await client.get("/health")

        # Assert
        assert response.status_code == 200, \
            "Health check should not require authentication"

        # Try all health endpoints
        endpoints = ["/health", "/health/db", "/health/ready", "/health/live"]

        for endpoint in endpoints:
            response = await client.get(endpoint)
            assert response.status_code in [200, 503], \
                f"{endpoint} requires authentication (got {response.status_code})"


# ============================================================================
# Summary
# ============================================================================

"""
Health Check Test Summary:

Total Tests: 14

Basic Health Check: 4 tests
  - Endpoint exists
  - Returns JSON
  - Has status field
  - Includes timestamp

Database Health Check: 3 tests
  - Endpoint exists
  - Checks connection
  - Includes DB info

Readiness Probe: 3 tests
  - Endpoint exists
  - Checks dependencies
  - Includes checks

Liveness Probe: 3 tests
  - Endpoint exists
  - Always returns OK
  - Lightweight (< 100ms)

Response Format: 2 tests
  - Consistent format
  - No authentication required

Health Check Endpoints:
  - GET /health - Basic health status
  - GET /health/db - Database connection
  - GET /health/ready - Readiness probe (K8s)
  - GET /health/live - Liveness probe (K8s)
"""
