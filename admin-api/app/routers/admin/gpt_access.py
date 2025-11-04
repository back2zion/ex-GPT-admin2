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
from app.models.access import AccessRequest, AccessRequestStatus, AccessChangeHistory, AccessChangeAction
from app.models.permission import Department
from app.middleware.spring_session_auth import get_current_user_optional
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
    ProcessRequestResponse,
    AccessChangeHistoryResponse,
    AccessChangeHistoryListResponse
)
from app.schemas.gpt_stats import (
    DepartmentStatsListResponse,
    DepartmentStatsResponse,
    ModelDistributionListResponse,
    ModelDistributionResponse
)

router = APIRouter(prefix="/api/v1/admin/gpt-access", tags=["admin-gpt-access"])


async def get_admin_user_id(db: AsyncSession, current_user: dict) -> int:
    """
    세션 사용자 정보에서 실제 DB user ID 조회

    Args:
        db: 데이터베이스 세션
        current_user: Spring Session에서 가져온 사용자 정보 {"user_id": "username", ...}

    Returns:
        int: 데이터베이스 user ID
    """
    username = current_user.get("user_id", "admin")

    # username으로 사용자 조회
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user:
        return user.id

    # 사용자가 없으면 첫 번째 superuser 사용
    query = select(User).where(User.is_superuser == True).limit(1)
    result = await db.execute(query)
    superuser = result.scalar_one_or_none()

    if superuser:
        return superuser.id

    # 아무도 없으면 에러
    raise HTTPException(status_code=500, detail="관리자 사용자를 찾을 수 없습니다")


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
            is_active=user.is_active,
            # 도로공사 조직 정보
            employee_number=user.employee_number,
            position=user.position,
            rank=user.rank,
            team=user.team,
            job_category=user.job_category
        ))

    return UsersListResponse(users=users_data, total=len(users_data))


@router.post("/grant", response_model=GrantAccessResponse)
async def grant_gpt_access(
    request: GrantAccessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    GPT 접근 권한 부여
    - 단일 또는 여러 사용자에게 일괄 권한 부여
    - 권한 변경 이력 자동 기록
    """
    # 현재 로그인한 관리자 ID 조회 (인증 실패 시 기본 superuser 사용)
    try:
        admin_id = await get_admin_user_id(db, current_user or {})
    except HTTPException:
        # 인증 실패 시 첫 번째 superuser 사용
        query = select(User).where(User.is_superuser == True).limit(1)
        result = await db.execute(query)
        superuser = result.scalar_one_or_none()
        admin_id = superuser.id if superuser else 1

    # 사용자 조회
    query = select(User).where(User.id.in_(request.user_ids))
    result = await db.execute(query)
    users = result.scalars().all()

    if not users:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    # 권한 부여 + 모델 할당 + 이력 기록
    granted_count = 0
    now = datetime.now(timezone.utc)

    for user in users:
        old_model = user.allowed_model
        old_access = user.gpt_access_granted

        # NO-OP 체크: 이미 같은 모델이 할당되어 있으면 스킵
        if old_access and old_model == request.model:
            continue

        user.gpt_access_granted = True
        user.allowed_model = request.model
        granted_count += 1

        # 이력 기록: 신규 권한 부여 vs 모델 변경 구분
        if not old_access:
            action_type = AccessChangeAction.GRANT.value
        else:
            action_type = AccessChangeAction.MODEL_CHANGE.value

        history = AccessChangeHistory(
            user_id=user.id,
            action=action_type,
            changed_by=admin_id,
            changed_at=now,
            old_value=old_model,
            new_value=request.model,
            reason=f"관리자가 {request.model} 모델 권한 부여"
        )
        db.add(history)

    await db.commit()

    return GrantAccessResponse(
        granted_count=granted_count,
        message=f"{granted_count}명의 사용자에게 {request.model} 모델이 할당되었습니다"
    )


@router.post("/revoke", response_model=RevokeAccessResponse)
async def revoke_gpt_access(
    request: RevokeAccessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    GPT 접근 권한 회수
    - 단일 또는 여러 사용자의 권한 일괄 회수
    - 권한 변경 이력 자동 기록
    """
    # 현재 로그인한 관리자 ID 조회 (인증 실패 시 기본 superuser 사용)
    try:
        admin_id = await get_admin_user_id(db, current_user or {})
    except HTTPException:
        # 인증 실패 시 첫 번째 superuser 사용
        query = select(User).where(User.is_superuser == True).limit(1)
        result = await db.execute(query)
        superuser = result.scalar_one_or_none()
        admin_id = superuser.id if superuser else 1

    # 사용자 조회
    query = select(User).where(User.id.in_(request.user_ids))
    result = await db.execute(query)
    users = result.scalars().all()

    if not users:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    # 권한 회수 + 이력 기록
    revoked_count = 0
    now = datetime.now(timezone.utc)

    for user in users:
        # NO-OP 체크: 이미 권한이 없으면 스킵
        if not user.gpt_access_granted:
            continue

        old_model = user.allowed_model

        user.gpt_access_granted = False
        user.allowed_model = None
        revoked_count += 1

        # 이력 기록
        history = AccessChangeHistory(
            user_id=user.id,
            action=AccessChangeAction.REVOKE.value,
            changed_by=admin_id,
            changed_at=now,
            old_value=old_model,
            new_value=None,
            reason="관리자가 GPT 접근 권한 회수"
        )
        db.add(history)

    await db.commit()

    return RevokeAccessResponse(
        revoked_count=revoked_count,
        message=f"{revoked_count}명의 사용자로부터 ex-GPT 접근 권한이 회수되었습니다"
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


@router.get("/stats/departments", response_model=DepartmentStatsListResponse)
async def get_department_stats(
    department_id: Optional[int] = Query(None, description="특정 부서 ID 필터"),
    db: AsyncSession = Depends(get_db)
):
    """
    부서별 GPT 접근 권한 통계 조회
    - department_id: 특정 부서만 조회 (선택)
    """
    # 부서 목록 조회
    dept_query = select(Department)
    if department_id is not None:
        dept_query = dept_query.where(Department.id == department_id)

    dept_result = await db.execute(dept_query)
    departments = dept_result.scalars().all()

    departments_data = []
    total_users = 0
    total_users_with_access = 0

    for dept in departments:
        # 부서별 전체 사용자 수
        user_count_query = select(func.count(User.id)).where(User.department_id == dept.id)
        user_count_result = await db.execute(user_count_query)
        users_count = user_count_result.scalar() or 0

        # 부서별 GPT 접근 권한 보유자 수
        access_count_query = select(func.count(User.id)).where(
            and_(User.department_id == dept.id, User.gpt_access_granted == True)
        )
        access_count_result = await db.execute(access_count_query)
        access_count = access_count_result.scalar() or 0

        access_rate = (access_count / users_count * 100) if users_count > 0 else 0.0

        departments_data.append(DepartmentStatsResponse(
            id=dept.id,
            name=dept.name,
            code=dept.code,
            total_users=users_count,
            users_with_gpt_access=access_count,
            access_rate=round(access_rate, 2)
        ))

        total_users += users_count
        total_users_with_access += access_count

    return DepartmentStatsListResponse(
        departments=departments_data,
        total_departments=len(departments_data),
        total_users=total_users,
        total_users_with_access=total_users_with_access
    )


@router.get("/stats/models", response_model=ModelDistributionListResponse)
async def get_model_distribution(
    db: AsyncSession = Depends(get_db)
):
    """
    모델별 사용자 분포 통계 조회
    """
    # 모델별 사용자 수 집계
    query = select(
        User.allowed_model,
        func.count(User.id).label("user_count")
    ).where(
        and_(
            User.gpt_access_granted == True,
            User.allowed_model.isnot(None)
        )
    ).group_by(User.allowed_model)

    result = await db.execute(query)
    rows = result.all()

    # 전체 사용자 수 계산
    total_users = sum(row.user_count for row in rows)

    models_data = []
    for row in rows:
        percentage = (row.user_count / total_users * 100) if total_users > 0 else 0.0
        models_data.append(ModelDistributionResponse(
            model=row.allowed_model,
            user_count=row.user_count,
            percentage=round(percentage, 2)
        ))

    return ModelDistributionListResponse(
        models=models_data,
        total_users_with_access=total_users
    )


@router.get("/history", response_model=AccessChangeHistoryListResponse)
async def get_access_change_history(
    user_id: Optional[int] = Query(None, description="특정 사용자 필터"),
    action: Optional[str] = Query(None, description="액션 필터 (grant, revoke, model_change)"),
    limit: int = Query(100, description="조회 개수"),
    db: AsyncSession = Depends(get_db)
):
    """
    GPT 접근 권한 변경 이력 조회 (감사 로그)
    - user_id: 특정 사용자의 이력만 조회
    - action: 특정 액션만 조회
    - limit: 최대 조회 개수
    """
    # 이력 조회
    query = select(AccessChangeHistory).options(
        selectinload(AccessChangeHistory.user).selectinload(User.department),
        selectinload(AccessChangeHistory.admin)
    ).order_by(AccessChangeHistory.changed_at.desc())

    # 필터 적용
    if user_id:
        query = query.where(AccessChangeHistory.user_id == user_id)

    if action:
        try:
            action_enum = AccessChangeAction(action.lower())
            query = query.where(AccessChangeHistory.action == action_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"잘못된 액션: {action}")

    # 개수 제한
    query = query.limit(limit)

    result = await db.execute(query)
    history_records = result.scalars().all()

    # 응답 생성
    history_data = []
    for record in history_records:
        history_data.append(AccessChangeHistoryResponse(
            id=record.id,
            user_id=record.user_id,
            username=record.user.username if record.user else None,
            full_name=record.user.full_name if record.user else None,
            employee_number=record.user.employee_number if record.user else None,
            department_name=record.user.department.name if record.user and record.user.department else None,
            action=record.action.value,
            changed_by=record.changed_by,
            admin_name=record.admin.full_name if record.admin else None,
            changed_at=record.changed_at,
            old_value=record.old_value,
            new_value=record.new_value,
            reason=record.reason
        ))

    return AccessChangeHistoryListResponse(
        history=history_data,
        total=len(history_data)
    )
