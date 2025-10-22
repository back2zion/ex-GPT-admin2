"""
엑셀 내보내기 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import pandas as pd
from io import BytesIO, StringIO
from datetime import date
from typing import Optional

from app.models import Notice, UsageHistory, SatisfactionSurvey
from app.core.database import get_db
from app.dependencies import require_permission
from cerbos.sdk.model import Principal

router = APIRouter(prefix="/api/v1/admin/export", tags=["admin-export"])


@router.get("/notices")
async def export_notices(
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("notice", "read"))
):
    """
    공지사항 엑셀 내보내기

    - 모든 공지사항 데이터를 Excel 파일로 내보내기
    - Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    """
    result = await db.execute(select(Notice))
    notices = result.scalars().all()

    # DataFrame 생성
    df = pd.DataFrame([{
        "ID": n.id,
        "제목": n.title,
        "내용": n.content,
        "우선순위": n.priority,
        "활성화": "활성" if n.is_active else "비활성",
        "조회수": n.view_count,
        "생성일": n.created_at.strftime("%Y-%m-%d %H:%M:%S") if n.created_at else ""
    } for n in notices])

    # Excel 파일 생성
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='공지사항')

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=notices.xlsx"}
    )


@router.get("/usage")
async def export_usage(
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("usage_history", "read")),
    start_date: Optional[date] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    user_id: Optional[str] = Query(None, description="사용자 ID"),
    format: str = Query("excel", description="파일 형식 (excel, csv)")
):
    """
    사용 이력 내보내기

    - 최대 10,000건의 사용 이력 데이터 내보내기
    - 답변은 100자로 제한하여 파일 크기 최적화
    - 날짜 범위 필터: start_date, end_date
    - 사용자 필터: user_id
    - 형식: excel (기본), csv
    """
    # 쿼리 구성
    query = select(UsageHistory)

    # 날짜 범위 필터
    if start_date:
        from datetime import datetime, timezone
        start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        query = query.where(UsageHistory.created_at >= start_datetime)

    if end_date:
        from datetime import datetime, timezone
        end_datetime = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        query = query.where(UsageHistory.created_at <= end_datetime)

    # 사용자 필터
    if user_id:
        query = query.where(UsageHistory.user_id == user_id)

    # 최대 10,000건 제한
    query = query.limit(10000)

    result = await db.execute(query)
    history = result.scalars().all()

    # DataFrame 생성
    df = pd.DataFrame([{
        "ID": h.id,
        "사용자": h.user_id,
        "질문": h.question,
        "답변": h.answer[:100] + "..." if h.answer and len(h.answer) > 100 else (h.answer or ""),
        "응답시간(ms)": h.response_time,
        "모델": h.model_name,
        "세션ID": h.session_id,
        "생성일": h.created_at.strftime("%Y-%m-%d %H:%M:%S") if h.created_at else ""
    } for h in history])

    # 형식에 따라 내보내기
    if format == "csv":
        # CSV 파일 생성
        buffer = StringIO()
        df.to_csv(buffer, index=False, encoding="utf-8")
        buffer.seek(0)

        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=usage_history.csv"}
        )
    else:
        # Excel 파일 생성 (기본)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='사용이력')

        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=usage_history.xlsx"}
        )


@router.get("/satisfaction")
async def export_satisfaction(
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("satisfaction", "read"))
):
    """
    만족도 조사 엑셀 내보내기

    - 모든 만족도 조사 데이터를 Excel 파일로 내보내기
    """
    result = await db.execute(select(SatisfactionSurvey))
    surveys = result.scalars().all()

    # DataFrame 생성
    df = pd.DataFrame([{
        "ID": s.id,
        "사용자": s.user_id,
        "평점": s.rating,
        "피드백": s.feedback or "",
        "카테고리": s.category or "",
        "관련질문ID": s.related_question_id or "",
        "생성일": s.created_at.strftime("%Y-%m-%d %H:%M:%S") if s.created_at else ""
    } for s in surveys])

    # Excel 파일 생성
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='만족도조사')

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=satisfaction.xlsx"}
    )
