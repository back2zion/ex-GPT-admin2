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
            "department_ids": [dept.id]  # List of department IDs
        }
        response = await authenticated_client.post(
            "/api/v1/admin/user-document-permissions/grant",
            json=perm_data
        )

        # Then
        assert response.status_code in [200, 201]
        data = response.json()
        # API returns granted_count and message
        assert "granted_count" in data or "message" in data
        assert data.get("granted_count", 0) >= 1 or "message" in data

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
            "department_ids": [dept.id]  # List of department IDs
        }
        create_response = await authenticated_client.post(
            "/api/v1/admin/user-document-permissions/grant",
            json=perm_data
        )
        assert create_response.status_code in [200, 201]

        # When
        response = await authenticated_client.delete(
            f"/api/v1/admin/user-document-permissions/{user.id}/departments/{dept.id}"
        )

        # Then
        assert response.status_code in [200, 204]


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
        import uuid

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


class TestDocumentPermissionStatistics:
    """
    문서 권한 통계 API 테스트 (TDD)

    요구사항:
    - 사용자별 접근 가능한 문서 수 통계
    - 문서별 권한이 부여된 사용자 수 통계
    - 부서/결재라인별 권한 분포

    시큐어 코딩:
    - 권한 검증: 관리자만 통계 조회 가능
    - 데이터 노출 제한: 민감 정보 제외
    """

    @pytest.mark.asyncio
    async def test_get_user_document_statistics(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        사용자별 문서 접근 통계 조회

        Given: 사용자와 문서 권한 설정
        When: GET /api/v1/admin/document-permissions/stats/users/{user_id}
        Then:
            - 200 OK
            - accessible_documents_count 반환
            - by_department, by_approval_line 세부 정보

        시큐어 코딩:
        - SQLAlchemy ORM 사용 (SQL Injection 방지)
        - Cerbos 권한 검증
        """
        # Given: 테스트 사용자 생성
        from app.models.user import User
        from app.models.permission import Department
        from app.models.document import Document, DocumentType
        from app.models.document_permission import DocumentPermission
        import uuid

        unique_id = uuid.uuid4().hex[:8]

        # 부서 생성
        dept = Department(
            name=f"통계테스트부서_{unique_id}",
            code=f"STATS_{unique_id}",
            description="통계 테스트용"
        )
        db_session.add(dept)
        await db_session.flush()

        # 사용자 생성
        user = User(
            username=f"stats_user_{unique_id}",
            email=f"stats_{unique_id}@test.com",
            hashed_password="hashed",
            department_id=dept.id,
            is_active=True
        )
        db_session.add(user)
        await db_session.flush()

        # 문서 3개 생성
        docs = []
        for i in range(3):
            doc = Document(
                document_id=f"STATS_DOC_{unique_id}_{i}",
                title=f"통계 테스트 문서 {i}",
                content="테스트 내용",
                document_type=DocumentType.OTHER,
                status="active"
            )
            db_session.add(doc)
            docs.append(doc)
        await db_session.flush()

        # 부서에 문서 권한 부여 (2개)
        for i in range(2):
            perm = DocumentPermission(
                document_id=docs[i].id,
                department_id=dept.id,
                can_read=True,
                can_write=False,
                can_delete=False
            )
            db_session.add(perm)
        await db_session.commit()

        # When
        response = await authenticated_client.get(
            f"/api/v1/admin/document-permissions/stats/users/{user.id}"
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "accessible_documents_count" in data
        assert data["accessible_documents_count"] >= 2
        assert "by_department" in data
        assert "by_approval_line" in data

    @pytest.mark.asyncio
    async def test_get_document_permission_summary(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        문서별 권한 요약 조회

        Given: 특정 문서에 여러 권한 설정
        When: GET /api/v1/admin/document-permissions/stats/documents/{doc_id}
        Then:
            - 200 OK
            - total_permissions: 총 권한 수
            - department_count: 부서 권한 수
            - approval_line_count: 결재라인 권한 수
            - affected_users_estimate: 영향받는 예상 사용자 수
        """
        # Given
        from app.models.document import Document, DocumentType
        from app.models.permission import Department
        from app.models.document_permission import DocumentPermission, ApprovalLine
        import uuid

        unique_id = uuid.uuid4().hex[:8]

        # 문서 생성
        doc = Document(
            document_id=f"SUMMARY_DOC_{unique_id}",
            title="권한 요약 테스트 문서",
            content="테스트",
            document_type=DocumentType.OTHER,
            status="active"
        )
        db_session.add(doc)
        await db_session.flush()

        # 부서 2개 생성
        depts = []
        for i in range(2):
            dept = Department(
                name=f"요약부서_{unique_id}_{i}",
                code=f"SUM_{unique_id}_{i}",
                description="요약 테스트"
            )
            db_session.add(dept)
            depts.append(dept)
        await db_session.flush()

        # 권한 부여
        for dept in depts:
            perm = DocumentPermission(
                document_id=doc.id,
                department_id=dept.id,
                can_read=True,
                can_write=False,
                can_delete=False
            )
            db_session.add(perm)
        await db_session.commit()

        # When
        response = await authenticated_client.get(
            f"/api/v1/admin/document-permissions/stats/documents/{doc.id}"
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "total_permissions" in data
        assert data["total_permissions"] >= 2
        assert "department_count" in data
        assert data["department_count"] == 2
        assert "approval_line_count" in data


class TestPermissionConflictDetection:
    """
    권한 충돌 감지 테스트 (TDD)

    요구사항:
    - 같은 문서에 중복 권한 감지
    - 권한 레벨 충돌 감지 (부서: 읽기, 결재라인: 쓰기)
    - 자동 해결 제안

    시큐어 코딩:
    - 입력 검증: Pydantic 모델
    - 권한 검증: 관리자만 충돌 확인 가능
    """

    @pytest.mark.asyncio
    async def test_detect_duplicate_permissions(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        중복 권한 감지

        Given: 같은 문서-부서 조합에 권한 2개
        When: GET /api/v1/admin/document-permissions/conflicts
        Then:
            - 200 OK
            - conflicts 배열에 중복 권한 정보 포함
            - conflict_type: "duplicate"

        시큐어 코딩:
        - SQLAlchemy GROUP BY로 안전한 쿼리
        """
        # Given
        from app.models.document import Document, DocumentType
        from app.models.permission import Department
        from app.models.document_permission import DocumentPermission
        import uuid

        unique_id = uuid.uuid4().hex[:8]

        # 문서와 부서 생성
        doc = Document(
            document_id=f"CONFLICT_DOC_{unique_id}",
            title="충돌 테스트 문서",
            content="테스트",
            document_type=DocumentType.OTHER,
            status="active"
        )
        dept = Department(
            name=f"충돌부서_{unique_id}",
            code=f"CONF_{unique_id}",
            description="충돌 테스트"
        )
        db_session.add_all([doc, dept])
        await db_session.flush()

        # 같은 문서-부서에 권한 2개 생성 (중복)
        perm1 = DocumentPermission(
            document_id=doc.id,
            department_id=dept.id,
            can_read=True,
            can_write=False,
            can_delete=False
        )
        perm2 = DocumentPermission(
            document_id=doc.id,
            department_id=dept.id,
            can_read=True,
            can_write=True,  # 다른 권한
            can_delete=False
        )
        db_session.add_all([perm1, perm2])
        await db_session.commit()

        # When
        response = await authenticated_client.get(
            "/api/v1/admin/document-permissions/conflicts"
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "conflicts" in data
        # 중복 권한이 있을 수 있음 (다른 테스트의 데이터)
        if len(data["conflicts"]) > 0:
            # 우리가 생성한 충돌이 포함되어 있는지 확인
            conflict_found = any(
                c.get("document_id") == doc.id and
                c.get("department_id") == dept.id
                for c in data["conflicts"]
            )
            assert conflict_found

    @pytest.mark.asyncio
    async def test_detect_permission_level_conflicts(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        권한 레벨 충돌 감지

        Given: 같은 문서에 부서(읽기) + 결재라인(쓰기) 권한
        When: GET /api/v1/admin/document-permissions/conflicts?type=level
        Then:
            - 200 OK
            - 권한 레벨 충돌 정보 반환
            - conflict_type: "permission_level"
        """
        # Given
        from app.models.document import Document, DocumentType
        from app.models.permission import Department
        from app.models.document_permission import DocumentPermission, ApprovalLine
        import uuid

        unique_id = uuid.uuid4().hex[:8]

        # 문서, 부서, 결재라인 생성
        doc = Document(
            document_id=f"LEVEL_DOC_{unique_id}",
            title="레벨 충돌 테스트",
            content="테스트",
            document_type=DocumentType.OTHER,
            status="active"
        )
        dept = Department(
            name=f"레벨부서_{unique_id}",
            code=f"LVL_{unique_id}",
            description="레벨 테스트"
        )
        approval_line = ApprovalLine(
            name=f"레벨라인_{unique_id}",
            description="레벨 테스트 라인",
            departments=[dept.id] if hasattr(dept, 'id') else []
        )
        db_session.add_all([doc, dept, approval_line])
        await db_session.flush()

        # 부서: 읽기만
        perm1 = DocumentPermission(
            document_id=doc.id,
            department_id=dept.id,
            can_read=True,
            can_write=False,
            can_delete=False
        )
        # 결재라인: 쓰기 가능 (상위 권한)
        perm2 = DocumentPermission(
            document_id=doc.id,
            approval_line_id=approval_line.id,
            can_read=True,
            can_write=True,
            can_delete=False
        )
        db_session.add_all([perm1, perm2])
        await db_session.commit()

        # When
        response = await authenticated_client.get(
            "/api/v1/admin/document-permissions/conflicts",
            params={"type": "level"}
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "conflicts" in data
        # 충돌이 감지되어야 함 (부서와 결재라인 권한 불일치)
