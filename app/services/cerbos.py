"""Cerbos 권한 관리 서비스"""
import httpx
from typing import Dict, List, Optional
from app.core.config import settings


class CerbosClient:
    """Cerbos API 클라이언트"""

    def __init__(self):
        self.base_url = f"http://{settings.CERBOS_HOST}:{settings.CERBOS_PORT}"
        self.api_url = f"{self.base_url}/api/check"

    async def check_permission(
        self,
        principal_id: str,
        principal_roles: List[str],
        resource_kind: str,
        resource_id: str,
        actions: List[str],
        resource_attr: Optional[Dict] = None,
        principal_attr: Optional[Dict] = None,
    ) -> Dict[str, bool]:
        """
        권한 확인

        Args:
            principal_id: 사용자 ID
            principal_roles: 사용자 역할 리스트
            resource_kind: 리소스 종류 (document, usage_history, notice 등)
            resource_id: 리소스 ID
            actions: 확인할 액션 리스트 (read, write, delete 등)
            resource_attr: 리소스 속성 (부서 정보 등)
            principal_attr: 사용자 속성 (부서 정보 등)

        Returns:
            Dict[str, bool]: 액션별 허용 여부
        """
        payload = {
            "principal": {
                "id": principal_id,
                "roles": principal_roles,
                "attr": principal_attr or {}
            },
            "resource": {
                "kind": resource_kind,
                "id": resource_id,
                "attr": resource_attr or {}
            },
            "actions": actions
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    timeout=5.0
                )
                response.raise_for_status()
                result = response.json()

                # 결과를 액션별 딕셔너리로 변환
                permissions = {}
                for action_result in result.get("results", []):
                    action = action_result.get("action")
                    effect = action_result.get("effect")
                    permissions[action] = effect == "EFFECT_ALLOW"

                return permissions

        except httpx.RequestError as e:
            # Cerbos 연결 실패 시 기본 권한 정책 적용
            print(f"Cerbos connection error: {e}")
            return {action: False for action in actions}

        except Exception as e:
            print(f"Cerbos permission check error: {e}")
            return {action: False for action in actions}

    async def check_single_permission(
        self,
        principal_id: str,
        principal_roles: List[str],
        resource_kind: str,
        resource_id: str,
        action: str,
        resource_attr: Optional[Dict] = None,
        principal_attr: Optional[Dict] = None,
    ) -> bool:
        """
        단일 권한 확인

        Returns:
            bool: 권한 허용 여부
        """
        result = await self.check_permission(
            principal_id=principal_id,
            principal_roles=principal_roles,
            resource_kind=resource_kind,
            resource_id=resource_id,
            actions=[action],
            resource_attr=resource_attr,
            principal_attr=principal_attr
        )
        return result.get(action, False)


# 싱글톤 인스턴스
cerbos_client = CerbosClient()


async def can_read_document(user_id: str, user_roles: List[str], document_id: str, user_department: str, document_department: str) -> bool:
    """문서 읽기 권한 확인"""
    return await cerbos_client.check_single_permission(
        principal_id=user_id,
        principal_roles=user_roles,
        resource_kind="document",
        resource_id=document_id,
        action="read",
        resource_attr={"department": document_department},
        principal_attr={"department": user_department}
    )


async def can_update_document(user_id: str, user_roles: List[str], document_id: str) -> bool:
    """문서 수정 권한 확인"""
    return await cerbos_client.check_single_permission(
        principal_id=user_id,
        principal_roles=user_roles,
        resource_kind="document",
        resource_id=document_id,
        action="update"
    )


async def can_delete_document(user_id: str, user_roles: List[str], document_id: str) -> bool:
    """문서 삭제 권한 확인"""
    return await cerbos_client.check_single_permission(
        principal_id=user_id,
        principal_roles=user_roles,
        resource_kind="document",
        resource_id=document_id,
        action="delete"
    )
