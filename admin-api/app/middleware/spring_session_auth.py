"""
Spring Boot 세션 인증 미들웨어

기존 Spring Boot (Tomcat) 서버의 JSESSIONID를 검증하여 사용자 인증 처리
Redis 공유 세션 방식 또는 API 검증 방식 지원
"""
import httpx
from fastapi import Cookie, HTTPException, Depends
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

# 설정
# Tomcat에 배포된 Spring Boot 애플리케이션 URL
# Docker 컨테이너에서 호스트 접근: 172.17.0.1 (Docker bridge network gateway)
SPRING_BOOT_URL = "http://172.17.0.1:18180/exGenBotDS"
SPRING_BOOT_VALIDATE_API = f"{SPRING_BOOT_URL}/api/auth/validate"


class SpringSessionAuth:
    """Spring Boot 세션 인증 헬퍼"""

    def __init__(self, use_redis: bool = False):
        """
        Args:
            use_redis: True면 Redis에서 직접 세션 조회, False면 Spring Boot API 호출
        """
        self.use_redis = use_redis
        if use_redis:
            try:
                from redis import Redis
                self.redis_client = Redis(host='localhost', port=6379, db=0, decode_responses=False)
            except ImportError:
                logger.error("Redis 라이브러리가 설치되지 않았습니다: pip install redis")
                raise

    async def validate_session_via_api(self, jsessionid: str) -> Dict:
        """
        Spring Boot API를 호출하여 세션 검증

        Args:
            jsessionid: JSESSIONID 쿠키 값

        Returns:
            dict: 사용자 정보 {"user_id": "...", "roles": [...]}

        Raises:
            HTTPException: 세션 유효하지 않을 때
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    SPRING_BOOT_VALIDATE_API,
                    cookies={"JSESSIONID": jsessionid}
                )

            if response.status_code == 200:
                user_info = response.json()

                # 시큐어 코딩: authenticated 필드 검증
                if not user_info.get("authenticated", False):
                    logger.warning(f"세션 인증 실패: {user_info.get('error', 'Unknown error')}")
                    raise HTTPException(status_code=401, detail="Session expired or invalid")

                logger.info(f"세션 검증 성공: user_id={user_info.get('user_id')}")
                return user_info
            elif response.status_code == 401:
                logger.warning("세션이 만료되었거나 유효하지 않습니다")
                raise HTTPException(status_code=401, detail="Session expired or invalid")
            else:
                logger.error(f"Spring Boot API 오류: {response.status_code}")
                raise HTTPException(status_code=500, detail="Authentication service error")

        except httpx.RequestError as e:
            logger.error(f"Spring Boot 서버 연결 실패: {e}")
            raise HTTPException(status_code=503, detail="Authentication service unavailable")

    async def validate_session_via_redis(self, jsessionid: str) -> Dict:
        """
        Redis에서 직접 세션 조회 (Spring Session 형식)

        Args:
            jsessionid: JSESSIONID 쿠키 값

        Returns:
            dict: 사용자 정보 {"user_id": "...", "roles": [...]}

        Raises:
            HTTPException: 세션 유효하지 않을 때
        """
        try:
            # Spring Session의 Redis key 형식
            session_key = f"spring:session:sessions:{jsessionid}"
            session_data = self.redis_client.get(session_key)

            if not session_data:
                logger.warning(f"Redis에 세션이 없습니다: {jsessionid[:8]}...")
                raise HTTPException(status_code=401, detail="Session not found")

            # Spring Session 데이터 파싱 (Java 직렬화 형식)
            # 실제 구현 시 Spring Session의 세션 포맷에 맞게 파싱 필요
            # 여기서는 간단한 예시만 제공

            # TODO: Spring Security Context에서 사용자 정보 추출
            # session_obj = parse_spring_session(session_data)
            # user_info = extract_user_from_security_context(session_obj)

            # 임시 구현 (실제로는 위 파싱 로직 필요)
            user_info = {
                "user_id": "admin",  # 실제로는 세션에서 추출
                "roles": ["ADMIN"]
            }

            logger.info(f"Redis 세션 검증 성공: user_id={user_info.get('user_id')}")
            return user_info

        except Exception as e:
            logger.error(f"Redis 세션 조회 실패: {e}")
            raise HTTPException(status_code=500, detail="Session validation error")

    async def get_current_user(
        self,
        JSESSIONID: Optional[str] = Cookie(None)
    ) -> Dict:
        """
        현재 로그인한 사용자 정보 조회

        FastAPI Depends에서 사용:
        @app.get("/api/admin/...")
        async def some_endpoint(
            current_user: dict = Depends(spring_auth.get_current_user)
        ):
            ...

        Args:
            JSESSIONID: 쿠키에서 자동으로 가져옴

        Returns:
            dict: 사용자 정보

        Raises:
            HTTPException: 인증 실패 시
        """
        if not JSESSIONID:
            logger.warning("JSESSIONID 쿠키가 없습니다")
            raise HTTPException(
                status_code=401,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Cookie"}
            )

        # Redis 또는 API 방식으로 검증
        if self.use_redis:
            return await self.validate_session_via_redis(JSESSIONID)
        else:
            return await self.validate_session_via_api(JSESSIONID)


# Singleton 인스턴스
# use_redis=False: Spring Boot API 호출 방식 (기본)
# use_redis=True: Redis 직접 조회 방식
spring_auth = SpringSessionAuth(use_redis=False)


# FastAPI Dependency로 사용
async def get_current_user(
    JSESSIONID: Optional[str] = Cookie(None)
) -> Dict:
    """
    현재 로그인한 사용자 정보 반환

    사용 예시:
    @router.get("/users")
    async def list_users(current_user: dict = Depends(get_current_user)):
        print(f"요청 사용자: {current_user['user_id']}")
        ...
    """
    return await spring_auth.get_current_user(JSESSIONID)


# Optional: 인증이 선택적인 경우 (개발 편의용)
async def get_current_user_optional(
    JSESSIONID: Optional[str] = Cookie(None)
) -> Optional[Dict]:
    """
    현재 로그인한 사용자 정보 반환 (선택적)
    인증이 실패해도 None을 반환하고 에러를 발생시키지 않음
    """
    if not JSESSIONID:
        return None

    try:
        return await spring_auth.get_current_user(JSESSIONID)
    except HTTPException:
        return None


# Optional: 관리자 권한 체크
async def require_admin(
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """관리자 권한 필수"""
    if "ADMIN" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin role required")
    return current_user
