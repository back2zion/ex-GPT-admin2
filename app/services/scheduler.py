"""
Document Synchronization Scheduler
자동 문서 동기화 스케줄러
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.services.legacy_db import LegacyDBService
from app.services.document_sync import DocumentSyncService
from app.services.approval_workflow import ApprovalWorkflowService
from app.services.diff_generator import DiffGenerator
from app.models.document import Document

logger = logging.getLogger(__name__)


class DocumentSyncScheduler:
    """문서 동기화 스케줄러"""

    def __init__(self):
        """스케줄러 초기화"""
        self.scheduler = AsyncIOScheduler()
        self.job_id = "document_sync"
        self._is_running = False

    def configure_sync_job(
        self,
        interval_hours: Optional[int] = None,
        start_hour: Optional[int] = None,
        start_minute: Optional[int] = None
    ):
        """
        동기화 작업 설정

        Args:
            interval_hours: 실행 간격 (시간 단위)
            start_hour: 시작 시간 (0-23)
            start_minute: 시작 분 (0-59)
        """
        # 기존 작업 제거
        if self.scheduler.get_job(self.job_id):
            self.scheduler.remove_job(self.job_id)

        # 트리거 설정
        if interval_hours:
            # 주기적 실행
            trigger = IntervalTrigger(hours=interval_hours)
        elif start_hour is not None and start_minute is not None:
            # 매일 특정 시간 실행
            trigger = CronTrigger(hour=start_hour, minute=start_minute)
        else:
            # 기본: 매일 자정
            trigger = CronTrigger(hour=0, minute=0)

        # 작업 등록 (실제 실행은 별도로)
        # Note: 실제 DB 세션은 실행 시점에 생성
        logger.info(f"Configured sync job with trigger: {trigger}")

    async def run_sync_job(self, db_session: AsyncSession) -> Dict:
        """
        동기화 작업 실행

        Args:
            db_session: DB 세션

        Returns:
            Dict: 실행 결과
        """
        logger.info("Starting document synchronization job")

        try:
            # 레거시 DB 서비스 생성
            legacy_service = LegacyDBService(
                host="postgres",  # 테스트용
                port=5432,
                database="admin_db",
                user="postgres",
                password="password"
            )

            # 레거시 문서 조회
            legacy_docs = await legacy_service.fetch_documents()
            logger.info(f"Fetched {len(legacy_docs)} documents from legacy DB")

            # 변경사항 처리
            result = await self.process_changes(db_session, legacy_docs)

            # 정리
            await legacy_service.close()

            logger.info(f"Sync job completed: {result}")
            return result

        except Exception as e:
            logger.error(f"Error during sync job: {e}")
            return {
                "error": str(e),
                "processed": 0,
                "change_requests_created": 0
            }

    async def process_changes(
        self,
        db_session: AsyncSession,
        legacy_docs: Optional[List[Dict]]
    ) -> Dict:
        """
        변경사항 처리 및 자동 요청 생성

        Args:
            db_session: DB 세션
            legacy_docs: 레거시 문서 목록

        Returns:
            Dict: 처리 결과
        """
        if legacy_docs is None:
            logger.warning("No legacy documents provided")
            return {
                "processed": 0,
                "change_requests_created": 0,
                "changes": {"new": [], "modified": [], "deleted": []}
            }

        try:
            # 변경사항 감지
            sync_service = DocumentSyncService(db_session)
            changes = await sync_service.detect_changes(legacy_docs)

            logger.info(f"Detected changes: {len(changes['new'])} new, "
                       f"{len(changes['modified'])} modified, "
                       f"{len(changes['deleted'])} deleted")

            # 변경 요청 생성
            approval_service = ApprovalWorkflowService(db_session)
            diff_generator = DiffGenerator()
            change_requests_created = 0

            # 신규 문서 처리
            for new_doc in changes["new"]:
                # 신규 문서는 현재 DB에 없으므로 먼저 생성
                doc = Document(
                    document_id=f"DOC_{new_doc['legacy_id']}",
                    title=new_doc["title"],
                    content=new_doc["content"],
                    document_type=new_doc["document_type"],
                    status="pending",
                    legacy_id=str(new_doc["legacy_id"])  # int to str
                )
                db_session.add(doc)
                await db_session.flush()

                # 변경 요청 생성
                await approval_service.create_change_request(
                    document_id=doc.id,
                    legacy_id=str(new_doc["legacy_id"]),  # int to str
                    change_type="new",
                    old_data=None,
                    new_data=new_doc,
                    diff_summary="신규 문서 추가"
                )
                change_requests_created += 1

            # 수정된 문서 처리
            for modified_doc in changes["modified"]:
                # 기존 문서 조회
                stmt = select(Document).where(
                    Document.legacy_id == str(modified_doc["legacy_id"])  # int to str
                )
                result = await db_session.execute(stmt)
                existing_doc = result.scalar_one_or_none()

                if existing_doc:
                    # Diff 생성
                    diff_result = diff_generator.generate_document_diff(
                        {
                            "title": existing_doc.title,
                            "content": existing_doc.content
                        },
                        {
                            "title": modified_doc["title"],
                            "content": modified_doc["content"]
                        }
                    )

                    # 변경 요청 생성
                    await approval_service.create_change_request(
                        document_id=existing_doc.id,
                        legacy_id=str(modified_doc["legacy_id"]),  # int to str
                        change_type="modified",
                        old_data={
                            "title": existing_doc.title,
                            "content": existing_doc.content
                        },
                        new_data={
                            "title": modified_doc["title"],
                            "content": modified_doc["content"]
                        },
                        diff_summary=f"변경사항: {', '.join(diff_result.get('changes', []))}"
                    )
                    change_requests_created += 1

            # 삭제된 문서 처리
            for deleted_doc in changes["deleted"]:
                # 변경 요청 생성 (삭제)
                stmt = select(Document).where(
                    Document.legacy_id == str(deleted_doc["legacy_id"])  # int to str
                )
                result = await db_session.execute(stmt)
                existing_doc = result.scalar_one_or_none()

                if existing_doc:
                    await approval_service.create_change_request(
                        document_id=existing_doc.id,
                        legacy_id=str(deleted_doc["legacy_id"]),  # int to str
                        change_type="deleted",
                        old_data={
                            "title": existing_doc.title,
                            "content": existing_doc.content
                        },
                        new_data=None,
                        diff_summary="레거시 DB에서 삭제됨"
                    )
                    change_requests_created += 1

            await db_session.flush()

            return {
                "processed": len(legacy_docs),
                "change_requests_created": change_requests_created,
                "changes": changes
            }

        except Exception as e:
            logger.error(f"Error processing changes: {e}")
            raise

    def start(self):
        """스케줄러 시작"""
        if not self._is_running:
            self.scheduler.start()
            self._is_running = True
            logger.info("Scheduler started")

    def shutdown(self):
        """스케줄러 중지"""
        if self._is_running:
            self.scheduler.shutdown(wait=False)
            self._is_running = False
            logger.info("Scheduler shutdown")

    def pause(self):
        """스케줄러 일시정지"""
        if self._is_running:
            self.scheduler.pause()
            self._is_running = False
            logger.info("Scheduler paused")

    def resume(self):
        """스케줄러 재개"""
        if not self._is_running:
            self.scheduler.resume()
            self._is_running = True
            logger.info("Scheduler resumed")

    def is_running(self) -> bool:
        """
        스케줄러 실행 상태 확인

        Returns:
            bool: 실행 중이면 True
        """
        return self._is_running

    def get_jobs(self) -> List:
        """
        등록된 작업 목록 조회

        Returns:
            List: 작업 목록
        """
        return self.scheduler.get_jobs()

    def remove_job(self, job_id: str) -> bool:
        """
        작업 제거

        Args:
            job_id: 작업 ID

        Returns:
            bool: 제거 성공 여부
        """
        try:
            self.scheduler.remove_job(job_id)
            return True
        except Exception:
            return False

    def get_next_run_time(self, job_id: str) -> Optional[datetime]:
        """
        다음 실행 시간 조회

        Args:
            job_id: 작업 ID

        Returns:
            Optional[datetime]: 다음 실행 시간
        """
        job = self.scheduler.get_job(job_id)
        if job:
            return job.next_run_time
        return None
