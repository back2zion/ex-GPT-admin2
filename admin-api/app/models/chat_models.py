"""
Chat Models
채팅 시스템 SQLAlchemy 모델
"""
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float,
    ForeignKey, Index, BigInteger, Boolean
)
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime


class ConversationSummary(Base):
    """
    대화방 요약 (USR_CNVS_SMRY)

    대화방의 메타데이터를 저장
    - CNVS_IDT_ID: Room ID (고유 식별자)
    - CNVS_SMRY_TXT: 자동 생성된 요약 (첫 질문)
    - REP_CNVS_NM: 사용자가 지정한 대화명
    """
    __tablename__ = "USR_CNVS_SMRY"

    # Primary Key
    cnvs_smry_id = Column(
        "CNVS_SMRY_ID",
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="대화방 요약 ID"
    )

    # Unique Room ID
    cnvs_idt_id = Column(
        "CNVS_IDT_ID",
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="대화방 ID (고유)"
    )

    # 요약 정보
    cnvs_smry_txt = Column(
        "CNVS_SMRY_TXT",
        Text,
        nullable=False,
        comment="대화 요약 (첫 질문)"
    )

    rep_cnvs_nm = Column(
        "REP_CNVS_NM",
        String(500),
        nullable=True,
        comment="대화명 (사용자 지정)"
    )

    # 사용자 정보
    usr_id = Column(
        "USR_ID",
        String(50),
        nullable=False,
        index=True,
        comment="사용자 ID"
    )

    # 상태
    use_yn = Column(
        "USE_YN",
        String(1),
        nullable=False,
        default="Y",
        comment="사용 여부 (Y/N)"
    )

    # 타임스탬프
    reg_dt = Column(
        "REG_DT",
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="등록일시"
    )

    mod_dt = Column(
        "MOD_DT",
        DateTime,
        nullable=True,
        onupdate=datetime.utcnow,
        comment="수정일시"
    )

    # Relationships
    conversations = relationship(
        "Conversation",
        back_populates="summary",
        cascade="all, delete-orphan"
    )

    uploaded_files = relationship(
        "UploadedFile",
        back_populates="room",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_usr_cnvs_smry_usr_id_reg_dt", "USR_ID", "REG_DT"),
        Index("idx_usr_cnvs_smry_use_yn", "USE_YN"),
    )


class Conversation(Base):
    """
    대화 메시지 (USR_CNVS)

    개별 질문-답변 쌍을 저장
    - QUES_TXT: 사용자 질문
    - ANS_TXT: AI 답변
    - TKN_USE_CNT: 토큰 사용량
    - RSP_TIM_MS: 응답 시간 (밀리초)
    """
    __tablename__ = "USR_CNVS"

    # Primary Key
    cnvs_id = Column(
        "CNVS_ID",
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="대화 ID"
    )

    # Foreign Key
    cnvs_idt_id = Column(
        "CNVS_IDT_ID",
        String(100),
        ForeignKey("USR_CNVS_SMRY.CNVS_IDT_ID"),
        nullable=False,
        index=True,
        comment="대화방 ID (FK)"
    )

    # 메시지 내용
    ques_txt = Column(
        "QUES_TXT",
        Text,
        nullable=False,
        comment="질문 텍스트"
    )

    ans_txt = Column(
        "ANS_TXT",
        Text,
        nullable=True,
        comment="답변 텍스트"
    )

    # 메타데이터
    tkn_use_cnt = Column(
        "TKN_USE_CNT",
        Integer,
        nullable=True,
        comment="토큰 사용 수"
    )

    rsp_tim_ms = Column(
        "RSP_TIM_MS",
        Integer,
        nullable=True,
        comment="응답 시간 (밀리초)"
    )

    sesn_id = Column(
        "SESN_ID",
        String(100),
        nullable=True,
        comment="HTTP 세션 ID"
    )

    # 상태
    use_yn = Column(
        "USE_YN",
        String(1),
        nullable=False,
        default="Y",
        comment="사용 여부 (Y/N)"
    )

    # 타임스탬프
    reg_dt = Column(
        "REG_DT",
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="등록일시"
    )

    mod_dt = Column(
        "MOD_DT",
        DateTime,
        nullable=True,
        onupdate=datetime.utcnow,
        comment="수정일시"
    )

    # Relationships
    summary = relationship("ConversationSummary", back_populates="conversations")

    reference_documents = relationship(
        "ReferenceDocument",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )

    suggested_questions = relationship(
        "SuggestedQuestion",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_usr_cnvs_cnvs_idt_id_reg_dt", "CNVS_IDT_ID", "REG_DT"),
    )


class ReferenceDocument(Base):
    """
    참조 문서 (USR_CNVS_REF_DOC_LST)

    RAG 검색으로 찾은 참조 문서를 저장
    - ATT_DOC_NM: 문서명
    - DOC_CHNK_TXT: 청크 텍스트
    - SMLT_RTE: 유사도 점수
    """
    __tablename__ = "USR_CNVS_REF_DOC_LST"

    # Primary Key
    cnvs_ref_doc_id = Column(
        "CNVS_REF_DOC_ID",
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="참조 문서 ID"
    )

    # Foreign Key
    cnvs_id = Column(
        "CNVS_ID",
        Integer,
        ForeignKey("USR_CNVS.CNVS_ID"),
        nullable=False,
        index=True,
        comment="대화 ID (FK)"
    )

    # 문서 정보
    ref_seq = Column(
        "REF_SEQ",
        Integer,
        nullable=False,
        comment="참조 순서"
    )

    att_doc_nm = Column(
        "ATT_DOC_NM",
        String(500),
        nullable=False,
        comment="문서명"
    )

    doc_chnk_txt = Column(
        "DOC_CHNK_TXT",
        Text,
        nullable=False,
        comment="문서 청크 텍스트"
    )

    smlt_rte = Column(
        "SMLT_RTE",
        Float,
        nullable=False,
        comment="유사도 점수"
    )

    # 타임스탬프
    reg_dt = Column(
        "REG_DT",
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="등록일시"
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="reference_documents")

    # Indexes
    __table_args__ = (
        Index("idx_usr_cnvs_ref_doc_cnvs_id", "CNVS_ID"),
    )


class SuggestedQuestion(Base):
    """
    추천 질문 (USR_CNVS_ADD_QUES_LST)

    AI가 생성한 추천 질문을 저장
    - ADD_QUES_TXT: 추천 질문 텍스트
    """
    __tablename__ = "USR_CNVS_ADD_QUES_LST"

    # Primary Key
    cnvs_add_ques_id = Column(
        "CNVS_ADD_QUES_ID",
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="추천 질문 ID"
    )

    # Foreign Key
    cnvs_id = Column(
        "CNVS_ID",
        Integer,
        ForeignKey("USR_CNVS.CNVS_ID"),
        nullable=False,
        index=True,
        comment="대화 ID (FK)"
    )

    # 질문 정보
    add_ques_seq = Column(
        "ADD_QUES_SEQ",
        Integer,
        nullable=False,
        comment="추천 질문 순서"
    )

    add_ques_txt = Column(
        "ADD_QUES_TXT",
        Text,
        nullable=False,
        comment="추천 질문 텍스트"
    )

    # 타임스탬프
    reg_dt = Column(
        "REG_DT",
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="등록일시"
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="suggested_questions")

    # Indexes
    __table_args__ = (
        Index("idx_usr_cnvs_add_ques_cnvs_id", "CNVS_ID"),
    )


class UploadedFile(Base):
    """
    업로드 파일 관리 (USR_UPLD_DOC_MNG)

    채팅 중 업로드된 파일의 메타데이터를 저장
    - FILE_UID: MinIO Object Name
    - FILE_DOWN_URL: 다운로드 URL
    """
    __tablename__ = "USR_UPLD_DOC_MNG"

    # Primary Key
    upld_doc_id = Column(
        "UPLD_DOC_ID",
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="업로드 문서 ID"
    )

    # Foreign Key
    cnvs_idt_id = Column(
        "CNVS_IDT_ID",
        String(100),
        ForeignKey("USR_CNVS_SMRY.CNVS_IDT_ID"),
        nullable=False,
        index=True,
        comment="대화방 ID (FK)"
    )

    # 파일 정보
    file_nm = Column(
        "FILE_NM",
        String(500),
        nullable=False,
        comment="파일명"
    )

    file_uid = Column(
        "FILE_UID",
        String(500),
        nullable=False,
        comment="MinIO Object Name (UUID)"
    )

    file_down_url = Column(
        "FILE_DOWN_URL",
        String(1000),
        nullable=False,
        comment="파일 다운로드 URL"
    )

    file_size = Column(
        "FILE_SIZE",
        BigInteger,
        nullable=False,
        comment="파일 크기 (bytes)"
    )

    file_typ_cd = Column(
        "FILE_TYP_CD",
        String(10),
        nullable=False,
        comment="파일 타입 (pdf, docx, xlsx, txt, png, jpg)"
    )

    # 사용자 정보
    usr_id = Column(
        "USR_ID",
        String(50),
        nullable=False,
        comment="업로드 사용자 ID"
    )

    # 타임스탬프
    reg_dt = Column(
        "REG_DT",
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="등록일시"
    )

    # Relationships
    room = relationship("ConversationSummary", back_populates="uploaded_files")

    # Indexes
    __table_args__ = (
        Index("idx_usr_upld_doc_cnvs_idt_id", "CNVS_IDT_ID"),
        Index("idx_usr_upld_doc_usr_id", "USR_ID"),
    )
