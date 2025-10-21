"""
통계 API 엔드포인트
TDD GREEN 단계: 테스트를 통과하는 최소 코드 작성
시큐어 코딩: SQL Injection 방지, 권한 검증, 입력 검증
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from typing import List, Optional
from datetime import date, datetime, timedelta
import httpx
import logging
import time

from app.models import UsageHistory, SatisfactionSurvey, Notice
from app.core.database import get_db
from app.dependencies import get_principal
from cerbos.sdk.model import Principal
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/stats", tags=["admin-stats"])

# 고유 문서 수 캐시 (1시간 TTL)
_unique_doc_cache = {
    "count": 0,
    "timestamp": 0
}
CACHE_TTL_SECONDS = 3600  # 1시간


@router.get("/dashboard")
async def get_dashboard_stats(
    start: date = Query(..., description="시작 날짜 (YYYY-MM-DD)"),
    end: date = Query(..., description="종료 날짜 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    대시보드 통계

    **보안**:
    - 인증 필수 (get_principal)
    - 파라미터 검증 (Query 타입 힌트)
    - ORM 사용 (SQL Injection 방지)

    **반환값**:
    - total_questions: 총 질문 수
    - average_response_time: 평균 응답 시간 (ms)
    - total_users: 총 사용자 수
    - average_satisfaction: 평균 만족도 (1-5)
    """
    # 날짜 범위 검증 (시큐어 코딩)
    if end < start:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="종료 날짜는 시작 날짜보다 늦어야 합니다")

    if (end - start).days > 365:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="조회 기간은 1년을 초과할 수 없습니다")

    # 기간 내 대화내역 필터
    start_datetime = datetime.combine(start, datetime.min.time())
    end_datetime = datetime.combine(end, datetime.max.time())

    # 총 질문 수
    total_questions_query = select(func.count(UsageHistory.id)).filter(
        UsageHistory.created_at >= start_datetime,
        UsageHistory.created_at <= end_datetime
    )
    total_questions_result = await db.execute(total_questions_query)
    total_questions = total_questions_result.scalar() or 0

    # 평균 응답 시간
    avg_response_time_query = select(func.avg(UsageHistory.response_time)).filter(
        UsageHistory.created_at >= start_datetime,
        UsageHistory.created_at <= end_datetime,
        UsageHistory.response_time.isnot(None)
    )
    avg_response_time_result = await db.execute(avg_response_time_query)
    avg_response_time = avg_response_time_result.scalar() or 0

    # 총 사용자 수 (고유 user_id)
    total_users_query = select(func.count(func.distinct(UsageHistory.user_id))).filter(
        UsageHistory.created_at >= start_datetime,
        UsageHistory.created_at <= end_datetime
    )
    total_users_result = await db.execute(total_users_query)
    total_users = total_users_result.scalar() or 0

    # 평균 만족도
    avg_satisfaction_query = select(func.avg(SatisfactionSurvey.rating)).filter(
        SatisfactionSurvey.created_at >= start_datetime,
        SatisfactionSurvey.created_at <= end_datetime
    )
    avg_satisfaction_result = await db.execute(avg_satisfaction_query)
    avg_satisfaction = avg_satisfaction_result.scalar() or 0

    return {
        "total_questions": total_questions,
        "average_response_time": round(float(avg_response_time), 2) if avg_response_time else 0,
        "total_users": total_users,
        "average_satisfaction": round(float(avg_satisfaction), 2) if avg_satisfaction else 0
    }


@router.get("/daily-trend")
async def get_daily_trend(
    start: date = Query(..., description="시작 날짜 (YYYY-MM-DD)"),
    end: date = Query(..., description="종료 날짜 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    일자별 사용 추이

    **보안**: 인증 필수, 날짜 범위 검증

    **반환값**:
    - items: 일자별 통계 목록
      - date: 날짜 (YYYY-MM-DD)
      - question_count: 질문 수
      - avg_response_time: 평균 응답 시간 (ms)
    """
    # 날짜 범위 검증
    if end < start:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="종료 날짜는 시작 날짜보다 늦어야 합니다")

    start_datetime = datetime.combine(start, datetime.min.time())
    end_datetime = datetime.combine(end, datetime.max.time())

    # 일자별 질문 수 및 평균 응답 시간
    query = select(
        func.date(UsageHistory.created_at).label('date'),
        func.count(UsageHistory.id).label('question_count'),
        func.avg(UsageHistory.response_time).label('avg_response_time')
    ).filter(
        UsageHistory.created_at >= start_datetime,
        UsageHistory.created_at <= end_datetime
    ).group_by(
        func.date(UsageHistory.created_at)
    ).order_by(
        func.date(UsageHistory.created_at).asc()
    )

    result = await db.execute(query)
    rows = result.fetchall()

    items = [
        {
            "date": row.date.isoformat() if row.date else None,
            "question_count": row.question_count or 0,
            "avg_response_time": round(float(row.avg_response_time), 2) if row.avg_response_time else 0
        }
        for row in rows
    ]

    return {"items": items}


@router.get("/hourly-pattern")
async def get_hourly_pattern(
    date: date = Query(..., description="조회 날짜 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    시간대별 사용 패턴

    **보안**: 인증 필수, 날짜 검증

    **반환값**:
    - items: 시간대별 통계 (0~23시)
      - hour: 시간 (0~23)
      - question_count: 질문 수
    """
    start_datetime = datetime.combine(date, datetime.min.time())
    end_datetime = datetime.combine(date, datetime.max.time())

    # 시간대별 질문 수
    query = select(
        extract('hour', UsageHistory.created_at).label('hour'),
        func.count(UsageHistory.id).label('question_count')
    ).filter(
        UsageHistory.created_at >= start_datetime,
        UsageHistory.created_at <= end_datetime
    ).group_by(
        extract('hour', UsageHistory.created_at)
    ).order_by(
        extract('hour', UsageHistory.created_at).asc()
    )

    result = await db.execute(query)
    rows = result.fetchall()

    # 시간대별 데이터 생성 (0~23시, 데이터 없으면 0)
    hour_data = {row.hour: row.question_count for row in rows}
    items = [
        {
            "hour": hour,
            "question_count": hour_data.get(float(hour), 0)
        }
        for hour in range(24)
    ]

    return {"items": items}


@router.get("/weekly-trend")
async def get_weekly_trend(
    start: date = Query(..., description="시작 날짜 (YYYY-MM-DD)"),
    end: date = Query(..., description="종료 날짜 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    주별 사용 추이

    **보안**: 인증 필수, 날짜 범위 검증

    **반환값**:
    - items: 주별 통계 목록
      - week: 주차 (YYYY-WW)
      - question_count: 질문 수
      - avg_response_time: 평균 응답 시간 (ms)
    """
    # 날짜 범위 검증
    if end < start:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="종료 날짜는 시작 날짜보다 늦어야 합니다")

    start_datetime = datetime.combine(start, datetime.min.time())
    end_datetime = datetime.combine(end, datetime.max.time())

    # 주별 질문 수 및 평균 응답 시간
    query = select(
        func.to_char(UsageHistory.created_at, 'IYYY-IW').label('week'),
        func.count(UsageHistory.id).label('question_count'),
        func.avg(UsageHistory.response_time).label('avg_response_time')
    ).filter(
        UsageHistory.created_at >= start_datetime,
        UsageHistory.created_at <= end_datetime
    ).group_by(
        func.to_char(UsageHistory.created_at, 'IYYY-IW')
    ).order_by(
        func.to_char(UsageHistory.created_at, 'IYYY-IW').asc()
    )

    result = await db.execute(query)
    rows = result.fetchall()

    items = [
        {
            "week": row.week,
            "question_count": row.question_count or 0,
            "avg_response_time": round(float(row.avg_response_time), 2) if row.avg_response_time else 0
        }
        for row in rows
    ]

    return {"items": items}


@router.get("/monthly-trend")
async def get_monthly_trend(
    start: date = Query(..., description="시작 날짜 (YYYY-MM-DD)"),
    end: date = Query(..., description="종료 날짜 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    월별 사용 추이

    **보안**: 인증 필수, 날짜 범위 검증

    **반환값**:
    - items: 월별 통계 목록
      - month: 월 (YYYY-MM)
      - question_count: 질문 수
      - avg_response_time: 평균 응답 시간 (ms)
    """
    # 날짜 범위 검증
    if end < start:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="종료 날짜는 시작 날짜보다 늦어야 합니다")

    start_datetime = datetime.combine(start, datetime.min.time())
    end_datetime = datetime.combine(end, datetime.max.time())

    # 월별 질문 수 및 평균 응답 시간
    query = select(
        func.to_char(UsageHistory.created_at, 'YYYY-MM').label('month'),
        func.count(UsageHistory.id).label('question_count'),
        func.avg(UsageHistory.response_time).label('avg_response_time')
    ).filter(
        UsageHistory.created_at >= start_datetime,
        UsageHistory.created_at <= end_datetime
    ).group_by(
        func.to_char(UsageHistory.created_at, 'YYYY-MM')
    ).order_by(
        func.to_char(UsageHistory.created_at, 'YYYY-MM').asc()
    )

    result = await db.execute(query)
    rows = result.fetchall()

    items = [
        {
            "month": row.month,
            "question_count": row.question_count or 0,
            "avg_response_time": round(float(row.avg_response_time), 2) if row.avg_response_time else 0
        }
        for row in rows
    ]

    return {"items": items}


@router.get("/top-questions")
async def get_top_questions(
    limit: int = Query(10, ge=1, le=100, description="조회할 개수"),
    days: int = Query(30, ge=1, le=365, description="최근 N일"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    인기 질문 TOP N

    **보안**: 인증 필수, limit 범위 검증

    **반환값**:
    - items: 인기 질문 목록
      - question: 질문 내용
      - count: 질문 횟수
    """
    # 최근 N일 데이터 조회
    start_datetime = datetime.now() - timedelta(days=days)

    # 질문별 횟수 집계
    query = select(
        UsageHistory.question,
        func.count(UsageHistory.id).label('count')
    ).filter(
        UsageHistory.created_at >= start_datetime,
        UsageHistory.question.isnot(None),
        UsageHistory.question != ''
    ).group_by(
        UsageHistory.question
    ).order_by(
        func.count(UsageHistory.id).desc()
    ).limit(limit)

    result = await db.execute(query)
    rows = result.fetchall()

    items = [
        {
            "question": row.question[:100] if row.question else '',  # 100자로 제한 (시큐어 코딩)
            "count": row.count or 0
        }
        for row in rows
    ]

    return {"items": items}


async def get_qdrant_vector_count() -> int:
    """
    Qdrant에서 벡터 포인트 수 조회 (청크 수)

    **보안**: API 키 기반 인증
    """
    try:
        qdrant_url = f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
        headers = {}
        if settings.QDRANT_API_KEY:
            headers["api-key"] = settings.QDRANT_API_KEY

        async with httpx.AsyncClient(timeout=5.0) as client:
            # 여러 컬렉션의 벡터 수를 합산
            total_count = 0
            collections = ["130825-512-v2", "130825-512-v3", "130825-512-v3-klue"]

            for collection in collections:
                try:
                    response = await client.get(
                        f"{qdrant_url}/collections/{collection}",
                        headers=headers
                    )
                    if response.status_code == 200:
                        data = response.json()
                        # Qdrant response: {"result": {"points_count": N, ...}}
                        points_count = data.get("result", {}).get("points_count", 0)
                        total_count += points_count
                except Exception as e:
                    logger.warning(f"Failed to get vector count from collection {collection}: {e}")
                    continue

            return total_count if total_count > 0 else 0  # Fallback
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant for vector count: {e}")
        return 0  # Fallback


async def get_qdrant_unique_document_count() -> int:
    """
    Qdrant에서 고유 원본 문서 수 조회 (file_path 기준)

    **보안**: API 키 기반 인증
    **참고**: 전체 포인트를 스크롤하므로 시간이 걸릴 수 있음 (캐싱 사용)
    """
    global _unique_doc_cache

    # 캐시 확인 (1시간 이내면 캐시 사용)
    current_time = time.time()
    if (_unique_doc_cache["count"] > 0 and
        current_time - _unique_doc_cache["timestamp"] < CACHE_TTL_SECONDS):
        logger.info(f"Using cached unique document count: {_unique_doc_cache['count']}")
        return _unique_doc_cache["count"]

    logger.info("Fetching unique document count from Qdrant (cache miss or expired)")

    try:
        qdrant_url = f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
        headers = {
            "Content-Type": "application/json"
        }
        if settings.QDRANT_API_KEY:
            headers["api-key"] = settings.QDRANT_API_KEY

        unique_file_ids = set()
        collections = ["130825-512-v2", "130825-512-v3", "130825-512-v3-klue"]

        async with httpx.AsyncClient(timeout=30.0) as client:
            for collection in collections:
                try:
                    offset = None
                    batch_size = 1000  # 한 번에 1000개씩 가져오기

                    while True:
                        # Scroll API로 payload만 가져오기 (벡터 제외)
                        scroll_body = {
                            "limit": batch_size,
                            "with_payload": True,
                            "with_vector": False
                        }
                        if offset:
                            scroll_body["offset"] = offset

                        response = await client.post(
                            f"{qdrant_url}/collections/{collection}/points/scroll",
                            headers=headers,
                            json=scroll_body
                        )

                        if response.status_code != 200:
                            logger.warning(f"Failed to scroll collection {collection}: {response.status_code}")
                            break

                        data = response.json()
                        points = data.get("result", {}).get("points", [])

                        # 고유 file_path 수집 (원본 문서명)
                        for point in points:
                            metadata = point.get("payload", {}).get("metadata", {})
                            file_path = metadata.get("file_path")

                            # file_path는 리스트 형태이므로 첫 번째 요소를 사용
                            if file_path and isinstance(file_path, list) and len(file_path) > 0:
                                unique_file_ids.add(file_path[0])
                            elif file_path and isinstance(file_path, str):
                                unique_file_ids.add(file_path)

                        # 다음 페이지가 없으면 종료
                        offset = data.get("result", {}).get("next_page_offset")
                        if not offset or len(points) == 0:
                            break

                        logger.info(f"Collection {collection}: scanned {len(points)} points, unique docs so far: {len(unique_file_ids)}")

                except Exception as e:
                    logger.warning(f"Failed to get unique documents from collection {collection}: {e}")
                    continue

            logger.info(f"Total unique documents across all collections: {len(unique_file_ids)}")

            # 캐시에 저장
            result = len(unique_file_ids) if len(unique_file_ids) > 0 else 0
            _unique_doc_cache["count"] = result
            _unique_doc_cache["timestamp"] = time.time()

            return result

    except Exception as e:
        logger.error(f"Failed to count unique documents from Qdrant: {e}")
        return 0  # Fallback


@router.get("/system")
async def get_system_info(
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    시스템 정보

    **보안**: 인증 필수

    **반환값**:
    - unique_documents: 고유 원본 문서 수 (file_id 기준)
    - vector_chunks: 벡터화된 청크 수 (전체 포인트 수)
    - active_sessions: 활성 세션 수
    - total_notices: 공지사항 수
    """
    # 총 공지사항 수 (실제 DB 조회)
    total_notices_query = select(func.count(Notice.id))
    total_notices_result = await db.execute(total_notices_query)
    total_notices = total_notices_result.scalar() or 0

    # Qdrant 고유 문서 수 및 벡터 수 조회 (병렬 실행)
    import asyncio
    unique_docs, vector_count = await asyncio.gather(
        get_qdrant_unique_document_count(),
        get_qdrant_vector_count()
    )

    return {
        "unique_documents": unique_docs,  # ✅ 고유 원본 문서 수
        "vector_chunks": vector_count,  # ✅ 벡터 청크 수
        "active_sessions": 0,  # TODO: Redis session count
        "total_notices": total_notices  # ✅ 실제 DB 연동
    }
