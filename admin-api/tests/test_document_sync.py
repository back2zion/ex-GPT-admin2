"""
Test Document Synchronization and Change Detection
문서 동기화 및 변경 감지 테스트 (TDD)
"""
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.unit
class TestDocumentChangeDetection:
    """문서 변경 감지 테스트"""

    async def test_detect_new_documents(self, db_session: AsyncSession):
        """신규 문서 감지 테스트"""
        from app.services.document_sync import DocumentSyncService
        from app.models.document import Document

        service = DocumentSyncService(db_session)

        # 레거시 문서 (가짜 데이터)
        legacy_docs = [
            {
                "legacy_id": "LEG001",
                "title": "신규 문서",
                "content": "신규 문서 내용",
                "document_type": "law",
                "updated_at": datetime.now()
            }
        ]

        # 변경 감지
        changes = await service.detect_changes(legacy_docs)

        # 신규 문서 확인
        assert "new" in changes
        assert len(changes["new"]) == 1
        assert changes["new"][0]["legacy_id"] == "LEG001"

    async def test_detect_modified_documents(self, db_session: AsyncSession):
        """수정된 문서 감지 테스트"""
        from app.services.document_sync import DocumentSyncService
        from app.models.document import Document

        service = DocumentSyncService(db_session)

        # 기존 문서 생성
        existing_doc = Document(
            document_id="DOC_MOD_001",
            title="기존 문서",
            content="기존 내용",
            document_type="law",
            status="active",
            legacy_id="LEG_MOD_001",
            legacy_updated_at="2024-01-01 00:00:00"
        )
        db_session.add(existing_doc)
        await db_session.flush()

        # 레거시 문서 (수정된 버전)
        legacy_docs = [
            {
                "legacy_id": "LEG_MOD_001",
                "title": "수정된 문서",
                "content": "수정된 내용",
                "document_type": "law",
                "updated_at": datetime(2024, 12, 1)
            }
        ]

        # 변경 감지
        changes = await service.detect_changes(legacy_docs)

        # 수정된 문서 확인
        assert "modified" in changes
        assert len(changes["modified"]) == 1
        assert changes["modified"][0]["legacy_id"] == "LEG_MOD_001"

    async def test_detect_deleted_documents(self, db_session: AsyncSession):
        """삭제된 문서 감지 테스트"""
        from app.services.document_sync import DocumentSyncService
        from app.models.document import Document

        service = DocumentSyncService(db_session)

        # 기존 문서 생성 (레거시에는 없음)
        existing_doc = Document(
            document_id="DOC_DEL_001",
            title="삭제될 문서",
            content="내용",
            document_type="law",
            status="active",
            legacy_id="LEG_DEL_999",
            legacy_updated_at="2024-01-01 00:00:00"
        )
        db_session.add(existing_doc)
        await db_session.flush()

        # 레거시 문서 (빈 리스트 - 모두 삭제됨)
        legacy_docs = []

        # 변경 감지
        changes = await service.detect_changes(legacy_docs)

        # 삭제된 문서 확인
        assert "deleted" in changes
        assert len(changes["deleted"]) >= 1

    async def test_no_changes(self, db_session: AsyncSession):
        """변경사항 없음 테스트"""
        from app.services.document_sync import DocumentSyncService
        from app.models.document import Document

        service = DocumentSyncService(db_session)

        # 기존 문서 생성
        existing_doc = Document(
            document_id="DOC_NOCHG_001",
            title="동일 문서",
            content="동일 내용",
            document_type="law",
            status="active",
            legacy_id="LEG_NOCHG_001",
            legacy_updated_at="2024-12-01 10:00:00"
        )
        db_session.add(existing_doc)
        await db_session.flush()

        # 레거시 문서 (동일)
        legacy_docs = [
            {
                "legacy_id": "LEG_NOCHG_001",
                "title": "동일 문서",
                "content": "동일 내용",
                "document_type": "law",
                "updated_at": datetime(2024, 12, 1, 10, 0, 0)
            }
        ]

        # 변경 감지
        changes = await service.detect_changes(legacy_docs)

        # 변경사항 없음 확인
        assert len(changes["new"]) == 0
        assert len(changes["modified"]) == 0
        assert len(changes["deleted"]) == 0


@pytest.mark.unit
class TestDocumentComparison:
    """문서 비교 테스트"""

    async def test_compare_documents_content_changed(self):
        """문서 내용 변경 비교 테스트"""
        from app.services.document_sync import DocumentSyncService

        service = DocumentSyncService(None)

        old_doc = {
            "title": "제목",
            "content": "원본 내용"
        }

        new_doc = {
            "title": "제목",
            "content": "수정된 내용"
        }

        # 변경 여부 확인
        is_changed = service.is_document_changed(old_doc, new_doc)
        assert is_changed is True

    async def test_compare_documents_no_change(self):
        """문서 변경 없음 비교 테스트"""
        from app.services.document_sync import DocumentSyncService

        service = DocumentSyncService(None)

        old_doc = {
            "title": "제목",
            "content": "동일 내용"
        }

        new_doc = {
            "title": "제목",
            "content": "동일 내용"
        }

        # 변경 여부 확인
        is_changed = service.is_document_changed(old_doc, new_doc)
        assert is_changed is False
