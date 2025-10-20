from fastapi import APIRouter, Query, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.models import UsageHistory

router = APIRouter()


class UsageLogCreate(BaseModel):
    """사용 이력 생성 스키마"""
    user_id: str
    session_id: Optional[str] = None
    question: str
    answer: Optional[str] = None
    response_time: Optional[float] = None
    referenced_documents: Optional[list] = None
    model_name: Optional[str] = None
    usage_metadata: Optional[dict] = None


@router.post("/log")
async def create_usage_log(
    log: UsageLogCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    사용 이력 기록

    질문/답변, 응답시간, 참조 문서 등을 기록합니다.
    """
    # IP 주소 추출
    client_host = request.client.host if request.client else None

    # 사용 이력 생성
    usage_history = UsageHistory(
        user_id=log.user_id,
        session_id=log.session_id,
        question=log.question,
        answer=log.answer,
        response_time=log.response_time,
        referenced_documents=log.referenced_documents,
        model_name=log.model_name,
        usage_metadata=log.usage_metadata,
        ip_address=client_host
    )

    db.add(usage_history)
    await db.commit()
    await db.refresh(usage_history)

    return {
        "id": usage_history.id,
        "message": "사용 이력이 기록되었습니다",
        "created_at": usage_history.created_at
    }


@router.get("/history")
async def get_usage_history(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """사용 이력 조회"""
    query = select(UsageHistory)
    count_query = select(func.count()).select_from(UsageHistory)

    # 필터 적용
    if start_date:
        query = query.filter(UsageHistory.created_at >= start_date)
        count_query = count_query.filter(UsageHistory.created_at >= start_date)

    if end_date:
        query = query.filter(UsageHistory.created_at <= end_date)
        count_query = count_query.filter(UsageHistory.created_at <= end_date)

    if user_id:
        query = query.filter(UsageHistory.user_id == user_id)
        count_query = count_query.filter(UsageHistory.user_id == user_id)

    # 전체 개수 조회
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 정렬 및 페이징
    query = query.order_by(UsageHistory.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "total": total,
        "items": [
            {
                "id": item.id,
                "user_id": item.user_id,
                "session_id": item.session_id,
                "question": item.question,
                "answer": item.answer,
                "thinking_content": item.thinking_content,
                "response_time": item.response_time,
                "referenced_documents": item.referenced_documents,
                "model_name": item.model_name,
                "usage_metadata": item.usage_metadata,
                "ip_address": item.ip_address,
                "created_at": item.created_at,
                "updated_at": item.updated_at
            }
            for item in items
        ],
        "skip": skip,
        "limit": limit
    }


@router.get("/statistics")
async def get_usage_statistics(
    period: str = Query("day", regex="^(day|week|month|year)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """사용 통계"""
    query = select(
        func.count(UsageHistory.id).label("total_questions"),
        func.count(func.distinct(UsageHistory.user_id)).label("total_users"),
        func.avg(UsageHistory.response_time).label("avg_response_time")
    )

    # 기간 필터
    if start_date:
        query = query.filter(UsageHistory.created_at >= start_date)
    if end_date:
        query = query.filter(UsageHistory.created_at <= end_date)

    result = await db.execute(query)
    stats = result.one()

    return {
        "total_questions": stats.total_questions or 0,
        "total_users": stats.total_users or 0,
        "avg_response_time": round(stats.avg_response_time, 2) if stats.avg_response_time else 0,
        "period": period
    }


@router.get("/export")
async def export_usage_data(
    start_date: datetime,
    end_date: datetime,
    format: str = Query("csv", regex="^(csv|json|excel)$"),
    db: AsyncSession = Depends(get_db)
):
    """사용 이력 내보내기"""
    query = select(UsageHistory).filter(
        UsageHistory.created_at >= start_date,
        UsageHistory.created_at <= end_date
    )

    result = await db.execute(query)
    items = result.scalars().all()

    # TODO: CSV/Excel/JSON 형식으로 실제 파일 생성
    return {
        "message": "Export started",
        "format": format,
        "count": len(items),
        "start_date": start_date,
        "end_date": end_date
    }
