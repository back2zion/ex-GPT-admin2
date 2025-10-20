"""
통계 API 엔드포인트

보안 기능:
- Cerbos RBAC 기반 권한 검증
- SQL Injection 방지 (SQLAlchemy ORM)
- 날짜 형식 검증
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract, desc
from datetime import datetime, date, timedelta
from typing import List, Optional
from collections import defaultdict

from app.models import UsageHistory
from app.core.database import get_db
from app.dependencies import get_principal, get_cerbos_client, check_resource_permission
from cerbos.sdk.model import Principal, Resource
from cerbos.sdk.client import AsyncCerbosClient

router = APIRouter(prefix="/api/v1/admin/statistics", tags=["admin-statistics"])

# Date format constant
DATE_FORMAT = "%Y-%m-%d"


# Helper function to parse date
def _parse_date_param(date_str: str, param_name: str) -> date:
    """
    날짜 문자열을 date 객체로 변환

    Args:
        date_str: YYYY-MM-DD 형식의 날짜 문자열
        param_name: 파라미터 이름 (오류 메시지용)

    Returns:
        date: 파싱된 date 객체

    Raises:
        HTTPException: 날짜 형식이 잘못된 경우
    """
    try:
        return datetime.strptime(date_str, DATE_FORMAT).date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"{param_name} 형식이 잘못되었습니다 (YYYY-MM-DD 형식 필요): {date_str}"
        )


@router.get("/summary")
async def get_statistics_summary(
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal),
    cerbos: AsyncCerbosClient = Depends(get_cerbos_client)
):
    """
    전체 통계 요약

    - 총 질문 수
    - 평균 응답시간
    - 고유 사용자 수
    - 일평균 사용량

    **권한 필요**: statistics:read
    """
    # 권한 검증
    resource = Resource(id="summary", kind="statistics")
    await check_resource_permission(principal, resource, "read", cerbos)

    # 날짜 필터링
    query_filters = []
    if start_date:
        start_dt = _parse_date_param(start_date, "시작 날짜")
        query_filters.append(UsageHistory.created_at >= datetime.combine(start_dt, datetime.min.time()))

    if end_date:
        end_dt = _parse_date_param(end_date, "종료 날짜")
        query_filters.append(UsageHistory.created_at < datetime.combine(end_dt + timedelta(days=1), datetime.min.time()))

    # 총 질문 수
    total_questions_query = select(func.count(UsageHistory.id))
    if query_filters:
        total_questions_query = total_questions_query.filter(and_(*query_filters))

    total_questions_result = await db.execute(total_questions_query)
    total_questions = total_questions_result.scalar() or 0

    # 평균 응답시간 (밀리초)
    avg_response_query = select(func.avg(UsageHistory.response_time)).filter(
        UsageHistory.response_time.isnot(None)
    )
    if query_filters:
        avg_response_query = avg_response_query.filter(and_(*query_filters))

    avg_response_result = await db.execute(avg_response_query)
    avg_response_time = avg_response_result.scalar() or 0

    # 고유 사용자 수
    unique_users_query = select(func.count(func.distinct(UsageHistory.user_id)))
    if query_filters:
        unique_users_query = unique_users_query.filter(and_(*query_filters))

    unique_users_result = await db.execute(unique_users_query)
    unique_users = unique_users_result.scalar() or 0

    # 일평균 계산
    if start_date and end_date:
        start_dt = _parse_date_param(start_date, "시작 날짜")
        end_dt = _parse_date_param(end_date, "종료 날짜")
        days_diff = max((end_dt - start_dt).days + 1, 1)
    else:
        # 전체 기간에 대한 일평균 (첫 레코드부터 현재까지)
        first_record_query = select(func.min(UsageHistory.created_at))
        first_record_result = await db.execute(first_record_query)
        first_record_date = first_record_result.scalar()

        if first_record_date:
            days_diff = max((datetime.utcnow().date() - first_record_date.date()).days + 1, 1)
        else:
            days_diff = 1

    daily_average = round(total_questions / days_diff, 1)

    return {
        "total_questions": total_questions,
        "average_response_time": round(avg_response_time, 2),
        "unique_users": unique_users,
        "daily_average": daily_average
    }


@router.get("/hourly")
async def get_hourly_statistics(
    start_date: str = Query(..., description="시작 날짜 (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str = Query(..., description="종료 날짜 (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal),
    cerbos: AsyncCerbosClient = Depends(get_cerbos_client)
):
    """
    시간별 통계 조회

    **권한 필요**: statistics:read
    """
    # 권한 검증
    resource = Resource(id="hourly", kind="statistics")
    await check_resource_permission(principal, resource, "read", cerbos)

    start_dt = _parse_date_param(start_date, "시작 날짜")
    end_dt = _parse_date_param(end_date, "종료 날짜")

    # 시간별 집계
    hourly_query = select(
        extract('hour', UsageHistory.created_at).label('hour'),
        func.count(UsageHistory.id).label('count'),
        func.avg(UsageHistory.response_time).label('avg_response_time')
    ).filter(
        and_(
            UsageHistory.created_at >= datetime.combine(start_dt, datetime.min.time()),
            UsageHistory.created_at < datetime.combine(end_dt + timedelta(days=1), datetime.min.time())
        )
    ).group_by('hour').order_by('hour')

    result = await db.execute(hourly_query)

    hourly_stats = []
    for row in result:
        hourly_stats.append({
            "hour": int(row.hour),
            "count": row.count,
            "average_response_time": round(row.avg_response_time or 0, 2)
        })

    return hourly_stats


@router.get("/daily")
async def get_daily_statistics(
    start_date: str = Query(..., description="시작 날짜 (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str = Query(..., description="종료 날짜 (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal),
    cerbos: AsyncCerbosClient = Depends(get_cerbos_client)
):
    """
    일별 통계 조회

    **권한 필요**: statistics:read
    """
    # 권한 검증
    resource = Resource(id="daily", kind="statistics")
    await check_resource_permission(principal, resource, "read", cerbos)

    start_dt = _parse_date_param(start_date, "시작 날짜")
    end_dt = _parse_date_param(end_date, "종료 날짜")

    # 일별 집계
    daily_query = select(
        func.date(UsageHistory.created_at).label('date'),
        func.count(UsageHistory.id).label('count'),
        func.avg(UsageHistory.response_time).label('avg_response_time'),
        func.count(func.distinct(UsageHistory.user_id)).label('unique_users')
    ).filter(
        and_(
            func.date(UsageHistory.created_at) >= start_dt,
            func.date(UsageHistory.created_at) <= end_dt
        )
    ).group_by(func.date(UsageHistory.created_at)).order_by('date')

    result = await db.execute(daily_query)

    daily_stats = []
    for row in result:
        daily_stats.append({
            "date": str(row.date),
            "count": row.count,
            "average_response_time": round(row.avg_response_time or 0, 2),
            "unique_users": row.unique_users
        })

    return daily_stats


@router.get("/weekly")
async def get_weekly_statistics(
    weeks: int = Query(4, ge=1, le=52, description="조회할 주 수"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal),
    cerbos: AsyncCerbosClient = Depends(get_cerbos_client)
):
    """
    주별 통계 조회

    **권한 필요**: statistics:read
    """
    # 권한 검증
    resource = Resource(id="weekly", kind="statistics")
    await check_resource_permission(principal, resource, "read", cerbos)

    # 주별 데이터 생성
    weekly_stats = []
    today = date.today()

    for i in range(weeks):
        week_end = today - timedelta(days=i * 7)
        week_start = week_end - timedelta(days=6)

        # 해당 주의 데이터 집계
        week_query = select(
            func.count(UsageHistory.id).label('count'),
            func.avg(UsageHistory.response_time).label('avg_response_time')
        ).filter(
            and_(
                func.date(UsageHistory.created_at) >= week_start,
                func.date(UsageHistory.created_at) <= week_end
            )
        )

        result = await db.execute(week_query)
        row = result.one()

        weekly_stats.insert(0, {
            "week_start": str(week_start),
            "week_end": str(week_end),
            "count": row.count or 0,
            "average_response_time": round(row.avg_response_time or 0, 2)
        })

    return weekly_stats


@router.get("/monthly")
async def get_monthly_statistics(
    months: int = Query(12, ge=1, le=24, description="조회할 월 수"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal),
    cerbos: AsyncCerbosClient = Depends(get_cerbos_client)
):
    """
    월별 통계 조회

    **권한 필요**: statistics:read
    """
    # 권한 검증
    resource = Resource(id="monthly", kind="statistics")
    await check_resource_permission(principal, resource, "read", cerbos)

    # 월별 집계
    monthly_query = select(
        extract('year', UsageHistory.created_at).label('year'),
        extract('month', UsageHistory.created_at).label('month'),
        func.count(UsageHistory.id).label('count'),
        func.avg(UsageHistory.response_time).label('avg_response_time')
    ).group_by('year', 'month').order_by(desc('year'), desc('month')).limit(months)

    result = await db.execute(monthly_query)

    monthly_stats = []
    for row in result:
        monthly_stats.append({
            "year": int(row.year),
            "month": int(row.month),
            "count": row.count,
            "average_response_time": round(row.avg_response_time or 0, 2)
        })

    # 최신순 정렬을 역순으로 (오래된 것부터)
    monthly_stats.reverse()

    return monthly_stats


@router.get("/by-department")
async def get_statistics_by_department(
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal),
    cerbos: AsyncCerbosClient = Depends(get_cerbos_client)
):
    """
    부서별 통계 조회

    usage_metadata.department에서 부서 정보 추출

    **권한 필요**: statistics:read
    """
    # 권한 검증
    resource = Resource(id="by-department", kind="statistics")
    await check_resource_permission(principal, resource, "read", cerbos)

    # 날짜 필터링
    query_filters = []
    if start_date:
        start_dt = _parse_date_param(start_date, "시작 날짜")
        query_filters.append(UsageHistory.created_at >= datetime.combine(start_dt, datetime.min.time()))

    if end_date:
        end_dt = _parse_date_param(end_date, "종료 날짜")
        query_filters.append(UsageHistory.created_at < datetime.combine(end_dt + timedelta(days=1), datetime.min.time()))

    # 모든 사용 이력 조회
    usage_query = select(UsageHistory)
    if query_filters:
        usage_query = usage_query.filter(and_(*query_filters))

    result = await db.execute(usage_query)
    all_usage = result.scalars().all()

    # Python에서 부서별로 집계
    dept_stats_dict = defaultdict(lambda: {"count": 0, "total_response_time": 0, "response_times": []})

    for usage in all_usage:
        # usage_metadata에서 부서 정보 추출
        department = "미분류"
        if usage.usage_metadata and isinstance(usage.usage_metadata, dict):
            department = usage.usage_metadata.get("department", "미분류")

        dept_stats_dict[department]["count"] += 1
        if usage.response_time:
            dept_stats_dict[department]["response_times"].append(usage.response_time)

    # 결과 생성
    dept_stats = []
    for dept, stats in dept_stats_dict.items():
        avg_response = (
            sum(stats["response_times"]) / len(stats["response_times"])
            if stats["response_times"] else 0
        )
        dept_stats.append({
            "department": dept,
            "department_name": dept,
            "count": stats["count"],
            "average_response_time": round(avg_response, 2)
        })

    # count 기준으로 정렬 후 상위 20개
    dept_stats.sort(key=lambda x: x["count"], reverse=True)
    return dept_stats[:20]


@router.get("/by-model")
async def get_statistics_by_model(
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal),
    cerbos: AsyncCerbosClient = Depends(get_cerbos_client)
):
    """
    모델별 통계 조회

    **권한 필요**: statistics:read
    """
    # 권한 검증
    resource = Resource(id="by-model", kind="statistics")
    await check_resource_permission(principal, resource, "read", cerbos)

    # 날짜 필터링
    query_filters = []
    if start_date:
        start_dt = _parse_date_param(start_date, "시작 날짜")
        query_filters.append(UsageHistory.created_at >= datetime.combine(start_dt, datetime.min.time()))

    if end_date:
        end_dt = _parse_date_param(end_date, "종료 날짜")
        query_filters.append(UsageHistory.created_at < datetime.combine(end_dt + timedelta(days=1), datetime.min.time()))

    # 모델별 집계
    model_query = select(
        UsageHistory.model_name,
        func.count(UsageHistory.id).label('count'),
        func.avg(UsageHistory.response_time).label('avg_response_time'),
        func.sum(UsageHistory.response_time).label('total_response_time')
    ).filter(
        UsageHistory.model_name.isnot(None)
    )

    if query_filters:
        model_query = model_query.filter(and_(*query_filters))

    model_query = model_query.group_by(UsageHistory.model_name).order_by(desc('count'))

    result = await db.execute(model_query)

    model_stats = []
    for row in result:
        model_stats.append({
            "model_name": row.model_name or "Unknown",
            "count": row.count,
            "average_response_time": round(row.avg_response_time or 0, 2),
            "total_response_time": round(row.total_response_time or 0, 2)
        })

    return model_stats
