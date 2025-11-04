"""
통계 API 엔드포인트
TDD GREEN 단계: 테스트를 통과하는 최소 코드 작성
시큐어 코딩: SQL Injection 방지, 권한 검증, 입력 검증
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, literal_column
from typing import List, Optional
from datetime import date, datetime, timedelta
import httpx
import logging
import time
import psutil
import subprocess
import asyncpg
import os
from typing import Dict, Any

from app.models import UsageHistory, SatisfactionSurvey, Notice
from app.core.database import get_db
from app.dependencies import get_principal
from cerbos.sdk.model import Principal
from app.core.config import settings

logger = logging.getLogger(__name__)

# EDB 설정
EDB_HOST = os.getenv("EDB_HOST", "host.docker.internal")
EDB_PORT = int(os.getenv("EDB_PORT", "5444"))
EDB_DATABASE = os.getenv("EDB_DATABASE", "AGENAI")
EDB_USER = os.getenv("EDB_USER", "wisenut_dev")
EDB_PASSWORD = os.getenv("EDB_PASSWORD", "express!12")

# Server monitoring cache (30 seconds TTL for real-time data)
_server_stats_cache = {
    "cpu_history": {"data": [], "timestamp": 0},
    "memory_history": {"data": [], "timestamp": 0},
}
SERVER_STATS_CACHE_TTL = 30  # 30 seconds

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
    # Note: literal_column() avoids asyncpg parameter binding issues with to_char()
    query = select(
        literal_column("to_char(usage_history.created_at, 'IYYY-IW')").label('week'),
        func.count(UsageHistory.id).label('question_count'),
        func.avg(UsageHistory.response_time).label('avg_response_time')
    ).filter(
        UsageHistory.created_at >= start_datetime,
        UsageHistory.created_at <= end_datetime
    ).group_by(
        literal_column("to_char(usage_history.created_at, 'IYYY-IW')")
    ).order_by(
        literal_column("to_char(usage_history.created_at, 'IYYY-IW')")
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
    # Note: literal_column() avoids asyncpg parameter binding issues with to_char()
    query = select(
        literal_column("to_char(usage_history.created_at, 'YYYY-MM')").label('month'),
        func.count(UsageHistory.id).label('question_count'),
        func.avg(UsageHistory.response_time).label('avg_response_time')
    ).filter(
        UsageHistory.created_at >= start_datetime,
        UsageHistory.created_at <= end_datetime
    ).group_by(
        literal_column("to_char(usage_history.created_at, 'YYYY-MM')")
    ).order_by(
        literal_column("to_char(usage_history.created_at, 'YYYY-MM')")
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


# =============================================================================
# EDB Helper Functions
# =============================================================================

async def get_edb_connection():
    """EDB 데이터베이스 연결 생성"""
    try:
        conn = await asyncpg.connect(
            host=EDB_HOST,
            port=EDB_PORT,
            database=EDB_DATABASE,
            user=EDB_USER,
            password=EDB_PASSWORD
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to EDB: {e}")
        raise


async def get_edb_document_count() -> int:
    """
    EDB에서 활성 문서 수 조회

    Returns:
        int: wisenut.doc_bas_lst에서 use_yn='Y'인 문서 수
    """
    conn = None
    try:
        conn = await get_edb_connection()

        # 활성 문서만 조회 (use_yn = 'Y')
        query = """
            SELECT COUNT(*)
            FROM wisenut.doc_bas_lst
            WHERE use_yn = 'Y'
        """
        count = await conn.fetchval(query)
        return count or 0

    except Exception as e:
        logger.error(f"Failed to get EDB document count: {e}")
        return 0
    finally:
        if conn:
            await conn.close()


# =============================================================================
# Qdrant Helper Functions
# =============================================================================

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
    - unique_documents: 고유 원본 문서 수 (EDB 기준)
    - vector_chunks: 벡터화된 청크 수 (PostgreSQL 기준)
    - active_sessions: 활성 세션 수
    - total_notices: 공지사항 수
    """
    # 총 공지사항 수 (실제 DB 조회)
    total_notices_query = select(func.count(Notice.id))
    total_notices_result = await db.execute(total_notices_query)
    total_notices = total_notices_result.scalar() or 0

    # Qdrant에서 실제 벡터 청크 수 조회 (모든 컬렉션 합산)
    vector_count = await get_qdrant_vector_count()

    # EDB에서 실제 문서 수 조회
    unique_docs = await get_edb_document_count()

    return {
        "unique_documents": unique_docs,  # ✅ EDB wisenut.doc_bas_lst (use_yn='Y')
        "vector_chunks": vector_count,  # ✅ Qdrant 실제 벡터 개수
        "active_sessions": 0,  # TODO: Redis session count
        "total_notices": total_notices  # ✅ 실제 DB 연동
    }


# =============================================================================
# Server Monitoring Endpoints
# =============================================================================

@router.get("/server/summary")
async def get_server_summary(
    principal: Principal = Depends(get_principal)
):
    """
    서버 전체 요약 정보

    **보안**: 인증 필수

    **반환값**:
    - cpu_percent: 현재 CPU 사용률 (%)
    - memory_percent: 현재 메모리 사용률 (%)
    - disk_percent: 디스크 사용률 (%)
    - uptime_seconds: 시스템 가동 시간 (초)
    """
    try:
        # CPU 사용률 (1초 간격 측정)
        cpu_percent = psutil.cpu_percent(interval=1)

        # 메모리 사용률
        memory = psutil.virtual_memory()

        # 디스크 사용률 (루트 파일시스템)
        disk = psutil.disk_usage('/')

        # 시스템 부팅 시간
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time

        return {
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory.percent, 2),
            "disk_percent": round(disk.percent, 2),
            "uptime_seconds": int(uptime_seconds)
        }
    except Exception as e:
        logger.error(f"Failed to get server summary: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Failed to retrieve server summary: {str(e)}")


@router.get("/server/cpu-history")
async def get_cpu_history(
    principal: Principal = Depends(get_principal)
):
    """
    CPU 사용 이력 (최근 10개 데이터 포인트)

    **보안**: 인증 필수

    **반환값**:
    - items: CPU 사용률 배열
      - timestamp: 타임스탬프 (ISO 8601)
      - cpu_percent: CPU 사용률 (%)
      - cpu_count: CPU 코어 수
    """
    try:
        current_time = time.time()

        # 캐시 확인
        if (current_time - _server_stats_cache["cpu_history"]["timestamp"] < SERVER_STATS_CACHE_TTL
            and len(_server_stats_cache["cpu_history"]["data"]) > 0):
            return {"items": _server_stats_cache["cpu_history"]["data"]}

        # CPU 정보 수집
        cpu_percent = psutil.cpu_percent(interval=1, percpu=False)
        cpu_count = psutil.cpu_count()

        # 새 데이터 포인트 생성
        data_point = {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": round(cpu_percent, 2),
            "cpu_count": cpu_count
        }

        # 히스토리에 추가 (최대 10개 유지)
        history = _server_stats_cache["cpu_history"]["data"]
        history.append(data_point)
        if len(history) > 10:
            history = history[-10:]

        # 캐시 업데이트
        _server_stats_cache["cpu_history"] = {
            "data": history,
            "timestamp": current_time
        }

        return {"items": history}

    except Exception as e:
        logger.error(f"Failed to get CPU history: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Failed to retrieve CPU history: {str(e)}")


@router.get("/server/memory-history")
async def get_memory_history(
    principal: Principal = Depends(get_principal)
):
    """
    메모리 사용 이력 (최근 10개 데이터 포인트)

    **보안**: 인증 필수

    **반환값**:
    - items: 메모리 사용률 배열
      - timestamp: 타임스탬프 (ISO 8601)
      - memory_percent: 메모리 사용률 (%)
      - memory_used_gb: 사용 중인 메모리 (GB)
      - memory_total_gb: 전체 메모리 (GB)
    """
    try:
        current_time = time.time()

        # 캐시 확인
        if (current_time - _server_stats_cache["memory_history"]["timestamp"] < SERVER_STATS_CACHE_TTL
            and len(_server_stats_cache["memory_history"]["data"]) > 0):
            return {"items": _server_stats_cache["memory_history"]["data"]}

        # 메모리 정보 수집
        memory = psutil.virtual_memory()

        # 새 데이터 포인트 생성
        data_point = {
            "timestamp": datetime.now().isoformat(),
            "memory_percent": round(memory.percent, 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_total_gb": round(memory.total / (1024**3), 2)
        }

        # 히스토리에 추가 (최대 10개 유지)
        history = _server_stats_cache["memory_history"]["data"]
        history.append(data_point)
        if len(history) > 10:
            history = history[-10:]

        # 캐시 업데이트
        _server_stats_cache["memory_history"] = {
            "data": history,
            "timestamp": current_time
        }

        return {"items": history}

    except Exception as e:
        logger.error(f"Failed to get memory history: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memory history: {str(e)}")


@router.get("/server/disk")
async def get_disk_usage(
    principal: Principal = Depends(get_principal)
):
    """
    디스크 사용량 정보

    **보안**: 인증 필수

    **반환값**:
    - items: 디스크 파티션별 사용량 배열
      - mountpoint: 마운트 포인트
      - total_gb: 전체 용량 (GB)
      - used_gb: 사용 중 용량 (GB)
      - free_gb: 남은 용량 (GB)
      - percent: 사용률 (%)
    """
    try:
        partitions = []

        # 주요 마운트 포인트만 조회
        for partition in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partitions.append({
                    "mountpoint": partition.mountpoint,
                    "device": partition.device,
                    "fstype": partition.fstype,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent": round(usage.percent, 2)
                })
            except (PermissionError, OSError):
                # 일부 마운트 포인트는 접근 권한이 없을 수 있음
                continue

        return {"items": partitions}

    except Exception as e:
        logger.error(f"Failed to get disk usage: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Failed to retrieve disk usage: {str(e)}")


@router.get("/server/gpu")
async def get_gpu_info(
    principal: Principal = Depends(get_principal)
):
    """
    GPU 정보 (nvidia-smi 사용)

    **보안**: 인증 필수

    **반환값**:
    - items: GPU 배열
      - index: GPU 인덱스
      - name: GPU 모델명
      - utilization_percent: GPU 사용률 (%)
      - memory_used_mb: 사용 중인 메모리 (MB)
      - memory_total_mb: 전체 메모리 (MB)
      - temperature_c: 온도 (°C)
    """
    try:
        # nvidia-smi 명령어 실행
        result = subprocess.run(
            [
                'nvidia-smi',
                '--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu',
                '--format=csv,noheader,nounits'
            ],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            # GPU가 없거나 nvidia-smi가 설치되지 않은 경우
            return {"items": [], "available": False}

        # CSV 파싱
        gpus = []
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue

            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 6:
                gpus.append({
                    "index": int(parts[0]),
                    "name": parts[1],
                    "utilization_percent": float(parts[2]),
                    "memory_used_mb": float(parts[3]),
                    "memory_total_mb": float(parts[4]),
                    "temperature_c": float(parts[5])
                })

        return {"items": gpus, "available": True}

    except FileNotFoundError:
        # nvidia-smi가 설치되지 않음
        return {"items": [], "available": False, "error": "nvidia-smi not found"}
    except subprocess.TimeoutExpired:
        logger.error("nvidia-smi command timed out")
        return {"items": [], "available": False, "error": "Command timed out"}
    except Exception as e:
        logger.error(f"Failed to get GPU info: {e}")
        return {"items": [], "available": False, "error": str(e)}


@router.get("/server/docker")
async def get_docker_stats(
    principal: Principal = Depends(get_principal)
):
    """
    Docker 컨테이너 통계

    **보안**: 인증 필수

    **반환값**:
    - items: 컨테이너 배열
      - id: 컨테이너 ID (짧은 형식)
      - name: 컨테이너 이름
      - status: 상태 (running, exited 등)
      - cpu_percent: CPU 사용률 (%)
      - memory_usage_mb: 메모리 사용량 (MB)
      - memory_limit_mb: 메모리 제한 (MB)
    """
    try:
        # docker ps 명령어 실행 (실행 중인 컨테이너만)
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.ID}}|{{.Names}}|{{.Status}}'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return {"items": [], "available": False, "error": "Docker not available"}

        containers = []
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue

            parts = line.split('|')
            if len(parts) >= 3:
                container_id = parts[0].strip()
                container_name = parts[1].strip()
                status = parts[2].strip()

                # docker stats 명령어로 실시간 통계 가져오기 (no-stream으로 한 번만 조회)
                try:
                    stats_result = subprocess.run(
                        ['docker', 'stats', container_id, '--no-stream', '--format', '{{.CPUPerc}}|{{.MemUsage}}'],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )

                    if stats_result.returncode == 0:
                        stats_line = stats_result.stdout.strip()
                        stats_parts = stats_line.split('|')

                        if len(stats_parts) >= 2:
                            # CPU 사용률 파싱 (예: "2.50%" -> 2.50)
                            cpu_str = stats_parts[0].replace('%', '').strip()
                            cpu_percent = float(cpu_str) if cpu_str else 0.0

                            # 메모리 사용량 파싱 (예: "256MiB / 4GiB")
                            mem_str = stats_parts[1].strip()
                            mem_parts = mem_str.split('/')

                            # 메모리 사용량 (MB 단위로 변환)
                            mem_used_str = mem_parts[0].strip()
                            mem_used_mb = parse_memory_size(mem_used_str)

                            # 메모리 제한 (MB 단위로 변환)
                            mem_limit_mb = 0
                            if len(mem_parts) > 1:
                                mem_limit_str = mem_parts[1].strip()
                                mem_limit_mb = parse_memory_size(mem_limit_str)

                            containers.append({
                                "id": container_id,
                                "name": container_name,
                                "status": status,
                                "cpu_percent": round(cpu_percent, 2),
                                "memory_usage_mb": round(mem_used_mb, 2),
                                "memory_limit_mb": round(mem_limit_mb, 2)
                            })
                except subprocess.TimeoutExpired:
                    logger.warning(f"Timeout getting stats for container {container_id}")
                    continue

        return {"items": containers, "available": True}

    except FileNotFoundError:
        return {"items": [], "available": False, "error": "Docker command not found"}
    except subprocess.TimeoutExpired:
        return {"items": [], "available": False, "error": "Command timed out"}
    except Exception as e:
        logger.error(f"Failed to get Docker stats: {e}")
        return {"items": [], "available": False, "error": str(e)}


def parse_memory_size(mem_str: str) -> float:
    """
    메모리 크기 문자열을 MB로 변환

    예: "256MiB" -> 256.0
        "4GiB" -> 4096.0
        "512KiB" -> 0.5
    """
    mem_str = mem_str.strip().upper()

    # 숫자와 단위 분리
    import re
    match = re.match(r'([\d.]+)\s*([KMGT]I?B?)', mem_str)

    if not match:
        return 0.0

    value = float(match.group(1))
    unit = match.group(2)

    # MB로 변환
    if 'K' in unit:
        return value / 1024
    elif 'M' in unit:
        return value
    elif 'G' in unit:
        return value * 1024
    elif 'T' in unit:
        return value * 1024 * 1024
    else:
        return value
