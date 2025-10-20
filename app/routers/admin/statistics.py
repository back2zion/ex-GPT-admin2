"""
통계 API 엔드포인트
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract
from datetime import datetime, date, timedelta
from typing import List, Dict
from collections import defaultdict

from app.models import UsageHistory, Document
from app.core.database import get_db
from app.dependencies import get_principal
from cerbos.sdk.model import Principal

router = APIRouter(prefix="/api/v1/admin/statistics", tags=["admin-statistics"])


@router.get("/daily")
async def get_daily_statistics(
    start: date = Query(..., description="시작일 (YYYY-MM-DD)"),
    end: date = Query(..., description="종료일 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    일자별 통계 조회

    - 기간 내 일자별 질문수
    - 기간 내 일자별 오류신고 (만족도 1-2점)
    - 카테고리별 문서 현황 및 질문 분류
    - 통계 요약
    """
    # 1. 일자별 질문수 집계
    daily_query = select(
        func.date(UsageHistory.created_at).label('date'),
        func.count(UsageHistory.id).label('count')
    ).filter(
        and_(
            func.date(UsageHistory.created_at) >= start,
            func.date(UsageHistory.created_at) <= end
        )
    ).group_by(func.date(UsageHistory.created_at)).order_by('date')

    daily_result = await db.execute(daily_query)
    daily_counts = {str(row.date): row.count for row in daily_result}

    # 2. 일자별 오류신고 (만족도가 낮은 것들) - satisfaction_surveys 테이블이 있다고 가정
    # 현재는 Mock 데이터 사용 (실제 오류신고 테이블이 있다면 여기서 조회)

    # 날짜 범위 생성
    date_range = []
    current = start
    while current <= end:
        date_range.append(str(current))
        current += timedelta(days=1)

    # 일자별 데이터 구성
    daily_data = {
        "labels": date_range,
        "questions": [daily_counts.get(d, 0) for d in date_range],
        "errors": [0 for _ in date_range]  # TODO: 실제 오류신고 데이터 연결
    }

    # 3. 카테고리별 문서 통계
    doc_type_query = select(
        Document.document_type,
        func.count(Document.id).label('count')
    ).group_by(Document.document_type)

    doc_type_result = await db.execute(doc_type_query)
    doc_counts = {row.document_type: row.count for row in doc_type_result}

    # 카테고리 한글 라벨
    category_labels = {
        'law': '법령',
        'regulation': '사규',
        'standard': '업무기준',
        'manual': '매뉴얼',
        'other': '기타'
    }

    # 카테고리별 질문 수 (실제로는 usage_history의 메타데이터에서 추출해야 함)
    # 현재는 문서 수에 비례하여 Mock 데이터 생성
    category_data = {
        "labels": [],
        "documents": [],
        "questions": []
    }

    for doc_type, korean_label in category_labels.items():
        count = doc_counts.get(doc_type, 0)
        category_data["labels"].append(korean_label)
        category_data["documents"].append(count)
        # Mock: 문서 수의 20% 정도를 질문 수로 가정
        category_data["questions"].append(int(count * 0.2))

    # 4. 통계 요약
    total_questions_query = select(func.count(UsageHistory.id)).filter(
        and_(
            func.date(UsageHistory.created_at) >= start,
            func.date(UsageHistory.created_at) <= end
        )
    )
    total_questions_result = await db.execute(total_questions_query)
    total_questions = total_questions_result.scalar() or 0

    # 평균 응답시간
    avg_response_query = select(func.avg(UsageHistory.response_time)).filter(
        and_(
            func.date(UsageHistory.created_at) >= start,
            func.date(UsageHistory.created_at) <= end,
            UsageHistory.response_time.isnot(None)
        )
    )
    avg_response_result = await db.execute(avg_response_query)
    avg_response_time = avg_response_result.scalar()

    # 밀리초를 초로 변환
    if avg_response_time:
        avg_response_time = round(avg_response_time / 1000, 2)
    else:
        avg_response_time = 0

    # 총 문서 수
    total_docs_query = select(func.count(Document.id))
    total_docs_result = await db.execute(total_docs_query)
    total_documents = total_docs_result.scalar() or 0

    # 최다 카테고리
    if doc_counts:
        most_used_category = max(doc_counts.items(), key=lambda x: x[1])[0]
        most_used_category = category_labels.get(most_used_category, most_used_category)
    else:
        most_used_category = "-"

    summary_data = {
        "totalQuestions": total_questions,
        "totalErrors": 0,  # TODO: 실제 오류신고 데이터
        "totalDocuments": total_documents,
        "avgResponseTime": avg_response_time,
        "peakHour": "14:00",  # TODO: 실제 피크 시간 계산
        "mostUsedCategory": most_used_category
    }

    return {
        "daily": daily_data,
        "category": category_data,
        "summary": summary_data
    }


@router.get("/hourly")
async def get_hourly_statistics(
    date: date = Query(..., description="조회일 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    시간대별 검색건수 통계

    - 특정 날짜의 시간대별 질문 수
    """
    # 시간대별 질문 수 집계
    hourly_query = select(
        extract('hour', UsageHistory.created_at).label('hour'),
        func.count(UsageHistory.id).label('count')
    ).filter(
        func.date(UsageHistory.created_at) == date
    ).group_by('hour').order_by('hour')

    hourly_result = await db.execute(hourly_query)
    hourly_counts = {int(row.hour): row.count for row in hourly_result}

    # 0-23시 전체 데이터 생성
    hourly_data = {
        "labels": [f"{h:02d}" for h in range(24)],
        "searches": [hourly_counts.get(h, 0) for h in range(24)]
    }

    return hourly_data


@router.get("/summary")
async def get_statistics_summary(
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    전체 통계 요약

    - 총 질문 수
    - 총 문서 수
    - 평균 응답시간
    - 오늘 질문 수
    """
    today = date.today()

    # 총 질문 수
    total_questions_query = select(func.count(UsageHistory.id))
    total_questions_result = await db.execute(total_questions_query)
    total_questions = total_questions_result.scalar() or 0

    # 오늘 질문 수
    today_questions_query = select(func.count(UsageHistory.id)).filter(
        func.date(UsageHistory.created_at) == today
    )
    today_questions_result = await db.execute(today_questions_query)
    today_questions = today_questions_result.scalar() or 0

    # 총 문서 수
    total_docs_query = select(func.count(Document.id))
    total_docs_result = await db.execute(total_docs_query)
    total_documents = total_docs_result.scalar() or 0

    # 평균 응답시간
    avg_response_query = select(func.avg(UsageHistory.response_time)).filter(
        UsageHistory.response_time.isnot(None)
    )
    avg_response_result = await db.execute(avg_response_query)
    avg_response_time = avg_response_result.scalar()

    if avg_response_time:
        avg_response_time = round(avg_response_time / 1000, 2)
    else:
        avg_response_time = 0

    return {
        "totalQuestions": total_questions,
        "todayQuestions": today_questions,
        "totalDocuments": total_documents,
        "avgResponseTime": avg_response_time
    }
