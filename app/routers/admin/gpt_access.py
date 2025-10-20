"""
GPT 접근 권한 관리 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime, timedelta, timezone

from app.core.database import get_db
from app.models.user import User
from app.models.access import AccessRequest, AccessRequestStatus
from app.models.permission import Department
from app.schemas.gpt_access import (
    UsersListResponse,
    UserGPTAccessResponse,
    GrantAccessRequest,
    RevokeAccessRequest,
    GrantAccessResponse,
    RevokeAccessResponse,
    AccessRequestsListResponse,
    AccessRequestResponse,
    ApproveRequestRequest,
    RejectRequestRequest,
    ProcessRequestResponse
)
from app.schemas.gpt_stats import (
    DepartmentStatsListResponse,
    DepartmentStatsResponse,
    ModelDistributionListResponse,
    ModelDistributionResponse
)

router = APIRouter(prefix="/api/v1/admin/gpt-access", tags=["admin-gpt-access"])


@router.get("/users", response_model=UsersListResponse)
async def list_users_with_gpt_access(
    inactive_days: Optional[int] = Query(None, description="미접속 일수 필터"),
    db: AsyncSession = Depends(get_db)
):
    """
    GPT 접근 권한 사용자 목록 조회
    - inactive_days: 지정한 일수 이상 미접속한 사용자만 조회
    """
    query = select(User).options(selectinload(User.department))

    # 미접속 일수 필터
    if inactive_days is not None:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=inactive_days)
        query = query.where(
            or_(
                User.last_login_at < cutoff_date,
                User.last_login_at.is_(None)
            )
        )

    result = await db.execute(query)
    users = result.scalars().all()

    users_data = []
    for user in users:
        users_data.append(UserGPTAccessResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            department_name=user.department.name if user.department else None,
            gpt_access_granted=user.gpt_access_granted,
            allowed_model=user.allowed_model,
            last_login_at=user.last_login_at,
            is_active=user.is_active
        ))

    return UsersListResponse(users=users_data, total=len(users_data))


@router.post("/grant", response_model=GrantAccessResponse)
async def grant_gpt_access(
    request: GrantAccessRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    GPT 접근 권한 부여
    - 단일 또는 여러 사용자에게 일괄 권한 부여
    """
    # 사용자 조회
    query = select(User).where(User.id.in_(request.user_ids))
    result = await db.execute(query)
    users = result.scalars().all()

    if not users:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    # 권한 부여
    granted_count = 0
    for user in users:
        user.gpt_access_granted = True
        user.allowed_model = request.model
        granted_count += 1

    await db.commit()

    return GrantAccessResponse(
        granted_count=granted_count,
        message=f"{granted_count}명의 사용자에게 GPT 접근 권한이 부여되었습니다"
    )


@router.post("/revoke", response_model=RevokeAccessResponse)
async def revoke_gpt_access(
    request: RevokeAccessRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    GPT 접근 권한 회수
    - 단일 또는 여러 사용자의 권한 일괄 회수
    """
    # 사용자 조회
    query = select(User).where(User.id.in_(request.user_ids))
    result = await db.execute(query)
    users = result.scalars().all()

    if not users:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    # 권한 회수
    revoked_count = 0
    for user in users:
        user.gpt_access_granted = False
        user.allowed_model = None
        revoked_count += 1

    await db.commit()

    return RevokeAccessResponse(
        revoked_count=revoked_count,
        message=f"{revoked_count}명의 사용자로부터 GPT 접근 권한이 회수되었습니다"
    )


@router.get("/requests", response_model=AccessRequestsListResponse)
async def list_access_requests(
    status: Optional[str] = Query(None, description="상태 필터 (PENDING, APPROVED, REJECTED)"),
    db: AsyncSession = Depends(get_db)
):
    """
    GPT 접근 신청 목록 조회
    - status: 상태별 필터링
    """
    query = select(AccessRequest).options(
        selectinload(AccessRequest.user).selectinload(User.department),
        selectinload(AccessRequest.processor)
    )

    # 상태 필터
    if status:
        try:
            status_enum = AccessRequestStatus(status.lower())
            query = query.where(AccessRequest.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"잘못된 상태값: {status}")

    result = await db.execute(query)
    requests = result.scalars().all()

    requests_data = []
    for req in requests:
        requests_data.append(AccessRequestResponse(
            id=req.id,
            user_id=req.user_id,
            username=req.user.username if req.user else None,
            full_name=req.user.full_name if req.user else None,
            department_name=req.user.department.name if req.user and req.user.department else None,
            status=req.status.value,
            requested_at=req.requested_at,
            processed_at=req.processed_at,
            processor_name=req.processor.full_name if req.processor else None,
            reject_reason=req.reject_reason
        ))

    return AccessRequestsListResponse(requests=requests_data, total=len(requests_data))


@router.post("/requests/{request_id}/approve", response_model=ProcessRequestResponse)
async def approve_access_request(
    request_id: int,
    request: ApproveRequestRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    GPT 접근 신청 승인
    - 승인 시 자동으로 사용자에게 GPT 접근 권한 부여
    """
    # 신청 조회
    query = select(AccessRequest).where(AccessRequest.id == request_id)
    result = await db.execute(query)
    access_request = result.scalar_one_or_none()

    if not access_request:
        raise HTTPException(status_code=404, detail="접근 신청을 찾을 수 없습니다")

    if access_request.status != AccessRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="이미 처리된 신청입니다")

    # 신청 승인
    access_request.status = AccessRequestStatus.APPROVED
    access_request.processed_at = datetime.now(timezone.utc)
    access_request.processed_by = request.processor_id

    # 사용자에게 권한 부여
    user_query = select(User).where(User.id == access_request.user_id)
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()

    if user:
        user.gpt_access_granted = True
        user.allowed_model = request.model

    await db.commit()

    return ProcessRequestResponse(
        id=access_request.id,
        status="approved",
        message="접근 신청이 승인되었습니다"
    )


@router.post("/requests/{request_id}/reject", response_model=ProcessRequestResponse)
async def reject_access_request(
    request_id: int,
    request: RejectRequestRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    GPT 접근 신청 거부
    """
    # 신청 조회
    query = select(AccessRequest).where(AccessRequest.id == request_id)
    result = await db.execute(query)
    access_request = result.scalar_one_or_none()

    if not access_request:
        raise HTTPException(status_code=404, detail="접근 신청을 찾을 수 없습니다")

    if access_request.status != AccessRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="이미 처리된 신청입니다")

    # 신청 거부
    access_request.status = AccessRequestStatus.REJECTED
    access_request.processed_at = datetime.now(timezone.utc)
    access_request.processed_by = request.processor_id
    access_request.reject_reason = request.reason

    await db.commit()

    return ProcessRequestResponse(
        id=access_request.id,
        status="rejected",
        message="접근 신청이 거부되었습니다"
    )
