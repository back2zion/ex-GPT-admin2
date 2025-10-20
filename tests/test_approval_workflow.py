"""
Test Approval Workflow for Document Changes
문서 변경 승인 워크플로우 테스트 (TDD)
"""
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.unit
class TestDocumentChangeRequest:
    """문서 변경 요청 테스트"""

    async def test_create_change_request(self, db_session: AsyncSession):
        """문서 변경 요청 생성 테스트"""
        from app.services.approval_workflow import ApprovalWorkflowService
        from app.models.document import Document

        service = ApprovalWorkflowService(db_session)

        # 기존 문서 생성
        existing_doc = Document(
            document_id="DOC_APPR_001",
            title="기존 문서",
            content="기존 내용",
            document_type="law",
            status="active",
            legacy_id="LEG_APPR_001"
        )
        db_session.add(existing_doc)
        await db_session.flush()

        # 변경 요청 생성
        change_request = await service.create_change_request(
            document_id=existing_doc.id,
            legacy_id="LEG_APPR_001",
            change_type="modified",
            old_data={
                "title": "기존 문서",
                "content": "기존 내용"
            },
            new_data={
                "title": "수정된 문서",
                "content": "수정된 내용"
            },
            diff_summary="제목 및 내용 수정"
        )

        # 검증
        assert change_request is not None
        assert change_request.document_id == existing_doc.id
        assert change_request.change_type == "modified"
        assert change_request.status == "pending"

    async def test_list_pending_change_requests(self, db_session: AsyncSession):
        """대기 중인 변경 요청 목록 조회 테스트"""
        from app.services.approval_workflow import ApprovalWorkflowService

        service = ApprovalWorkflowService(db_session)

        # 대기 중인 요청 목록 조회
        pending_requests = await service.list_change_requests(status="pending")

        # 검증
        assert isinstance(pending_requests, list)

    async def test_get_change_request_detail(self, db_session: AsyncSession):
        """변경 요청 상세 조회 테스트"""
        from app.services.approval_workflow import ApprovalWorkflowService
        from app.models.document import Document

        service = ApprovalWorkflowService(db_session)

        # 문서 및 변경 요청 생성
        doc = Document(
            document_id="DOC_APPR_002",
            title="테스트 문서",
            content="테스트 내용",
            document_type="law",
            status="active"
        )
        db_session.add(doc)
        await db_session.flush()

        change_request = await service.create_change_request(
            document_id=doc.id,
            legacy_id="LEG002",
            change_type="new",
            old_data=None,
            new_data={"title": "신규 문서", "content": "신규 내용"},
            diff_summary="신규 문서 추가"
        )

        # 상세 조회
        detail = await service.get_change_request(change_request.id)

        # 검증
        assert detail is not None
        assert detail.id == change_request.id
        assert detail.change_type == "new"


@pytest.mark.unit
class TestApprovalProcess:
    """승인 프로세스 테스트"""

    async def test_initiate_approval_process(self, db_session: AsyncSession):
        """승인 프로세스 시작 테스트"""
        from app.services.approval_workflow import ApprovalWorkflowService
        from app.models.document import Document
        from app.models.user import User

        service = ApprovalWorkflowService(db_session)

        # 승인자 생성
        user1 = User(username="init_user1", email="init1@example.com", full_name="사용자1", hashed_password="hashed")
        user2 = User(username="init_user2", email="init2@example.com", full_name="사용자2", hashed_password="hashed")
        db_session.add(user1)
        db_session.add(user2)
        await db_session.flush()

        # 문서 및 변경 요청 생성
        doc = Document(
            document_id="DOC_APPR_003",
            title="승인 테스트",
            content="내용",
            document_type="law",
            status="active"
        )
        db_session.add(doc)
        await db_session.flush()

        change_request = await service.create_change_request(
            document_id=doc.id,
            legacy_id="LEG003",
            change_type="modified",
            old_data={"content": "기존"},
            new_data={"content": "수정"},
            diff_summary="내용 수정"
        )

        # 승인 프로세스 시작 (승인자 리스트 지정)
        approvers = [
            {"level": 1, "user_id": user1.id, "name": "1차 승인자"},
            {"level": 2, "user_id": user2.id, "name": "2차 승인자"}
        ]

        approval_process = await service.initiate_approval(
            change_request_id=change_request.id,
            approvers=approvers
        )

        # 검증
        assert approval_process is not None
        assert len(approval_process) >= 1
        assert approval_process[0]["level"] == 1
        assert approval_process[0]["status"] == "pending"

    async def test_approve_request(self, db_session: AsyncSession, sample_user_data):
        """승인 처리 테스트"""
        from app.services.approval_workflow import ApprovalWorkflowService
        from app.models.document import Document
        from app.models.user import User

        service = ApprovalWorkflowService(db_session)

        # 승인자 생성
        user_data = sample_user_data.copy()
        user_data["hashed_password"] = user_data.pop("password")  # Use hashed_password instead of password
        user_data.pop("role_ids", None)  # Remove role_ids if it exists
        user_data["username"] = "approve_user"
        user_data["email"] = "approve@example.com"
        approver = User(**user_data)
        db_session.add(approver)
        await db_session.flush()

        # 문서 및 변경 요청 생성
        doc = Document(
            document_id="DOC_APPR_004",
            title="승인 처리 테스트",
            content="내용",
            document_type="law",
            status="active"
        )
        db_session.add(doc)
        await db_session.flush()

        change_request = await service.create_change_request(
            document_id=doc.id,
            legacy_id="LEG004",
            change_type="modified",
            old_data={"content": "기존"},
            new_data={"content": "수정"},
            diff_summary="수정"
        )

        # 승인 프로세스 시작
        await service.initiate_approval(
            change_request_id=change_request.id,
            approvers=[{"level": 1, "user_id": approver.id, "name": approver.username}]
        )

        # 승인 처리
        result = await service.approve(
            change_request_id=change_request.id,
            approver_id=approver.id,
            level=1,
            comment="승인합니다"
        )

        # 검증
        assert result is not None
        assert result["status"] == "approved"

    async def test_reject_request(self, db_session: AsyncSession, sample_user_data):
        """반려 처리 테스트"""
        from app.services.approval_workflow import ApprovalWorkflowService
        from app.models.document import Document
        from app.models.user import User

        service = ApprovalWorkflowService(db_session)

        # 승인자 생성
        user_data = sample_user_data.copy()
        user_data["hashed_password"] = user_data.pop("password")
        user_data.pop("role_ids", None)  # Remove role_ids if it exists
        user_data["username"] = "rejector"
        user_data["email"] = "rejector@example.com"
        approver = User(**user_data)
        db_session.add(approver)
        await db_session.flush()

        # 문서 및 변경 요청 생성
        doc = Document(
            document_id="DOC_APPR_005",
            title="반려 테스트",
            content="내용",
            document_type="law",
            status="active"
        )
        db_session.add(doc)
        await db_session.flush()

        change_request = await service.create_change_request(
            document_id=doc.id,
            legacy_id="LEG005",
            change_type="modified",
            old_data={"content": "기존"},
            new_data={"content": "수정"},
            diff_summary="수정"
        )

        # 승인 프로세스 시작
        await service.initiate_approval(
            change_request_id=change_request.id,
            approvers=[{"level": 1, "user_id": approver.id, "name": approver.username}]
        )

        # 반려 처리
        result = await service.reject(
            change_request_id=change_request.id,
            approver_id=approver.id,
            level=1,
            comment="수정이 필요합니다"
        )

        # 검증
        assert result is not None
        assert result["status"] == "rejected"

    async def test_multi_level_approval(self, db_session: AsyncSession):
        """다단계 승인 테스트"""
        from app.services.approval_workflow import ApprovalWorkflowService
        from app.models.document import Document
        from app.models.user import User

        service = ApprovalWorkflowService(db_session)

        # 승인자 2명 생성
        user1 = User(
            username="approver1",
            email="approver1@example.com",
            full_name="승인자1",
            hashed_password="hashed"
        )
        user2 = User(
            username="approver2",
            email="approver2@example.com",
            full_name="승인자2",
            hashed_password="hashed"
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.flush()

        # 문서 및 변경 요청 생성
        doc = Document(
            document_id="DOC_APPR_006",
            title="다단계 승인",
            content="내용",
            document_type="law",
            status="active"
        )
        db_session.add(doc)
        await db_session.flush()

        change_request = await service.create_change_request(
            document_id=doc.id,
            legacy_id="LEG006",
            change_type="modified",
            old_data={"content": "기존"},
            new_data={"content": "수정"},
            diff_summary="수정"
        )

        # 2단계 승인 프로세스 시작
        await service.initiate_approval(
            change_request_id=change_request.id,
            approvers=[
                {"level": 1, "user_id": user1.id, "name": user1.username},
                {"level": 2, "user_id": user2.id, "name": user2.username}
            ]
        )

        # 1차 승인
        result1 = await service.approve(
            change_request_id=change_request.id,
            approver_id=user1.id,
            level=1,
            comment="1차 승인"
        )

        # 검증: 1차 승인 완료, 전체 상태는 여전히 pending
        assert result1["status"] == "approved"

        # 2차 승인
        result2 = await service.approve(
            change_request_id=change_request.id,
            approver_id=user2.id,
            level=2,
            comment="2차 승인"
        )

        # 검증: 모든 승인 완료
        assert result2["status"] == "approved"

        # 전체 요청 상태 확인
        change_request_updated = await service.get_change_request(change_request.id)
        assert change_request_updated.status in ["approved", "completed"]


@pytest.mark.unit
class TestAutoApplyChanges:
    """자동 변경 적용 테스트"""

    async def test_auto_apply_after_full_approval(self, db_session: AsyncSession):
        """전체 승인 후 자동 적용 테스트"""
        from app.services.approval_workflow import ApprovalWorkflowService
        from app.models.document import Document
        from app.models.user import User

        service = ApprovalWorkflowService(db_session)

        # 승인자 생성
        approver = User(
            username="auto_approver",
            email="auto@example.com",
            full_name="자동승인자",
            hashed_password="hashed"
        )
        db_session.add(approver)
        await db_session.flush()

        # 문서 생성
        doc = Document(
            document_id="DOC_APPR_007",
            title="기존 제목",
            content="기존 내용",
            document_type="law",
            status="active"
        )
        db_session.add(doc)
        await db_session.flush()

        # 변경 요청 생성
        change_request = await service.create_change_request(
            document_id=doc.id,
            legacy_id="LEG007",
            change_type="modified",
            old_data={"title": "기존 제목", "content": "기존 내용"},
            new_data={"title": "수정된 제목", "content": "수정된 내용"},
            diff_summary="제목 및 내용 수정"
        )

        # 승인 프로세스 및 승인
        await service.initiate_approval(
            change_request_id=change_request.id,
            approvers=[{"level": 1, "user_id": approver.id, "name": approver.username}]
        )

        await service.approve(
            change_request_id=change_request.id,
            approver_id=approver.id,
            level=1,
            comment="최종 승인"
        )

        # 변경사항 자동 적용
        applied = await service.apply_changes(change_request.id)

        # 검증
        assert applied is True

        # 문서가 실제로 변경되었는지 확인
        await db_session.refresh(doc)
        assert doc.title == "수정된 제목"
        assert doc.content == "수정된 내용"
