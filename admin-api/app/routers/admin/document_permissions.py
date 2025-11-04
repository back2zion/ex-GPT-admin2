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


@router.get("")
async def list_document_permissions(
    skip: int = Query(0, ge=0, description="오프셋"),
    limit: int = Query(100, le=1000, description="최대 개수"),
    document_id: Optional[int] = Query(None, description="문서 ID 필터"),
    department_id: Optional[int] = Query(None, description="부서 ID 필터"),
    approval_line_id: Optional[int] = Query(None, description="결재라인 ID 필터"),
    sort_by: Optional[str] = Query("document_id", description="정렬 필드"),
    order: Optional[str] = Query("asc", description="정렬 방향 (asc, desc)"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    문서 권한 목록 조회 (Pagination 및 Sorting 지원)

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
    query = select(DocumentPermission).options(
        selectinload(DocumentPermission.document),
        selectinload(DocumentPermission.department),
        selectinload(DocumentPermission.approval_line)
    )
    count_query = select(func.count()).select_from(DocumentPermission)

    # Filters
    if document_id is not None:
        query = query.filter(DocumentPermission.document_id == document_id)
        count_query = count_query.filter(DocumentPermission.document_id == document_id)

    if department_id is not None:
        query = query.filter(DocumentPermission.department_id == department_id)
        count_query = count_query.filter(DocumentPermission.department_id == department_id)

    if approval_line_id is not None:
        query = query.filter(DocumentPermission.approval_line_id == approval_line_id)
        count_query = count_query.filter(DocumentPermission.approval_line_id == approval_line_id)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Sorting
    sort_column = getattr(DocumentPermission, sort_by, DocumentPermission.document_id)
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


@router.post("", response_model=DocumentPermissionResponse, status_code=201)
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


# === 통계 및 분석 API (TDD) ===
# IMPORTANT: 이 라우트들은 /{permission_id} 보다 먼저 정의되어야 함 (FastAPI 경로 매칭 순서)

@router.get("/stats/users/{user_id}")
async def get_user_document_statistics(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    사용자별 문서 접근 통계 조회

    시큐어 코딩:
    - SQLAlchemy ORM 사용 (SQL Injection 방지)
    - Cerbos 권한 검증
    - 민감 정보 제외

    Returns:
        {
            "accessible_documents_count": int,
            "by_department": int,
            "by_approval_line": int,
            "details": [...]
        }
    """
    from app.models.user import User
    from sqlalchemy import func, or_

    # 사용자 조회
    user_result = await db.execute(
        select(User).filter(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    # 부서 기반 권한 수
    dept_perms_query = select(func.count(DocumentPermission.id)).filter(
        DocumentPermission.department_id == user.department_id
    )
    dept_perms_result = await db.execute(dept_perms_query)
    by_department = dept_perms_result.scalar() or 0

    # 결재라인 기반 권한 수 (사용자 부서가 결재라인에 포함된 경우)
    # JSONB 필드 확인: PostgreSQL의 @> 연산자 사용
    approval_line_perms = 0
    if user.department_id:
        # ApprovalLine에서 사용자 부서를 포함하는 라인 찾기
        # JSONB @> 연산자: departments 배열에 user.department_id가 포함되는지 확인
        from sqlalchemy.dialects.postgresql import JSONB
        from sqlalchemy import cast, literal

        # departments 필드가 null이 아니고, 배열에 부서 ID가 포함된 경우
        approval_lines_query = select(ApprovalLine).filter(
            ApprovalLine.departments.isnot(None)
        )
        approval_lines_result = await db.execute(approval_lines_query)
        approval_lines = approval_lines_result.scalars().all()

        # Python에서 필터링
        matching_lines = [
            al for al in approval_lines
            if al.departments and user.department_id in al.departments
        ]

        if matching_lines:
            approval_line_ids = [al.id for al in matching_lines]
            al_perms_query = select(func.count(DocumentPermission.id)).filter(
                DocumentPermission.approval_line_id.in_(approval_line_ids)
            )
            al_perms_result = await db.execute(al_perms_query)
            approval_line_perms = al_perms_result.scalar() or 0

    by_approval_line = approval_line_perms
    total = by_department + by_approval_line

    return {
        "user_id": user_id,
        "accessible_documents_count": total,
        "by_department": by_department,
        "by_approval_line": by_approval_line
    }


@router.get("/stats/documents/{document_id}")
async def get_document_permission_summary(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    문서별 권한 요약 조회

    시큐어 코딩:
    - Pydantic 입력 검증
    - ORM 사용으로 SQL Injection 방지

    Returns:
        {
            "document_id": int,
            "total_permissions": int,
            "department_count": int,
            "approval_line_count": int,
            "affected_users_estimate": int
        }
    """
    from app.models.user import User
    from sqlalchemy import func

    # 문서 존재 확인
    doc_result = await db.execute(
        select(Document).filter(Document.id == document_id)
    )
    doc = doc_result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    # 총 권한 수
    total_perms_query = select(func.count(DocumentPermission.id)).filter(
        DocumentPermission.document_id == document_id
    )
    total_perms_result = await db.execute(total_perms_query)
    total_permissions = total_perms_result.scalar() or 0

    # 부서 권한 수
    dept_count_query = select(func.count(DocumentPermission.id)).filter(
        DocumentPermission.document_id == document_id,
        DocumentPermission.department_id.isnot(None)
    )
    dept_count_result = await db.execute(dept_count_query)
    department_count = dept_count_result.scalar() or 0

    # 결재라인 권한 수
    al_count_query = select(func.count(DocumentPermission.id)).filter(
        DocumentPermission.document_id == document_id,
        DocumentPermission.approval_line_id.isnot(None)
    )
    al_count_result = await db.execute(al_count_query)
    approval_line_count = al_count_result.scalar() or 0

    # 영향받는 예상 사용자 수 계산
    affected_users = 0

    # 부서 권한으로 인한 사용자
    dept_perms_query = select(DocumentPermission.department_id).filter(
        DocumentPermission.document_id == document_id,
        DocumentPermission.department_id.isnot(None)
    )
    dept_perms_result = await db.execute(dept_perms_query)
    dept_ids = [row[0] for row in dept_perms_result.fetchall()]

    if dept_ids:
        users_by_dept_query = select(func.count(User.id)).filter(
            User.department_id.in_(dept_ids)
        )
        users_by_dept_result = await db.execute(users_by_dept_query)
        affected_users += users_by_dept_result.scalar() or 0

    return {
        "document_id": document_id,
        "total_permissions": total_permissions,
        "department_count": department_count,
        "approval_line_count": approval_line_count,
        "affected_users_estimate": affected_users
    }


@router.get("/conflicts")
async def detect_permission_conflicts(
    conflict_type: Optional[str] = Query(None, description="충돌 유형 (duplicate, level)"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("document_permission", "view"))
):
    """
    권한 충돌 감지

    시큐어 코딩:
    - SQLAlchemy GROUP BY로 안전한 쿼리
    - 관리자 권한 검증
    - 입력 검증 (conflict_type)

    Returns:
        {
            "conflicts": [
                {
                    "conflict_type": "duplicate",
                    "document_id": int,
                    "department_id": int,
                    "count": int,
                    "permission_ids": [...]
                }
            ]
        }
    """
    from sqlalchemy import func, and_

    conflicts = []

    # 중복 권한 감지 (같은 document_id + department_id 조합)
    if conflict_type is None or conflict_type == "duplicate":
        duplicate_query = select(
            DocumentPermission.document_id,
            DocumentPermission.department_id,
            func.count(DocumentPermission.id).label('count')
        ).filter(
            DocumentPermission.department_id.isnot(None)
        ).group_by(
            DocumentPermission.document_id,
            DocumentPermission.department_id
        ).having(
            func.count(DocumentPermission.id) > 1
        )

        duplicate_result = await db.execute(duplicate_query)
        duplicates = duplicate_result.fetchall()

        for dup in duplicates:
            # 해당 권한 ID들 조회
            perm_ids_query = select(DocumentPermission.id).filter(
                and_(
                    DocumentPermission.document_id == dup.document_id,
                    DocumentPermission.department_id == dup.department_id
                )
            )
            perm_ids_result = await db.execute(perm_ids_query)
            perm_ids = [row[0] for row in perm_ids_result.fetchall()]

            conflicts.append({
                "conflict_type": "duplicate",
                "document_id": dup.document_id,
                "department_id": dup.department_id,
                "count": dup.count,
                "permission_ids": perm_ids,
                "severity": "high",
                "recommendation": "중복 권한을 하나로 통합하세요"
            })

    # 권한 레벨 충돌 감지 (같은 문서에 다른 레벨의 권한)
    if conflict_type == "level":
        # 같은 문서에 대해 부서와 결재라인 권한이 동시에 존재하는 경우
        level_query = select(
            DocumentPermission.document_id,
            func.count(DocumentPermission.id).label('total_count'),
            func.count(DocumentPermission.department_id).label('dept_count'),
            func.count(DocumentPermission.approval_line_id).label('al_count')
        ).group_by(
            DocumentPermission.document_id
        ).having(
            and_(
                func.count(DocumentPermission.department_id) > 0,
                func.count(DocumentPermission.approval_line_id) > 0
            )
        )

        level_result = await db.execute(level_query)
        level_conflicts = level_result.fetchall()

        for lc in level_conflicts:
            conflicts.append({
                "conflict_type": "permission_level",
                "document_id": lc.document_id,
                "department_count": lc.dept_count,
                "approval_line_count": lc.al_count,
                "severity": "medium",
                "recommendation": "부서와 결재라인 권한 레벨을 일치시키세요"
            })

    return {
        "conflicts": conflicts,
        "total_conflicts": len(conflicts)
    }


# === CRUD API (경로 매칭 순서상 나중에 정의) ===

@router.get("/{permission_id}", response_model=DocumentPermissionResponse)
async def get_document_permission(
    permission_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """문서 권한 상세 조회"""
    result = await db.execute(
        select(DocumentPermission).options(
            selectinload(DocumentPermission.document),
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
