"""
문서 PII 스캐너
PRD_v2.md P0 요구사항: FUN-003

문서를 스캔하여 개인정보를 검출하고 결과를 저장합니다.
"""
import json
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document import Document
from app.models.pii_detection import PIIDetectionResult, PIIStatus
from app.services.pii_detector import PIIDetector, PIIMatch


class PIIScanner:
    """문서 PII 스캐너"""

    def __init__(self):
        self.detector = PIIDetector()

    async def scan_document(
        self,
        document_id: int,
        db: AsyncSession
    ) -> PIIDetectionResult:
        """
        문서를 스캔하여 PII를 검출합니다.

        Args:
            document_id: 문서 ID
            db: 데이터베이스 세션

        Returns:
            PII 검출 결과
        """
        # 문서 조회
        result = await db.execute(
            select(Document).filter(Document.id == document_id)
        )
        document = result.scalar_one_or_none()
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # PII 검출
        content = document.content or ""
        matches = self.detector.detect(content)

        # 결과 저장
        pii_data = self._serialize_matches(matches)
        detection_result = PIIDetectionResult(
            document_id=document_id,
            has_pii=len(matches) > 0,
            pii_data=pii_data,
            status=PIIStatus.PENDING if matches else PIIStatus.APPROVED
        )

        db.add(detection_result)
        await db.commit()
        await db.refresh(detection_result)

        return detection_result

    async def scan_multiple_documents(
        self,
        document_ids: List[int],
        db: AsyncSession
    ) -> List[PIIDetectionResult]:
        """
        여러 문서를 일괄 스캔합니다.

        Args:
            document_ids: 문서 ID 목록
            db: 데이터베이스 세션

        Returns:
            PII 검출 결과 목록
        """
        results = []
        for doc_id in document_ids:
            try:
                result = await self.scan_document(doc_id, db)
                results.append(result)
            except Exception as e:
                # 개별 문서 스캔 실패는 로깅하고 계속 진행
                print(f"Failed to scan document {doc_id}: {e}")

        return results

    def _serialize_matches(self, matches: List[PIIMatch]) -> str:
        """
        PII 매치를 JSON으로 직렬화합니다.

        Args:
            matches: PII 매치 목록

        Returns:
            JSON 문자열
        """
        data = [
            {
                "type": match.pii_type.value,
                "value": self._mask_for_storage(match.value),
                "start_pos": match.start_pos,
                "end_pos": match.end_pos,
                "confidence": match.confidence
            }
            for match in matches
        ]
        return json.dumps(data, ensure_ascii=False)

    def _mask_for_storage(self, value: str) -> str:
        """
        저장용 마스킹 (부분만 표시)

        Args:
            value: 원본 값

        Returns:
            마스킹된 값
        """
        if len(value) > 4:
            return value[:2] + "*" * (len(value) - 4) + value[-2:]
        else:
            return "***"
