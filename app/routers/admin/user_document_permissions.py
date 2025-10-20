"""
사용자별 문서 권한 관리 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import Optional

from app.core.database import get_db
from app.models.user import User
from app.models.document_permission import UserDocumentPermission
from app.models.permission import Department
from app.schemas.user_document_permission import (
    UsersListWithDocPermissionsResponse,
    UserWithDocPermissionsResponse,
    GrantDocPermissionRequest,
    GrantDocPermissionResponse,
    RevokeDocPermissionResponse
)


router = APIRouter(prefix="/api/v1/admin/user-document-permissions", tags=["admin-user-document-permissions"])


@router.get("/users", response_model=UsersListWithDocPermissionsResponse)
async def list_users_with_doc_permissions(
    search: Optional[str] = Query(None, description="검색어 (이름, 이메일, 사번)"),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자 목록 조회 (문서 권한 포함)
    """
    # 사용자와 관련된 문서 권한을 함께 조회
    query = select(User).options(
        selectinload(User.department),
        selectinload(User.document_permissions).selectinload(UserDocumentPermission.department)
    ).where(User.is_active == True)

    # 검색 조건
    if search:
        query = query.where(
            (User.username.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%")) |
            (User.full_name.ilike(f"%{search}%"))
        )

    result = await db.execute(query)
    users = result.scalars().all()

    # 응답 데이터 구성
    users_data = []
    for user in users:
        # 사용자가 접근 가능한 부서명 목록
        doc_permissions = [perm.department.name for perm in user.document_permissions if perm.department]

        users_data.append(UserWithDocPermissionsResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            department_name=user.department.name if user.department else None,
            doc_permissions=doc_permissions
        ))

    return UsersListWithDocPermissionsResponse(users=users_data, total=len(users_data))


@router.post("/grant", response_model=GrantDocPermissionResponse)
async def grant_doc_permission(
    request: GrantDocPermissionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    사용자에게 부서 문서 권한 부여
    - 기존 권한은 모두 삭제하고 새로 부여
    """
    # 사용자 조회
    user_result = await db.execute(select(User).where(User.id == request.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    # 부서 존재 확인
    dept_result = await db.execute(
        select(Department).where(Department.id.in_(request.department_ids))
    )
    departments = dept_result.scalars().all()
    if len(departments) != len(request.department_ids):
        raise HTTPException(status_code=404, detail="일부 부서를 찾을 수 없습니다")

    # 기존 권한 삭제
    await db.execute(
        delete(UserDocumentPermission).where(UserDocumentPermission.user_id == request.user_id)
    )

    # 새 권한 부여
    granted_count = 0
    for dept_id in request.department_ids:
        new_permission = UserDocumentPermission(
            user_id=request.user_id,
            department_id=dept_id
        )
        db.add(new_permission)
        granted_count += 1

    await db.commit()

    return GrantDocPermissionResponse(
        granted_count=granted_count,
        message=f"{granted_count}개 부서에 대한 문서 접근 권한이 부여되었습니다"
    )


@router.delete("/{user_id}/departments/{department_id}", response_model=RevokeDocPermissionResponse)
async def revoke_doc_permission(
    user_id: int,
    department_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    특정 부서에 대한 사용자 문서 권한 회수
    """
    # 권한 조회
    result = await db.execute(
        select(UserDocumentPermission).where(
            UserDocumentPermission.user_id == user_id,
            UserDocumentPermission.department_id == department_id
        )
    )
    permission = result.scalar_one_or_none()

    if not permission:
        raise HTTPException(status_code=404, detail="권한을 찾을 수 없습니다")

    await db.delete(permission)
    await db.commit()

    return RevokeDocPermissionResponse(
        revoked_count=1,
        message="문서 접근 권한이 회수되었습니다"
    )


@router.delete("/{user_id}/all", response_model=RevokeDocPermissionResponse)
async def revoke_all_doc_permissions(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    사용자의 모든 문서 권한 회수
    """
    # 사용자 존재 확인
    user_result = await db.execute(select(User).where(User.id == user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    # 모든 권한 삭제
    result = await db.execute(
        delete(UserDocumentPermission).where(UserDocumentPermission.user_id == user_id)
    )

    revoked_count = result.rowcount
    await db.commit()

    return RevokeDocPermissionResponse(
        revoked_count=revoked_count,
        message=f"{revoked_count}개 부서에 대한 문서 접근 권한이 회수되었습니다"
    )
