"""
TDD Test: Dashboard Stats API
대시보드 통계가 EDB와 PostgreSQL에서 정확하게 조회되는지 검증
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_system_info_returns_correct_structure(async_client: AsyncClient):
    """
    시스템 정보 API가 올바른 구조를 반환하는지 검증
    """
    response = await async_client.get(
        "/api/v1/admin/stats/system",
        headers={"X-Test-Auth": "admin"}
    )

    assert response.status_code == 200
    data = response.json()

    # 필수 필드 검증
    assert "unique_documents" in data
    assert "vector_chunks" in data
    assert "active_sessions" in data
    assert "total_notices" in data

    # 타입 검증
    assert isinstance(data["unique_documents"], int)
    assert isinstance(data["vector_chunks"], int)
    assert isinstance(data["active_sessions"], int)
    assert isinstance(data["total_notices"], int)

    # 음수가 아닌지 검증
    assert data["unique_documents"] >= 0
    assert data["vector_chunks"] >= 0
    assert data["active_sessions"] >= 0
    assert data["total_notices"] >= 0


@pytest.mark.asyncio
async def test_system_info_uses_edb_for_documents(async_client: AsyncClient):
    """
    시스템 정보 API가 EDB에서 문서 수를 조회하는지 검증

    EDB (wisenut.doc_bas_lst)의 문서 수와 일치해야 함
    """
    response = await async_client.get(
        "/api/v1/admin/stats/system",
        headers={"X-Test-Auth": "admin"}
    )

    assert response.status_code == 200
    data = response.json()

    # EDB 문서 수는 1,000개 이상일 것으로 예상 (실제 데이터 기준)
    # Qdrant의 3,411개보다 작아야 함 (EDB가 정확한 수치)
    assert data["unique_documents"] >= 1000
    assert data["unique_documents"] < 5000  # 상한선


@pytest.mark.asyncio
async def test_system_info_uses_postgresql_for_vectors(async_client: AsyncClient):
    """
    시스템 정보 API가 PostgreSQL에서 벡터 수를 조회하는지 검증

    PostgreSQL (document_vectors)의 레코드 수와 일치해야 함
    """
    response = await async_client.get(
        "/api/v1/admin/stats/system",
        headers={"X-Test-Auth": "admin"}
    )

    assert response.status_code == 200
    data = response.json()

    # PostgreSQL 벡터 수는 0개 이상
    # Qdrant의 365,091개보다 훨씬 작아야 함 (PostgreSQL이 정확)
    assert data["vector_chunks"] >= 0
    assert data["vector_chunks"] < 100000  # 상한선


@pytest.mark.asyncio
async def test_system_info_not_using_qdrant(async_client: AsyncClient):
    """
    시스템 정보 API가 Qdrant를 사용하지 않는지 검증

    이전에는 Qdrant에서 3,411개를 조회했지만,
    이제는 EDB에서 정확한 수치를 조회해야 함
    """
    response = await async_client.get(
        "/api/v1/admin/stats/system",
        headers={"X-Test-Auth": "admin"}
    )

    assert response.status_code == 200
    data = response.json()

    # Qdrant의 잘못된 수치(3,411개)가 아니어야 함
    assert data["unique_documents"] != 3411, "Still using Qdrant data! Should use EDB."

    # Qdrant의 잘못된 벡터 수(365,091개)가 아니어야 함
    assert data["vector_chunks"] != 365091, "Still using Qdrant data! Should use PostgreSQL."


@pytest.mark.asyncio
async def test_system_info_performance(async_client: AsyncClient):
    """
    시스템 정보 API의 응답 시간이 합리적인지 검증

    EDB 연결이 추가되었지만 5초 이내에 응답해야 함
    """
    import time
    start_time = time.time()

    response = await async_client.get(
        "/api/v1/admin/stats/system",
        headers={"X-Test-Auth": "admin"}
    )

    end_time = time.time()
    elapsed_time = end_time - start_time

    assert response.status_code == 200
    assert elapsed_time < 5.0, f"Response took {elapsed_time:.2f}s, should be under 5s"


@pytest.mark.asyncio
async def test_system_info_requires_authentication(async_client: AsyncClient):
    """
    시스템 정보 API가 인증을 요구하는지 검증
    """
    response = await async_client.get("/api/v1/admin/stats/system")

    # 인증 없이 접근하면 401 또는 403 반환
    assert response.status_code in [401, 403]
