"""
문서 접근 제어 서비스
PRD_v2.md P0 요구사항: FUN-001

기존 DocumentPermission을 활용하여 부서별 학습데이터 참조 범위를 관리합니다.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.models.document import Document
from app.models.document_permission import DocumentPermission
from app.models.permission import Department
from app.models.user import User


class DocumentAccessService:
    """문서 접근 제어 서비스"""

    async def grant_department_access(
        self,
        document_id: int,
        department_ids: List[int],
        db: AsyncSession,
        can_read: bool = True,
        can_write: bool = False
    ) -> List[DocumentPermission]:
        """
        문서에 대한 부서 접근 권한을 부여합니다.

        Args:
            document_id: 문서 ID
            department_ids: 부서 ID 목록
            db: 데이터베이스 세션
            can_read: 읽기 권한
            can_write: 쓰기 권한

        Returns:
            생성된 DocumentPermission 목록
        """
        permissions = []
        for dept_id in department_ids:
            # 기존 권한 확인
            existing = await db.execute(
                select(DocumentPermission).filter(
                    DocumentPermission.document_id == document_id,
                    DocumentPermission.department_id == dept_id
                )
            )
            permission = existing.scalar_one_or_none()

            if permission:
                # 기존 권한 업데이트
                permission.can_read = can_read
                permission.can_write = can_write
            else:
                # 새 권한 생성
                permission = DocumentPermission(
                    document_id=document_id,
                    department_id=dept_id,
                    can_read=can_read,
                    can_write=can_write
                )
                db.add(permission)

            permissions.append(permission)

        await db.commit()
        return permissions

    async def grant_all_departments_access(
        self,
        document_id: int,
        db: AsyncSession
    ) -> List[DocumentPermission]:
        """
        문서를 전체 부서에 공개합니다.

        PRD 예시: 국가계약법 → 전부서

        Args:
            document_id: 문서 ID
            db: 데이터베이스 세션

        Returns:
            생성된 DocumentPermission 목록
        """
        # 모든 부서 조회
        all_depts_result = await db.execute(select(Department))
        all_depts = all_depts_result.scalars().all()

        # 모든 부서에 대해 권한 부여
        return await self.grant_department_access(
            document_id=document_id,
            department_ids=[dept.id for dept in all_depts],
            db=db,
            can_read=True
        )

    async def revoke_department_access(
        self,
        document_id: int,
        department_ids: List[int],
        db: AsyncSession
    ) -> int:
        """
        문서에 대한 부서 접근 권한을 회수합니다.

        Args:
            document_id: 문서 ID
            department_ids: 부서 ID 목록
            db: 데이터베이스 세션

        Returns:
            삭제된 권한 수
        """
        result = await db.execute(
            select(DocumentPermission).filter(
                DocumentPermission.document_id == document_id,
                DocumentPermission.department_id.in_(department_ids)
            )
        )
        permissions = result.scalars().all()

        for permission in permissions:
            await db.delete(permission)

        await db.commit()
        return len(permissions)

    async def can_user_access_document(
        self,
        user_id: int,
        document_id: int,
        db: AsyncSession
    ) -> bool:
        """
        사용자가 문서에 접근 가능한지 확인합니다.

        Args:
            user_id: 사용자 ID
            document_id: 문서 ID
            db: 데이터베이스 세션

        Returns:
            접근 가능 여부
        """
        # 사용자 조회
        user_result = await db.execute(
            select(User).filter(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user or not user.department_id:
            return False

        # 문서 권한 확인
        permission_result = await db.execute(
            select(DocumentPermission).filter(
                DocumentPermission.document_id == document_id,
                DocumentPermission.department_id == user.department_id,
                DocumentPermission.can_read == True
            )
        )
        permission = permission_result.scalar_one_or_none()

        return permission is not None

    async def get_accessible_documents(
        self,
        user_id: int,
        db: AsyncSession
    ) -> List[Document]:
        """
        사용자가 접근 가능한 문서 목록을 조회합니다.

        RAG 검색 시 이 메서드를 호출하여 부서별로 문서를 필터링합니다.

        Args:
            user_id: 사용자 ID
            db: 데이터베이스 세션

        Returns:
            접근 가능한 문서 목록
        """
        # 사용자 조회
        user_result = await db.execute(
            select(User).filter(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user or not user.department_id:
            return []

        # 사용자 부서에서 접근 가능한 문서 권한 조회
        permissions_result = await db.execute(
            select(DocumentPermission).filter(
                DocumentPermission.department_id == user.department_id,
                DocumentPermission.can_read == True
            )
        )
        permissions = permissions_result.scalars().all()

        if not permissions:
            return []

        # 문서 ID 추출
        document_ids = [p.document_id for p in permissions]

        # 문서 조회
        docs_result = await db.execute(
            select(Document).filter(
                Document.id.in_(document_ids),
                Document.status == "active"
            )
        )
        return docs_result.scalars().all()

    async def get_document_accessible_departments(
        self,
        document_id: int,
        db: AsyncSession
    ) -> List[Department]:
        """
        문서에 접근 가능한 부서 목록을 조회합니다.

        Args:
            document_id: 문서 ID
            db: 데이터베이스 세션

        Returns:
            접근 가능한 부서 목록
        """
        permissions_result = await db.execute(
            select(DocumentPermission).filter(
                DocumentPermission.document_id == document_id,
                DocumentPermission.can_read == True
            )
        )
        permissions = permissions_result.scalars().all()

        if not permissions:
            return []

        # 부서 ID 추출
        dept_ids = [p.department_id for p in permissions if p.department_id]

        if not dept_ids:
            return []

        # 부서 조회
        depts_result = await db.execute(
            select(Department).filter(Department.id.in_(dept_ids))
        )
        return depts_result.scalars().all()
