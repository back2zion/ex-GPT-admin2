"""
Authentication Utilities
인증 관련 유틸리티 (HTTP 세션 기반)
"""
from fastapi import Cookie, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
import redis.asyncio as aioredis
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Redis 클라이언트 (세션 스토어)
# TODO: app/core/redis.py로 이동
redis_client: Optional[aioredis.Redis] = None


async def get_redis_client():
    """Redis 클라이언트 가져오기"""
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url("redis://localhost:6379")
    return redis_client


async def get_current_user_from_session(
    session_id: str = Cookie(None, alias="JSESSIONID"),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    HTTP 세션에서 사용자 정보 조회

    Args:
        session_id: HTTP 세션 ID (쿠키)
        db: 데이터베이스 세션

    Returns:
        dict: {
            "user_id": str,
            "department": str,
            "name": str
        }

    Raises:
        HTTPException: 세션이 없거나 만료된 경우 (401)

    Security:
        - 세션 검증
        - 사용자 정보 조회
    """
    if not session_id:
        logger.warning("Session ID not found in cookie")
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다")

    try:
        # Redis에서 세션 조회
        redis = await get_redis_client()
        user_data = await redis.get(f"session:{session_id}")

        if not user_data:
            logger.warning(f"Session not found in Redis: {session_id}")
            raise HTTPException(status_code=401, detail="세션이 만료되었습니다")

        # 사용자 정보 파싱
        user_info = json.loads(user_data)

        logger.info(f"User authenticated - user_id: {user_info.get('user_id')}")

        return {
            "user_id": user_info.get("usr_id") or user_info.get("user_id"),
            "department": user_info.get("dept_cd") or user_info.get("department"),
            "name": user_info.get("usr_nm") or user_info.get("name")
        }

    except json.JSONDecodeError as e:
        logger.error(f"Session data parse error: {e}")
        raise HTTPException(status_code=401, detail="세션 데이터 오류")
    except Exception as e:
        logger.error(f"Session validation error: {e}")
        raise HTTPException(status_code=401, detail="인증 실패")


# TODO: JWT 토큰 기반 인증 (Phase 2)
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from jose import JWTError, jwt
#
# security = HTTPBearer()
#
# async def get_current_user_from_jwt(
#     credentials: HTTPAuthorizationCredentials = Depends(security)
# ) -> dict:
#     """JWT 토큰 검증"""
#     pass
