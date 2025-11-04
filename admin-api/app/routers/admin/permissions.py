"""
권한 관리 CRUD API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.models.permission import Permission
from app.schemas.permission import PermissionCreate, PermissionUpdate, PermissionResponse
from app.core.database import get_db
from app.dependencies import require_permission, get_principal
from cerbos.sdk.model import Principal


router = APIRouter(prefix="/api/v1/admin/permissions", tags=["admin-permissions"])


@router.get("/", response_model=List[PermissionResponse])
async def list_permissions(
    skip: int = Query(0, ge=0, description="오프셋"),
    limit: int = Query(100, le=1000, description="최대 개수"),
    resource: Optional[str] = Query(None, description="리소스 필터"),
    action: Optional[str] = Query(None, description="작업 필터"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """권한 목록 조회"""
    query = select(Permission)

    if resource:
        query = query.filter(Permission.resource == resource)

    if action:
        query = query.filter(Permission.action == action)

    query = query.order_by(Permission.resource, Permission.action).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=PermissionResponse, status_code=201)
async def create_permission(
    permission: PermissionCreate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("permission", "create"))
):
    """권한 생성 (admin만)"""
    # 동일한 리소스-작업 조합 중복 확인
    existing = await db.execute(
        select(Permission).filter(
            Permission.resource == permission.resource,
            Permission.action == permission.action
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"권한 {permission.resource}:{permission.action}이 이미 존재합니다"
        )

    db_permission = Permission(**permission.model_dump())
    db.add(db_permission)
    await db.commit()
    await db.refresh(db_permission)
    return db_permission


@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """권한 상세 조회"""
    result = await db.execute(
        select(Permission).filter(Permission.id == permission_id)
    )
    permission = result.scalar_one_or_none()
    if not permission:
        raise HTTPException(status_code=404, detail="권한을 찾을 수 없습니다")
    return permission


@router.put("/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: int,
    permission_update: PermissionUpdate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("permission", "update"))
):
    """권한 수정 (admin만)"""
    result = await db.execute(
        select(Permission).filter(Permission.id == permission_id)
    )
    db_permission = result.scalar_one_or_none()
    if not db_permission:
        raise HTTPException(status_code=404, detail="권한을 찾을 수 없습니다")

    # 리소스-작업 변경 시 중복 확인
    if permission_update.resource or permission_update.action:
        new_resource = permission_update.resource or db_permission.resource
        new_action = permission_update.action or db_permission.action

        if new_resource != db_permission.resource or new_action != db_permission.action:
            existing = await db.execute(
                select(Permission).filter(
                    Permission.resource == new_resource,
                    Permission.action == new_action
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=400,
                    detail=f"권한 {new_resource}:{new_action}이 이미 존재합니다"
                )

    # 업데이트
    for field, value in permission_update.model_dump(exclude_unset=True).items():
        setattr(db_permission, field, value)

    await db.commit()
    await db.refresh(db_permission)
    return db_permission


@router.delete("/{permission_id}", status_code=204)
async def delete_permission(
    permission_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("permission", "delete"))
):
    """권한 삭제 (admin만)"""
    result = await db.execute(
        select(Permission).filter(Permission.id == permission_id)
    )
    db_permission = result.scalar_one_or_none()
    if not db_permission:
        raise HTTPException(status_code=404, detail="권한을 찾을 수 없습니다")

    await db.delete(db_permission)
    await db.commit()
