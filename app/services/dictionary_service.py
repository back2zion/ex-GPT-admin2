"""
동의어 서비스
사용자 쿼리에서 동의어를 찾아 정식명칭으로 치환
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List, Dict, Optional
import logging
import re

from app.models.dictionary import Dictionary, DictionaryTerm, DictType

logger = logging.getLogger(__name__)


class DictionaryService:
    """
    동의어 치환 서비스

    Features:
        - 사용자 쿼리에서 동의어 탐지
        - 동의어를 정식명칭으로 치환
        - 캐시를 통한 성능 최적화

    Security:
        - SQL Injection 방지 (SQLAlchemy ORM 사용)
        - XSS 방지 (HTML 이스케이프)
    """

    def __init__(self):
        """초기화"""
        self._cache: Dict[str, Dict[str, any]] = {}  # {동의어: {"formal_name": str, "case_sensitive": bool, "word_boundary": bool}}
        self._cache_loaded = False

    async def load_dictionaries(self, db: AsyncSession) -> None:
        """
        DB에서 모든 동의어 사전을 로드하여 캐시

        Args:
            db: 데이터베이스 세션

        Security:
            - SQL Injection 방지 (파라미터 바인딩)
        """
        try:
            # 활성화된 동의어 사전만 조회 (Dictionary 정보도 함께 로드)
            query = select(DictionaryTerm, Dictionary).join(Dictionary).where(
                Dictionary.dict_type == DictType.synonym,
                Dictionary.use_yn == True,
                DictionaryTerm.use_yn == True
            )

            result = await db.execute(query)
            rows = result.all()

            # 캐시 구축
            self._cache.clear()

            for term, dictionary in rows:
                case_sensitive = dictionary.case_sensitive
                word_boundary = dictionary.word_boundary

                # 동의어를 캐시에 추가하는 헬퍼 함수
                def add_to_cache(synonym: str):
                    if not synonym or not synonym.strip():
                        return
                    key = synonym.strip() if case_sensitive else synonym.strip().lower()
                    self._cache[key] = {
                        "formal_name": term.main_term,
                        "case_sensitive": case_sensitive,
                        "word_boundary": word_boundary
                    }

                # 정식명칭은 자기 자신으로 매핑
                add_to_cache(term.main_term)

                # 주요약칭
                add_to_cache(term.main_alias)

                # 추가 약칭들
                add_to_cache(term.alias_1)
                add_to_cache(term.alias_2)
                add_to_cache(term.alias_3)

                # 영문명
                add_to_cache(term.english_name)

                # 영문약칭
                add_to_cache(term.english_alias)

            self._cache_loaded = True
            logger.info(f"Dictionary cache loaded - {len(self._cache)} entries")

        except Exception as e:
            logger.error(f"Failed to load dictionaries: {e}", exc_info=True)
            self._cache_loaded = False

    async def expand_query(self, query: str, db: AsyncSession) -> str:
        """
        사용자 쿼리를 동의어로 확장

        예: "육본에 대해 알려줘"
            → "육본(육군본부)에 대해 알려줘"

        Args:
            query: 사용자 질문
            db: 데이터베이스 세션

        Returns:
            str: 확장된 쿼리

        Security:
            - XSS 방지 (HTML 태그 제거)
            - 입력 검증
        """
        # 캐시 로드 확인
        if not self._cache_loaded:
            await self.load_dictionaries(db)

        if not self._cache:
            return query

        # HTML 태그 제거 (XSS 방지)
        cleaned_query = re.sub(r'<[^>]+>', '', query)

        # 동의어 찾기 및 치환
        expanded_query = cleaned_query
        replacements = []

        # 긴 단어부터 검색 (예: "기재부" 보다 "기획재정부"가 먼저)
        for synonym in sorted(self._cache.keys(), key=len, reverse=True):
            cache_entry = self._cache[synonym]
            formal_name = cache_entry["formal_name"]
            case_sensitive = cache_entry["case_sensitive"]

            # 대소문자 구분에 따라 매칭
            found = False
            if case_sensitive:
                # 대소문자 구분: 정확히 일치하는 경우만
                if synonym in expanded_query:
                    found = True
            else:
                # 대소문자 구분 안 함
                if synonym in expanded_query.lower():
                    found = True

            if found:
                # 이미 정식명칭이 있으면 스킵
                if formal_name.lower() in expanded_query.lower():
                    continue

                # 동의어를 "동의어(정식명칭)" 형태로 치환
                if case_sensitive:
                    # 대소문자 구분하여 치환
                    expanded_query = expanded_query.replace(synonym, f"{synonym}({formal_name})", 1)
                else:
                    # 대소문자 구분 없이 치환
                    pattern = re.compile(re.escape(synonym), re.IGNORECASE)
                    expanded_query = pattern.sub(f"{synonym}({formal_name})", expanded_query, count=1)

                replacements.append(f"{synonym} → {formal_name}")

        if replacements:
            logger.info(f"Query expanded - {len(replacements)} replacements: {replacements}")

        return expanded_query

    async def replace_query(self, query: str, db: AsyncSession) -> str:
        """
        사용자 쿼리의 동의어를 정식명칭으로 완전 치환

        예: "육본에 대해 알려줘"
            → "육군본부에 대해 알려줘"

        Args:
            query: 사용자 질문
            db: 데이터베이스 세션

        Returns:
            str: 치환된 쿼리

        Security:
            - XSS 방지 (HTML 태그 제거)
            - 입력 검증
        """
        # 캐시 로드 확인
        if not self._cache_loaded:
            await self.load_dictionaries(db)

        if not self._cache:
            return query

        # HTML 태그 제거 (XSS 방지)
        cleaned_query = re.sub(r'<[^>]+>', '', query)

        # 동의어 찾기 및 완전 치환
        replaced_query = cleaned_query
        replacements = []

        # 긴 단어부터 검색 (예: "기재부" 보다 "기획재정부"가 먼저)
        for synonym in sorted(self._cache.keys(), key=len, reverse=True):
            cache_entry = self._cache[synonym]
            formal_name = cache_entry["formal_name"]
            case_sensitive = cache_entry["case_sensitive"]
            word_boundary = cache_entry["word_boundary"]

            # 이미 정식명칭이 있으면 스킵
            if case_sensitive:
                if formal_name == synonym:
                    continue
            else:
                if formal_name.lower() == synonym.lower():
                    continue

            # 띄어쓰기 구분 여부에 따라 매칭
            if word_boundary:
                # 띄어쓰기 구분 ON: 정확히 일치하는 경우만
                if case_sensitive:
                    pattern = re.compile(re.escape(synonym))
                else:
                    pattern = re.compile(re.escape(synonym), re.IGNORECASE)

                if pattern.search(replaced_query):
                    replaced_query = pattern.sub(formal_name, replaced_query)
                    replacements.append(f"{synonym} → {formal_name}")
            else:
                # 띄어쓰기 구분 OFF: 공백 무시하고 매칭
                # 쿼리와 동의어 모두에서 공백 제거 후 비교
                query_no_space = replaced_query.replace(' ', '')
                synonym_no_space = synonym.replace(' ', '')

                # 대소문자 처리
                if case_sensitive:
                    search_query = query_no_space
                    search_synonym = synonym_no_space
                else:
                    search_query = query_no_space.lower()
                    search_synonym = synonym_no_space.lower()

                # 매칭 확인
                if search_synonym in search_query:
                    # 원본 쿼리에서 공백 포함/제외 모든 변형 찾기
                    # 예: "한국도로공사", "한국 도로공사", "한국도로 공사" 등
                    # 간단히 처리: 공백이 있는/없는 모든 경우를 패턴으로
                    flexible_pattern = '\\s*'.join([re.escape(char) for char in synonym_no_space])

                    if case_sensitive:
                        pattern = re.compile(flexible_pattern)
                    else:
                        pattern = re.compile(flexible_pattern, re.IGNORECASE)

                    if pattern.search(replaced_query):
                        replaced_query = pattern.sub(formal_name, replaced_query, count=1)
                        replacements.append(f"{synonym} → {formal_name}")

        if replacements:
            logger.info(f"Query replaced - {len(replacements)} replacements: {replacements}")

        return replaced_query

    def reload_cache(self):
        """캐시 재로드 플래그 설정"""
        self._cache_loaded = False
        logger.info("Dictionary cache invalidated - will reload on next query")


# Singleton 인스턴스
dictionary_service = DictionaryService()
