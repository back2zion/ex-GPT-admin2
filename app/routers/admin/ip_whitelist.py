"""
IP 화이트리스트 관리 API
adminpage.txt: 8. 설정 > 1) 관리자관리>IP접근권한 관리
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from pydantic import BaseModel, Field

from app.models.ip_whitelist import IPWhitelist
from app.services.ip_access import IPAccessService
from app.core.database import get_db
from app.dependencies import require_permission
from cerbos.sdk.model import Principal


router = APIRouter(prefix="/api/v1/admin/ip-whitelist", tags=["admin-ip"])


class IPWhitelistCreate(BaseModel):
    """IP 추가 요청"""
    ip_address: str = Field(..., description="IP 주소 (IPv4/IPv6)")
    description: Optional[str] = Field(None, description="설명")
    is_allowed: bool = Field(True, description="액세스 허용 여부")


class IPWhitelistUpdate(BaseModel):
    """IP 수정 요청"""
    description: Optional[str] = Field(None, description="설명")
    is_allowed: Optional[bool] = Field(None, description="액세스 허용 여부")


class IPWhitelistResponse(BaseModel):
    """IP 응답"""
    id: int
    ip_address: str
    description: Optional[str]
    is_allowed: bool
    created_by: Optional[int]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[IPWhitelistResponse])
async def list_ip_whitelist(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    is_allowed: Optional[bool] = Query(None, description="액세스 허용 여부 필터"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("ip_whitelist", "view"))
):
    """
    IP 화이트리스트 목록을 조회합니다.

    시큐어 코딩:
    - 권한 검증: Cerbos를 통한 조회 권한 확인
    - 페이징: 대량 데이터 조회 방지
    """
    query = select(IPWhitelist).order_by(IPWhitelist.created_at.desc())

    # 필터링
    if is_allowed is not None:
        query = query.filter(IPWhitelist.is_allowed == is_allowed)

    # 페이징
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=IPWhitelistResponse, status_code=201)
async def add_ip_whitelist(
    ip_create: IPWhitelistCreate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("ip_whitelist", "create"))
):
    """
    IP 주소를 화이트리스트에 추가합니다.

    시큐어 코딩:
    - 권한 검증: Cerbos를 통한 생성 권한 확인
    - 입력 검증: IP 주소 유효성 검증
    - 감사 로그: 등록한 관리자 기록
    """
    ip_service = IPAccessService()

    try:
        # TODO: principal에서 user_id 추출
        ip_entry = await ip_service.add_ip(
            ip_address=ip_create.ip_address,
            description=ip_create.description,
            is_allowed=ip_create.is_allowed,
            created_by=None,  # TODO: principal.id
            db=db
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ip_entry


@router.get("/{ip_id}", response_model=IPWhitelistResponse)
async def get_ip_whitelist(
    ip_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("ip_whitelist", "view"))
):
    """
    IP 화이트리스트 상세를 조회합니다.

    시큐어 코딩:
    - 권한 검증: Cerbos를 통한 조회 권한 확인
    """
    result = await db.execute(
        select(IPWhitelist).filter(IPWhitelist.id == ip_id)
    )
    ip_entry = result.scalar_one_or_none()

    if not ip_entry:
        raise HTTPException(status_code=404, detail="IP를 찾을 수 없습니다")

    return ip_entry


@router.put("/{ip_id}", response_model=IPWhitelistResponse)
async def update_ip_whitelist(
    ip_id: int,
    ip_update: IPWhitelistUpdate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("ip_whitelist", "update"))
):
    """
    IP 화이트리스트 정보를 수정합니다.

    adminpage.txt 요구사항:
    - IP 주소는 수정 불가
    - 설명과 액세스 여부만 수정 가능

    시큐어 코딩:
    - 권한 검증: Cerbos를 통한 수정 권한 확인
    - 감사 로그: 수정 이력 기록
    """
    ip_service = IPAccessService()

    try:
        ip_entry = await ip_service.update_ip(
            ip_id=ip_id,
            description=ip_update.description,
            is_allowed=ip_update.is_allowed,
            db=db
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return ip_entry


@router.delete("/{ip_id}", status_code=204)
async def delete_ip_whitelist(
    ip_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("ip_whitelist", "delete"))
):
    """
    IP 주소를 화이트리스트에서 삭제합니다.

    시큐어 코딩:
    - 권한 검증: Cerbos를 통한 삭제 권한 확인
    - 감사 로그: 삭제 이력 기록
    """
    ip_service = IPAccessService()

    success = await ip_service.delete_ip(ip_id, db)

    if not success:
        raise HTTPException(status_code=404, detail="IP를 찾을 수 없습니다")
