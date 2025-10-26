"""
대화 제목 자동 생성 유틸리티

규칙 기반 즉시 생성 방식으로 LLM 호출 없이 밀리초 단위 처리
"""
import re
from typing import Tuple


def generate_conversation_title(
    user_question: str,
    max_length: int = 50,
    min_length: int = 20
) -> Tuple[str, bool]:
    """
    사용자 질문으로부터 대화 제목 자동 생성

    Args:
        user_question: 사용자의 첫 질문
        max_length: 최대 제목 길이 (기본 50자)
        min_length: 의미 단위 보존을 위한 최소 길이 (기본 20자)

    Returns:
        Tuple[str, bool]: (생성된 제목, 잘림 여부)

    Examples:
        >>> generate_conversation_title("회계규정에 대해 알려줘")
        ("회계규정에 대해 알려줘", False)

        >>> generate_conversation_title("한국도로공사의 2024년 회계규정 중 제11조와 제28조에 대한 상세한 설명이 필요합니다")
        ("한국도로공사의 2024년 회계규정 중 제11조와...", True)
    """
    if not user_question or not user_question.strip():
        return "대화 제목 없음", False

    # 1. 전처리: 연속 공백 제거 및 정규화
    cleaned = re.sub(r'\s+', ' ', user_question.strip())

    # 2. 길이가 max_length 이하면 그대로 반환
    if len(cleaned) <= max_length:
        return cleaned, False

    # 3. 의미 단위 보존을 위한 지능적 절단

    # 3-1. 문장 종결 부호에서 자르기 시도
    for delimiter in ['. ', '? ', '! ', '。', '？', '！']:
        idx = cleaned[:max_length].rfind(delimiter)
        if idx > min_length:  # 최소 길이 이상 유지
            return cleaned[:idx+1], True

    # 3-2. 쉼표나 세미콜론에서 자르기 시도
    for delimiter in [', ', '; ', '、', '，', '；']:
        idx = cleaned[:max_length].rfind(delimiter)
        if idx > min_length:
            return cleaned[:idx+1] + '...', True

    # 3-3. 단어 경계에서 자르기 (한글/영문 모두 처리)
    # 한글: 조사 앞에서 자르기, 영문: 공백에서 자르기
    truncated = cleaned[:max_length]

    # 마지막 공백 위치 찾기
    last_space_idx = truncated.rfind(' ')
    if last_space_idx > min_length:
        truncated = cleaned[:last_space_idx]

    return truncated + '...', True


def sanitize_title(title: str) -> str:
    """
    제목에서 부적절한 문자 제거

    Args:
        title: 원본 제목

    Returns:
        str: 정제된 제목
    """
    # NULL 바이트 제거 (PostgreSQL 보호)
    title = title.replace('\x00', '')

    # 제어 문자 제거 (줄바꿈, 탭 등)
    title = re.sub(r'[\r\n\t]', ' ', title)

    # 연속 공백 정리
    title = re.sub(r'\s+', ' ', title).strip()

    return title


def extract_topic_keywords(question: str, max_keywords: int = 3) -> list:
    """
    질문에서 핵심 키워드 추출 (향후 검색 기능용)

    Args:
        question: 사용자 질문
        max_keywords: 최대 키워드 개수

    Returns:
        list: 추출된 키워드 리스트

    Note:
        현재는 사용하지 않지만, 향후 대화 검색 기능 구현 시 활용 가능
    """
    # 불용어 제거 (간단한 버전)
    stopwords = {
        '에', '대해', '알려', '줘', '주세요', '입니다', '있습니다', '해주세요',
        '의', '를', '을', '이', '가', '은', '는', '과', '와',
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'
    }

    # 공백으로 분리
    words = question.split()

    # 불용어가 아니고 2자 이상인 단어만 추출
    keywords = [
        word.strip(',.?!;:')
        for word in words
        if len(word) >= 2 and word not in stopwords
    ]

    return keywords[:max_keywords]
