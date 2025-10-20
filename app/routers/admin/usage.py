"""
사용 이력 API 엔드포인트

보안 기능:
- Cerbos RBAC 기반 권한 검증
- SQL Injection 방지 (SQLAlchemy ORM)
- Input validation (Pydantic + Query parameters)
- 데이터 길이 제한
"""
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timedelta

from app.models import UsageHistory
from app.schemas.usage import UsageHistoryResponse, UsageHistoryCreate
from app.core.database import get_db
from app.dependencies import get_principal, get_cerbos_client, check_resource_permission
from cerbos.sdk.model import Principal, Resource
from cerbos.sdk.client import AsyncCerbosClient

# Constants for data protection
MAX_QUESTION_LENGTH = 10000
MAX_ANSWER_LENGTH = 50000
MAX_THINKING_LENGTH = 100000
DATE_FORMAT = "%Y-%m-%d"

router = APIRouter(prefix="/api/v1/admin/usage", tags=["admin-usage"])


# Helper Functions
def _parse_date_filter(date_str: str, field_name: str, is_end_date: bool = False) -> datetime:
    """
    날짜 문자열을 datetime 객체로 변환

    Args:
        date_str: YYYY-MM-DD 형식의 날짜 문자열
        field_name: 오류 메시지에 표시할 필드명
        is_end_date: 종료일인 경우 True (하루 추가)

    Returns:
        datetime: 파싱된 datetime 객체

    Raises:
        HTTPException: 날짜 형식이 잘못된 경우
    """
    try:
        parsed_date = datetime.strptime(date_str, DATE_FORMAT)
        if is_end_date:
            # 종료일 포함을 위해 다음날 00:00:00 사용
            parsed_date += timedelta(days=1)
        return parsed_date
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} 형식이 잘못되었습니다 (YYYY-MM-DD 형식 필요): {date_str}"
        )


def _extract_client_ip(request: Request) -> Optional[str]:
    """
    요청에서 클라이언트 IP 주소 추출

    X-Forwarded-For 헤더를 우선으로 사용하고,
    없으면 request.client.host 사용

    Args:
        request: FastAPI Request 객체

    Returns:
        str | None: 클라이언트 IP 주소 또는 None
    """
    # X-Forwarded-For 헤더 확인 (프록시 환경)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # 여러 프록시를 거친 경우 첫 번째 IP 사용
        return forwarded_for.split(",")[0].strip()

    # 직접 연결된 경우
    return request.client.host if request.client else None


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

    # 날짜 범위 필터 (Helper 함수 사용 - DRY 원칙)
    if start_date:
        start_dt = _parse_date_filter(start_date, "시작 날짜", is_end_date=False)
        query = query.filter(UsageHistory.created_at >= start_dt)

    if end_date:
        end_dt = _parse_date_filter(end_date, "종료 날짜", is_end_date=True)
        query = query.filter(UsageHistory.created_at < end_dt)

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
    # IP 주소 자동 수집 (Helper 함수 사용)
    client_ip = _extract_client_ip(request)

    # UsageHistory 모델 생성 (상수 사용으로 유지보수성 향상)
    new_history = UsageHistory(
        user_id=usage_data.user_id,
        session_id=usage_data.session_id,
        question=usage_data.question[:MAX_QUESTION_LENGTH],  # 길이 제한 (DB 보호)
        answer=usage_data.answer[:MAX_ANSWER_LENGTH] if usage_data.answer else None,
        thinking_content=usage_data.thinking_content[:MAX_THINKING_LENGTH] if usage_data.thinking_content else None,
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
