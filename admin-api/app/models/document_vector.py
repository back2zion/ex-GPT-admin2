from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import enum


class VectorStatus(str, enum.Enum):
    """벡터화 상태"""
    PENDING = "PENDING"  # 대기 중
    PROCESSING = "PROCESSING"  # 처리 중
    COMPLETED = "COMPLETED"  # 완료
    FAILED = "FAILED"  # 실패


class DocumentVector(Base, TimestampMixin):
    """
    문서 벡터 메타데이터 모델
    Qdrant에 저장된 벡터와 문서 간의 연결 정보 관리
    """
    __tablename__ = "document_vectors"

    id = Column(Integer, primary_key=True, index=True)

    # 문서 참조
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False, index=True)

    # Qdrant 정보
    qdrant_point_id = Column(String(255), nullable=False, index=True)  # Qdrant point UUID
    qdrant_collection = Column(String(255), nullable=False)  # Collection name

    # 청크 정보
    chunk_index = Column(Integer, nullable=False)  # 문서 내 청크 순서
    chunk_text = Column(String(10000))  # 벡터화된 텍스트 (최대 10KB, 보안: 길이 제한)
    chunk_metadata = Column(JSON)  # 청크 메타데이터 (페이지 번호, 위치 등)

    # 벡터 정보
    vector_dimension = Column(Integer)  # 벡터 차원 (512, 768, 1024 등)
    embedding_model = Column(String(255))  # 사용된 임베딩 모델명

    # 상태
    status = Column(Enum(VectorStatus), default=VectorStatus.PENDING, nullable=False)
    error_message = Column(String(1000))  # 실패 시 에러 메시지 (보안: 길이 제한)

    # 관계
    document = relationship("Document", back_populates="vectors")

    def __repr__(self):
        return f"<DocumentVector(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"

    def to_dict(self):
        """Secure: DTO 패턴으로 민감 정보 제외"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "qdrant_point_id": self.qdrant_point_id,
            "qdrant_collection": self.qdrant_collection,
            "chunk_index": self.chunk_index,
            "vector_dimension": self.vector_dimension,
            "embedding_model": self.embedding_model,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
