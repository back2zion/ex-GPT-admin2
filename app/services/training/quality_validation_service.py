"""
Quality Validation Service for Training Datasets
데이터셋 품질 검증을 담당하는 서비스

시큐어 코딩 적용:
- PII(개인정보) 검출
- 민감 정보 보호
- 데이터 품질 보장

유지보수 용이성:
- 단일 책임 원칙 (SRP)
- 명확한 결과 타입
- 확장 가능한 검증 규칙
"""
import re
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Result Data Classes
# ============================================================================

@dataclass
class PIIDetectionResult:
    """PII 검출 결과"""
    passed: bool
    pii_count: int
    pii_locations: List[Dict[str, Any]]
    pii_types: Set[str]
    message: str


@dataclass
class DuplicateCheckResult:
    """중복 검사 결과"""
    passed: bool
    duplicate_count: int
    duplicate_pairs: List[tuple]
    message: str


@dataclass
class FormatCheckResult:
    """포맷 검증 결과"""
    passed: bool
    invalid_count: int
    invalid_samples: List[Dict[str, Any]]
    message: str


# ============================================================================
# PII Detection Patterns (시큐어 코딩)
# ============================================================================

# 이메일 주소 패턴
EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
)

# 전화번호 패턴 (한국, 국제)
PHONE_PATTERNS = [
    re.compile(r'\b0\d{1,2}-\d{3,4}-\d{4}\b'),  # 02-1234-5678
    re.compile(r'\b01\d-\d{3,4}-\d{4}\b'),  # 010-1234-5678
    re.compile(r'\+82-\d{1,2}-\d{3,4}-\d{4}\b'),  # +82-10-1234-5678
    re.compile(r'\b\d{3}-\d{3}-\d{4}\b'),  # 123-456-7890
]

# 주민등록번호 패턴 (한국)
SSN_PATTERN = re.compile(
    r'\b\d{6}-\d{7}\b'
)

# 신용카드 번호 패턴 (4자리씩 구분 또는 연속)
CREDIT_CARD_PATTERNS = [
    re.compile(r'\b\d{4}-\d{4}-\d{4}-\d{4}\b'),
    re.compile(r'\b\d{13,16}\b')
]


class QualityValidationService:
    """
    데이터셋 품질 검증 서비스

    책임:
    - PII 검출 (개인정보 보호)
    - 중복 샘플 검출
    - 포맷 검증
    - 품질 점수 계산
    """

    def __init__(self):
        """생성자"""
        pass

    def check_pii(self, samples: List[Dict[str, Any]]) -> PIIDetectionResult:
        """
        PII 검출 (시큐어 코딩: 개인정보 보호)

        검출 항목:
        - 이메일 주소
        - 전화번호 (한국, 국제)
        - 주민등록번호
        - 신용카드 번호

        Args:
            samples: 데이터셋 샘플 리스트

        Returns:
            PIIDetectionResult
        """
        if not samples:
            return PIIDetectionResult(
                passed=True,
                pii_count=0,
                pii_locations=[],
                pii_types=set(),
                message="PII 검사 통과 (샘플 없음)"
            )

        pii_locations = []
        pii_types = set()

        for idx, sample in enumerate(samples):
            # 모든 필드의 텍스트 검사
            text_fields = self._extract_text_fields(sample)

            for field_name, text in text_fields.items():
                if not isinstance(text, str):
                    continue

                # 이메일 검출
                emails = EMAIL_PATTERN.findall(text)
                if emails:
                    pii_types.add("email")
                    for email in emails:
                        pii_locations.append({
                            "sample_index": idx,
                            "field": field_name,
                            "type": "email",
                            "value": self._mask_pii(email)
                        })

                # 전화번호 검출
                for pattern in PHONE_PATTERNS:
                    phones = pattern.findall(text)
                    if phones:
                        pii_types.add("phone")
                        for phone in phones:
                            pii_locations.append({
                                "sample_index": idx,
                                "field": field_name,
                                "type": "phone",
                                "value": self._mask_pii(phone)
                            })

                # 주민등록번호 검출
                ssns = SSN_PATTERN.findall(text)
                if ssns:
                    pii_types.add("korean_ssn")
                    for ssn in ssns:
                        pii_locations.append({
                            "sample_index": idx,
                            "field": field_name,
                            "type": "korean_ssn",
                            "value": self._mask_pii(ssn)
                        })

                # 신용카드 번호 검출
                for pattern in CREDIT_CARD_PATTERNS:
                    cards = pattern.findall(text)
                    if cards:
                        # Luhn 알고리즘으로 검증
                        valid_cards = [c for c in cards if self._is_valid_credit_card(c)]
                        if valid_cards:
                            pii_types.add("credit_card")
                            for card in valid_cards:
                                pii_locations.append({
                                    "sample_index": idx,
                                    "field": field_name,
                                    "type": "credit_card",
                                    "value": self._mask_pii(card)
                                })

        pii_count = len(pii_locations)
        passed = pii_count == 0

        message = (
            f"PII 검사 통과 (PII 없음)"
            if passed
            else f"PII 검출: {pii_count}개 발견 (타입: {', '.join(pii_types)})"
        )

        return PIIDetectionResult(
            passed=passed,
            pii_count=pii_count,
            pii_locations=pii_locations,
            pii_types=pii_types,
            message=message
        )

    def check_duplicates(
        self,
        samples: List[Dict[str, Any]],
        similarity_threshold: float = 0.95
    ) -> DuplicateCheckResult:
        """
        중복 샘플 검출

        Args:
            samples: 데이터셋 샘플 리스트
            similarity_threshold: 유사도 임계값 (0.0 ~ 1.0)

        Returns:
            DuplicateCheckResult
        """
        if len(samples) <= 1:
            return DuplicateCheckResult(
                passed=True,
                duplicate_count=0,
                duplicate_pairs=[],
                message="중복 검사 통과 (샘플 1개 이하)"
            )

        duplicate_pairs = []

        # 완전 중복 및 유사 중복 검출
        for i in range(len(samples)):
            for j in range(i + 1, len(samples)):
                similarity = self._calculate_similarity(samples[i], samples[j])

                if similarity >= similarity_threshold:
                    duplicate_pairs.append((i, j, similarity))

        duplicate_count = len(duplicate_pairs)
        passed = duplicate_count == 0

        message = (
            "중복 검사 통과 (중복 없음)"
            if passed
            else f"중복 발견: {duplicate_count}쌍 (임계값: {similarity_threshold})"
        )

        return DuplicateCheckResult(
            passed=passed,
            duplicate_count=duplicate_count,
            duplicate_pairs=duplicate_pairs,
            message=message
        )

    def check_format(
        self,
        samples: List[Dict[str, Any]],
        required_fields: List[str],
        field_aliases: Optional[Dict[str, List[str]]] = None
    ) -> FormatCheckResult:
        """
        포맷 검증

        검증 항목:
        - 필수 필드 존재 여부
        - 필드 값이 비어있지 않은지
        - 필드 타입이 문자열인지

        Args:
            samples: 데이터셋 샘플 리스트
            required_fields: 필수 필드 리스트
            field_aliases: 필드 별칭 (유연한 필드명 지원)

        Returns:
            FormatCheckResult
        """
        if not samples:
            return FormatCheckResult(
                passed=True,
                invalid_count=0,
                invalid_samples=[],
                message="포맷 검사 통과 (샘플 없음)"
            )

        invalid_samples = []

        for idx, sample in enumerate(samples):
            issues = []

            for field in required_fields:
                # 필드 별칭 지원
                actual_field = self._find_field(sample, field, field_aliases)

                if actual_field is None:
                    issues.append(f"필수 필드 '{field}' 누락")
                    continue

                value = sample[actual_field]

                # 빈 값 검사
                if not value or (isinstance(value, str) and not value.strip()):
                    issues.append(f"필드 '{actual_field}'가 비어있음")

                # 타입 검사 (문자열이어야 함)
                if not isinstance(value, str):
                    issues.append(f"필드 '{actual_field}' 타입 오류 (문자열 필요, {type(value).__name__} 발견)")

            if issues:
                invalid_samples.append({
                    "sample_index": idx,
                    "sample": sample,
                    "issues": issues
                })

        invalid_count = len(invalid_samples)
        passed = invalid_count == 0

        message = (
            "포맷 검사 통과"
            if passed
            else f"포맷 오류: {invalid_count}개 샘플"
        )

        return FormatCheckResult(
            passed=passed,
            invalid_count=invalid_count,
            invalid_samples=invalid_samples,
            message=message
        )

    def calculate_quality_score(
        self,
        samples: List[Dict[str, Any]],
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        데이터셋 품질 점수 계산

        Args:
            samples: 데이터셋 샘플 리스트
            weights: 검증 항목별 가중치 (format, pii, duplicates)

        Returns:
            품질 점수 (0.0 ~ 1.0)
        """
        if not samples:
            return 1.0

        # 기본 가중치
        if weights is None:
            weights = {
                "format": 0.4,
                "pii": 0.4,
                "duplicates": 0.2
            }

        # 각 검증 항목 실행
        pii_result = self.check_pii(samples)
        dup_result = self.check_duplicates(samples)
        fmt_result = self.check_format(samples, required_fields=["instruction", "output"])

        # 각 항목별 점수 계산 (0.0 ~ 1.0)
        pii_score = 1.0 if pii_result.passed else max(0.0, 1.0 - (pii_result.pii_count / len(samples)))
        dup_score = 1.0 if dup_result.passed else max(0.0, 1.0 - (dup_result.duplicate_count / len(samples)))
        fmt_score = 1.0 if fmt_result.passed else max(0.0, 1.0 - (fmt_result.invalid_count / len(samples)))

        # 가중 평균
        quality_score = (
            pii_score * weights.get("pii", 0.4) +
            dup_score * weights.get("duplicates", 0.2) +
            fmt_score * weights.get("format", 0.4)
        )

        return round(quality_score, 2)

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _extract_text_fields(self, sample: Dict[str, Any]) -> Dict[str, str]:
        """샘플에서 텍스트 필드 추출"""
        text_fields = {}

        for key, value in sample.items():
            if isinstance(value, str):
                text_fields[key] = value

        return text_fields

    def _mask_pii(self, pii_value: str) -> str:
        """PII 값 마스킹 (보안)"""
        if len(pii_value) <= 4:
            return "*" * len(pii_value)

        # 앞 2자, 뒤 2자만 보여주고 나머지는 마스킹
        visible_chars = 2
        masked_length = len(pii_value) - (visible_chars * 2)

        return (
            pii_value[:visible_chars] +
            "*" * masked_length +
            pii_value[-visible_chars:]
        )

    def _is_valid_credit_card(self, card_number: str) -> bool:
        """
        Luhn 알고리즘으로 신용카드 번호 검증

        Args:
            card_number: 신용카드 번호 (숫자만)

        Returns:
            유효 여부
        """
        # 하이픈 제거
        card_number = card_number.replace("-", "")

        # 숫자만 있는지 확인
        if not card_number.isdigit():
            return False

        # 길이 확인 (13~16자리)
        if not (13 <= len(card_number) <= 16):
            return False

        # Luhn 알고리즘
        digits = [int(d) for d in card_number]
        checksum = 0

        # 뒤에서부터 두 번째 자리부터 시작하여 매 두 번째 자리를 2배
        for i in range(len(digits) - 2, -1, -2):
            digits[i] *= 2
            if digits[i] > 9:
                digits[i] -= 9

        checksum = sum(digits)

        return checksum % 10 == 0

    def _calculate_similarity(self, sample1: Dict[str, Any], sample2: Dict[str, Any]) -> float:
        """
        두 샘플 간의 유사도 계산

        Args:
            sample1: 첫 번째 샘플
            sample2: 두 번째 샘플

        Returns:
            유사도 (0.0 ~ 1.0)
        """
        # 텍스트 필드 추출
        text1 = " ".join(str(v) for v in sample1.values() if isinstance(v, str))
        text2 = " ".join(str(v) for v in sample2.values() if isinstance(v, str))

        # 완전 일치
        if text1 == text2:
            return 1.0

        # 텍스트 정규화 (구두점 제거)
        text1_normalized = re.sub(r'[^\w\s]', '', text1.lower())
        text2_normalized = re.sub(r'[^\w\s]', '', text2.lower())

        # 간단한 토큰 기반 유사도 (Jaccard Similarity)
        tokens1 = set(text1_normalized.split())
        tokens2 = set(text2_normalized.split())

        if not tokens1 and not tokens2:
            return 1.0

        if not tokens1 or not tokens2:
            return 0.0

        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)

        return intersection / union if union > 0 else 0.0

    def _find_field(
        self,
        sample: Dict[str, Any],
        field: str,
        field_aliases: Optional[Dict[str, List[str]]] = None
    ) -> Optional[str]:
        """
        필드 또는 별칭 찾기

        Args:
            sample: 샘플
            field: 필드명
            field_aliases: 필드 별칭

        Returns:
            실제 필드명 또는 None
        """
        # 직접 존재하는 경우
        if field in sample:
            return field

        # 별칭 확인
        if field_aliases and field in field_aliases:
            for alias in field_aliases[field]:
                if alias in sample:
                    return alias

        return None
