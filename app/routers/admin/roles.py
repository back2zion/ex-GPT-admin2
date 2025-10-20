"""
역할 관리 CRUD API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.models.permission import Role, Permission
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse
from app.core.database import get_db
from app.dependencies import require_permission, get_principal
from cerbos.sdk.model import Principal


router = APIRouter(prefix="/api/v1/admin/roles", tags=["admin-roles"])


@router.get("/", response_model=List[RoleResponse])
async def list_roles(
    skip: int = Query(0, ge=0, description="오프셋"),
    limit: int = Query(100, le=1000, description="최대 개수"),
    search: Optional[str] = Query(None, description="검색어 (이름)"),
    is_active: bool | None = Query(None, description="활성화 여부"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """역할 목록 조회"""
    query = select(Role).options(selectinload(Role.permissions))

    if search:
        query = query.filter(Role.name.contains(search))

    if is_active is not None:
        query = query.filter(Role.is_active == is_active)

    query = query.order_by(Role.name).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=RoleResponse, status_code=201)
async def create_role(
    role: RoleCreate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("role", "create"))
):
    """역할 생성 (admin만)"""
    # 역할명 중복 확인
    existing = await db.execute(
        select(Role).filter(Role.name == role.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="역할명이 이미 존재합니다")

    # 권한 조회
    permissions = []
    if role.permission_ids:
        perm_result = await db.execute(
            select(Permission).filter(Permission.id.in_(role.permission_ids))
        )
        permissions = perm_result.scalars().all()
        if len(permissions) != len(role.permission_ids):
            raise HTTPException(status_code=404, detail="일부 권한을 찾을 수 없습니다")

    # 역할 생성
    role_data = role.model_dump(exclude={'permission_ids'})
    db_role = Role(**role_data)
    db_role.permissions = permissions

    db.add(db_role)
    await db.commit()
    await db.refresh(db_role, attribute_names=['permissions'])
    return db_role


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """역할 상세 조회"""
    result = await db.execute(
        select(Role).options(selectinload(Role.permissions)).filter(Role.id == role_id)
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="역할을 찾을 수 없습니다")
    return role


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_update: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("role", "update"))
):
    """역할 수정 (admin만)"""
    result = await db.execute(
        select(Role).options(selectinload(Role.permissions)).filter(Role.id == role_id)
    )
    db_role = result.scalar_one_or_none()
    if not db_role:
        raise HTTPException(status_code=404, detail="역할을 찾을 수 없습니다")

    # 역할명 변경 시 중복 확인
    if role_update.name and role_update.name != db_role.name:
        existing = await db.execute(
            select(Role).filter(Role.name == role_update.name)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="역할명이 이미 존재합니다")

    # 권한 업데이트
    if role_update.permission_ids is not None:
        perm_result = await db.execute(
            select(Permission).filter(Permission.id.in_(role_update.permission_ids))
        )
        permissions = perm_result.scalars().all()
        if len(permissions) != len(role_update.permission_ids):
            raise HTTPException(status_code=404, detail="일부 권한을 찾을 수 없습니다")
        db_role.permissions = permissions

    # 나머지 필드 업데이트
    for field, value in role_update.model_dump(exclude_unset=True, exclude={'permission_ids'}).items():
        setattr(db_role, field, value)

    await db.commit()
    await db.refresh(db_role, attribute_names=['permissions'])
    return db_role


@router.delete("/{role_id}", status_code=204)
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("role", "delete"))
):
    """역할 삭제 (admin만)"""
    result = await db.execute(
        select(Role).filter(Role.id == role_id)
    )
    db_role = result.scalar_one_or_none()
    if not db_role:
        raise HTTPException(status_code=404, detail="역할을 찾을 수 없습니다")

    await db.delete(db_role)
    await db.commit()
