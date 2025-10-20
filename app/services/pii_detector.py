"""
개인정보 검출기 (PII Detector)
PRD_v2.md P0 요구사항: FUN-003

주민등록번호, 전화번호, 이메일, 주소, 신용카드 번호 등을 자동으로 검출합니다.
"""
import re
from dataclasses import dataclass
from enum import Enum
from typing import List


class PIIType(str, Enum):
    """개인정보 유형"""
    RESIDENT_NUMBER = "resident_number"  # 주민등록번호
    PHONE_NUMBER = "phone_number"  # 전화번호
    EMAIL = "email"  # 이메일
    ADDRESS = "address"  # 주소
    CREDIT_CARD = "credit_card"  # 신용카드


@dataclass
class PIIMatch:
    """PII 검출 결과"""
    pii_type: PIIType
    value: str
    start_pos: int
    end_pos: int
    confidence: float  # 0.0 ~ 1.0


class PIIDetector:
    """개인정보 검출기"""

    # 정규표현식 패턴
    PATTERNS = {
        PIIType.RESIDENT_NUMBER: [
            # 주민등록번호: 901234-1234567 형식
            (r'\d{6}[-\s]?\d{7}', 1.0),
        ],
        PIIType.PHONE_NUMBER: [
            # 휴대폰: 010-1234-5678, 01012345678
            (r'01[016789][-\s]?\d{3,4}[-\s]?\d{4}', 0.95),
            # 일반 전화: 02-123-4567
            (r'0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}', 0.9),
        ],
        PIIType.EMAIL: [
            # 이메일: user@example.com
            (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 0.95),
        ],
        PIIType.ADDRESS: [
            # 주소: 서울특별시, 경기도 등
            (r'(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)[특별광역]?(시|도)\s+\S+\s+\S+', 0.85),
        ],
        PIIType.CREDIT_CARD: [
            # 신용카드: 1234-5678-9012-3456, 1234567890123456
            (r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}', 0.8),
        ],
    }

    def detect(self, text: str) -> List[PIIMatch]:
        """
        텍스트에서 개인정보를 검출합니다.

        Args:
            text: 검사할 텍스트

        Returns:
            검출된 PII 목록
        """
        matches = []

        for pii_type, patterns in self.PATTERNS.items():
            for pattern, confidence in patterns:
                for match in re.finditer(pattern, text):
                    # False Positive 필터링
                    if self._is_valid_match(pii_type, match.group()):
                        matches.append(PIIMatch(
                            pii_type=pii_type,
                            value=match.group(),
                            start_pos=match.start(),
                            end_pos=match.end(),
                            confidence=confidence
                        ))

        return matches

    def _is_valid_match(self, pii_type: PIIType, value: str) -> bool:
        """
        False Positive를 필터링합니다.

        Args:
            pii_type: PII 유형
            value: 검출된 값

        Returns:
            유효한 매치인지 여부
        """
        # 주민등록번호 검증
        if pii_type == PIIType.RESIDENT_NUMBER:
            # 하이픈 제거
            digits = re.sub(r'[-\s]', '', value)
            if len(digits) != 13:
                return False
            # 앞 6자리는 생년월일 (간단한 검증)
            month = int(digits[2:4])
            day = int(digits[4:6])
            if not (1 <= month <= 12 and 1 <= day <= 31):
                return False

        # 전화번호 검증
        elif pii_type == PIIType.PHONE_NUMBER:
            digits = re.sub(r'[-\s]', '', value)
            # 전화번호는 최소 9자리, 최대 11자리
            if not (9 <= len(digits) <= 11):
                return False
            # 1234567890 같은 연속된 숫자는 제외
            if digits == ''.join(str(i % 10) for i in range(len(digits))):
                return False

        # 신용카드 검증 (Luhn 알고리즘은 생략, 단순 길이 검증)
        elif pii_type == PIIType.CREDIT_CARD:
            digits = re.sub(r'[-\s]', '', value)
            if len(digits) != 16:
                return False

        return True

    def mask(self, text: str) -> str:
        """
        텍스트에서 개인정보를 마스킹합니다.

        Args:
            text: 원본 텍스트

        Returns:
            마스킹된 텍스트
        """
        masked_text = text
        matches = self.detect(text)

        # 뒤에서부터 마스킹 (인덱스 유지)
        for match in sorted(matches, key=lambda x: x.start_pos, reverse=True):
            masked_value = self._mask_value(match.pii_type, match.value)
            masked_text = (
                masked_text[:match.start_pos] +
                masked_value +
                masked_text[match.end_pos:]
            )

        return masked_text

    def _mask_value(self, pii_type: PIIType, value: str) -> str:
        """
        개인정보 유형에 따라 마스킹합니다.

        Args:
            pii_type: PII 유형
            value: 원본 값

        Returns:
            마스킹된 값
        """
        if pii_type == PIIType.RESIDENT_NUMBER:
            # 주민번호: 901234-******* (뒤 7자리 마스킹)
            return value[:7] + "*******"

        elif pii_type == PIIType.PHONE_NUMBER:
            # 전화번호: 010-****-5678 (중간 마스킹)
            digits = re.sub(r'[-\s]', '', value)
            if len(digits) == 11:
                return f"{digits[:3]}-****-{digits[7:]}"
            elif len(digits) == 10:
                return f"{digits[:3]}-***-{digits[6:]}"
            else:
                return "***-****-****"

        elif pii_type == PIIType.EMAIL:
            # 이메일: u***@example.com (사용자명 일부 마스킹)
            parts = value.split('@')
            if len(parts) == 2:
                username = parts[0]
                if len(username) > 2:
                    masked_username = username[0] + "***"
                else:
                    masked_username = "***"
                return f"{masked_username}@{parts[1]}"

        elif pii_type == PIIType.CREDIT_CARD:
            # 카드번호: 1234-****-****-3456 (중간 8자리 마스킹)
            digits = re.sub(r'[-\s]', '', value)
            return f"{digits[:4]}-****-****-{digits[12:]}"

        # 기본: 전체 마스킹
        return "***"
