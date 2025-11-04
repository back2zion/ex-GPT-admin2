"""
Test cases for Quality Validation Service
TDD: Red-Green-Refactor 방식으로 작성

시큐어 코딩 테스트:
- PII 검출 (email, phone, SSN, etc.)
- 민감 정보 보호

유지보수 용이성 테스트:
- 의존성 주입
- 단일 책임 원칙
- 명확한 에러 처리
"""
import pytest
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock

from app.services.training.quality_validation_service import (
    QualityValidationService,
    PIIDetectionResult,
    DuplicateCheckResult,
    FormatCheckResult
)


class TestPIIDetection:
    """PII 검출 테스트 (시큐어 코딩)"""

    @pytest.fixture
    def quality_service(self):
        """QualityValidationService 인스턴스"""
        return QualityValidationService()

    def test_detect_email_pii(self, quality_service):
        """정상: 이메일 주소 PII 검출"""
        samples = [
            {"instruction": "Contact john.doe@example.com for info", "output": "OK"},
            {"instruction": "Email: admin@company.com", "output": "Done"}
        ]

        result = quality_service.check_pii(samples)

        assert isinstance(result, PIIDetectionResult)
        assert result.passed is False  # PII found
        assert result.pii_count > 0
        assert len(result.pii_locations) == 2
        assert "email" in str(result.pii_types).lower()

    def test_detect_phone_number_pii(self, quality_service):
        """정상: 전화번호 PII 검출"""
        samples = [
            {"instruction": "Call 010-1234-5678", "output": "OK"},
            {"instruction": "Phone: +82-10-9876-5432", "output": "Done"}
        ]

        result = quality_service.check_pii(samples)

        assert result.passed is False
        assert result.pii_count > 0
        assert "phone" in str(result.pii_types).lower()

    def test_detect_ssn_pii(self, quality_service):
        """정상: 주민등록번호 PII 검출"""
        samples = [
            {"instruction": "SSN: 123456-1234567", "output": "OK"},
            {"instruction": "Check 901231-2345678", "output": "Done"}
        ]

        result = quality_service.check_pii(samples)

        assert result.passed is False
        assert result.pii_count > 0
        assert "ssn" in str(result.pii_types).lower() or "korean" in str(result.pii_types).lower()

    def test_detect_credit_card_pii(self, quality_service):
        """정상: 신용카드 번호 PII 검출"""
        samples = [
            {"instruction": "Card: 4532-1234-5678-9010", "output": "OK"},
            {"instruction": "Pay with 5425233430109903", "output": "Done"}
        ]

        result = quality_service.check_pii(samples)

        assert result.passed is False
        assert result.pii_count > 0

    def test_no_pii_detected(self, quality_service):
        """정상: PII 없는 데이터"""
        samples = [
            {"instruction": "What is Python?", "output": "A programming language"},
            {"instruction": "Explain AI", "output": "Artificial Intelligence"}
        ]

        result = quality_service.check_pii(samples)

        assert result.passed is True
        assert result.pii_count == 0
        assert len(result.pii_locations) == 0

    def test_pii_detection_with_empty_samples(self, quality_service):
        """정상: 빈 샘플 처리"""
        samples = []

        result = quality_service.check_pii(samples)

        assert result.passed is True
        assert result.pii_count == 0


class TestDuplicateDetection:
    """중복 검출 테스트"""

    @pytest.fixture
    def quality_service(self):
        return QualityValidationService()

    def test_detect_exact_duplicates(self, quality_service):
        """정상: 완전히 동일한 중복 검출"""
        samples = [
            {"instruction": "What is AI?", "output": "Artificial Intelligence"},
            {"instruction": "What is AI?", "output": "Artificial Intelligence"},
            {"instruction": "What is ML?", "output": "Machine Learning"}
        ]

        result = quality_service.check_duplicates(samples)

        assert isinstance(result, DuplicateCheckResult)
        assert result.passed is False
        assert result.duplicate_count > 0
        assert len(result.duplicate_pairs) > 0

    def test_detect_similar_duplicates(self, quality_service):
        """정상: 유사한 중복 검출 (80% 이상 유사도)"""
        samples = [
            {"instruction": "What is artificial intelligence?", "output": "AI"},
            {"instruction": "What is artificial intelligence", "output": "AI"},  # Similar
            {"instruction": "Completely different question", "output": "Different"}
        ]

        result = quality_service.check_duplicates(samples, similarity_threshold=0.9)

        assert result.passed is False
        assert result.duplicate_count > 0

    def test_no_duplicates_found(self, quality_service):
        """정상: 중복 없는 데이터"""
        samples = [
            {"instruction": "What is Python?", "output": "A programming language"},
            {"instruction": "What is Java?", "output": "Another language"},
            {"instruction": "What is JavaScript?", "output": "Web language"}
        ]

        result = quality_service.check_duplicates(samples)

        assert result.passed is True
        assert result.duplicate_count == 0
        assert len(result.duplicate_pairs) == 0

    def test_duplicate_detection_with_single_sample(self, quality_service):
        """정상: 단일 샘플 (중복 불가능)"""
        samples = [
            {"instruction": "What is AI?", "output": "Artificial Intelligence"}
        ]

        result = quality_service.check_duplicates(samples)

        assert result.passed is True
        assert result.duplicate_count == 0


class TestFormatValidation:
    """포맷 검증 테스트"""

    @pytest.fixture
    def quality_service(self):
        return QualityValidationService()

    def test_valid_instruction_output_format(self, quality_service):
        """정상: 올바른 instruction-output 형식"""
        samples = [
            {"instruction": "What is AI?", "output": "Artificial Intelligence"},
            {"instruction": "Explain ML", "output": "Machine Learning"}
        ]

        result = quality_service.check_format(samples, required_fields=["instruction", "output"])

        assert isinstance(result, FormatCheckResult)
        assert result.passed is True
        assert result.invalid_count == 0

    def test_missing_required_fields(self, quality_service):
        """실패: 필수 필드 누락"""
        samples = [
            {"instruction": "What is AI?"},  # Missing output
            {"output": "Machine Learning"},  # Missing instruction
            {"instruction": "Valid", "output": "Valid"}
        ]

        result = quality_service.check_format(samples, required_fields=["instruction", "output"])

        assert result.passed is False
        assert result.invalid_count == 2
        assert len(result.invalid_samples) == 2

    def test_empty_field_values(self, quality_service):
        """실패: 빈 값 검출"""
        samples = [
            {"instruction": "", "output": "Valid"},
            {"instruction": "Valid", "output": ""},
            {"instruction": "Valid", "output": "Valid"}
        ]

        result = quality_service.check_format(samples, required_fields=["instruction", "output"])

        assert result.passed is False
        assert result.invalid_count == 2

    def test_field_type_validation(self, quality_service):
        """실패: 필드 타입 검증 (문자열이어야 함)"""
        samples = [
            {"instruction": 123, "output": "Valid"},  # Wrong type
            {"instruction": "Valid", "output": ["list"]},  # Wrong type
            {"instruction": "Valid", "output": "Valid"}
        ]

        result = quality_service.check_format(samples, required_fields=["instruction", "output"])

        assert result.passed is False
        assert result.invalid_count == 2

    def test_flexible_field_names(self, quality_service):
        """정상: 다양한 필드명 지원 (prompt/response 등)"""
        samples = [
            {"prompt": "What is AI?", "response": "Artificial Intelligence"},
            {"question": "What is ML?", "answer": "Machine Learning"}
        ]

        # Should accept alternative field names
        result = quality_service.check_format(
            samples,
            required_fields=["input", "output"],
            field_aliases={
                "input": ["instruction", "prompt", "question"],
                "output": ["output", "response", "answer"]
            }
        )

        assert result.passed is True
        assert result.invalid_count == 0


class TestQualityScoreCalculation:
    """품질 점수 계산 테스트"""

    @pytest.fixture
    def quality_service(self):
        return QualityValidationService()

    def test_perfect_quality_score(self, quality_service):
        """정상: 완벽한 데이터셋 (1.0 점수)"""
        samples = [
            {"instruction": "What is Python?", "output": "A programming language"},
            {"instruction": "What is Java?", "output": "Another language"}
        ]

        score = quality_service.calculate_quality_score(samples)

        assert score == 1.0

    def test_quality_score_with_issues(self, quality_service):
        """정상: 문제가 있는 데이터셋 (점수 감소)"""
        samples = [
            {"instruction": "Contact me@email.com", "output": "OK"},  # PII
            {"instruction": "What is AI?", "output": "AI"},
            {"instruction": "What is AI?", "output": "AI"}  # Duplicate
        ]

        score = quality_service.calculate_quality_score(samples)

        assert 0.0 <= score < 1.0

    def test_quality_score_weights(self, quality_service):
        """정상: 가중치 적용된 점수 계산"""
        samples = [
            {"instruction": "Test", "output": ""}  # Format issue
        ]

        # Format issues should have higher weight
        score = quality_service.calculate_quality_score(
            samples,
            weights={"format": 0.5, "pii": 0.3, "duplicates": 0.2}
        )

        assert 0.0 <= score < 1.0


class TestQualityValidationIntegration:
    """통합 테스트 (전체 검증 프로세스)"""

    @pytest.fixture
    def quality_service(self):
        return QualityValidationService()

    @pytest.mark.asyncio
    async def test_full_validation_process(self, quality_service):
        """정상: 전체 검증 프로세스"""
        samples = [
            {"instruction": "What is Python?", "output": "A programming language"},
            {"instruction": "What is Java?", "output": "Another language"},
            {"instruction": "What is JavaScript?", "output": "Web language"}
        ]

        # Run all checks
        pii_result = quality_service.check_pii(samples)
        dup_result = quality_service.check_duplicates(samples)
        fmt_result = quality_service.check_format(samples, required_fields=["instruction", "output"])
        quality_score = quality_service.calculate_quality_score(samples)

        # All checks should pass
        assert pii_result.passed is True
        assert dup_result.passed is True
        assert fmt_result.passed is True
        assert quality_score == 1.0

    @pytest.mark.asyncio
    async def test_validation_with_multiple_issues(self, quality_service):
        """정상: 여러 문제가 있는 데이터셋"""
        samples = [
            {"instruction": "Contact john@email.com", "output": "OK"},  # PII
            {"instruction": "What is AI?", "output": "AI"},
            {"instruction": "What is AI?", "output": "AI"},  # Duplicate
            {"instruction": "Missing output field"}  # Format issue
        ]

        pii_result = quality_service.check_pii(samples)
        dup_result = quality_service.check_duplicates(samples)
        fmt_result = quality_service.check_format(samples, required_fields=["instruction", "output"])
        quality_score = quality_service.calculate_quality_score(samples)

        # Multiple checks should fail
        assert pii_result.passed is False
        assert dup_result.passed is False
        assert fmt_result.passed is False
        assert quality_score < 1.0
