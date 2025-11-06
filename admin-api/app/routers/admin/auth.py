"""
관리자 인증 API
JWT 기반 로그인/로그아웃
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.models.user import User
from app.services.auth import AuthService, create_access_token, decode_access_token
from datetime import timedelta
from app.core.config import settings

router = APIRouter(prefix="/api/v1/admin/auth", tags=["admin-auth"])
security = HTTPBearer()


# Request/Response Models
class LoginRequest(BaseModel):
    """로그인 요청"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """로그인 응답"""
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserInfoResponse(BaseModel):
    """사용자 정보 응답"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_superuser: bool
    is_active: bool


# JWT 토큰 의존성
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    JWT 토큰에서 현재 사용자를 조회합니다.

    Args:
        credentials: Bearer 토큰
        db: 데이터베이스 세션

    Returns:
        User: 현재 로그인한 사용자

    Raises:
        HTTPException: 인증 실패 시 401
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: str = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰에 사용자 정보가 없습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 사용자 조회
    result = await db.execute(
        select(User).filter(User.username == username)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비활성화된 사용자입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# API Endpoints
@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    관리자 로그인
    로그인 5회 실패 시 30분간 계정 잠금

    Args:
        request: 로그인 요청 (username, password)
        db: 데이터베이스 세션

    Returns:
        LoginResponse: JWT 토큰 및 사용자 정보

    Raises:
        HTTPException: 인증 실패 시 401
    """
    auth_service = AuthService()

    # 계정 잠금 상태 확인 (더 자세한 메시지 제공)
    result = await db.execute(
        select(User).filter(User.username == request.username)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user and existing_user.locked_until:
        from datetime import datetime
        now = datetime.utcnow()
        if existing_user.locked_until > now:
            remaining_minutes = int((existing_user.locked_until - now).total_seconds() / 60)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"로그인 5회 실패로 계정이 잠겼습니다. {remaining_minutes}분 후 다시 시도해주세요.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 사용자 인증
    user = await auth_service.authenticate_user(
        username=request.username,
        password=request.password,
        db=db
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # JWT 토큰 생성
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "is_superuser": user.is_superuser},
        expires_delta=access_token_expires
    )

    # 마지막 로그인 시간 업데이트
    await auth_service.update_last_login(user.id, db)

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_superuser": user.is_superuser,
        }
    )


@router.get("/me", response_model=UserInfoResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    현재 로그인한 사용자 정보 조회

    Args:
        current_user: 현재 사용자 (JWT 토큰에서 추출)

    Returns:
        UserInfoResponse: 사용자 정보
    """
    return UserInfoResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        is_superuser=current_user.is_superuser,
        is_active=current_user.is_active,
    )


@router.post("/logout")
async def logout():
    """
    로그아웃 (JWT는 서버에서 무효화할 수 없으므로 클라이언트에서 토큰 삭제)

    Returns:
        dict: 성공 메시지
    """
    return {"message": "로그아웃 되었습니다"}
