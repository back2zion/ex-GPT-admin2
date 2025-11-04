"""
IP 접근 제어 서비스
adminpage.txt: 8. 설정 > 1) 관리자관리>IP접근권한 관리

시큐어 코딩: IP 기반 접근 제어
"""
import ipaddress
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.ip_whitelist import IPWhitelist


class IPAccessService:
    """IP 접근 제어 서비스"""

    async def is_ip_allowed(
        self,
        ip_address: str,
        db: AsyncSession
    ) -> bool:
        """
        IP 주소가 접근 허용 목록에 있는지 확인합니다.

        Args:
            ip_address: 검사할 IP 주소
            db: 데이터베이스 세션

        Returns:
            접근 허용 여부
        """
        # IP 주소 조회
        result = await db.execute(
            select(IPWhitelist).filter(IPWhitelist.ip_address == ip_address)
        )
        ip_entry = result.scalar_one_or_none()

        # 화이트리스트에 없으면 차단
        if not ip_entry:
            return False

        # is_allowed가 False면 차단
        return ip_entry.is_allowed

    async def add_ip(
        self,
        ip_address: str,
        description: Optional[str],
        is_allowed: bool,
        created_by: Optional[int],
        db: AsyncSession
    ) -> IPWhitelist:
        """
        IP 주소를 화이트리스트에 추가합니다.

        Args:
            ip_address: IP 주소
            description: 설명
            is_allowed: 액세스 허용 여부
            created_by: 등록한 관리자 ID
            db: 데이터베이스 세션

        Returns:
            IPWhitelist 객체

        Raises:
            ValueError: 유효하지 않은 IP 주소
        """
        # IP 주소 유효성 검증
        try:
            ipaddress.ip_address(ip_address)
        except ValueError:
            raise ValueError(f"유효하지 않은 IP 주소입니다: {ip_address}")

        # 중복 확인
        existing = await db.execute(
            select(IPWhitelist).filter(IPWhitelist.ip_address == ip_address)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"이미 등록된 IP 주소입니다: {ip_address}")

        # 추가
        ip_entry = IPWhitelist(
            ip_address=ip_address,
            description=description,
            is_allowed=is_allowed,
            created_by=created_by
        )
        db.add(ip_entry)
        await db.commit()
        await db.refresh(ip_entry)

        return ip_entry

    async def update_ip(
        self,
        ip_id: int,
        description: Optional[str],
        is_allowed: Optional[bool],
        db: AsyncSession
    ) -> IPWhitelist:
        """
        IP 주소 정보를 수정합니다.

        Args:
            ip_id: IP ID
            description: 설명
            is_allowed: 액세스 허용 여부
            db: 데이터베이스 세션

        Returns:
            IPWhitelist 객체

        Raises:
            ValueError: IP를 찾을 수 없음
        """
        result = await db.execute(
            select(IPWhitelist).filter(IPWhitelist.id == ip_id)
        )
        ip_entry = result.scalar_one_or_none()

        if not ip_entry:
            raise ValueError(f"IP를 찾을 수 없습니다: {ip_id}")

        # 수정
        if description is not None:
            ip_entry.description = description
        if is_allowed is not None:
            ip_entry.is_allowed = is_allowed

        await db.commit()
        await db.refresh(ip_entry)

        return ip_entry

    async def delete_ip(
        self,
        ip_id: int,
        db: AsyncSession
    ) -> bool:
        """
        IP 주소를 화이트리스트에서 삭제합니다.

        Args:
            ip_id: IP ID
            db: 데이터베이스 세션

        Returns:
            성공 여부
        """
        result = await db.execute(
            select(IPWhitelist).filter(IPWhitelist.id == ip_id)
        )
        ip_entry = result.scalar_one_or_none()

        if not ip_entry:
            return False

        await db.delete(ip_entry)
        await db.commit()

        return True
