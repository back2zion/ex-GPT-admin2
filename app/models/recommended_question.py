"""추천 질문 모델

DATABASE_SCHEMA.md의 RCM_QUES 테이블 정의:
- RCM_QUES_ID: 추천 질문 고유 ID
- QUES_TXT: 질문 텍스트
- CAT_NM: 카테고리명
- DESC_TXT: 설명 텍스트
- DISP_ORD: 표시 순서
- USE_YN: 사용 여부 (Y/N)
- REG_USR_ID, REG_DT, MOD_USR_ID, MOD_DT: 등록/수정 정보
"""
from sqlalchemy import Column, BigInteger, String, Text, Integer
from app.models.base import Base, TimestampMixin


class RecommendedQuestion(Base, TimestampMixin):
    """추천 질문 모델"""
    __tablename__ = "rcm_ques"

    # 기본 키
    rcm_ques_id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)

    # 질문 정보
    ques_txt = Column(String(500), nullable=False, comment="질문 텍스트")
    cat_nm = Column(String(100), nullable=True, comment="카테고리명")
    desc_txt = Column(Text, nullable=True, comment="설명 텍스트")

    # 표시 순서
    disp_ord = Column(Integer, default=999, nullable=False, comment="표시 순서")

    # 사용 여부
    use_yn = Column(String(1), default='Y', nullable=False, comment="사용 여부 (Y/N)")

    # 등록/수정 정보 (TimestampMixin에서 상속)
    # created_at, updated_at, created_by, updated_by

    def __repr__(self):
        return f"<RecommendedQuestion(id={self.rcm_ques_id}, question={self.ques_txt[:30]}, active={self.use_yn})>"
