"""
만족도 조사 조회 API 엔드포인트 (읽기 전용)
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from app.models import SatisfactionSurvey
from app.schemas.satisfaction import SatisfactionResponse
from app.core.database import get_db
from app.dependencies import get_principal
from cerbos.sdk.model import Principal

router = APIRouter(prefix="/api/v1/admin/satisfaction", tags=["admin-satisfaction"])


@router.get("/", response_model=List[SatisfactionResponse])
async def list_satisfaction(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(100, le=1000, description="조회할 최대 레코드 수"),
    rating: Optional[int] = Query(None, ge=1, le=5, description="평점 필터 (1-5)"),
    category: Optional[str] = Query(None, pattern="^(ui|speed|accuracy|other)$", description="카테고리 필터"),
    user_id: Optional[str] = Query(None, description="사용자 ID 필터"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    만족도 조사 목록 조회

    - 평점, 피드백, 카테고리 등 조회
    - 필터링 및 페이지네이션 지원
    """
    query = select(SatisfactionSurvey)

    # 필터
    if rating:
        query = query.filter(SatisfactionSurvey.rating == rating)
    if category:
        query = query.filter(SatisfactionSurvey.category == category)
    if user_id:
        query = query.filter(SatisfactionSurvey.user_id == user_id)

    # 정렬 및 페이징
    query = query.order_by(SatisfactionSurvey.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats")
async def get_satisfaction_stats(
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    만족도 통계

    - 평균 평점
    - 총 응답 수
    - 카테고리별 집계 (Phase 2에서 구현)
    """
    result = await db.execute(
        select(
            func.avg(SatisfactionSurvey.rating).label('average'),
            func.count(SatisfactionSurvey.id).label('total')
        )
    )
    stats = result.one()

    return {
        "average_rating": round(float(stats.average), 2) if stats.average else 0.0,
        "total_surveys": stats.total
    }


@router.get("/{survey_id}", response_model=SatisfactionResponse)
async def get_satisfaction(
    survey_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    특정 만족도 조사 상세 조회
    """
    from fastapi import HTTPException

    result = await db.execute(select(SatisfactionSurvey).filter(SatisfactionSurvey.id == survey_id))
    survey = result.scalar_one_or_none()

    if not survey:
        raise HTTPException(status_code=404, detail="만족도 조사를 찾을 수 없습니다")

    return survey
