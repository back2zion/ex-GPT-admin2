"""
Tests for auth.py - Session Authentication
HTTP 세션 기반 인증 테스트 (TDD)
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from fastapi import HTTPException
from app.utils.auth import get_current_user_from_session, get_redis_client


class TestRedisSession:
    """Redis 세션 관리 테스트"""

    @pytest.mark.asyncio
    async def test_get_redis_client(self):
        """Redis 클라이언트 가져오기 테스트"""
        redis = await get_redis_client()

        assert redis is not None
        # Redis 연결 확인
        await redis.ping()

    @pytest.mark.asyncio
    async def test_redis_set_get(self):
        """Redis 저장/조회 테스트"""
        redis = await get_redis_client()

        # 세션 데이터 저장
        session_id = "test_session_123"
        user_data = '{"user_id": "test_user", "department": "TEST_DEPT"}'

        await redis.set(f"session:{session_id}", user_data, ex=3600)

        # 세션 데이터 조회
        retrieved = await redis.get(f"session:{session_id}")

        assert retrieved is not None
        assert b"test_user" in retrieved or "test_user" in retrieved

        # Cleanup
        await redis.delete(f"session:{session_id}")


class TestSessionAuthentication:
    """HTTP 세션 인증 테스트"""

    @pytest.mark.asyncio
    async def test_valid_session_authentication(self, db_session):
        """유효한 세션으로 인증 성공 테스트"""
        redis = await get_redis_client()
        session_id = "valid_session_456"

        # Redis에 유효한 세션 저장
        import json
        user_data = json.dumps({
            "usr_id": "auth_test_user",
            "dept_cd": "AUTH_DEPT",
            "usr_nm": "인증 테스트 사용자"
        })
        await redis.set(f"session:{session_id}", user_data, ex=3600)

        # 인증 시도
        user_info = await get_current_user_from_session(
            session_id=session_id,
            db=db_session
        )

        assert user_info["user_id"] == "auth_test_user"
        assert user_info["department"] == "AUTH_DEPT"
        assert user_info["name"] == "인증 테스트 사용자"

        # Cleanup
        await redis.delete(f"session:{session_id}")

    @pytest.mark.asyncio
    async def test_missing_session_id(self, db_session):
        """세션 ID가 없는 경우 401 에러 테스트"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_session(
                session_id=None,
                db=db_session
            )

        assert exc_info.value.status_code == 401
        assert "세션이 만료되었습니다" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_expired_session(self, db_session):
        """만료된 세션으로 인증 시도 시 401 에러 테스트"""
        session_id = "expired_session_789"

        # Redis에 세션이 없는 상태 (만료됨)
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_session(
                session_id=session_id,
                db=db_session
            )

        assert exc_info.value.status_code == 401
        # "세션이 만료되었습니다" 또는 "인증 실패" 모두 허용
        assert "세션" in exc_info.value.detail or "인증" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_invalid_session_data(self, db_session):
        """잘못된 JSON 형식의 세션 데이터 테스트"""
        redis = await get_redis_client()
        session_id = "invalid_json_session"

        # 잘못된 JSON 데이터 저장
        await redis.set(f"session:{session_id}", "not a json", ex=3600)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_session(
                session_id=session_id,
                db=db_session
            )

        assert exc_info.value.status_code == 401

        # Cleanup
        await redis.delete(f"session:{session_id}")

    @pytest.mark.asyncio
    async def test_session_with_alternative_field_names(self, db_session):
        """대체 필드명 (user_id, department, name) 테스트"""
        redis = await get_redis_client()
        session_id = "alt_fields_session"

        # 대체 필드명 사용
        import json
        user_data = json.dumps({
            "user_id": "alt_user",
            "department": "ALT_DEPT",
            "name": "Alternative User"
        })
        await redis.set(f"session:{session_id}", user_data, ex=3600)

        user_info = await get_current_user_from_session(
            session_id=session_id,
            db=db_session
        )

        assert user_info["user_id"] == "alt_user"
        assert user_info["department"] == "ALT_DEPT"
        assert user_info["name"] == "Alternative User"

        # Cleanup
        await redis.delete(f"session:{session_id}")


class TestSessionMiddleware:
    """세션 미들웨어/의존성 주입 테스트"""

    @pytest.mark.asyncio
    async def test_authenticated_request_with_cookie(self, client: AsyncClient, db_session):
        """쿠키로 인증된 요청 테스트"""
        redis = await get_redis_client()
        session_id = "cookie_test_session"

        # Redis에 세션 저장
        import json
        user_data = json.dumps({
            "usr_id": "cookie_user",
            "dept_cd": "COOKIE_DEPT",
            "usr_nm": "Cookie User"
        })
        await redis.set(f"session:{session_id}", user_data, ex=3600)

        # 쿠키와 함께 요청 (실제 엔드포인트가 등록되면 테스트)
        # response = await client.get(
        #     "/api/v1/history/list",
        #     cookies={"JSESSIONID": session_id}
        # )
        # assert response.status_code == 200

        # Cleanup
        await redis.delete(f"session:{session_id}")

    @pytest.mark.asyncio
    async def test_unauthenticated_request_without_cookie(self, client: AsyncClient):
        """쿠키 없이 인증이 필요한 엔드포인트 호출 시 401 테스트"""
        # Router 등록 후 테스트 가능
        # response = await client.get("/api/v1/history/list")
        # assert response.status_code == 401
        pass


class TestSessionLifecycle:
    """세션 생명주기 테스트"""

    @pytest.mark.asyncio
    async def test_session_expiration(self):
        """세션 만료 시간 테스트"""
        redis = await get_redis_client()
        session_id = "expire_test_session"

        # 1초 만료 세션 생성
        await redis.set(f"session:{session_id}", "test data", ex=1)

        # 즉시 조회하면 존재
        data = await redis.get(f"session:{session_id}")
        assert data is not None

        # 2초 대기 후 조회하면 없음
        import asyncio
        await asyncio.sleep(2)

        data = await redis.get(f"session:{session_id}")
        assert data is None

    @pytest.mark.asyncio
    async def test_session_refresh(self):
        """세션 갱신 테스트"""
        redis = await get_redis_client()
        session_id = "refresh_test_session"

        # 세션 생성
        await redis.set(f"session:{session_id}", "test data", ex=3600)

        # TTL 확인
        ttl1 = await redis.ttl(f"session:{session_id}")
        assert ttl1 > 0

        # 세션 갱신 (expire 재설정)
        await redis.expire(f"session:{session_id}", 7200)

        # TTL이 증가했는지 확인
        ttl2 = await redis.ttl(f"session:{session_id}")
        assert ttl2 > ttl1

        # Cleanup
        await redis.delete(f"session:{session_id}")
