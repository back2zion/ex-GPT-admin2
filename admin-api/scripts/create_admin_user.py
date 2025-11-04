"""
관리자 계정 생성 스크립트
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.services.auth import AuthService
from app.core.config import settings

async def create_admin():
    # DB 연결
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        auth_service = AuthService()

        # 비밀번호 해싱
        from app.services.auth import get_password_hash

        # 관리자 계정 생성
        admin_user = User(
            username="admin",
            email="admin@ex.co.kr",
            full_name="관리자",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_superuser=True
        )

        session.add(admin_user)
        await session.commit()

        print("✅ 관리자 계정 생성 완료!")
        print(f"   아이디: {admin_user.username}")
        print(f"   비밀번호: admin123")
        print(f"   이메일: {admin_user.email}")

if __name__ == "__main__":
    asyncio.run(create_admin())
