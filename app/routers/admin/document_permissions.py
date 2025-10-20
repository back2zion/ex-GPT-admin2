"""
문서 권한 관리 CRUD API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.models.permission import Department
from app.models.document_permission import DocumentPermission, ApprovalLine
from app.models.document import Document
from app.schemas.document_permission import (
    DocumentPermissionCreate,
    DocumentPermissionUpdate,
    DocumentPermissionResponse
)
from app.core.database import get_db
from app.dependencies import require_permission, get_principal
from cerbos.sdk.model import Principal


router = APIRouter(prefix="/api/v1/admin/document-permissions", tags=["admin-document-permissions"])


@router.get("/", response_model=List[DocumentPermissionResponse])
async def list_document_permissions(
    skip: int = Query(0, ge=0, description="오프셋"),
    limit: int = Query(100, le=1000, description="최대 개수"),
    document_id: Optional[int] = Query(None, description="문서 ID 필터"),
    department_id: Optional[int] = Query(None, description="부서 ID 필터"),
    approval_line_id: Optional[int] = Query(None, description="결재라인 ID 필터"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """문서 권한 목록 조회"""
    query = select(DocumentPermission).options(
        selectinload(DocumentPermission.department),
        selectinload(DocumentPermission.approval_line)
    )

    if document_id is not None:
        query = query.filter(DocumentPermission.document_id == document_id)

    if department_id is not None:
        query = query.filter(DocumentPermission.department_id == department_id)

    if approval_line_id is not None:
        query = query.filter(DocumentPermission.approval_line_id == approval_line_id)

    query = query.order_by(DocumentPermission.document_id).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=DocumentPermissionResponse, status_code=201)
async def create_document_permission(
    doc_perm: DocumentPermissionCreate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("document_permission", "create"))
):
    """문서 권한 생성 (admin/manager만)"""
    # 문서 존재 확인
    doc_result = await db.execute(
        select(Document).filter(Document.id == doc_perm.document_id)
    )
    if not doc_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    # 부서 또는 결재라인 중 하나는 있어야 함
    if not doc_perm.department_id and not doc_perm.approval_line_id:
        raise HTTPException(
            status_code=400,
            detail="부서 또는 결재라인 중 하나는 지정해야 합니다"
        )

    # 부서 존재 확인
    if doc_perm.department_id:
        dept_result = await db.execute(
            select(Department).filter(Department.id == doc_perm.department_id)
        )
        if not dept_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")

    # 결재라인 존재 확인
    if doc_perm.approval_line_id:
        approval_result = await db.execute(
            select(ApprovalLine).filter(ApprovalLine.id == doc_perm.approval_line_id)
        )
        if not approval_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="결재라인을 찾을 수 없습니다")

    # 중복 확인
    existing_query = select(DocumentPermission).filter(
        DocumentPermission.document_id == doc_perm.document_id
    )
    if doc_perm.department_id:
        existing_query = existing_query.filter(
            DocumentPermission.department_id == doc_perm.department_id
        )
    if doc_perm.approval_line_id:
        existing_query = existing_query.filter(
            DocumentPermission.approval_line_id == doc_perm.approval_line_id
        )

    existing = await db.execute(existing_query)
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="동일한 권한이 이미 존재합니다")

    db_doc_perm = DocumentPermission(**doc_perm.model_dump())
    db.add(db_doc_perm)
    await db.commit()
    await db.refresh(
        db_doc_perm,
        attribute_names=['department', 'approval_line']
    )
    return db_doc_perm


@router.get("/{permission_id}", response_model=DocumentPermissionResponse)
async def get_document_permission(
    permission_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """문서 권한 상세 조회"""
    result = await db.execute(
        select(DocumentPermission).options(
            selectinload(DocumentPermission.department),
            selectinload(DocumentPermission.approval_line)
        ).filter(DocumentPermission.id == permission_id)
    )
    doc_perm = result.scalar_one_or_none()
    if not doc_perm:
        raise HTTPException(status_code=404, detail="문서 권한을 찾을 수 없습니다")
    return doc_perm


@router.put("/{permission_id}", response_model=DocumentPermissionResponse)
async def update_document_permission(
    permission_id: int,
    doc_perm_update: DocumentPermissionUpdate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("document_permission", "update"))
):
    """문서 권한 수정 (admin/manager만)"""
    result = await db.execute(
        select(DocumentPermission).options(
            selectinload(DocumentPermission.department),
            selectinload(DocumentPermission.approval_line)
        ).filter(DocumentPermission.id == permission_id)
    )
    db_doc_perm = result.scalar_one_or_none()
    if not db_doc_perm:
        raise HTTPException(status_code=404, detail="문서 권한을 찾을 수 없습니다")

    # 부서 존재 확인 (업데이트 시)
    if doc_perm_update.department_id:
        dept_result = await db.execute(
            select(Department).filter(Department.id == doc_perm_update.department_id)
        )
        if not dept_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")

    # 결재라인 존재 확인 (업데이트 시)
    if doc_perm_update.approval_line_id:
        approval_result = await db.execute(
            select(ApprovalLine).filter(ApprovalLine.id == doc_perm_update.approval_line_id)
        )
        if not approval_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="결재라인을 찾을 수 없습니다")

    # 업데이트
    for field, value in doc_perm_update.model_dump(exclude_unset=True).items():
        setattr(db_doc_perm, field, value)

    await db.commit()
    await db.refresh(
        db_doc_perm,
        attribute_names=['department', 'approval_line']
    )
    return db_doc_perm


@router.delete("/{permission_id}", status_code=204)
async def delete_document_permission(
    permission_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("document_permission", "delete"))
):
    """문서 권한 삭제 (admin만)"""
    result = await db.execute(
        select(DocumentPermission).filter(DocumentPermission.id == permission_id)
    )
    db_doc_perm = result.scalar_one_or_none()
    if not db_doc_perm:
        raise HTTPException(status_code=404, detail="문서 권한을 찾을 수 없습니다")

    await db.delete(db_doc_perm)
    await db.commit()
