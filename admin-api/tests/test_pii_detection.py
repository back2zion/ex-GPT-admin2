"""
개인정보 검출 (PII Detection) 테스트
PRD_v2.md P0 요구사항: FUN-003
"""
import pytest
from app.services.pii_detector import PIIDetector, PIIType, PIIMatch


class TestPIIDetector:
    """PII 검출기 테스트"""

    @pytest.fixture
    def detector(self):
        """PII 검출기 인스턴스"""
        return PIIDetector()

    def test_detect_resident_number(self, detector):
        """주민등록번호 패턴 감지"""
        # Given: 주민등록번호가 포함된 텍스트
        text = "홍길동의 주민등록번호는 901234-1234567입니다."

        # When: PII 검출 실행
        matches = detector.detect(text)

        # Then: 주민등록번호가 감지됨
        assert len(matches) > 0
        assert any(m.pii_type == PIIType.RESIDENT_NUMBER for m in matches)
        resident_match = next(m for m in matches if m.pii_type == PIIType.RESIDENT_NUMBER)
        assert resident_match.value == "901234-1234567"
        assert resident_match.confidence >= 0.9

    def test_detect_phone_number(self, detector):
        """전화번호 패턴 감지"""
        # Given: 전화번호가 포함된 텍스트
        test_cases = [
            "연락처: 010-1234-5678",
            "전화번호 02-123-4567",
            "휴대폰 01012345678"
        ]

        for text in test_cases:
            # When: PII 검출 실행
            matches = detector.detect(text)

            # Then: 전화번호가 감지됨
            assert len(matches) > 0, f"Failed to detect in: {text}"
            assert any(m.pii_type == PIIType.PHONE_NUMBER for m in matches)

    def test_detect_email(self, detector):
        """이메일 주소 감지"""
        # Given: 이메일이 포함된 텍스트
        text = "문의: hong@example.com"

        # When: PII 검출 실행
        matches = detector.detect(text)

        # Then: 이메일이 감지됨
        assert len(matches) > 0
        assert any(m.pii_type == PIIType.EMAIL for m in matches)
        email_match = next(m for m in matches if m.pii_type == PIIType.EMAIL)
        assert email_match.value == "hong@example.com"

    def test_detect_address(self, detector):
        """주소 정보 감지"""
        # Given: 주소가 포함된 텍스트
        text = "서울특별시 강남구 테헤란로 123"

        # When: PII 검출 실행
        matches = detector.detect(text)

        # Then: 주소가 감지됨
        assert len(matches) > 0
        assert any(m.pii_type == PIIType.ADDRESS for m in matches)

    def test_detect_credit_card(self, detector):
        """신용카드 번호 감지"""
        # Given: 신용카드 번호가 포함된 텍스트
        test_cases = [
            "카드번호: 1234-5678-9012-3456",
            "1234567890123456"
        ]

        for text in test_cases:
            # When: PII 검출 실행
            matches = detector.detect(text)

            # Then: 신용카드 번호가 감지됨
            assert len(matches) > 0, f"Failed to detect in: {text}"
            assert any(m.pii_type == PIIType.CREDIT_CARD for m in matches)

    def test_mask_pii_data(self, detector):
        """개인정보 마스킹 처리"""
        # Given: 개인정보가 포함된 텍스트
        text = "홍길동(010-1234-5678, hong@example.com)"

        # When: 마스킹 처리
        masked_text = detector.mask(text)

        # Then: 개인정보가 마스킹됨
        assert "010-1234-5678" not in masked_text
        assert "hong@example.com" not in masked_text
        assert "***" in masked_text or "****" in masked_text

    def test_no_false_positives(self, detector):
        """False Positive 방지 - 일반 숫자는 감지하지 않음"""
        # Given: 개인정보가 없는 일반 텍스트
        text = "총 금액은 1,234,567원이며, 계좌번호 확인이 필요합니다."

        # When: PII 검출 실행
        matches = detector.detect(text)

        # Then: 개인정보가 감지되지 않음 (또는 신뢰도가 낮음)
        high_confidence_matches = [m for m in matches if m.confidence >= 0.7]
        assert len(high_confidence_matches) == 0


@pytest.mark.asyncio
class TestPIIDocumentScanner:
    """문서 PII 스캔 테스트"""

    async def test_scan_document_for_pii(self, db_session):
        """문서 PII 스캔"""
        from app.services.pii_scanner import PIIScanner
        from app.models.document import Document, DocumentType
        import uuid

        # Given: PII가 포함된 문서
        doc = Document(
            document_id=f"DOC_TEST_PII_{uuid.uuid4().hex[:8]}",
            title="개인정보 포함 문서",
            content="직원: 홍길동, 주민번호: 901234-1234567, 연락처: 010-1234-5678",
            document_type=DocumentType.OTHER,
            status="active"
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)

        scanner = PIIScanner()

        # When: 문서 스캔
        scan_result = await scanner.scan_document(doc.id, db_session)

        # Then: PII가 검출되고 결과가 저장됨
        assert scan_result.has_pii is True
        assert len(scan_result.pii_matches) >= 2  # 주민번호, 전화번호
        assert scan_result.document_id == doc.id

    async def test_admin_approval_workflow(self, db_session, authenticated_client):
        """관리자 승인 워크플로우"""
        from app.models.pii_detection import PIIDetectionResult, PIIStatus
        from app.models.document import Document, DocumentType
        import uuid

        # Given: 문서 먼저 생성
        doc = Document(
            document_id=f"DOC_TEST_APPROVAL_{uuid.uuid4().hex[:8]}",
            title="승인 테스트 문서",
            content="테스트 내용",
            document_type=DocumentType.OTHER,
            status="active"
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)

        # Given: PII가 검출된 문서
        detection = PIIDetectionResult(
            document_id=doc.id,
            has_pii=True,
            pii_data='[{"type": "RESIDENT_NUMBER", "value": "901234-*******", "start_pos": 10, "end_pos": 24, "confidence": 1.0}]',
            status=PIIStatus.PENDING
        )
        db_session.add(detection)
        await db_session.commit()
        await db_session.refresh(detection)

        # When: 관리자가 승인 처리
        response = await authenticated_client.post(
            f"/api/v1/admin/pii-detections/{detection.id}/approve",
            json={"action": "mask"}
        )

        # Then: 마스킹 처리됨
        assert response.status_code == 200
        await db_session.refresh(detection)
        assert detection.status == PIIStatus.MASKED
