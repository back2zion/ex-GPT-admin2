"""
사용자 관리 및 역할 매핑 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.models.user import User
from app.models.permission import Role, Department
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserRoleAssignment
from app.core.database import get_db
from app.dependencies import require_permission, get_principal
from cerbos.sdk.model import Principal


router = APIRouter(prefix="/api/v1/admin/users", tags=["admin-users"])


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0, description="오프셋"),
    limit: int = Query(100, le=1000, description="최대 개수"),
    search: Optional[str] = Query(None, description="검색어 (이름/이메일)"),
    department_id: Optional[int] = Query(None, description="부서 ID 필터"),
    is_active: Optional[bool] = Query(None, description="활성화 여부"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """사용자 목록 조회"""
    query = select(User).options(
        selectinload(User.roles),
        selectinload(User.department)
    )

    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.email.contains(search)) |
            (User.full_name.contains(search))
        )

    if department_id is not None:
        query = query.filter(User.department_id == department_id)

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    query = query.order_by(User.username).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("user", "create"))
):
    """사용자 생성 (admin만)"""
    # 사용자명 중복 확인
    existing_username = await db.execute(
        select(User).filter(User.username == user.username)
    )
    if existing_username.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="사용자명이 이미 존재합니다")

    # 이메일 중복 확인
    existing_email = await db.execute(
        select(User).filter(User.email == user.email)
    )
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이메일이 이미 존재합니다")

    # 부서 확인
    if user.department_id:
        dept_result = await db.execute(
            select(Department).filter(Department.id == user.department_id)
        )
        if not dept_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")

    # 역할 조회
    roles = []
    if user.role_ids:
        role_result = await db.execute(
            select(Role).filter(Role.id.in_(user.role_ids))
        )
        roles = role_result.scalars().all()
        if len(roles) != len(user.role_ids):
            raise HTTPException(status_code=404, detail="일부 역할을 찾을 수 없습니다")

    # 사용자 생성 (비밀번호 해싱 - MVP에서는 단순 처리)
    # TODO: 실제 환경에서는 bcrypt 등으로 안전하게 해싱 필요
    user_data = user.model_dump(exclude={'role_ids', 'password'})
    user_data['hashed_password'] = f"hashed_{user.password}"  # MVP: 간단한 해싱
    db_user = User(**user_data)
    db_user.roles = roles

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user, attribute_names=['roles', 'department'])
    return db_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """사용자 상세 조회"""
    result = await db.execute(
        select(User).options(
            selectinload(User.roles),
            selectinload(User.department)
        ).filter(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("user", "update"))
):
    """사용자 수정 (admin만)"""
    result = await db.execute(
        select(User).options(
            selectinload(User.roles),
            selectinload(User.department)
        ).filter(User.id == user_id)
    )
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    # 사용자명 변경 시 중복 확인
    if user_update.username and user_update.username != db_user.username:
        existing = await db.execute(
            select(User).filter(User.username == user_update.username)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="사용자명이 이미 존재합니다")

    # 이메일 변경 시 중복 확인
    if user_update.email and user_update.email != db_user.email:
        existing = await db.execute(
            select(User).filter(User.email == user_update.email)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="이메일이 이미 존재합니다")

    # 부서 확인
    if user_update.department_id:
        dept_result = await db.execute(
            select(Department).filter(Department.id == user_update.department_id)
        )
        if not dept_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")

    # 업데이트 (비밀번호는 해싱 필요)
    for field, value in user_update.model_dump(exclude_unset=True).items():
        if field == 'password':
            # MVP: 간단한 해싱 (실제로는 bcrypt 사용)
            setattr(db_user, 'hashed_password', f"hashed_{value}")
        else:
            setattr(db_user, field, value)

    await db.commit()
    await db.refresh(db_user, attribute_names=['roles', 'department'])
    return db_user


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("user", "delete"))
):
    """사용자 삭제 (admin만)"""
    result = await db.execute(
        select(User).filter(User.id == user_id)
    )
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    await db.delete(db_user)
    await db.commit()


# === 역할 매핑 API ===

@router.post("/{user_id}/roles", response_model=UserResponse)
async def assign_user_roles(
    user_id: int,
    role_assignment: UserRoleAssignment,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("user", "update"))
):
    """사용자 역할 할당 (admin만)"""
    result = await db.execute(
        select(User).options(
            selectinload(User.roles),
            selectinload(User.department)
        ).filter(User.id == user_id)
    )
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    # 역할 조회
    role_result = await db.execute(
        select(Role).filter(Role.id.in_(role_assignment.role_ids))
    )
    roles = role_result.scalars().all()
    if len(roles) != len(role_assignment.role_ids):
        raise HTTPException(status_code=404, detail="일부 역할을 찾을 수 없습니다")

    # 역할 할당 (기존 역할은 모두 제거하고 새로 할당)
    db_user.roles = roles

    await db.commit()
    await db.refresh(db_user, attribute_names=['roles', 'department'])
    return db_user


@router.delete("/{user_id}/roles/{role_id}", status_code=204)
async def remove_user_role(
    user_id: int,
    role_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("user", "update"))
):
    """사용자 역할 제거 (admin만)"""
    result = await db.execute(
        select(User).options(selectinload(User.roles)).filter(User.id == user_id)
    )
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    # 역할 제거
    db_user.roles = [r for r in db_user.roles if r.id != role_id]

    await db.commit()
