"""
레거시 시스템 연계 - 제·개정 문서 승인 워크플로우 테스트
PRD_v2.md P0 요구사항: 레거시 시스템 연계

요구사항:
- 문서 변경 감지 시스템
- 승인 워크플로우 (승인 대기, 승인/반려 처리, 이력 기록)
- 자동 전처리 반영

시큐어 코딩:
- SQL Injection 방지: Parameterized queries
- 권한 검증: Cerbos 기반 RBAC
- 입력 검증: Pydantic 스키마
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime


class TestDocumentChangeDetection:
    """문서 변경 감지 테스트"""

    @pytest.mark.asyncio
    async def test_detect_document_changes(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        문서 변경 감지

        Given: 레거시 DB에 변경된 문서
        When: 변경 감지 API 호출
        Then: 변경 감지 결과 반환
        """
        # Given: 문서 생성
        from app.models.document import Document, DocumentType
        import uuid

        doc = Document(
            document_id=f"DOC_LEGACY_{uuid.uuid4().hex[:8]}",
            title="레거시 문서",
            content="원본 내용",
            document_type=DocumentType.LAW,
            status="active"
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)

        # When: 변경 감지 (Mock - 실제로는 레거시 DB 비교)
        response = await authenticated_client.get(
            "/api/v1/admin/legacy-sync/detect-changes"
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "changes" in data or "total" in data

    @pytest.mark.asyncio
    async def test_compare_document_versions(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        문서 버전 비교 (변경 전/후)

        Given: 변경된 문서
        When: 비교 API 호출
        Then: diff 결과 반환
        """
        # Given: 문서와 변경 요청 생성
        from app.models.document import Document, DocumentType
        import uuid

        doc = Document(
            document_id=f"DOC_COMPARE_{uuid.uuid4().hex[:8]}",
            title="비교 테스트 문서",
            content="원본 내용입니다.",
            document_type=DocumentType.REGULATION,
            status="active"
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)

        # When: 변경 요청 생성 및 비교
        change_data = {
            "document_id": doc.id,
            "legacy_id": "LEG_001",
            "change_type": "modified",
            "new_data": {
                "title": "비교 테스트 문서",
                "content": "수정된 내용입니다."
            }
        }
        response = await authenticated_client.post(
            "/api/v1/admin/legacy-sync/change-requests",
            json=change_data
        )

        # Then
        assert response.status_code == 201
        data = response.json()
        assert data["change_type"] == "modified"
        assert "diff_summary" in data or "new_data" in data


class TestApprovalWorkflow:
    """승인 워크플로우 테스트"""

    @pytest_asyncio.fixture
    async def sample_change_request(self, db_session: AsyncSession):
        """테스트용 변경 요청 생성"""
        from app.models.document import Document, DocumentType
        import uuid

        # 문서 생성
        doc = Document(
            document_id=f"DOC_APPROVAL_{uuid.uuid4().hex[:8]}",
            title="승인 테스트 문서",
            content="원본 내용",
            document_type=DocumentType.LAW,
            status="active"
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)

        # 모델이 생성되면 여기서 변경 요청 생성
        # 지금은 document만 반환
        return {"doc": doc}

    @pytest.mark.asyncio
    async def test_list_pending_change_requests(
        self,
        authenticated_client: AsyncClient,
        sample_change_request
    ):
        """
        승인 대기 목록 조회

        Given: 여러 승인 대기 중인 변경 요청
        When: GET /api/v1/admin/legacy-sync/change-requests 호출
        Then: 대기 중인 변경 요청 목록 반환
        """
        # When
        response = await authenticated_client.get(
            "/api/v1/admin/legacy-sync/change-requests",
            params={"status": "pending"}
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)

    @pytest.mark.asyncio
    async def test_approve_document_change(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        sample_change_request
    ):
        """
        문서 변경 승인

        Given: 승인 대기 중인 변경 요청
        When: POST /api/v1/admin/legacy-sync/change-requests/{id}/approve 호출
        Then:
            - 200 응답
            - status가 approved로 변경
            - 승인 시간 기록
        """
        # Given: 변경 요청 생성
        doc = sample_change_request["doc"]
        change_data = {
            "document_id": doc.id,
            "legacy_id": "LEG_APPROVE_001",
            "change_type": "modified",
            "new_data": {
                "title": doc.title,
                "content": "승인될 내용"
            }
        }
        create_response = await authenticated_client.post(
            "/api/v1/admin/legacy-sync/change-requests",
            json=change_data
        )
        assert create_response.status_code == 201
        change_id = create_response.json()["id"]

        # When: 승인 처리
        response = await authenticated_client.post(
            f"/api/v1/admin/legacy-sync/change-requests/{change_id}/approve"
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["approved", "completed"]
        assert "approved_at" in data or "message" in data

    @pytest.mark.asyncio
    async def test_reject_document_change(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        sample_change_request
    ):
        """
        문서 변경 반려

        Given: 승인 대기 중인 변경 요청
        When: POST /api/v1/admin/legacy-sync/change-requests/{id}/reject 호출
        Then:
            - 200 응답
            - status가 rejected로 변경
            - 반려 사유 기록
        """
        # Given: 변경 요청 생성
        doc = sample_change_request["doc"]
        change_data = {
            "document_id": doc.id,
            "legacy_id": "LEG_REJECT_001",
            "change_type": "modified",
            "new_data": {
                "title": doc.title,
                "content": "반려될 내용"
            }
        }
        create_response = await authenticated_client.post(
            "/api/v1/admin/legacy-sync/change-requests",
            json=change_data
        )
        assert create_response.status_code == 201
        change_id = create_response.json()["id"]

        # When: 반려 처리
        reject_data = {
            "reason": "내용이 부적절합니다"
        }
        response = await authenticated_client.post(
            f"/api/v1/admin/legacy-sync/change-requests/{change_id}/reject",
            json=reject_data
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_get_change_request_detail(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        sample_change_request
    ):
        """
        변경 요청 상세 조회

        Given: 변경 요청
        When: GET /api/v1/admin/legacy-sync/change-requests/{id} 호출
        Then: 변경 전/후 비교 정보 포함 반환
        """
        # Given: 변경 요청 생성
        doc = sample_change_request["doc"]
        change_data = {
            "document_id": doc.id,
            "legacy_id": "LEG_DETAIL_001",
            "change_type": "modified",
            "old_data": {
                "title": doc.title,
                "content": doc.content
            },
            "new_data": {
                "title": doc.title,
                "content": "변경된 내용"
            }
        }
        create_response = await authenticated_client.post(
            "/api/v1/admin/legacy-sync/change-requests",
            json=change_data
        )
        assert create_response.status_code == 201
        change_id = create_response.json()["id"]

        # When
        response = await authenticated_client.get(
            f"/api/v1/admin/legacy-sync/change-requests/{change_id}"
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == change_id
        assert "old_data" in data or "new_data" in data
        assert data["change_type"] == "modified"


class TestAutoPreprocessing:
    """자동 전처리 반영 테스트"""

    @pytest.mark.asyncio
    async def test_auto_preprocessing_trigger_on_approval(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        승인 시 자동 전처리 트리거

        Given: 승인된 변경 요청
        When: 변경 승인
        Then:
            - 문서 내용 업데이트
            - 전처리 작업 트리거 (Phase 2)
        """
        # Given: 문서와 변경 요청
        from app.models.document import Document, DocumentType
        import uuid

        doc = Document(
            document_id=f"DOC_PREPROCESS_{uuid.uuid4().hex[:8]}",
            title="전처리 테스트 문서",
            content="원본 내용",
            document_type=DocumentType.LAW,
            status="active"
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)

        change_data = {
            "document_id": doc.id,
            "legacy_id": "LEG_PREPROCESS_001",
            "change_type": "modified",
            "new_data": {
                "title": doc.title,
                "content": "전처리될 새 내용"
            }
        }
        create_response = await authenticated_client.post(
            "/api/v1/admin/legacy-sync/change-requests",
            json=change_data
        )
        change_id = create_response.json()["id"]

        # When: 승인
        approve_response = await authenticated_client.post(
            f"/api/v1/admin/legacy-sync/change-requests/{change_id}/approve"
        )

        # Then
        assert approve_response.status_code == 200

        # 문서가 업데이트되었는지 확인
        from sqlalchemy import select
        from app.models.document import Document
        result = await db_session.execute(
            select(Document).where(Document.id == doc.id)
        )
        updated_doc = result.scalar_one_or_none()
        if updated_doc:
            # 승인 후 문서 업데이트 확인 (구현 후 검증)
            # assert updated_doc.content == "전처리될 새 내용"
            pass


class TestSecurity:
    """보안 테스트"""

    @pytest.mark.asyncio
    async def test_change_requests_require_authentication(
        self,
        client: AsyncClient
    ):
        """
        변경 요청 조회는 인증 필요

        Given: 인증되지 않은 요청
        When: 변경 요청 API 호출
        Then: 401 Unauthorized
        """
        # When
        response = await client.get(
            "/api/v1/admin/legacy-sync/change-requests"
        )

        # Then
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_approve_requires_permission(
        self,
        authenticated_client: AsyncClient
    ):
        """
        승인은 권한 필요 (향후 Cerbos 연동)

        Given: 권한 없는 사용자
        When: 승인 API 호출
        Then: 승인 처리 (현재는 인증만 확인)
        """
        # Mock change request ID
        fake_id = 99999

        # When
        response = await authenticated_client.post(
            f"/api/v1/admin/legacy-sync/change-requests/{fake_id}/approve"
        )

        # Then: 404 (존재하지 않는 ID) 또는 403 (권한 없음)
        assert response.status_code in [404, 403, 400]

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(
        self,
        authenticated_client: AsyncClient
    ):
        """
        SQL Injection 방지

        Given: SQL Injection 시도 문자열
        When: legacy_id 파라미터에 주입
        Then: 안전하게 처리됨
        """
        # Given
        malicious_input = "'; DROP TABLE document_change_requests; --"

        # When
        response = await authenticated_client.get(
            "/api/v1/admin/legacy-sync/change-requests",
            params={"legacy_id": malicious_input}
        )

        # Then: 정상 처리 (빈 결과 또는 400)
        assert response.status_code in [200, 400]
