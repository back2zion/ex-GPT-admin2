"""
인증 시스템 테스트
PRD_v2.md P0 요구사항: 시큐어 코딩 (A07)
adminpage.txt: 1. 로그인
"""
import pytest
from datetime import datetime, timedelta
from app.services.auth import AuthService, create_access_token, verify_password, get_password_hash
from app.models.user import User


class TestPasswordHashing:
    """비밀번호 해싱 테스트"""

    def test_hash_password(self):
        """비밀번호를 안전하게 해싱"""
        # Given: 평문 비밀번호
        plain_password = "SecurePass123!"

        # When: 비밀번호 해싱
        hashed = get_password_hash(plain_password)

        # Then: 해시가 생성되고 원본과 다름
        assert hashed is not None
        assert hashed != plain_password
        assert hashed.startswith("$2b$")  # bcrypt

    def test_verify_correct_password(self):
        """올바른 비밀번호 검증"""
        # Given: 해시된 비밀번호
        plain_password = "SecurePass123!"
        hashed = get_password_hash(plain_password)

        # When: 올바른 비밀번호로 검증
        is_valid = verify_password(plain_password, hashed)

        # Then: 검증 성공
        assert is_valid is True

    def test_verify_wrong_password(self):
        """잘못된 비밀번호 검증"""
        # Given: 해시된 비밀번호
        plain_password = "SecurePass123!"
        hashed = get_password_hash(plain_password)

        # When: 잘못된 비밀번호로 검증
        is_valid = verify_password("WrongPassword", hashed)

        # Then: 검증 실패
        assert is_valid is False


class TestJWTToken:
    """JWT 토큰 테스트"""

    def test_create_access_token(self):
        """JWT Access Token 생성"""
        # Given: 사용자 데이터
        data = {"sub": "testuser"}

        # When: 토큰 생성
        token = create_access_token(data)

        # Then: 토큰이 생성됨
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        """만료 시간이 있는 JWT 토큰 생성"""
        # Given: 사용자 데이터와 만료 시간
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=15)

        # When: 토큰 생성
        token = create_access_token(data, expires_delta)

        # Then: 토큰이 생성됨
        assert token is not None
        assert isinstance(token, str)

    def test_decode_valid_token(self):
        """유효한 JWT 토큰 디코딩"""
        from app.services.auth import decode_access_token

        # Given: 생성된 토큰
        data = {"sub": "testuser", "role": "admin"}
        token = create_access_token(data)

        # When: 토큰 디코딩
        payload = decode_access_token(token)

        # Then: 원본 데이터가 복원됨
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["role"] == "admin"

    def test_decode_expired_token(self):
        """만료된 JWT 토큰 디코딩"""
        from app.services.auth import decode_access_token

        # Given: 이미 만료된 토큰 (만료 시간 -1분)
        data = {"sub": "testuser"}
        token = create_access_token(data, expires_delta=timedelta(minutes=-1))

        # When: 토큰 디코딩
        payload = decode_access_token(token)

        # Then: None 반환 (만료됨)
        assert payload is None

    def test_decode_invalid_token(self):
        """잘못된 JWT 토큰 디코딩"""
        from app.services.auth import decode_access_token

        # Given: 잘못된 토큰
        invalid_token = "invalid.token.here"

        # When: 토큰 디코딩
        payload = decode_access_token(invalid_token)

        # Then: None 반환
        assert payload is None


@pytest.mark.asyncio
class TestAuthService:
    """인증 서비스 테스트"""

    async def test_authenticate_user_success(self, db_session):
        """사용자 인증 성공"""
        # Given: 사용자 생성
        password = "SecurePass123!"
        user = User(
            username="testuser",
            email="test@ex.co.kr",
            hashed_password=get_password_hash(password),
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()

        auth_service = AuthService()

        # When: 올바른 username과 password로 인증
        authenticated_user = await auth_service.authenticate_user(
            username="testuser",
            password=password,
            db=db_session
        )

        # Then: 인증 성공
        assert authenticated_user is not None
        assert authenticated_user.username == "testuser"

    async def test_authenticate_user_wrong_password(self, db_session):
        """잘못된 비밀번호로 인증 실패"""
        # Given: 사용자 생성
        password = "SecurePass123!"
        user = User(
            username="testuser",
            email="test@ex.co.kr",
            hashed_password=get_password_hash(password),
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()

        auth_service = AuthService()

        # When: 잘못된 password로 인증
        authenticated_user = await auth_service.authenticate_user(
            username="testuser",
            password="WrongPassword",
            db=db_session
        )

        # Then: 인증 실패
        assert authenticated_user is None

    async def test_authenticate_inactive_user(self, db_session):
        """비활성 사용자 인증 실패"""
        # Given: 비활성 사용자
        password = "SecurePass123!"
        user = User(
            username="inactive",
            email="inactive@ex.co.kr",
            hashed_password=get_password_hash(password),
            is_active=False
        )
        db_session.add(user)
        await db_session.commit()

        auth_service = AuthService()

        # When: 비활성 사용자 인증
        authenticated_user = await auth_service.authenticate_user(
            username="inactive",
            password=password,
            db=db_session
        )

        # Then: 인증 실패
        assert authenticated_user is None

    async def test_login_updates_last_login(self, db_session):
        """로그인 시 마지막 로그인 시간 업데이트"""
        # Given: 사용자 생성
        password = "SecurePass123!"
        user = User(
            username="testuser",
            email="test@ex.co.kr",
            hashed_password=get_password_hash(password),
            is_active=True,
            last_login_at=None
        )
        db_session.add(user)
        await db_session.commit()

        auth_service = AuthService()

        # When: 로그인
        authenticated_user = await auth_service.authenticate_user(
            username="testuser",
            password=password,
            db=db_session
        )

        # 로그인 시간 업데이트
        await auth_service.update_last_login(authenticated_user.id, db_session)
        await db_session.refresh(user)

        # Then: last_login_at이 업데이트됨
        assert user.last_login_at is not None
        assert isinstance(user.last_login_at, datetime)
