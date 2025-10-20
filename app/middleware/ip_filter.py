"""
IP 필터링 미들웨어
adminpage.txt: 8. 설정 > 1) 관리자관리>IP접근권한 관리

시큐어 코딩: IP 기반 접근 제어
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ip_access import IPAccessService
from app.core.database import async_session


class IPFilterMiddleware(BaseHTTPMiddleware):
    """
    IP 화이트리스트 기반 접근 제어 미들웨어

    시큐어 코딩:
    - IP 기반 접근 제어
    - 허용되지 않은 IP 차단
    - 로깅 및 감사
    """

    # IP 체크를 건너뛸 경로 (공개 API)
    SKIP_PATHS = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health"
    ]

    async def dispatch(self, request: Request, call_next):
        """
        요청을 가로채서 IP 주소를 확인합니다.
        """
        # 경로 체크
        if any(request.url.path.startswith(path) for path in self.SKIP_PATHS):
            return await call_next(request)

        # 클라이언트 IP 주소 추출
        client_ip = self._get_client_ip(request)

        # IP 주소 확인
        async with async_session() as db:
            ip_service = IPAccessService()
            is_allowed = await ip_service.is_ip_allowed(client_ip, db)

        if not is_allowed:
            # 로깅 (실제 환경에서는 logging 모듈 사용)
            print(f"[IP BLOCKED] {client_ip} attempted to access {request.url.path}")

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="접근이 거부되었습니다. IP 주소가 허용 목록에 없습니다."
            )

        # 다음 미들웨어 또는 엔드포인트로 전달
        response = await call_next(request)
        return response

    def _get_client_ip(self, request: Request) -> str:
        """
        클라이언트의 실제 IP 주소를 추출합니다.

        프록시/로드밸런서 뒤에 있는 경우 X-Forwarded-For 헤더를 확인합니다.

        Args:
            request: FastAPI Request 객체

        Returns:
            클라이언트 IP 주소
        """
        # X-Forwarded-For 헤더 확인 (프록시 환경)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # 여러 프록시를 거친 경우 첫 번째 IP가 실제 클라이언트 IP
            return forwarded_for.split(",")[0].strip()

        # X-Real-IP 헤더 확인 (nginx 등)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 직접 연결된 경우
        return request.client.host if request.client else "unknown"
