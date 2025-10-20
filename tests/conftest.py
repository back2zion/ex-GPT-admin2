"""
pytest configuration and fixtures
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.models.base import Base
from app.core.database import get_db


# Test database URL (use existing admin_db for testing)
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@postgres:5432/admin_db"

# Test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

# Test session maker
test_async_session = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    # Note: Using existing admin_db, tables already created via Alembic
    # No need to drop/create tables in tests

    # Create session
    async with test_async_session() as session:
        yield session
        # Rollback any changes made during test
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override"""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=True  # Follow 307 redirects for trailing slashes
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_department_data():
    """Sample department data for tests"""
    return {
        "name": "테스트 부서",
        "code": "TEST001",
        "description": "테스트용 부서"
    }


@pytest.fixture
def sample_role_data():
    """Sample role data for tests"""
    return {
        "name": "test_role",
        "description": "테스트 역할",
        "is_active": True,
        "permission_ids": []
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for tests"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "테스트 사용자",
        "password": "testpassword123",
        "is_active": True,
        "role_ids": []
    }


@pytest.fixture
def sample_document_data():
    """Sample document data for tests"""
    return {
        "document_id": "DOC001",
        "title": "테스트 문서",
        "document_type": "law",
        "content": "테스트 문서 내용",
        "status": "active"
    }


@pytest.fixture
def mock_admin_principal():
    """Mock admin Principal for Cerbos authorization tests"""
    from cerbos.sdk.model import Principal
    return Principal(
        id="test_admin",
        roles=["admin", "superuser"],
        attr={
            "department": "테스트부서",
            "is_superuser": True
        }
    )


@pytest_asyncio.fixture
async def authenticated_client(
    db_session: AsyncSession,
    mock_admin_principal
) -> AsyncGenerator[AsyncClient, None]:
    """Create authenticated test client with admin Principal"""
    from app.dependencies import get_principal, get_cerbos_client, check_resource_permission
    from unittest.mock import AsyncMock

    async def override_get_db():
        yield db_session

    async def override_get_principal():
        return mock_admin_principal

    # Mock Cerbos client to bypass authorization
    async def override_get_cerbos():
        mock_cerbos = AsyncMock()
        # Always allow all actions
        mock_cerbos.is_allowed.return_value = True
        return mock_cerbos

    # Mock permission checker to bypass all checks
    async def override_check_permission(principal, resource, action, cerbos):
        # Always allow
        return True

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_principal] = override_get_principal
    app.dependency_overrides[get_cerbos_client] = override_get_cerbos

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=True  # Follow 307 redirects automatically
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
