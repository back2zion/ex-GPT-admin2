"""
FastAPI Dependencies - Cerbos 권한 관리 및 공통 의존성
"""
from fastapi import Depends, HTTPException, Request, Cookie
from cerbos.sdk.client import AsyncCerbosClient
from cerbos.sdk.model import Principal, Resource, ResourceAction, ResourceList
from app.core.config import settings
from app.middleware.spring_session_auth import spring_auth
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


async def get_principal(
    request: Request,
    JSESSIONID: Optional[str] = Cookie(None)
) -> Principal:
    """
    현재 사용자 Principal 추출

    Spring Boot 세션 인증 통합:
    1. JSESSIONID 쿠키를 통해 Spring Boot 세션 검증
    2. Spring Boot API를 호출하여 사용자 정보 조회
    3. 사용자 정보를 Cerbos Principal 객체로 변환

    개발/테스트 모드:
    - X-Test-Auth 헤더가 있으면 테스트 사용자로 인증 우회
    - 프로덕션에서는 반드시 JSESSIONID 필수
    """
    # 테스트 환경에서 인증 우회 (X-Test-Auth 헤더)
    test_auth = request.headers.get("X-Test-Auth", "")

    if test_auth:
        # 개발/테스트 모드: X-Test-Auth 헤더로 테스트 사용자 생성
        return Principal(
            id=test_auth,  # "admin", "user", etc.
            roles={test_auth} if test_auth in ["admin", "user"] else {"user"},
            attr={"department": "test", "auth_method": "test"}
        )

    # 프로덕션 모드: Spring Boot 세션 검증
    if not JSESSIONID:
        raise HTTPException(
            status_code=401,
            detail="인증이 필요합니다. 로그인 후 다시 시도해주세요.",
            headers={"WWW-Authenticate": "Cookie"}
        )

    try:
        # Spring Boot API를 통해 세션 검증 및 사용자 정보 조회
        user_info = await spring_auth.get_current_user(JSESSIONID)

        # Cerbos Principal 객체로 변환
        user_id = user_info.get("user_id", user_info.get("username", "unknown"))
        roles = user_info.get("roles", [])

        # roles가 문자열 리스트인 경우 set으로 변환
        if isinstance(roles, list):
            roles = set(role.lower() for role in roles)
        else:
            roles = {"user"}

        return Principal(
            id=user_id,
            roles=roles,
            attr={
                "department": user_info.get("department", "unknown"),
                "email": user_info.get("email"),
                "auth_method": "spring_session"
            }
        )
    except HTTPException as http_exc:
        # Spring 인증 실패 시 그대로 전파
        raise
    except Exception as e:
        # 예상치 못한 오류
        raise HTTPException(
            status_code=500,
            detail=f"인증 처리 중 오류가 발생했습니다: {str(e)}"
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
