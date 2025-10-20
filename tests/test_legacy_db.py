"""
Test Legacy Database Connection and Synchronization
TDD: Write tests first, then implement
"""
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.unit
class TestLegacyDBConnection:
    """레거시 DB 연결 테스트"""

    async def test_legacy_db_connection_success(self):
        """레거시 DB 연결 성공 테스트 (postgres 컨테이너 사용)"""
        from app.services.legacy_db import LegacyDBService

        service = LegacyDBService(
            host="postgres",  # Docker 컨테이너 이름
            port=5432,
            database="admin_db",  # 기존 DB 사용
            user="postgres",
            password="password"
        )

        # 연결 테스트
        is_connected = await service.test_connection()
        assert is_connected is True

    async def test_legacy_db_connection_failure(self):
        """레거시 DB 연결 실패 테스트"""
        from app.services.legacy_db import LegacyDBService

        service = LegacyDBService(
            host="invalid_host",
            port=5432,
            database="legacy_db",
            user="postgres",
            password="wrong_password"
        )

        # 연결 실패 확인
        is_connected = await service.test_connection()
        assert is_connected is False

    async def test_fetch_documents_from_legacy(self):
        """레거시 DB에서 문서 목록 조회 테스트"""
        from app.services.legacy_db import LegacyDBService

        service = LegacyDBService(
            host="postgres",
            port=5432,
            database="admin_db",
            user="postgres",
            password="password"
        )

        # 문서 조회 (빈 리스트 또는 문서 목록)
        documents = await service.fetch_documents()

        # 결과 검증
        assert isinstance(documents, list)
        # documents 테이블이 없어도 빈 리스트가 반환되어야 함
        if documents:
            doc = documents[0]
            assert "legacy_id" in doc
            assert "title" in doc
            assert "content" in doc
            assert "updated_at" in doc

        await service.close()

    async def test_fetch_document_by_id(self):
        """레거시 DB에서 특정 문서 조회 테스트"""
        from app.services.legacy_db import LegacyDBService

        service = LegacyDBService(
            host="postgres",
            port=5432,
            database="admin_db",
            user="postgres",
            password="password"
        )

        # 특정 문서 조회 (없을 경우 None)
        document = await service.fetch_document_by_id("LEG001")

        # 결과 검증 - None이거나 문서 객체
        assert document is None or isinstance(document, dict)
        if document:
            assert document["legacy_id"] == "LEG001"
            assert "title" in document
            assert "content" in document

        await service.close()
