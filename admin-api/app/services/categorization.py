"""
Conversation Categorization Service
규칙 기반 대화 자동 분류 서비스 (MVP)
TODO: LLM 기반 분류로 업그레이드
"""
import httpx
import json
import logging
import re
from typing import Dict, Tuple, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# 카테고리 매핑 (ConversationsPage.jsx와 동일 - 조직도 기반)
CATEGORY_MAP = {
    '경영분야': {
        'subcategories': ['기획/전략', '관리/인사', '고객/통행료', '디지털/IT', '홍보/감사']
    },
    '기술분야': {
        'subcategories': ['도로/시설', '교통/ITS', '건설/설계', '신사업/연구', '안전/재난']
    },
    '기타': {
        'subcategories': ['지역본부', '경영/기술 외']
    }
}

# 키워드 기반 분류 규칙 (한국도로공사 조직도 기반)
KEYWORD_RULES = {
    '경영분야': {
        '기획/전략': [
            '기획', '전략', '미래', '성과', '혁신', '목표', '계획', '정책',
            '비전', '중장기', 'KPI', '평가', '지표', '목표관리'
        ],
        '관리/인사': [
            '총무', '인사', '인력', '채용', '승진', '교육', '급여', '보수',
            '재무', '회계', '예산', '결산', '법무', '계약', '소송', '토지',
            '용지', '보상', '인재', '직원', '근무', '조직', '부서'
        ],
        '고객/통행료': [
            '통행료', '요금', '정산', '하이패스', '미납', '할인', '면제',
            '고객', '민원', '휴게소', '매점', '주유', '식당', '편의시설',
            '서비스', '만족도', '불편', '개선'
        ],
        '디지털/IT': [
            '디지털', 'IT', '정보', '시스템', '전산', '데이터', '융합',
            '빅데이터', 'AI', '인공지능', '보안', '해킹', '사이버',
            '클라우드', '서버', '네트워크', '프로그램', '앱', '모바일'
        ],
        '홍보/감사': [
            '홍보', '보도', '언론', '미디어', '광고', '캠페인', '대외',
            '감사', '내부통제', '감사처', '점검', '위반', '부정', '비리'
        ],
    },
    '기술분야': {
        '도로/시설': [
            '도로', '포장', '노면', '구조물', '교량', '터널', '시설물',
            '유지보수', '보수', '관리', '점검', '보강', '개량', '정비',
            '파손', '균열', '손상', '열화', '특수교'
        ],
        '교통/ITS': [
            '교통', 'ITS', '지능형', '관제', '통제', 'CCTV', '영상',
            '소통', '정체', '혼잡', '차량', '속도', '제한', '단속',
            '재난', '사고', '응급', '긴급', '제설', '집중호우',
            '첨단기계화', '교통관제센터'
        ],
        '건설/설계': [
            '건설', '공사', '시공', '공정', '설계', '도면', '실시설계',
            '토목', '토공', '구조', '품질', '환경', '친환경',
            '환경영향평가', '안전관리', '공정관리', '계약', '발주'
        ],
        '신사업/연구': [
            '신사업', '사업개발', '해외', '수출', '기술심사', '기술마켓',
            '연구', 'R&D', '개발', '스마트', '자율주행', '전기차',
            '친환경', '신기술', '특허', '혁신', '실증', '테스트베드',
            '도로교통연구원'
        ],
        '안전/재난': [
            '안전', '안전점검', '위험', '위험물', '재해', '재난관리',
            '비상', '비상계획', '대응', '대피', '사고예방', '안전교육',
            '안전혁신', '화재', '폭발', '붕괴'
        ],
    },
    '기타': {
        '지역본부': [
            '수도권', '서울경기', '강원', '충북', '대전충남', '전북',
            '광주전남', '대구경북', '부산경남', '지역본부', '지사',
            '관리소', '건설사업단'
        ],
    }
}

CATEGORIZATION_PROMPT = """다음은 한국도로공사 ex-GPT 시스템의 사용자 질문과 AI 응답입니다.
이 대화를 한국도로공사 조직도 기반으로 대분류와 소분류로 분류해주세요.

**대분류:**
- 경영분야: 기획, 전략, 관리, 인사, 고객, 통행료, 디지털, IT, 홍보, 감사 등
- 기술분야: 도로, 시설, 교통, ITS, 건설, 설계, 신사업, 연구, 안전, 재난 등
- 기타: 지역본부 관련 또는 위 두 가지에 해당하지 않는 경우

**소분류 (경영분야):**
- 기획/전략: 기획본부 관련 (경영기획, 미래전략, 성과혁신)
- 관리/인사: 관리본부 관련 (총무, 인사, 재무, 법무, 토지)
- 고객/통행료: 고객사업본부 관련 (통행료정책, 통행료시스템, 휴게사업, 정산)
- 디지털/IT: 디지털본부 관련 (디지털, 데이터융합, 정보보안)
- 홍보/감사: 홍보처, 감사처 관련

**소분류 (기술분야):**
- 도로/시설: 도로본부 관련 (도로유지, 구조물, 시설관리)
- 교통/ITS: 교통본부 관련 (교통관리, 재난관리, ITS, 관제)
- 건설/설계: 건설본부 관련 (건설, 설계, 품질환경)
- 신사업/연구: 신사업본부, 도로교통연구원 관련 (신사업, R&D, 스마트도로)
- 안전/재난: 안전혁신처, 비상계획처 관련

**소분류 (기타):**
- 지역본부: 지역본부 관련 (수도권, 서울경기, 강원 등)
- 경영/기술 외: 일반적인 질문, 분류 불가

질문: {question}

응답: {answer}

위 대화를 다음 JSON 형식으로 분류하세요:
{{"main_category": "대분류", "sub_category": "소분류"}}

대분류가 불명확하면 "미분류"를 사용하고, 소분류는 "없음"으로 하세요.
JSON만 출력하세요."""


def categorize_by_keywords(question: str, answer: str) -> Tuple[str, str]:
    """
    키워드 기반 대화 분류 (규칙 기반 MVP)

    Args:
        question: 사용자 질문
        answer: AI 응답

    Returns:
        (main_category, sub_category) 튜플
    """
    text = (question + " " + answer).lower()

    # 각 카테고리별로 점수 계산
    scores = {}
    for main_cat, sub_cats in KEYWORD_RULES.items():
        for sub_cat, keywords in sub_cats.items():
            score = sum(1 for keyword in keywords if keyword.lower() in text)
            if score > 0:
                scores[(main_cat, sub_cat)] = score

    # 가장 높은 점수를 가진 카테고리 선택
    if scores:
        best_category = max(scores.items(), key=lambda x: x[1])[0]
        main_cat, sub_cat = best_category
        logger.info(f"Keyword-based categorization: {main_cat} > {sub_cat} (score: {scores[best_category]})")
        return main_cat, sub_cat
    else:
        # 키워드 매치 없으면 미분류
        return "미분류", "없음"


async def categorize_conversation_vllm(question: str, answer: str) -> Tuple[str, str]:
    """
    vLLM을 직접 호출하여 대화를 자동 분류

    Args:
        question: 사용자 질문
        answer: AI 응답

    Returns:
        (main_category, sub_category) 튜플

    Raises:
        Exception: LLM API 호출 실패 시
    """
    try:
        # 조직도 기반 분류 프롬프트
        prompt = f"""다음 대화를 한국도로공사 조직도 기반으로 분류하세요.

질문: {question[:300]}
답변: {answer[:300]}

대분류:
- 경영분야: 기획, 전략, 관리, 인사, 고객, 통행료, 디지털, IT, 홍보, 감사
- 기술분야: 도로, 시설, 교통, ITS, 건설, 설계, 신사업, 연구, 안전, 재난
- 기타: 지역본부 또는 분류 불가

소분류(경영분야): 기획/전략, 관리/인사, 고객/통행료, 디지털/IT, 홍보/감사
소분류(기술분야): 도로/시설, 교통/ITS, 건설/설계, 신사업/연구, 안전/재난
소분류(기타): 지역본부, 경영/기술 외

다음 JSON 형식으로만 답변하세요 (다른 텍스트 없이):
{{"main_category": "대분류", "sub_category": "소분류"}}"""

        # vLLM 직접 호출 (OpenAI 호환 API)
        llm_payload = {
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 150,
            "temperature": 0.0
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://host.docker.internal:8000/v1/chat/completions",
                json=llm_payload,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code != 200:
                logger.error(f"vLLM categorization failed: {response.status_code} {response.text}")
                return "미분류", "없음"

            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

            # <think> 태그 제거
            if "<think>" in content:
                # think 태그 이후의 내용만 사용
                parts = content.split("</think>")
                if len(parts) > 1:
                    content = parts[1].strip()
                else:
                    # think 태그가 닫히지 않은 경우 전체 내용 사용
                    content = content.replace("<think>", "").strip()

            # JSON 파싱
            try:
                # JSON 블록 추출
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                # JSON 찾기 (중괄호 시작)
                if "{" in content:
                    start = content.index("{")
                    end = content.rindex("}") + 1
                    content = content[start:end]

                category_data = json.loads(content)
                main_category = category_data.get("main_category", "미분류")
                sub_category = category_data.get("sub_category", "없음")

                # 유효성 검증
                if main_category not in CATEGORY_MAP and main_category != "미분류":
                    logger.warning(f"Invalid main_category from LLM: {main_category}, using 미분류")
                    main_category = "미분류"
                    sub_category = "없음"
                elif main_category in CATEGORY_MAP:
                    if sub_category not in CATEGORY_MAP[main_category]['subcategories']:
                        logger.warning(f"Invalid sub_category from LLM: {sub_category}, using 기타")
                        sub_category = "기타"

                logger.info(f"LLM Categorized: {main_category} > {sub_category}")
                return main_category, sub_category

            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse LLM response as JSON: {content}, error: {e}")
                return "미분류", "없음"

    except Exception as e:
        logger.error(f"Error during LLM categorization: {e}", exc_info=True)
        return "미분류", "없음"


async def categorize_conversation_safe(question: str, answer: str) -> Tuple[str, str]:
    """
    대화 분류 (안전 버전 - LLM 우선, 실패 시 키워드 기반 폴백)

    Args:
        question: 사용자 질문
        answer: AI 응답

    Returns:
        (main_category, sub_category) 튜플 (항상 성공)
    """
    try:
        # LLM 기반 분류 시도
        main_cat, sub_cat = await categorize_conversation_vllm(question, answer)

        # LLM이 분류에 실패한 경우 (미분류 반환) 키워드 기반 시도
        if main_cat == "미분류":
            logger.info("LLM categorization returned 미분류, falling back to keyword-based")
            return categorize_by_keywords(question, answer)

        return main_cat, sub_cat

    except Exception as e:
        logger.error(f"LLM categorization error, falling back to keyword-based: {e}")
        # 키워드 기반 폴백
        try:
            return categorize_by_keywords(question, answer)
        except Exception as e2:
            logger.error(f"Keyword categorization also failed: {e2}")
            return "미분류", "없음"
