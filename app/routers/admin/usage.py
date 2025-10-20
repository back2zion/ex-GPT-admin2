"""
사용 이력 API 엔드포인트
"""
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timedelta

from app.models import UsageHistory
from app.schemas.usage import UsageHistoryResponse, UsageHistoryCreate
from app.core.database import get_db
from app.dependencies import get_principal, require_permission
from cerbos.sdk.model import Principal, Resource
from cerbos.sdk.client import AsyncCerbosClient
from app.dependencies import get_cerbos_client, check_resource_permission

router = APIRouter(prefix="/api/v1/admin/usage", tags=["admin-usage"])


@router.get("/", response_model=List[UsageHistoryResponse])
async def list_usage_history(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(100, le=1000, description="조회할 최대 레코드 수"),
    user_id: Optional[str] = Query(None, description="사용자 ID 필터"),
    search: Optional[str] = Query(None, description="검색어 (질문/답변)", max_length=200),
    model_name: Optional[str] = Query(None, description="모델명 필터", max_length=100),
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal),
    cerbos: AsyncCerbosClient = Depends(get_cerbos_client)
):
    """
    사용 이력 조회 (관리자 전용)

    - 질문, 답변, 응답시간, 모델 정보 등 조회
    - 검색 및 필터링 지원 (날짜 범위, 사용자 ID, 검색어, 모델명)
    - 페이지네이션 지원

    **권한 필요**: usage_history:read
    **시큐어 코딩**: 날짜 형식 검증 (regex), SQL Injection 방지 (SQLAlchemy ORM)
    """
    # 권한 검증
    resource = Resource(id="any", kind="usage_history")
    await check_resource_permission(principal, resource, "read", cerbos)

    query = select(UsageHistory)

    # 날짜 범위 필터 (시큐어 코딩: datetime 객체로 변환하여 Type Safety 보장)
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(UsageHistory.created_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="잘못된 시작 날짜 형식입니다 (YYYY-MM-DD)")

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # 종료일 포함
            query = query.filter(UsageHistory.created_at < end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="잘못된 종료 날짜 형식입니다 (YYYY-MM-DD)")

    # 사용자 ID 필터
    if user_id:
        query = query.filter(UsageHistory.user_id == user_id)

    # 검색어 필터 (시큐어 코딩: SQLAlchemy contains()는 파라미터화된 쿼리 사용)
    if search:
        query = query.filter(
            (UsageHistory.question.contains(search)) |
            (UsageHistory.answer.contains(search))
        )

    # 모델명 필터
    if model_name:
        query = query.filter(UsageHistory.model_name == model_name)

    # 정렬 및 페이징
    query = query.order_by(UsageHistory.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{history_id}", response_model=UsageHistoryResponse)
async def get_usage_history(
    history_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal),
    cerbos: AsyncCerbosClient = Depends(get_cerbos_client)
):
    """
    특정 사용 이력 상세 조회 (관리자 전용)

    **권한 필요**: usage_history:read
    """
    # 권한 검증
    resource = Resource(id=str(history_id), kind="usage_history")
    await check_resource_permission(principal, resource, "read", cerbos)

    result = await db.execute(select(UsageHistory).filter(UsageHistory.id == history_id))
    history = result.scalar_one_or_none()

    if not history:
        raise HTTPException(status_code=404, detail="사용 이력을 찾을 수 없습니다")

    return history


@router.post("/log", response_model=UsageHistoryResponse, status_code=201)
async def log_usage_history(
    usage_data: UsageHistoryCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    사용 이력 로깅 (layout.html에서 자동 호출)

    - 질문/답변 자동 기록
    - IP 주소 자동 수집
    - 인증 불필요 (공개 엔드포인트 - 사용 로깅 용도)

    **주의**:
    - Rate limiting 적용 권장 (slowapi 또는 nginx)
    - Input validation 자동 적용 (Pydantic)
    - 민감 정보 로깅 금지
    """
    # Input validation (Pydantic 스키마에서 자동 처리)
    # - question: max_length=10000
    # - answer: max_length=50000
    # - user_id: max_length=100

    # IP 주소 자동 수집 (X-Forwarded-For 헤더 우선)
    client_ip = request.headers.get("X-Forwarded-For")
    if client_ip:
        # 프록시를 거친 경우 첫 번째 IP 사용
        client_ip = client_ip.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else None

    # UsageHistory 모델 생성
    new_history = UsageHistory(
        user_id=usage_data.user_id,
        session_id=usage_data.session_id,
        question=usage_data.question[:10000],  # 길이 제한 (DB 보호)
        answer=usage_data.answer[:50000] if usage_data.answer else None,
        thinking_content=usage_data.thinking_content[:100000] if usage_data.thinking_content else None,
        response_time=usage_data.response_time,
        referenced_documents=usage_data.referenced_documents,
        model_name=usage_data.model_name,
        usage_metadata=usage_data.usage_metadata,
        ip_address=usage_data.ip_address or client_ip
    )

    db.add(new_history)
    await db.commit()
    await db.refresh(new_history)

    return new_history
