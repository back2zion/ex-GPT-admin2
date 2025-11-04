"""
Document Synchronization Service
문서 동기화 서비스
"""
from typing import List, Dict
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.models.document import Document

logger = logging.getLogger(__name__)


class DocumentSyncService:
    """문서 동기화 및 변경 감지 서비스"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def detect_changes(self, legacy_docs: List[Dict]) -> Dict[str, List]:
        """
        레거시 문서와 현재 문서 비교하여 변경사항 감지

        Args:
            legacy_docs: 레거시 DB에서 조회한 문서 목록

        Returns:
            {
                "new": [...],      # 신규 문서 (레거시에 있지만 현재 DB에 없음)
                "modified": [...], # 수정된 문서 (양쪽에 있지만 내용이 다름)
                "deleted": [...]   # 삭제된 문서 (현재 DB에 있지만 레거시에 없음)
            }
        """
        changes = {
            "new": [],
            "modified": [],
            "deleted": []
        }

        # 레거시 문서를 legacy_id로 인덱싱
        legacy_dict = {doc["legacy_id"]: doc for doc in legacy_docs}

        # 현재 DB의 모든 문서 조회 (legacy_id가 있는 것만)
        stmt = select(Document).where(Document.legacy_id.isnot(None))
        result = await self.db_session.execute(stmt)
        current_docs = result.scalars().all()

        # 현재 문서를 legacy_id로 인덱싱
        current_dict = {doc.legacy_id: doc for doc in current_docs}

        # 1. 신규 문서 감지 (레거시에는 있지만 현재 DB에 없음)
        for legacy_id, legacy_doc in legacy_dict.items():
            if legacy_id not in current_dict:
                changes["new"].append(legacy_doc)

        # 2. 수정된 문서 감지 (양쪽에 있지만 내용이 다름)
        for legacy_id, legacy_doc in legacy_dict.items():
            if legacy_id in current_dict:
                current_doc = current_dict[legacy_id]

                # 문서를 딕셔너리로 변환하여 비교
                current_doc_dict = {
                    "title": current_doc.title,
                    "content": current_doc.content,
                    "document_type": current_doc.document_type
                }

                legacy_doc_dict = {
                    "title": legacy_doc["title"],
                    "content": legacy_doc["content"],
                    "document_type": legacy_doc["document_type"]
                }

                # updated_at 시간 비교 (레거시가 더 최신인 경우)
                legacy_updated = legacy_doc["updated_at"]
                current_updated = self._parse_datetime(current_doc.legacy_updated_at)

                if current_updated and legacy_updated > current_updated:
                    changes["modified"].append(legacy_doc)
                elif not current_updated and self.is_document_changed(current_doc_dict, legacy_doc_dict):
                    changes["modified"].append(legacy_doc)

        # 3. 삭제된 문서 감지 (현재 DB에는 있지만 레거시에 없음)
        for legacy_id, current_doc in current_dict.items():
            if legacy_id not in legacy_dict:
                changes["deleted"].append({
                    "legacy_id": legacy_id,
                    "document_id": current_doc.document_id,
                    "title": current_doc.title
                })

        return changes

    def is_document_changed(self, old_doc: Dict, new_doc: Dict) -> bool:
        """
        문서 변경 여부 확인

        Args:
            old_doc: 기존 문서 (딕셔너리)
            new_doc: 새 문서 (딕셔너리)

        Returns:
            bool: 변경되었으면 True, 동일하면 False
        """
        # 주요 필드 비교 (title, content)
        comparable_fields = ["title", "content"]

        for field in comparable_fields:
            old_value = old_doc.get(field, "")
            new_value = new_doc.get(field, "")

            if old_value != new_value:
                return True

        return False

    def _parse_datetime(self, dt_str: str) -> datetime:
        """
        문자열을 datetime으로 파싱

        Args:
            dt_str: datetime 문자열

        Returns:
            datetime 객체 또는 None
        """
        if not dt_str:
            return None

        try:
            # "2024-01-01 00:00:00" 형식 파싱
            return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.warning(f"Failed to parse datetime: {dt_str}, error: {e}")
            return None
