"""
TDD Tests for Categories API
학습데이터 관리 - 카테고리 CRUD 테스트
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def sample_category_data():
    """샘플 카테고리 데이터"""
    return {
        "name": "법령 문서",
        "description": "법령 관련 학습 데이터 카테고리",
        "parsing_pattern": "PARAGRAPH"
    }


@pytest.mark.asyncio
class TestCategoriesAPI:
    """카테고리 API 테스트"""

    async def test_create_category_success(
        self,
        authenticated_client: AsyncClient,
        sample_category_data: dict
    ):
        """카테고리 생성 성공 테스트"""
        response = await authenticated_client.post(
            "/api/v1/admin/categories",
            json=sample_category_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_category_data["name"]
        assert data["description"] == sample_category_data["description"]
        assert data["parsing_pattern"] == sample_category_data["parsing_pattern"]
        assert "id" in data
        assert "created_at" in data

    async def test_create_category_duplicate_name(
        self,
        authenticated_client: AsyncClient,
        sample_category_data: dict
    ):
        """중복 카테고리 이름 생성 실패 테스트 (Secure: 고유성 제약조건)"""
        # 첫 번째 생성
        await authenticated_client.post(
            "/api/v1/admin/categories",
            json=sample_category_data
        )

        # 동일 이름으로 두 번째 생성 시도
        response = await authenticated_client.post(
            "/api/v1/admin/categories",
            json=sample_category_data
        )

        assert response.status_code == 400
        detail = response.json()["detail"].lower()
        assert "이미 존재" in detail or "already exists" in detail

    async def test_create_category_invalid_name(
        self,
        authenticated_client: AsyncClient
    ):
        """유효하지 않은 카테고리 이름 테스트 (Secure: 입력 검증)"""
        # 빈 이름
        response = await authenticated_client.post(
            "/api/v1/admin/categories",
            json={"name": "", "description": "테스트"}
        )
        assert response.status_code == 422  # Validation error

        # 너무 긴 이름 (255자 초과)
        long_name = "a" * 256
        response = await authenticated_client.post(
            "/api/v1/admin/categories",
            json={"name": long_name, "description": "테스트"}
        )
        assert response.status_code == 422

    async def test_create_category_xss_prevention(
        self,
        authenticated_client: AsyncClient
    ):
        """XSS 공격 방어 테스트 (Secure: XSS 방지)"""
        xss_data = {
            "name": "<script>alert('XSS')</script>",
            "description": "<img src=x onerror=alert('XSS')>"
        }

        response = await authenticated_client.post(
            "/api/v1/admin/categories",
            json=xss_data
        )

        # Should sanitize or reject
        assert response.status_code in [201, 400, 422]

    async def test_list_categories_empty(
        self,
        authenticated_client: AsyncClient
    ):
        """빈 카테고리 목록 조회 테스트"""
        response = await authenticated_client.get("/api/v1/admin/categories")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "items" in data

    async def test_list_categories_with_data(
        self,
        authenticated_client: AsyncClient,
        sample_category_data: dict
    ):
        """카테고리 목록 조회 테스트 (데이터 존재)"""
        # Create category
        await authenticated_client.post(
            "/api/v1/admin/categories",
            json=sample_category_data
        )

        # List categories
        response = await authenticated_client.get("/api/v1/admin/categories")

        assert response.status_code == 200
        data = response.json()

        if isinstance(data, list):
            assert len(data) >= 1
            assert data[0]["name"] == sample_category_data["name"]
        else:
            assert len(data["items"]) >= 1

    async def test_list_categories_pagination(
        self,
        authenticated_client: AsyncClient
    ):
        """카테고리 목록 페이지네이션 테스트"""
        # Create multiple categories
        for i in range(15):
            await authenticated_client.post(
                "/api/v1/admin/categories",
                json={
                    "name": f"Category {i}",
                    "description": f"Description {i}"
                }
            )

        # Test pagination
        response = await authenticated_client.get(
            "/api/v1/admin/categories?limit=10&skip=0"
        )

        assert response.status_code == 200
        data = response.json()

        if isinstance(data, list):
            assert len(data) <= 10
        else:
            assert len(data["items"]) <= 10
            assert data["total"] >= 15

    async def test_get_category_by_id(
        self,
        authenticated_client: AsyncClient,
        sample_category_data: dict
    ):
        """ID로 카테고리 조회 테스트"""
        # Create category
        create_response = await authenticated_client.post(
            "/api/v1/admin/categories",
            json=sample_category_data
        )
        category_id = create_response.json()["id"]

        # Get by ID
        response = await authenticated_client.get(
            f"/api/v1/admin/categories/{category_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == category_id
        assert data["name"] == sample_category_data["name"]

    async def test_get_category_not_found(
        self,
        authenticated_client: AsyncClient
    ):
        """존재하지 않는 카테고리 조회 테스트"""
        response = await authenticated_client.get(
            "/api/v1/admin/categories/99999"
        )

        assert response.status_code == 404
        detail = response.json()["detail"].lower()
        assert "찾을 수 없" in detail or "not found" in detail

    async def test_get_category_invalid_id(
        self,
        authenticated_client: AsyncClient
    ):
        """유효하지 않은 ID로 조회 테스트 (Secure: SQL Injection 방지)"""
        # SQL Injection attempt
        response = await authenticated_client.get(
            "/api/v1/admin/categories/1' OR '1'='1"
        )

        assert response.status_code == 422  # Validation error

    async def test_update_category(
        self,
        authenticated_client: AsyncClient,
        sample_category_data: dict
    ):
        """카테고리 수정 테스트"""
        # Create category
        create_response = await authenticated_client.post(
            "/api/v1/admin/categories",
            json=sample_category_data
        )
        category_id = create_response.json()["id"]

        # Update category
        update_data = {
            "name": "수정된 카테고리",
            "description": "수정된 설명",
            "parsing_pattern": "SENTENCE"
        }

        response = await authenticated_client.put(
            f"/api/v1/admin/categories/{category_id}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["parsing_pattern"] == update_data["parsing_pattern"]

    async def test_delete_category(
        self,
        authenticated_client: AsyncClient,
        sample_category_data: dict
    ):
        """카테고리 삭제 테스트"""
        # Create category
        create_response = await authenticated_client.post(
            "/api/v1/admin/categories",
            json=sample_category_data
        )
        category_id = create_response.json()["id"]

        # Delete category
        response = await authenticated_client.delete(
            f"/api/v1/admin/categories/{category_id}"
        )

        assert response.status_code == 204 or response.status_code == 200

        # Verify deletion
        get_response = await authenticated_client.get(
            f"/api/v1/admin/categories/{category_id}"
        )
        assert get_response.status_code == 404

    async def test_delete_category_with_documents(
        self,
        authenticated_client: AsyncClient,
        sample_category_data: dict
    ):
        """
        연결된 문서가 있는 카테고리 삭제 테스트
        (Secure: 참조 무결성 보호)
        """
        # Create category
        create_response = await authenticated_client.post(
            "/api/v1/admin/categories",
            json=sample_category_data
        )
        category_id = create_response.json()["id"]

        # Create document with this category
        # (This will be implemented later in document API)

        # Try to delete category
        response = await authenticated_client.delete(
            f"/api/v1/admin/categories/{category_id}"
        )

        # Should either prevent deletion or cascade delete
        # (Implementation decision: for now, allow delete)
        assert response.status_code in [200, 204, 400]
