from sqlalchemy import Column, Integer, String, Text, Enum
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import enum


class ParsingPattern(str, enum.Enum):
    """문서 파싱 패턴"""
    SENTENCE = "SENTENCE"  # 문장 단위
    PARAGRAPH = "PARAGRAPH"  # 단락 단위
    PAGE = "PAGE"  # 페이지 단위
    CUSTOM = "CUSTOM"  # 사용자 정의


class Category(Base, TimestampMixin):
    """
    문서 카테고리 모델
    학습데이터 관리를 위한 문서 분류
    """
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text)
    parsing_pattern = Column(
        Enum(ParsingPattern),
        default=ParsingPattern.PARAGRAPH,
        nullable=False
    )

    # 관계: 이 카테고리에 속한 문서들
    documents = relationship("Document", back_populates="category")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"

    def to_dict(self):
        """Secure: DTO 패턴으로 민감 정보 제외"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parsing_pattern": self.parsing_pattern.value if self.parsing_pattern else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
