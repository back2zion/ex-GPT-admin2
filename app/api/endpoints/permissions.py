from fastapi import APIRouter
from typing import List

router = APIRouter()


@router.get("/roles")
async def list_roles():
    """역할 목록 조회"""
    # TODO: 역할 목록 반환
    return {
        "roles": ["admin", "manager", "user", "viewer"]
    }


@router.get("/departments")
async def list_departments():
    """부서 목록 조회"""
    # TODO: 부서 목록 반환
    return {
        "departments": []
    }


@router.post("/document-access")
async def set_document_access(
    document_id: str,
    departments: List[str] = [],
    approval_lines: List[str] = []
):
    """문서 접근 권한 설정"""
    # TODO: Cerbos 정책 업데이트
    return {
        "message": "Access permissions updated",
        "document_id": document_id
    }


@router.get("/user/{user_id}/permissions")
async def get_user_permissions(user_id: str):
    """사용자 권한 조회"""
    # TODO: Cerbos를 통한 사용자 권한 확인
    return {
        "user_id": user_id,
        "roles": [],
        "permissions": []
    }


@router.post("/check")
async def check_permission(
    user_id: str,
    resource: str,
    action: str
):
    """권한 확인"""
    # TODO: Cerbos를 통한 권한 확인
    return {
        "allowed": False,
        "user_id": user_id,
        "resource": resource,
        "action": action
    }
