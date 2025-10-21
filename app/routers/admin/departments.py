"""
부서 관리 CRUD API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.models.permission import Department
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentTreeResponse
)
from app.core.database import get_db
from app.dependencies import require_permission, get_principal
from cerbos.sdk.model import Principal


router = APIRouter(prefix="/api/v1/admin/departments", tags=["admin-departments"])


@router.get("/")
async def list_departments(
    skip: int = Query(0, ge=0, description="오프셋"),
    limit: int = Query(100, le=1000, description="최대 개수"),
    search: Optional[str] = Query(None, description="검색어 (이름/코드)"),
    parent_id: Optional[int] = Query(None, description="상위 부서 ID"),
    sort_by: Optional[str] = Query("code", description="정렬 필드 (id, code, name, created_at)"),
    order: Optional[str] = Query("asc", description="정렬 방향 (asc, desc)"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    부서 목록 조회 (Pagination 및 Sorting 지원)

    Returns:
        {
            "items": [...],
            "total": N,
            "page": 1,
            "limit": 100
        }
    """
    from sqlalchemy import func, asc, desc

    # Base query
    query = select(Department)
    count_query = select(func.count()).select_from(Department)

    # Filters
    if search:
        search_filter = (Department.name.contains(search)) | (Department.code.contains(search))
        query = query.filter(search_filter)
        count_query = count_query.filter(search_filter)

    if parent_id is not None:
        query = query.filter(Department.parent_id == parent_id)
        count_query = count_query.filter(Department.parent_id == parent_id)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Sorting
    sort_column = getattr(Department, sort_by, Department.code)
    if order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # Pagination
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "limit": limit
    }


@router.get("/tree", response_model=List[DepartmentTreeResponse])
async def get_department_tree(
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """부서 계층 구조 조회"""
    # 최상위 부서만 조회 (parent_id가 None)
    query = select(Department).filter(Department.parent_id == None).options(
        selectinload(Department.children)
    )
    result = await db.execute(query)
    departments = result.scalars().all()

    # 재귀적으로 하위 부서 로드
    async def load_children(dept):
        dept_dict = {
            "id": dept.id,
            "name": dept.name,
            "code": dept.code,
            "description": dept.description,
            "parent_id": dept.parent_id,
            "created_at": dept.created_at,
            "updated_at": dept.updated_at,
            "children": []
        }

        # 하위 부서 조회
        child_query = select(Department).filter(Department.parent_id == dept.id)
        child_result = await db.execute(child_query)
        children = child_result.scalars().all()

        for child in children:
            child_data = await load_children(child)
            dept_dict["children"].append(child_data)

        return dept_dict

    tree = []
    for dept in departments:
        dept_data = await load_children(dept)
        tree.append(dept_data)

    return tree


@router.post("/", response_model=DepartmentResponse, status_code=201)
async def create_department(
    department: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("department", "create"))
):
    """부서 생성 (admin/manager만)"""
    # 부서 코드 중복 확인
    existing = await db.execute(
        select(Department).filter(Department.code == department.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="부서 코드가 이미 존재합니다")

    # 상위 부서 존재 확인
    if department.parent_id:
        parent = await db.execute(
            select(Department).filter(Department.id == department.parent_id)
        )
        if not parent.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="상위 부서를 찾을 수 없습니다")

    db_department = Department(**department.model_dump())
    db.add(db_department)
    await db.commit()
    await db.refresh(db_department)
    return db_department


@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """부서 상세 조회"""
    result = await db.execute(
        select(Department).filter(Department.id == department_id)
    )
    department = result.scalar_one_or_none()
    if not department:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")
    return department


@router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: int,
    department_update: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("department", "update"))
):
    """부서 수정 (admin/manager만)"""
    result = await db.execute(
        select(Department).filter(Department.id == department_id)
    )
    db_department = result.scalar_one_or_none()
    if not db_department:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")

    # 부서 코드 변경 시 중복 확인
    if department_update.code and department_update.code != db_department.code:
        existing = await db.execute(
            select(Department).filter(Department.code == department_update.code)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="부서 코드가 이미 존재합니다")

    # 업데이트
    for field, value in department_update.model_dump(exclude_unset=True).items():
        setattr(db_department, field, value)

    await db.commit()
    await db.refresh(db_department)
    return db_department


@router.delete("/{department_id}", status_code=204)
async def delete_department(
    department_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("department", "delete"))
):
    """부서 삭제 (admin만)"""
    result = await db.execute(
        select(Department).filter(Department.id == department_id)
    )
    db_department = result.scalar_one_or_none()
    if not db_department:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")

    # 하위 부서가 있는지 확인
    children = await db.execute(
        select(Department).filter(Department.parent_id == department_id)
    )
    if children.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="하위 부서가 존재합니다. 먼저 하위 부서를 삭제하세요."
        )

    await db.delete(db_department)
    await db.commit()
