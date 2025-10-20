"""
엑셀 내보내기 API 엔드포인트
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import pandas as pd
from io import BytesIO

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
    principal: Principal = Depends(require_permission("usage_history", "read"))
):
    """
    사용 이력 엑셀 내보내기

    - 최대 10,000건의 사용 이력 데이터 내보내기
    - 답변은 100자로 제한하여 파일 크기 최적화
    """
    result = await db.execute(select(UsageHistory).limit(10000))
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

    # Excel 파일 생성
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
