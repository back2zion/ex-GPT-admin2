"""
인증 API
PRD_v2.md P0 요구사항: 시큐어 코딩 (A07)
adminpage.txt: 1. 로그인
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import timedelta
from typing import Optional

from app.services.auth import AuthService, create_access_token, decode_access_token
from app.core.database import get_db
from app.core.config import settings
from app.utils.auth import get_redis_client
import uuid
import json

router = APIRouter(tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class Token(BaseModel):
    """토큰 응답"""
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    """사용자 정보 응답"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool


class PasswordChange(BaseModel):
    """비밀번호 변경 요청"""
    old_password: str
    new_password: str


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    로그인

    시큐어 코딩:
    - bcrypt를 사용한 비밀번호 검증
    - JWT 토큰 발급
    - 마지막 로그인 시간 기록
    - 비활성 사용자 차단
    """
    auth_service = AuthService()

    # 사용자 인증
    user = await auth_service.authenticate_user(
        username=form_data.username,
        password=form_data.password,
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
        data={
            "sub": user.username,
            "user_id": user.id,
            "is_superuser": user.is_superuser
        },
        expires_delta=access_token_expires
    )

    # 마지막 로그인 시간 업데이트
    await auth_service.update_last_login(user.id, db)

    # Redis 세션 생성 (채팅 API 호환성)
    session_id = str(uuid.uuid4())
    redis = await get_redis_client()
    session_data = {
        "user_id": str(user.id),
        "usr_id": str(user.id),
        "username": user.username,
        "usr_nm": user.full_name or user.username,
        "name": user.full_name or user.username,
        "department": "",
        "dept_cd": ""
    }
    # 세션 TTL: ACCESS_TOKEN_EXPIRE_MINUTES와 동일
    await redis.set(
        f"session:{session_id}",
        json.dumps(session_data),
        ex=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    # 세션 ID 쿠키 설정
    response.set_cookie(
        key="JSESSIONID",
        value=session_id,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        samesite="lax"
    )

    # 아이디 기억하기 (adminpage.txt 요구사항)
    # 쿠키에 username 저장 (보안상 비밀번호는 저장하지 않음)
    if form_data.username:
        response.set_cookie(
            key="remembered_username",
            value=form_data.username,
            max_age=30 * 24 * 60 * 60,  # 30일
            httponly=True,
            samesite="lax"
        )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout(response: Response):
    """
    로그아웃

    쿠키 삭제
    """
    response.delete_cookie("remembered_username")
    return {"message": "로그아웃 성공"}


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    현재 사용자 조회 (의존성)

    시큐어 코딩:
    - JWT 토큰 검증
    - 만료된 토큰 차단
    - 비활성 사용자 차단
    """
    from sqlalchemy import select
    from app.models.user import User

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 토큰 디코딩
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    # 사용자 조회
    result = await db.execute(
        select(User).filter(User.username == username)
    )
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exception

    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """
    현재 사용자 정보 조회

    시큐어 코딩:
    - JWT 토큰 검증을 통한 인증
    - 민감 정보 (비밀번호 등) 제외
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser
    )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    비밀번호 변경

    시큐어 코딩:
    - 기존 비밀번호 확인 필수
    - bcrypt를 사용한 안전한 해싱
    """
    auth_service = AuthService()

    success = await auth_service.change_password(
        user_id=current_user.id,
        old_password=password_data.old_password,
        new_password=password_data.new_password,
        db=db
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="기존 비밀번호가 올바르지 않습니다"
        )

    return {"message": "비밀번호가 변경되었습니다"}


@router.get("/remembered-username")
async def get_remembered_username(request: Request):
    """
    기억된 아이디 조회 (adminpage.txt 요구사항: 아이디 기억하기)
    """
    remembered_username = request.cookies.get("remembered_username")

    if remembered_username:
        return {"username": remembered_username}
    else:
        return {"username": None}
