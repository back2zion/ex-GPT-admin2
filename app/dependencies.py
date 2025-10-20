"""
FastAPI Dependencies - Cerbos 권한 관리 및 공통 의존성
"""
from fastapi import Depends, HTTPException, Request
from cerbos.sdk.client import AsyncCerbosClient
from cerbos.sdk.model import Principal, Resource, ResourceAction, ResourceList
from app.core.config import settings
from typing import Callable, Optional

# Cerbos 클라이언트 싱글톤
_cerbos_client: Optional[AsyncCerbosClient] = None


async def get_cerbos_client() -> AsyncCerbosClient:
    """Cerbos 클라이언트 의존성 (싱글톤 패턴)"""
    global _cerbos_client
    if _cerbos_client is None:
        _cerbos_client = AsyncCerbosClient(
            host=f"http://{settings.CERBOS_HOST}:{settings.CERBOS_PORT}"
        )
    return _cerbos_client


async def get_principal(request: Request) -> Principal:
    """
    현재 사용자 Principal 추출

    ⚠️ **보안 경고**: 현재 하드코딩된 admin 사용자 사용 중
    ⚠️ **프로덕션 배포 전 필수**: JWT 인증 구현 필요

    **TODO Phase 1**: JWT 토큰 기반 인증 구현
    1. Authorization 헤더에서 Bearer 토큰 추출
    2. JWT 서명 검증 (HS256 또는 RS256)
    3. 토큰에서 사용자 정보 추출 (user_id, roles, department)
    4. 토큰 만료 시간 검증
    5. 블랙리스트 확인 (옵션)

    **구현 예시**:
    ```python
    from jose import JWTError, jwt
    from datetime import datetime

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        roles = payload.get("roles", [])
        department = payload.get("department")

        if not user_id:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰")

        return Principal(
            id=user_id,
            roles=set(roles),
            attr={"department": department}
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="토큰 검증 실패")
    ```
    """
    # ⚠️ MVP ONLY: 임시 하드코딩 (프로덕션 사용 금지)
    # TODO: 위의 JWT 인증 코드로 교체 필요
    import warnings
    warnings.warn(
        "하드코딩된 admin principal 사용 중! 프로덕션 배포 전 JWT 인증 구현 필수",
        UserWarning,
        stacklevel=2
    )

    return Principal(
        id="admin",  # ⚠️ HARDCODED - INSECURE
        roles={"admin"},  # ⚠️ ALL PERMISSIONS
        attr={"department": "engineering"}
    )


async def check_resource_permission(
    principal: Principal,
    resource: Resource,
    action: str,
    cerbos: AsyncCerbosClient
) -> bool:
    """
    Cerbos CheckResources API 호출

    Args:
        principal: 사용자 정보
        resource: 리소스 정보
        action: 작업 (read, create, update, delete 등)
        cerbos: Cerbos 클라이언트

    Returns:
        권한이 있으면 True

    Raises:
        HTTPException(403): 권한이 없는 경우
    """
    try:
        result = await cerbos.check_resources(
            principal=principal,
            resources=ResourceList(
                resources=[ResourceAction(resource=resource, actions=[action])]
            )
        )

        resource_result = result.results[0]
        if not resource_result.is_allowed(action):
            raise HTTPException(
                status_code=403,
                detail=f"{resource.kind}에 대한 {action} 권한이 없습니다"
            )
        return True
    except HTTPException:
        raise
    except Exception as e:
        # Cerbos 연결 실패 등의 오류
        raise HTTPException(
            status_code=503,
            detail=f"권한 서버 연결 실패: {str(e)}"
        )


def require_permission(resource_kind: str, action: str) -> Callable:
    """
    권한 체크 Depends 생성 팩토리

    Usage:
        @router.post("/")
        async def create_notice(
            ...,
            principal: Principal = Depends(require_permission("notice", "create"))
        ):
            ...

    Args:
        resource_kind: 리소스 종류 (notice, usage_history, satisfaction 등)
        action: 작업 (read, create, update, delete)

    Returns:
        FastAPI Depends에서 사용할 수 있는 함수
    """
    async def permission_checker(
        principal: Principal = Depends(get_principal),
        cerbos: AsyncCerbosClient = Depends(get_cerbos_client)
    ) -> Principal:
        resource = Resource(id="any", kind=resource_kind)
        await check_resource_permission(principal, resource, action, cerbos)
        return principal

    return permission_checker


def require_resource_permission(resource_kind: str, action: str, id_param: str = "id") -> Callable:
    """
    특정 리소스 ID에 대한 권한 체크 (향후 사용)

    Phase 2에서 리소스별 세밀한 권한 제어 시 사용

    Args:
        resource_kind: 리소스 종류
        action: 작업
        id_param: 리소스 ID 파라미터 이름 (기본: "id")

    Returns:
        FastAPI Depends에서 사용할 수 있는 함수
    """
    async def permission_checker(
        resource_id: int,
        principal: Principal = Depends(get_principal),
        cerbos: AsyncCerbosClient = Depends(get_cerbos_client)
    ) -> Principal:
        resource = Resource(id=str(resource_id), kind=resource_kind)
        await check_resource_permission(principal, resource, action, cerbos)
        return principal

    return permission_checker
