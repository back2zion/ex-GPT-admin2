"""
인증 서비스
PRD_v2.md P0 요구사항: 시큐어 코딩 (A07)
adminpage.txt: 1. 로그인

JWT 기반 인증 시스템
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.core.config import settings


# bcrypt를 사용한 비밀번호 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    평문 비밀번호와 해시를 비교합니다.

    Args:
        plain_password: 평문 비밀번호
        hashed_password: 해시된 비밀번호

    Returns:
        비밀번호 일치 여부
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    비밀번호를 bcrypt로 해싱합니다.

    Args:
        password: 평문 비밀번호

    Returns:
        해시된 비밀번호
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT Access Token을 생성합니다.

    Args:
        data: 토큰에 포함할 데이터 (sub, role 등)
        expires_delta: 토큰 만료 시간 (기본값: 30분)

    Returns:
        JWT 토큰 문자열
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    JWT Access Token을 디코딩합니다.

    Args:
        token: JWT 토큰 문자열

    Returns:
        디코딩된 페이로드 (실패 시 None)
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


class AuthService:
    """인증 서비스"""

    async def authenticate_user(
        self,
        username: str,
        password: str,
        db: AsyncSession
    ) -> Optional[User]:
        """
        사용자 인증을 수행합니다.
        로그인 5회 실패 시 30분간 계정 잠금

        Args:
            username: 사용자명
            password: 비밀번호
            db: 데이터베이스 세션

        Returns:
            인증된 사용자 (실패 시 None)
        """
        # 사용자 조회
        result = await db.execute(
            select(User).filter(User.username == username)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        # 비활성 사용자 차단
        if not user.is_active:
            return None

        # 계정 잠금 확인
        now = datetime.utcnow()
        if user.locked_until and user.locked_until > now:
            # 아직 잠금 상태
            return None

        # 잠금 해제 시간이 지났으면 자동 해제
        if user.locked_until and user.locked_until <= now:
            user.failed_login_attempts = 0
            user.locked_until = None
            await db.commit()

        # 비밀번호 검증
        if not verify_password(password, user.hashed_password):
            # 로그인 실패 카운트 증가
            user.failed_login_attempts += 1

            # 5회 실패 시 계정 잠금 (30분)
            if user.failed_login_attempts >= 5:
                user.locked_until = now + timedelta(minutes=30)

            await db.commit()
            return None

        # 로그인 성공 - 실패 카운트 리셋
        user.failed_login_attempts = 0
        user.locked_until = None
        await db.commit()

        return user

    async def update_last_login(
        self,
        user_id: int,
        db: AsyncSession
    ) -> None:
        """
        마지막 로그인 시간을 업데이트합니다.

        Args:
            user_id: 사용자 ID
            db: 데이터베이스 세션
        """
        result = await db.execute(
            select(User).filter(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            user.last_login_at = datetime.utcnow()
            await db.commit()

    async def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
        db: AsyncSession
    ) -> bool:
        """
        사용자 비밀번호를 변경합니다.

        Args:
            user_id: 사용자 ID
            old_password: 기존 비밀번호
            new_password: 새 비밀번호
            db: 데이터베이스 세션

        Returns:
            성공 여부
        """
        # 사용자 조회
        result = await db.execute(
            select(User).filter(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return False

        # 기존 비밀번호 확인
        if not verify_password(old_password, user.hashed_password):
            return False

        # 새 비밀번호로 변경
        user.hashed_password = get_password_hash(new_password)
        await db.commit()

        return True

    async def reset_password(
        self,
        user_id: int,
        new_password: str,
        db: AsyncSession
    ) -> bool:
        """
        관리자가 사용자 비밀번호를 초기화합니다.

        Args:
            user_id: 사용자 ID
            new_password: 새 비밀번호
            db: 데이터베이스 세션

        Returns:
            성공 여부
        """
        # 사용자 조회
        result = await db.execute(
            select(User).filter(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return False

        # 비밀번호 초기화
        user.hashed_password = get_password_hash(new_password)
        await db.commit()

        return True
