"""
문서 권한 관리 테스트
PRD_v2.md P0 요구사항: 문서 권한 관리

요구사항:
- 부서별 권한 관리
- 결재라인 기반 권한
- 개별 사용자 권한
- 권한 검증 (read, write, delete)

시큐어 코딩:
- 권한 검증: Cerbos 정책 기반
- 최소 권한 원칙: Least Privilege
- 권한 변경 감사 로그
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime


class TestDocumentPermissionCRUD:
    """문서 권한 CRUD 테스트"""

    @pytest_asyncio.fixture
    async def sample_department(self, db_session: AsyncSession):
        """테스트용 부서 생성"""
        from app.models.permission import Department
        import uuid

        dept = Department(
            name=f"테스트부서_{uuid.uuid4().hex[:8]}",
            code=f"TEST_DEPT_{uuid.uuid4().hex[:8]}",
            description="테스트용 부서"
        )
        db_session.add(dept)
        await db_session.commit()
        await db_session.refresh(dept)
        return dept

    @pytest_asyncio.fixture
    async def sample_document(self, db_session: AsyncSession):
        """테스트용 문서 생성"""
        from app.models.document import Document, DocumentType
        import uuid

        doc = Document(
            document_id=f"DOC_PERM_{uuid.uuid4().hex[:8]}",
            title="권한 테스트 문서",
            content="이 문서는 권한 테스트용입니다",
            document_type=DocumentType.OTHER,
            status="active"
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)
        return doc

    @pytest.mark.asyncio
    async def test_grant_department_permission(
        self,
        authenticated_client: AsyncClient,
        sample_document,
        sample_department
    ):
        """
        부서별 권한 부여

        Given: 문서와 부서
        When: POST /api/v1/admin/document-permissions 호출
        Then:
            - 201 Created
            - 권한이 생성됨
        """
        # Given
        perm_data = {
            "document_id": sample_document.id,
            "department_id": sample_department.id,
            "can_read": True,
            "can_write": False,
            "can_delete": False
        }

        # When
        response = await authenticated_client.post(
            "/api/v1/admin/document-permissions/",
            json=perm_data
        )

        # Then
        assert response.status_code == 201
        data = response.json()
        assert data["document_id"] == sample_document.id
        assert data["department_id"] == sample_department.id
        assert data["can_read"] is True
        assert data["can_write"] is False

    @pytest.mark.asyncio
    async def test_list_document_permissions(
        self,
        authenticated_client: AsyncClient,
        sample_document,
        sample_department
    ):
        """
        문서 권한 목록 조회

        Given: 여러 권한 데이터
        When: GET /api/v1/admin/document-permissions/ 호출
        Then: 권한 목록 반환
        """
        # Given: 권한 생성
        perm_data = {
            "document_id": sample_document.id,
            "department_id": sample_department.id,
            "can_read": True
        }
        await authenticated_client.post(
            "/api/v1/admin/document-permissions/",
            json=perm_data
        )

        # When
        response = await authenticated_client.get("/api/v1/admin/document-permissions/")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_permissions_with_filter(
        self,
        authenticated_client: AsyncClient,
        sample_document,
        sample_department
    ):
        """
        필터링으로 권한 조회

        Given: 특정 문서의 권한
        When: document_id 파라미터로 조회
        Then: 해당 문서의 권한만 반환
        """
        # Given
        perm_data = {
            "document_id": sample_document.id,
            "department_id": sample_department.id,
            "can_read": True
        }
        await authenticated_client.post(
            "/api/v1/admin/document-permissions/",
            json=perm_data
        )

        # When
        response = await authenticated_client.get(
            "/api/v1/admin/document-permissions/",
            params={"document_id": sample_document.id}
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        if len(data["items"]) > 0:
            for item in data["items"]:
                assert item["document_id"] == sample_document.id

    @pytest.mark.asyncio
    async def test_update_document_permission(
        self,
        authenticated_client: AsyncClient,
        sample_document,
        sample_department
    ):
        """
        권한 수정

        Given: 기존 권한 (read only)
        When: PUT /api/v1/admin/document-permissions/{id} 호출
        Then: 권한이 수정됨 (read + write)
        """
        # Given: 권한 생성
        perm_data = {
            "document_id": sample_document.id,
            "department_id": sample_department.id,
            "can_read": True,
            "can_write": False
        }
        create_response = await authenticated_client.post(
            "/api/v1/admin/document-permissions/",
            json=perm_data
        )
        perm_id = create_response.json()["id"]

        # When: 쓰기 권한 추가
        update_data = {
            "can_read": True,
            "can_write": True,
            "can_delete": False
        }
        response = await authenticated_client.put(
            f"/api/v1/admin/document-permissions/{perm_id}",
            json=update_data
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["can_write"] is True

    @pytest.mark.asyncio
    async def test_delete_document_permission(
        self,
        authenticated_client: AsyncClient,
        sample_document,
        sample_department
    ):
        """
        권한 삭제

        Given: 기존 권한
        When: DELETE /api/v1/admin/document-permissions/{id} 호출
        Then: 204 No Content
        """
        # Given: 권한 생성
        perm_data = {
            "document_id": sample_document.id,
            "department_id": sample_department.id,
            "can_read": True
        }
        create_response = await authenticated_client.post(
            "/api/v1/admin/document-permissions/",
            json=perm_data
        )
        perm_id = create_response.json()["id"]

        # When
        response = await authenticated_client.delete(
            f"/api/v1/admin/document-permissions/{perm_id}"
        )

        # Then
        assert response.status_code == 204


class TestApprovalLinePermissions:
    """결재라인 기반 권한 테스트"""

    @pytest_asyncio.fixture
    async def sample_approval_line(self, db_session: AsyncSession):
        """테스트용 결재라인 생성"""
        from app.models.document_permission import ApprovalLine

        line = ApprovalLine(
            name="일반 결재라인",
            description="일반 문서 결재라인",
            departments=["1", "2", "3"],
            approvers=[{"name": "홍길동", "position": "부장"}]
        )
        db_session.add(line)
        await db_session.commit()
        await db_session.refresh(line)
        return line

    @pytest.mark.asyncio
    async def test_grant_approval_line_permission(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        sample_approval_line
    ):
        """
        결재라인 기반 권한 부여

        Given: 문서와 결재라인
        When: approval_line_id로 권한 부여
        Then: 결재라인의 모든 부서가 문서 접근 가능
        """
        # Given: 문서 생성
        from app.models.document import Document, DocumentType
        import uuid

        doc = Document(
            document_id=f"DOC_APPROVAL_{uuid.uuid4().hex[:8]}",
            title="결재라인 테스트 문서",
            content="결재라인 기반 권한 테스트",
            document_type=DocumentType.OTHER,
            status="active"
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)

        # When
        perm_data = {
            "document_id": doc.id,
            "approval_line_id": sample_approval_line.id,
            "can_read": True,
            "can_write": False
        }
        response = await authenticated_client.post(
            "/api/v1/admin/document-permissions/",
            json=perm_data
        )

        # Then
        assert response.status_code == 201
        data = response.json()
        assert data["approval_line_id"] == sample_approval_line.id


class TestUserDocumentPermissions:
    """개별 사용자 권한 테스트"""

    @pytest.mark.asyncio
    async def test_grant_user_permission(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        개별 사용자 권한 부여

        Given: 사용자와 부서
        When: POST /api/v1/admin/user-document-permissions/ 호출
        Then: 사용자가 해당 부서 문서 접근 가능
        """
        # Given: 사용자와 부서 생성
        from app.models.user import User
        from app.models.permission import Department
        import uuid

        unique_email = f"test_{uuid.uuid4().hex[:8]}@test.com"
        user = User(
            username=f"user_{uuid.uuid4().hex[:8]}",
            email=unique_email,
            hashed_password="hashed_password",
            full_name="테스트 사용자"
        )
        dept = Department(
            name=f"특별부서_{uuid.uuid4().hex[:8]}",
            code=f"SPECIAL_{uuid.uuid4().hex[:8]}",
            description="특별 접근 부서"
        )
        db_session.add(user)
        db_session.add(dept)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(dept)

        # When
        perm_data = {
            "user_id": user.id,
            "department_id": dept.id
        }
        response = await authenticated_client.post(
            "/api/v1/admin/user-document-permissions/",
            json=perm_data
        )

        # Then
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == user.id
        assert data["department_id"] == dept.id

    @pytest.mark.asyncio
    async def test_revoke_user_permission(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        사용자 권한 회수

        Given: 부여된 사용자 권한
        When: DELETE /api/v1/admin/user-document-permissions/{id} 호출
        Then: 권한이 삭제됨
        """
        # Given: 사용자 권한 부여
        from app.models.user import User
        from app.models.permission import Department
        import uuid

        unique_email = f"test_{uuid.uuid4().hex[:8]}@test.com"
        user = User(
            username=f"user_{uuid.uuid4().hex[:8]}",
            email=unique_email,
            hashed_password="hashed_password",
            full_name="권한 회수 테스트"
        )
        dept = Department(
            name=f"임시부서_{uuid.uuid4().hex[:8]}",
            code=f"TEMP_{uuid.uuid4().hex[:8]}",
            description="임시 접근 부서"
        )
        db_session.add(user)
        db_session.add(dept)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(dept)

        perm_data = {
            "user_id": user.id,
            "department_id": dept.id
        }
        create_response = await authenticated_client.post(
            "/api/v1/admin/user-document-permissions/",
            json=perm_data
        )
        perm_id = create_response.json()["id"]

        # When
        response = await authenticated_client.delete(
            f"/api/v1/admin/user-document-permissions/{perm_id}"
        )

        # Then
        assert response.status_code == 204


class TestPermissionSecurity:
    """권한 관리 보안 테스트"""

    @pytest.mark.asyncio
    async def test_permission_requires_authentication(self, client: AsyncClient):
        """
        권한 관리는 인증 필요

        Given: 인증되지 않은 요청
        When: 권한 API 호출
        Then: 401 Unauthorized
        """
        # When
        response = await client.get("/api/v1/admin/document-permissions/")

        # Then
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_cannot_grant_nonexistent_document(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        존재하지 않는 문서에 권한 부여 불가

        Given: 존재하지 않는 document_id
        When: 권한 부여 시도
        Then: 404 또는 400 에러
        """
        # Given: 부서는 생성
        from app.models.permission import Department

        dept = Department(
            name=f"권한테스트부서_{uuid.uuid4().hex[:8]}",
            code=f"PERM_TEST_{uuid.uuid4().hex[:8]}",
            description="권한 테스트"
        )
        db_session.add(dept)
        await db_session.commit()
        await db_session.refresh(dept)

        # When: 존재하지 않는 문서에 권한 부여
        perm_data = {
            "document_id": 999999,
            "department_id": dept.id,
            "can_read": True
        }
        response = await authenticated_client.post(
            "/api/v1/admin/document-permissions/",
            json=perm_data
        )

        # Then
        assert response.status_code in [400, 404, 422, 500]


class TestPermissionPagination:
    """권한 목록 페이지네이션 테스트"""

    @pytest.mark.asyncio
    async def test_pagination_with_limit(
        self,
        authenticated_client: AsyncClient
    ):
        """
        페이지네이션 (limit)

        Given: 여러 권한 데이터
        When: limit=10으로 조회
        Then: 최대 10개만 반환
        """
        # When
        response = await authenticated_client.get(
            "/api/v1/admin/document-permissions/",
            params={"limit": 10}
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 10

    @pytest.mark.asyncio
    async def test_sort_by_field(
        self,
        authenticated_client: AsyncClient
    ):
        """
        정렬 기능

        Given: 여러 권한 데이터
        When: sort_by=document_id, order=desc로 조회
        Then: document_id 내림차순 정렬
        """
        # When
        response = await authenticated_client.get(
            "/api/v1/admin/document-permissions/",
            params={"sort_by": "document_id", "order": "desc", "limit": 10}
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        if len(data["items"]) >= 2:
            # 내림차순 확인
            for i in range(len(data["items"]) - 1):
                assert data["items"][i]["document_id"] >= data["items"][i + 1]["document_id"]
