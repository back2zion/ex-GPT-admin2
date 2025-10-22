"""
Approval Workflow Service
승인 워크플로우 서비스
"""
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
import logging

from app.models.approval import (
    DocumentChangeRequest,
    ApprovalStep,
    ChangeType,
    RequestStatus,
    ApprovalStatus
)
from app.models.document import Document

logger = logging.getLogger(__name__)


class ApprovalWorkflowService:
    """승인 워크플로우 서비스"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_change_request(
        self,
        document_id: int,
        legacy_id: str,
        change_type: str,
        old_data: Optional[Dict],
        new_data: Dict,
        diff_summary: str,
        requester_id: Optional[int] = None
    ) -> DocumentChangeRequest:
        """
        문서 변경 요청 생성

        Args:
            document_id: 문서 ID
            legacy_id: 레거시 문서 ID
            change_type: 변경 유형 (new, modified, deleted)
            old_data: 기존 데이터
            new_data: 새 데이터
            diff_summary: Diff 요약
            requester_id: 요청자 ID (없으면 시스템 자동)

        Returns:
            DocumentChangeRequest: 생성된 변경 요청
        """
        change_request = DocumentChangeRequest(
            document_id=document_id,
            legacy_id=legacy_id,
            change_type=change_type,
            old_data=old_data,
            new_data=new_data,
            diff_summary=diff_summary,
            status="pending",
            requester_id=requester_id
        )

        self.db_session.add(change_request)
        await self.db_session.flush()
        await self.db_session.refresh(change_request)

        return change_request

    async def list_change_requests(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[DocumentChangeRequest]:
        """
        변경 요청 목록 조회

        Args:
            status: 상태 필터 (pending, approved, rejected, completed)
            limit: 최대 조회 수

        Returns:
            List[DocumentChangeRequest]: 변경 요청 목록
        """
        stmt = select(DocumentChangeRequest).options(
            joinedload(DocumentChangeRequest.document),
            joinedload(DocumentChangeRequest.approval_steps)
        ).order_by(DocumentChangeRequest.created_at.desc()).limit(limit)

        if status:
            stmt = stmt.where(DocumentChangeRequest.status == status)

        result = await self.db_session.execute(stmt)
        return result.unique().scalars().all()

    async def get_change_request(
        self,
        change_request_id: int
    ) -> Optional[DocumentChangeRequest]:
        """
        변경 요청 상세 조회

        Args:
            change_request_id: 변경 요청 ID

        Returns:
            Optional[DocumentChangeRequest]: 변경 요청
        """
        stmt = select(DocumentChangeRequest).options(
            joinedload(DocumentChangeRequest.document),
            joinedload(DocumentChangeRequest.approval_steps)
        ).where(DocumentChangeRequest.id == change_request_id)

        result = await self.db_session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def initiate_approval(
        self,
        change_request_id: int,
        approvers: List[Dict]
    ) -> List[Dict]:
        """
        승인 프로세스 시작

        Args:
            change_request_id: 변경 요청 ID
            approvers: 승인자 리스트
                [
                    {"level": 1, "user_id": 1, "name": "홍길동"},
                    {"level": 2, "user_id": 2, "name": "김철수"}
                ]

        Returns:
            List[Dict]: 생성된 승인 단계 정보
        """
        # 변경 요청 조회
        change_request = await self.get_change_request(change_request_id)
        if not change_request:
            raise ValueError(f"Change request {change_request_id} not found")

        # 승인 단계 생성
        approval_steps = []
        for approver in approvers:
            step = ApprovalStep(
                change_request_id=change_request_id,
                level=approver["level"],
                approver_id=approver["user_id"],
                approver_name=approver["name"],
                status="pending"
            )
            self.db_session.add(step)
            approval_steps.append(step)

        await self.db_session.flush()

        # 결과 반환
        return [
            {
                "id": step.id,
                "level": step.level,
                "approver_id": step.approver_id,
                "approver_name": step.approver_name,
                "status": step.status
            }
            for step in approval_steps
        ]

    async def approve(
        self,
        change_request_id: int,
        approver_id: int,
        level: int,
        comment: Optional[str] = None
    ) -> Dict:
        """
        승인 처리

        Args:
            change_request_id: 변경 요청 ID
            approver_id: 승인자 ID
            level: 승인 단계
            comment: 승인 코멘트

        Returns:
            Dict: 승인 결과
        """
        # 승인 단계 조회
        stmt = select(ApprovalStep).where(
            ApprovalStep.change_request_id == change_request_id,
            ApprovalStep.level == level,
            ApprovalStep.approver_id == approver_id
        )
        result = await self.db_session.execute(stmt)
        step = result.scalar_one_or_none()

        if not step:
            raise ValueError(f"Approval step not found")

        # 승인 처리
        step.status = "approved"
        step.approved_at = datetime.now().isoformat()
        step.comment = comment

        await self.db_session.flush()

        # 모든 단계가 승인되었는지 확인
        all_approved = await self._check_all_approved(change_request_id)

        if all_approved:
            # 변경 요청 상태 업데이트
            change_request = await self.get_change_request(change_request_id)
            change_request.status = "approved"
            change_request.approved_at = datetime.now().isoformat()
            await self.db_session.flush()

        return {
            "id": step.id,
            "level": step.level,
            "status": step.status,
            "approved_at": step.approved_at,
            "all_approved": all_approved
        }

    async def reject(
        self,
        change_request_id: int,
        approver_id: int,
        level: int,
        comment: Optional[str] = None
    ) -> Dict:
        """
        반려 처리

        Args:
            change_request_id: 변경 요청 ID
            approver_id: 승인자 ID
            level: 승인 단계
            comment: 반려 사유

        Returns:
            Dict: 반려 결과
        """
        # 승인 단계 조회
        stmt = select(ApprovalStep).where(
            ApprovalStep.change_request_id == change_request_id,
            ApprovalStep.level == level,
            ApprovalStep.approver_id == approver_id
        )
        result = await self.db_session.execute(stmt)
        step = result.scalar_one_or_none()

        if not step:
            raise ValueError(f"Approval step not found")

        # 반려 처리
        step.status = "rejected"
        step.approved_at = datetime.now().isoformat()
        step.comment = comment

        # 변경 요청 상태 업데이트
        change_request = await self.get_change_request(change_request_id)
        change_request.status = "rejected"

        await self.db_session.flush()

        return {
            "id": step.id,
            "level": step.level,
            "status": step.status,
            "approved_at": step.approved_at,
            "comment": comment
        }

    async def apply_changes(
        self,
        change_request_id: int
    ) -> bool:
        """
        승인된 변경사항을 문서에 적용

        Args:
            change_request_id: 변경 요청 ID

        Returns:
            bool: 적용 성공 여부
        """
        # 변경 요청 조회
        change_request = await self.get_change_request(change_request_id)

        if not change_request:
            logger.error(f"Change request {change_request_id} not found")
            return False

        if change_request.status != "approved":
            logger.warning(f"Change request {change_request_id} is not approved")
            return False

        # 문서 조회
        stmt = select(Document).where(Document.id == change_request.document_id)
        result = await self.db_session.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            logger.error(f"Document {change_request.document_id} not found")
            return False

        try:
            # 변경사항 적용
            new_data = change_request.new_data

            if "title" in new_data:
                document.title = new_data["title"]

            if "content" in new_data:
                document.content = new_data["content"]

            if "document_type" in new_data:
                document.document_type = new_data["document_type"]

            # 변경 요청 상태 업데이트
            change_request.status = "completed"
            change_request.applied_at = datetime.now().isoformat()

            await self.db_session.flush()

            logger.info(f"Successfully applied changes from request {change_request_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to apply changes from request {change_request_id}: {e}")
            return False

    async def _check_all_approved(self, change_request_id: int) -> bool:
        """
        모든 승인 단계가 승인되었는지 확인

        Args:
            change_request_id: 변경 요청 ID

        Returns:
            bool: 모든 단계가 승인되었으면 True
        """
        stmt = select(ApprovalStep).where(
            ApprovalStep.change_request_id == change_request_id
        )
        result = await self.db_session.execute(stmt)
        steps = result.scalars().all()

        if not steps:
            return False

        return all(step.status == "approved" for step in steps)
