"""
결재라인 관리 CRUD API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.models.permission import Department
from app.models.document_permission import ApprovalLine
from app.schemas.approval_line import ApprovalLineCreate, ApprovalLineUpdate, ApprovalLineResponse
from app.core.database import get_db
from app.dependencies import require_permission, get_principal
from cerbos.sdk.model import Principal


router = APIRouter(prefix="/api/v1/admin/approval-lines", tags=["admin-approval-lines"])


@router.get("")
async def list_approval_lines(
    skip: int = Query(0, ge=0, description="오프셋"),
    limit: int = Query(100, le=1000, description="최대 개수"),
    search: Optional[str] = Query(None, description="검색어 (이름)"),
    sort_by: Optional[str] = Query("name", description="정렬 필드"),
    order: Optional[str] = Query("asc", description="정렬 방향 (asc, desc)"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    결재라인 목록 조회 (Pagination 및 Sorting 지원)

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
    query = select(ApprovalLine)
    count_query = select(func.count()).select_from(ApprovalLine)

    # Filters
    if search:
        search_filter = ApprovalLine.name.contains(search)
        query = query.filter(search_filter)
        count_query = count_query.filter(search_filter)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Sorting
    sort_column = getattr(ApprovalLine, sort_by, ApprovalLine.name)
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


@router.post("", response_model=ApprovalLineResponse, status_code=201)
async def create_approval_line(
    approval_line: ApprovalLineCreate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("approval_line", "create"))
):
    """결재라인 생성 (admin/manager만)"""
    # 부서 ID 유효성 검증
    if approval_line.departments:
        dept_ids = approval_line.departments if isinstance(approval_line.departments, list) else []
        if dept_ids:
            result = await db.execute(
                select(Department).filter(Department.id.in_(dept_ids))
            )
            existing_depts = result.scalars().all()
            if len(existing_depts) != len(dept_ids):
                raise HTTPException(status_code=404, detail="일부 부서를 찾을 수 없습니다")

    db_approval_line = ApprovalLine(**approval_line.model_dump())
    db.add(db_approval_line)
    await db.commit()
    await db.refresh(db_approval_line)
    return db_approval_line


@router.get("/{approval_line_id}", response_model=ApprovalLineResponse)
async def get_approval_line(
    approval_line_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """결재라인 상세 조회"""
    result = await db.execute(
        select(ApprovalLine).filter(ApprovalLine.id == approval_line_id)
    )
    approval_line = result.scalar_one_or_none()
    if not approval_line:
        raise HTTPException(status_code=404, detail="결재라인을 찾을 수 없습니다")
    return approval_line


@router.put("/{approval_line_id}", response_model=ApprovalLineResponse)
async def update_approval_line(
    approval_line_id: int,
    approval_line_update: ApprovalLineUpdate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("approval_line", "update"))
):
    """결재라인 수정 (admin/manager만)"""
    result = await db.execute(
        select(ApprovalLine).filter(ApprovalLine.id == approval_line_id)
    )
    db_approval_line = result.scalar_one_or_none()
    if not db_approval_line:
        raise HTTPException(status_code=404, detail="결재라인을 찾을 수 없습니다")

    # 부서 ID 유효성 검증 (업데이트 시)
    if approval_line_update.departments is not None:
        dept_ids = approval_line_update.departments if isinstance(approval_line_update.departments, list) else []
        if dept_ids:
            dept_result = await db.execute(
                select(Department).filter(Department.id.in_(dept_ids))
            )
            existing_depts = dept_result.scalars().all()
            if len(existing_depts) != len(dept_ids):
                raise HTTPException(status_code=404, detail="일부 부서를 찾을 수 없습니다")

    # 업데이트
    for field, value in approval_line_update.model_dump(exclude_unset=True).items():
        setattr(db_approval_line, field, value)

    await db.commit()
    await db.refresh(db_approval_line)
    return db_approval_line


@router.delete("/{approval_line_id}", status_code=204)
async def delete_approval_line(
    approval_line_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("approval_line", "delete"))
):
    """결재라인 삭제 (admin만)"""
    result = await db.execute(
        select(ApprovalLine).filter(ApprovalLine.id == approval_line_id)
    )
    db_approval_line = result.scalar_one_or_none()
    if not db_approval_line:
        raise HTTPException(status_code=404, detail="결재라인을 찾을 수 없습니다")

    await db.delete(db_approval_line)
    await db.commit()
