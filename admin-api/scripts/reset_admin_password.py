"""
관리자 비밀번호 재설정 스크립트
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.user import User
from app.services.auth import get_password_hash
from app.core.config import settings

async def reset_admin_password():
    # DB 연결
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # admin 사용자 조회
        result = await session.execute(
            select(User).filter(User.username == "admin")
        )
        admin_user = result.scalar_one_or_none()

        if not admin_user:
            print("❌ 관리자 계정을 찾을 수 없습니다!")
            return

        # 비밀번호 재설정
        new_password = "admin123"
        admin_user.hashed_password = get_password_hash(new_password)

        await session.commit()

        print("✅ 관리자 비밀번호 재설정 완료!")
        print(f"   아이디: {admin_user.username}")
        print(f"   비밀번호: {new_password}")
        print(f"   이메일: {admin_user.email}")

if __name__ == "__main__":
    asyncio.run(reset_admin_password())
