from fastapi import APIRouter, Query, Depends, HTTPException, Request
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models import SatisfactionSurvey

router = APIRouter()


class SatisfactionSubmit(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="평점 (1-5)")
    feedback: Optional[str] = Field(None, max_length=1000, description="피드백")
    category: Optional[str] = Field(None, pattern="^(UI|SPEED|ACCURACY|OTHER)$", description="카테고리")
    user_id: Optional[str] = Field(None, max_length=100, description="사용자 ID")
    related_question_id: Optional[str] = Field(None, max_length=100, description="관련 질문 ID")


@router.post("/submit")
async def submit_satisfaction_survey(
    survey: SatisfactionSubmit,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """만족도 조사 제출"""
    try:
        # IP 주소 추출
        ip_address = request.client.host if request.client else None

        # DB에 저장
        new_survey = SatisfactionSurvey(
            user_id=survey.user_id if survey.user_id else 'anonymous',
            rating=survey.rating,
            feedback=survey.feedback,
            category=survey.category if survey.category else 'OTHER',
            related_question_id=survey.related_question_id,
            ip_address=ip_address
        )

        db.add(new_survey)
        await db.commit()
        await db.refresh(new_survey)

        return {
            "status": "success",
            "message": "만족도 조사가 제출되었습니다",
            "survey_id": new_survey.id,
            "rating": survey.rating
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"만족도 조사 제출 실패: {str(e)}")


@router.get("/results")
async def get_satisfaction_results(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category: Optional[str] = None
):
    """만족도 조사 결과 조회"""
    # TODO: 만족도 통계 반환
    return {
        "average_rating": 0,
        "total_responses": 0,
        "distribution": {
            "1": 0,
            "2": 0,
            "3": 0,
            "4": 0,
            "5": 0
        }
    }


@router.get("/export")
async def export_satisfaction_data(
    start_date: datetime,
    end_date: datetime,
    format: str = Query("csv", regex="^(csv|json|excel)$")
):
    """만족도 데이터 내보내기"""
    # TODO: CSV/Excel/JSON 형식으로 데이터 내보내기
    return {
        "message": "Export started",
        "format": format
    }
