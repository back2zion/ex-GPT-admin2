"""
GPT 접근 승인 관리 API
adminpage.txt: 1) 관리자관리>가입요청, 1) ex-GPT 접근권한>접근승인관리
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.models.access import AccessRequest, AccessRequestStatus
from app.models.user import User
from app.core.database import get_db


router = APIRouter(prefix="/api/v1/admin/access-requests", tags=["admin-access-requests"])


class AccessRequestResponse(BaseModel):
    """접근 신청 응답"""
    id: int
    user_id: int
    username: str
    email: str
    full_name: Optional[str]
    status: AccessRequestStatus
    requested_at: datetime
    processed_at: Optional[datetime]
    processed_by: Optional[int]
    reject_reason: Optional[str]

    # 도로공사 조직 정보
    department_name: Optional[str] = None
    employee_number: Optional[str] = None
    position: Optional[str] = None
    rank: Optional[str] = None
    team: Optional[str] = None
    job_category: Optional[str] = None

    class Config:
        from_attributes = True


class AccessRequestApproval(BaseModel):
    """접근 승인 요청"""
    user_ids: List[int] = Field(..., description="승인할 사용자 ID 목록")
    allowed_model: Optional[str] = Field(None, description="허용할 모델명")


class AccessRequestRejection(BaseModel):
    """접근 거부 요청"""
    user_id: int = Field(..., description="거부할 사용자 ID")
    reject_reason: Optional[str] = Field(None, description="거부 사유")


@router.get("/", response_model=List[AccessRequestResponse])
async def list_access_requests(
    status: Optional[AccessRequestStatus] = Query(None, description="상태 필터 (pending/approved/rejected)"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=10000, description="페이지 크기"),
    db: AsyncSession = Depends(get_db)
):
    """
    GPT 접근 신청 목록을 조회합니다.

    adminpage.txt 요구사항:
    - 상태별 검색 (신청/미신청/거부)
    """
    query = select(AccessRequest).options(
        selectinload(AccessRequest.user).selectinload(User.department)
    ).order_by(AccessRequest.requested_at.desc())

    # 필터링
    if status is not None:
        query = query.filter(AccessRequest.status == status)

    # 페이징
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    requests = result.scalars().all()

    # Response 변환
    return [
        AccessRequestResponse(
            id=req.id,
            user_id=req.user_id,
            username=req.user.username if req.user else "",
            email=req.user.email if req.user else "",
            full_name=req.user.full_name if req.user else None,
            status=req.status,
            requested_at=req.requested_at,
            processed_at=req.processed_at,
            processed_by=req.processed_by,
            reject_reason=req.reject_reason,
            # 도로공사 조직 정보
            department_name=req.user.department.name if (req.user and req.user.department) else None,
            employee_number=req.user.employee_number if req.user else None,
            position=req.user.position if req.user else None,
            rank=req.user.rank if req.user else None,
            team=req.user.team if req.user else None,
            job_category=req.user.job_category if req.user else None
        )
        for req in requests
    ]


@router.post("/approve", response_model=dict)
async def approve_access_requests(
    approval: AccessRequestApproval,
    db: AsyncSession = Depends(get_db)
):
    """
    GPT 접근 신청을 일괄 승인합니다.

    adminpage.txt 요구사항:
    - 여러 명을 선택하여 일괄 승인
    - 사용할 모델 지정
    """
    approved_count = 0

    for user_id in approval.user_ids:
        # 신청 조회
        request_result = await db.execute(
            select(AccessRequest).filter(
                AccessRequest.user_id == user_id,
                AccessRequest.status == AccessRequestStatus.PENDING
            )
        )
        access_request = request_result.scalar_one_or_none()

        if access_request:
            # 승인 처리
            access_request.status = AccessRequestStatus.APPROVED
            access_request.processed_at = datetime.utcnow()
            # TODO: principal에서 user_id 추출
            # access_request.processed_by = principal.id

            # 사용자 GPT 접근 권한 부여
            user_result = await db.execute(
                select(User).filter(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()

            if user:
                user.gpt_access_granted = True
                user.allowed_model = approval.allowed_model

            approved_count += 1

    await db.commit()

    return {
        "message": f"{approved_count}명의 접근 신청이 승인되었습니다",
        "approved_count": approved_count,
        "total_requested": len(approval.user_ids)
    }


@router.post("/reject", response_model=dict)
async def reject_access_request(
    rejection: AccessRequestRejection,
    db: AsyncSession = Depends(get_db)
):
    """
    GPT 접근 신청을 거부합니다.
    """
    # 신청 조회
    request_result = await db.execute(
        select(AccessRequest).filter(
            AccessRequest.user_id == rejection.user_id,
            AccessRequest.status == AccessRequestStatus.PENDING
        )
    )
    access_request = request_result.scalar_one_or_none()

    if not access_request:
        raise HTTPException(
            status_code=404,
            detail="대기 중인 접근 신청을 찾을 수 없습니다"
        )

    # 거부 처리
    access_request.status = AccessRequestStatus.REJECTED
    access_request.processed_at = datetime.utcnow()
    access_request.reject_reason = rejection.reject_reason
    # TODO: principal에서 user_id 추출
    # access_request.processed_by = principal.id

    await db.commit()

    return {
        "message": "접근 신청이 거부되었습니다",
        "user_id": rejection.user_id
    }
