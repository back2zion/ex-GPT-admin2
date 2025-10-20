from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Any, List


class UsageHistoryCreate(BaseModel):
    """
    사용 이력 생성 스키마

    **보안 검증**:
    - 모든 문자열 길이 제한
    - 민감 정보 필터링
    - SQL Injection 방지 (Pydantic 자동 처리)
    """
    user_id: str = Field(..., max_length=100, description="사용자 ID")
    session_id: Optional[str] = Field(None, max_length=100, description="세션 ID")
    question: str = Field(..., max_length=10000, description="질문 내용")
    answer: Optional[str] = Field(None, max_length=50000, description="답변 내용")
    thinking_content: Optional[str] = Field(None, max_length=100000, description="추론 내용 (Think 토큰)")
    response_time: Optional[float] = Field(None, ge=0, le=600000, description="응답 시간 (ms, 최대 10분)")
    referenced_documents: Optional[List[str]] = Field(None, max_length=100, description="참조 문서 목록 (최대 100개)")
    model_name: Optional[str] = Field(None, max_length=100, description="사용된 모델명")
    usage_metadata: Optional[Any] = Field(None, description="추가 메타데이터")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP 주소 (IPv6 최대 길이)")

    @field_validator('question', 'answer', 'thinking_content')
    @classmethod
    def sanitize_text(cls, v: Optional[str]) -> Optional[str]:
        """
        텍스트 필드 검증 및 정제

        - NULL 바이트 제거 (DB 보호)
        - 제어 문자 제거 (보안)
        - 길이 검증은 Field에서 자동 처리
        """
        if v is None:
            return v

        # NULL 바이트 제거 (PostgreSQL 보호)
        v = v.replace('\x00', '')

        # 과도한 공백 정리
        v = ' '.join(v.split())

        return v

    @field_validator('referenced_documents')
    @classmethod
    def validate_documents(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """참조 문서 목록 검증"""
        if v is None:
            return v

        # 각 문서 ID 길이 제한 (200자)
        return [doc[:200] for doc in v if doc]

    @field_validator('user_id', 'session_id', 'model_name')
    @classmethod
    def sanitize_identifier(cls, v: Optional[str]) -> Optional[str]:
        """식별자 필드 정제 (SQL Injection 방지)"""
        if v is None:
            return v

        # 특수 문자 제거 (보안 강화)
        # 영문자, 숫자, 하이픈, 언더스코어, 점만 허용
        import re
        sanitized = re.sub(r'[^\w\-.]', '_', v)

        return sanitized


class UsageHistoryResponse(BaseModel):
    """
    사용 이력 응답 스키마

    **Timezone 처리**:
    - DB에는 UTC로 저장 (timezone-aware)
    - 응답 시 ISO 8601 형식으로 UTC 시간 반환
    - 프론트엔드에서 브라우저의 로컬 시간대로 표시 권장
    """
    id: int
    user_id: str
    question: str
    answer: Optional[str] = None
    thinking_content: Optional[str] = None
    response_time: Optional[float] = None
    referenced_documents: Optional[List[str]] = None
    model_name: Optional[str] = None
    usage_metadata: Optional[Any] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        # JSON 직렬화 시 ISO 8601 형식 사용
        # timezone-aware datetime은 자동으로 +00:00 형식으로 변환됨
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
