"""
사전 관리 모델

동의어 사전 및 사용자 사전을 관리하기 위한 데이터 모델
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.models.base import Base, TimestampMixin


class DictType(str, enum.Enum):
    """사전 종류"""
    synonym = "synonym"  # 동의어 사전
    user = "user"  # 사용자 사전


class Dictionary(Base, TimestampMixin):
    """
    사전 기본 테이블

    동의어 사전 또는 사용자 사전의 메타 정보를 저장
    """
    __tablename__ = "dictionary"

    dict_id = Column(Integer, primary_key=True, autoincrement=True, comment="사전 ID")
    dict_type = Column(SQLEnum(DictType), nullable=False, comment="사전 종류 (synonym: 동의어사전, user: 사용자사전)")
    dict_name = Column(String(200), nullable=False, comment="사전명")
    dict_desc = Column(Text, nullable=True, comment="사전 설명")
    case_sensitive = Column(Boolean, default=False, nullable=False, comment="대소문자 구분 여부")
    word_boundary = Column(Boolean, default=False, nullable=False, comment="띄어쓰기 구분 여부 (단어 경계 인식)")
    word_count = Column(Integer, default=0, nullable=False, comment="용어 개수")
    use_yn = Column(Boolean, default=True, nullable=False, comment="사용 여부")

    # Relationship
    terms = relationship("DictionaryTerm", back_populates="dictionary", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Dictionary(dict_id={self.dict_id}, name={self.dict_name}, type={self.dict_type})>"


class DictionaryTerm(Base, TimestampMixin):
    """
    사전 용어 테이블

    각 사전에 속한 개별 용어를 저장
    - 정식명칭, 약칭들, 영문명, 분류 등
    """
    __tablename__ = "dictionary_term"

    term_id = Column(Integer, primary_key=True, autoincrement=True, comment="용어 ID")
    dict_id = Column(Integer, ForeignKey("dictionary.dict_id", ondelete="CASCADE"), nullable=False, comment="사전 ID")

    # 한글 명칭
    main_term = Column(String(200), nullable=False, comment="정식명칭 (예: 기획재정부)")
    main_alias = Column(String(200), nullable=True, comment="주요약칭 (예: 기재부)")
    alias_1 = Column(String(200), nullable=True, comment="추가약칭1")
    alias_2 = Column(String(200), nullable=True, comment="추가약칭2")
    alias_3 = Column(String(200), nullable=True, comment="추가약칭3")

    # 영문 명칭
    english_name = Column(String(500), nullable=True, comment="영문명 (예: Ministry of Economy and Finance)")
    english_alias = Column(String(100), nullable=True, comment="영문약칭 (예: MOEF)")

    # 메타 정보
    category = Column(String(100), nullable=True, comment="분류 (예: 중앙정부부처, 출연연, 공기업)")
    definition = Column(Text, nullable=True, comment="정의/설명")

    # 사용 여부
    use_yn = Column(Boolean, default=True, nullable=False, comment="사용 여부")

    # Relationship
    dictionary = relationship("Dictionary", back_populates="terms")

    def __repr__(self):
        return f"<DictionaryTerm(term_id={self.term_id}, main_term={self.main_term}, category={self.category})>"

    @property
    def all_synonyms(self) -> list[str]:
        """모든 동의어 반환 (약칭들)"""
        synonyms = []
        if self.main_alias:
            synonyms.append(self.main_alias)
        if self.alias_1:
            synonyms.append(self.alias_1)
        if self.alias_2:
            synonyms.append(self.alias_2)
        if self.alias_3:
            synonyms.append(self.alias_3)
        if self.english_alias:
            synonyms.append(self.english_alias)
        return synonyms
