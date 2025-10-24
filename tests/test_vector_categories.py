"""
벡터 데이터 카테고리 관리 API 테스트
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import asyncpg

from app.main import app


# EDB 연결 설정
EDB_HOST = "host.docker.internal"
EDB_PORT = 5444
EDB_DATABASE = "AGENAI"
EDB_USER = "wisenut_dev"
EDB_PASSWORD = "express!12"


@pytest_asyncio.fixture
async def edb_connection():
    """EDB 연결 fixture"""
    conn = await asyncpg.connect(
        host=EDB_HOST,
        port=EDB_PORT,
        database=EDB_DATABASE,
        user=EDB_USER,
        password=EDB_PASSWORD
    )
    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """Test client"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=True
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def test_category(edb_connection):
    """테스트 카테고리 생성 및 정리"""
    # 테스트 카테고리 코드
    test_code = "99"

    # 기존 테스트 카테고리 삭제 (있을 경우)
    await edb_connection.execute(
        """
        DELETE FROM wisenut.com_cd_lv2
        WHERE level_n1_cd = 'DOC_CAT_CD' AND level_n2_cd = $1
        """,
        test_code
    )

    # 테스트 카테고리 생성
    await edb_connection.execute(
        """
        INSERT INTO wisenut.com_cd_lv2
        (level_n1_cd, level_n2_cd, level_n2_nm, level_n2_desc, level_n2_add_info, use_yn, reg_usr_id, reg_dt)
        VALUES ('DOC_CAT_CD', $1, $2, $3, '', 'Y', 'test', CURRENT_TIMESTAMP)
        """,
        test_code,
        "테스트 카테고리",
        "테스트용 카테고리"
    )

    yield test_code

    # 정리: 테스트 카테고리 삭제
    await edb_connection.execute(
        """
        DELETE FROM wisenut.com_cd_lv2
        WHERE level_n1_cd = 'DOC_CAT_CD' AND level_n2_cd = $1
        """,
        test_code
    )


class TestVectorCategoriesList:
    """카테고리 목록 조회 테스트"""

    @pytest.mark.asyncio
    async def test_list_categories_success(self, client: AsyncClient):
        """카테고리 목록 조회 성공"""
        response = await client.get("/api/v1/admin/vector-categories")

        assert response.status_code == 200
        data = response.json()

        # 응답이 리스트여야 함
        assert isinstance(data, list)

        # 각 카테고리는 필수 필드를 가져야 함
        if len(data) > 0:
            category = data[0]
            assert "code" in category
            assert "name" in category
            assert "document_count" in category
            assert "use_yn" in category
            assert "created_at" in category

    @pytest.mark.asyncio
    async def test_list_categories_with_inactive(self, client: AsyncClient):
        """비활성 카테고리 포함 조회"""
        response = await client.get(
            "/api/v1/admin/vector-categories",
            params={"include_inactive": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestVectorCategoriesNextCode:
    """다음 카테고리 코드 조회 테스트"""

    @pytest.mark.asyncio
    async def test_get_next_code_success(self, client: AsyncClient):
        """다음 사용 가능한 코드 조회 성공"""
        response = await client.get("/api/v1/admin/vector-categories/next-code")

        assert response.status_code == 200
        data = response.json()

        assert "next_code" in data
        assert isinstance(data["next_code"], str)
        # 코드는 2자리 숫자여야 함
        assert len(data["next_code"]) == 2
        assert data["next_code"].isdigit()


class TestVectorCategoriesCreate:
    """카테고리 생성 테스트"""

    @pytest.mark.asyncio
    async def test_create_category_success(self, client: AsyncClient, edb_connection):
        """카테고리 생성 성공"""
        # 준비: 98 코드가 없는지 확인
        existing = await edb_connection.fetchval(
            """
            SELECT COUNT(*) FROM wisenut.com_cd_lv2
            WHERE level_n1_cd = 'DOC_CAT_CD' AND level_n2_cd = '98'
            """
        )
        if existing > 0:
            await edb_connection.execute(
                """
                DELETE FROM wisenut.com_cd_lv2
                WHERE level_n1_cd = 'DOC_CAT_CD' AND level_n2_cd = '98'
                """
            )

        # 실행
        response = await client.post(
            "/api/v1/admin/vector-categories",
            json={
                "code": "98",
                "name": "새 카테고리",
                "description": "테스트용 새 카테고리"
            }
        )

        # 검증
        assert response.status_code == 201
        data = response.json()

        assert data["code"] == "98"
        assert data["name"] == "새 카테고리"
        assert data["description"] == "테스트용 새 카테고리"
        assert data["use_yn"] == "Y"
        assert data["document_count"] == 0

        # 정리
        await edb_connection.execute(
            """
            DELETE FROM wisenut.com_cd_lv2
            WHERE level_n1_cd = 'DOC_CAT_CD' AND level_n2_cd = '98'
            """
        )

    @pytest.mark.asyncio
    async def test_create_category_duplicate_code(self, client: AsyncClient, test_category):
        """중복 코드로 카테고리 생성 실패"""
        response = await client.post(
            "/api/v1/admin/vector-categories",
            json={
                "code": test_category,  # 이미 존재하는 코드
                "name": "중복 카테고리",
                "description": "중복 테스트"
            }
        )

        assert response.status_code == 400
        assert "이미 존재하는 카테고리 코드" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_category_missing_name(self, client: AsyncClient):
        """카테고리명 없이 생성 실패"""
        response = await client.post(
            "/api/v1/admin/vector-categories",
            json={
                "code": "97",
                "description": "이름 없음"
            }
        )

        assert response.status_code == 422  # Validation error


class TestVectorCategoriesUpdate:
    """카테고리 수정 테스트"""

    @pytest.mark.asyncio
    async def test_update_category_success(self, client: AsyncClient, test_category):
        """카테고리 수정 성공"""
        response = await client.put(
            f"/api/v1/admin/vector-categories/{test_category}",
            json={
                "name": "수정된 카테고리",
                "description": "수정된 설명"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["code"] == test_category
        assert data["name"] == "수정된 카테고리"
        assert data["description"] == "수정된 설명"
        assert data["updated_at"] is not None

    @pytest.mark.asyncio
    async def test_update_category_not_found(self, client: AsyncClient):
        """존재하지 않는 카테고리 수정 실패"""
        response = await client.put(
            "/api/v1/admin/vector-categories/00",  # 존재하지 않는 코드
            json={
                "name": "수정 시도"
            }
        )

        assert response.status_code == 404
        assert "카테고리를 찾을 수 없습니다" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_category_use_yn(self, client: AsyncClient, test_category):
        """카테고리 사용 여부 변경"""
        response = await client.put(
            f"/api/v1/admin/vector-categories/{test_category}",
            json={
                "use_yn": "N"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["use_yn"] == "N"


class TestVectorCategoriesDelete:
    """카테고리 삭제 테스트"""

    @pytest.mark.asyncio
    async def test_delete_category_soft_delete(self, client: AsyncClient, test_category, edb_connection):
        """카테고리 soft delete 성공"""
        response = await client.delete(
            f"/api/v1/admin/vector-categories/{test_category}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["code"] == test_category
        assert data["deleted"] is True
        assert data["hard_delete"] is False

        # 실제로 use_yn이 N으로 변경되었는지 확인
        use_yn = await edb_connection.fetchval(
            """
            SELECT use_yn FROM wisenut.com_cd_lv2
            WHERE level_n1_cd = 'DOC_CAT_CD' AND level_n2_cd = $1
            """,
            test_category
        )
        assert use_yn == "N"

    @pytest.mark.asyncio
    async def test_delete_category_not_found(self, client: AsyncClient):
        """존재하지 않는 카테고리 삭제 실패"""
        response = await client.delete(
            "/api/v1/admin/vector-categories/00"
        )

        assert response.status_code == 404
        assert "카테고리를 찾을 수 없습니다" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_category_hard_delete_with_documents(
        self,
        client: AsyncClient,
        edb_connection
    ):
        """문서가 있는 카테고리 hard delete 실패"""
        # 문서가 있는 카테고리 코드 (예: "11" - 국회)
        # 실제 데이터에서 문서가 있는 카테고리를 찾아야 함
        category_with_docs = await edb_connection.fetchrow(
            """
            SELECT d.doc_cat_cd, COUNT(*) as doc_count
            FROM wisenut.doc_bas_lst d
            WHERE d.use_yn = 'Y'
            GROUP BY d.doc_cat_cd
            HAVING COUNT(*) > 0
            LIMIT 1
            """
        )

        if category_with_docs:
            response = await client.delete(
                f"/api/v1/admin/vector-categories/{category_with_docs['doc_cat_cd']}",
                params={"hard_delete": True}
            )

            assert response.status_code == 400
            assert "문서가" in response.json()["detail"]
            assert "존재하는 카테고리는 삭제할 수 없습니다" in response.json()["detail"]


class TestVectorCategoriesIntegration:
    """통합 테스트"""

    @pytest.mark.asyncio
    async def test_full_category_lifecycle(self, client: AsyncClient, edb_connection):
        """카테고리 생성 → 수정 → 삭제 전체 흐름"""
        # 1. 다음 코드 조회
        next_code_response = await client.get("/api/v1/admin/vector-categories/next-code")
        assert next_code_response.status_code == 200
        next_code = next_code_response.json()["next_code"]

        # 2. 카테고리 생성
        create_response = await client.post(
            "/api/v1/admin/vector-categories",
            json={
                "code": next_code,
                "name": "라이프사이클 테스트",
                "description": "전체 흐름 테스트"
            }
        )
        assert create_response.status_code == 201
        created = create_response.json()
        assert created["code"] == next_code

        # 3. 목록에서 확인
        list_response = await client.get("/api/v1/admin/vector-categories")
        assert list_response.status_code == 200
        categories = list_response.json()
        assert any(cat["code"] == next_code for cat in categories)

        # 4. 카테고리 수정
        update_response = await client.put(
            f"/api/v1/admin/vector-categories/{next_code}",
            json={
                "name": "수정된 라이프사이클",
                "description": "수정된 설명"
            }
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["name"] == "수정된 라이프사이클"

        # 5. 카테고리 삭제
        delete_response = await client.delete(
            f"/api/v1/admin/vector-categories/{next_code}"
        )
        assert delete_response.status_code == 200

        # 6. 삭제 후 비활성 확인
        use_yn = await edb_connection.fetchval(
            """
            SELECT use_yn FROM wisenut.com_cd_lv2
            WHERE level_n1_cd = 'DOC_CAT_CD' AND level_n2_cd = $1
            """,
            next_code
        )
        assert use_yn == "N"

        # 정리
        await edb_connection.execute(
            """
            DELETE FROM wisenut.com_cd_lv2
            WHERE level_n1_cd = 'DOC_CAT_CD' AND level_n2_cd = $1
            """,
            next_code
        )
