"""
대화내역 조회 API 엔드포인트
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel

from app.models import UsageHistory
from app.core.database import get_db
from app.dependencies import get_principal
from cerbos.sdk.model import Principal

router = APIRouter(prefix="/api/v1/admin/conversations", tags=["admin-conversations"])


class ConversationListItem(BaseModel):
    """대화내역 목록 아이템"""
    id: int
    user_id: str
    question: str
    answer: Optional[str] = None
    thinking_content: Optional[str] = None
    response_time: Optional[float] = None
    created_at: datetime

    # 질문 내용 미리보기 (최대 100자)
    @property
    def question_preview(self) -> str:
        if len(self.question) > 100:
            return self.question[:100] + "..."
        return self.question

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ConversationDetail(BaseModel):
    """대화내역 상세"""
    id: int
    user_id: str
    session_id: Optional[str] = None
    question: str
    answer: Optional[str] = None
    thinking_content: Optional[str] = None
    response_time: Optional[float] = None
    model_name: Optional[str] = None
    referenced_documents: Optional[List[str]] = None
    usage_metadata: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ConversationListResponse(BaseModel):
    """대화내역 목록 응답"""
    items: List[ConversationListItem]
    total: int
    page: int
    limit: int
    total_pages: int


@router.get("/", response_model=ConversationListResponse)
async def get_conversations(
    start: Optional[date] = Query(None, description="시작일 (YYYY-MM-DD)"),
    end: Optional[date] = Query(None, description="종료일 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(50, ge=1, le=10000, description="페이지당 항목 수 (최대 10000)"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    대화내역 목록 조회

    - 날짜 필터링 가능
    - 페이지네이션 지원 (최대 10000개/페이지 - 엑셀 다운로드용)
    - 최신순 정렬
    """
    # 기본 쿼리
    conditions = []

    # 날짜 필터
    if start:
        conditions.append(func.date(UsageHistory.created_at) >= start)
    if end:
        conditions.append(func.date(UsageHistory.created_at) <= end)

    # 전체 개수 조회
    count_query = select(func.count(UsageHistory.id))
    if conditions:
        count_query = count_query.filter(and_(*conditions))

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # 페이지네이션 계산
    offset = (page - 1) * limit
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    # 목록 조회
    list_query = select(UsageHistory)
    if conditions:
        list_query = list_query.filter(and_(*conditions))

    list_query = list_query.order_by(desc(UsageHistory.created_at)).offset(offset).limit(limit)

    result = await db.execute(list_query)
    conversations = result.scalars().all()

    return ConversationListResponse(
        items=[ConversationListItem.model_validate(conv) for conv in conversations],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation_detail(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    대화내역 상세 조회

    - 전체 질문/답변 내용
    - 사용자 정보
    - 세션 정보
    - 참조 문서 목록
    - 메타데이터
    """
    query = select(UsageHistory).filter(UsageHistory.id == conversation_id)
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()

    if not conversation:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="대화내역을 찾을 수 없습니다.")

    return ConversationDetail.model_validate(conversation)
