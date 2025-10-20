"""
Legacy Database Service
레거시 DB 연결 및 문서 동기화 서비스
"""
import asyncpg
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class LegacyDBService:
    """레거시 DB 연결 및 조회 서비스"""

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self._pool: Optional[asyncpg.Pool] = None

    async def test_connection(self) -> bool:
        """
        DB 연결 테스트

        Returns:
            bool: 연결 성공 시 True, 실패 시 False
        """
        try:
            conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                timeout=5
            )
            await conn.close()
            return True
        except Exception as e:
            logger.error(f"Legacy DB connection failed: {e}")
            return False

    async def get_pool(self) -> asyncpg.Pool:
        """
        연결 풀 획득 (재사용)

        Returns:
            asyncpg.Pool: 연결 풀
        """
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
        return self._pool

    async def fetch_documents(self) -> List[Dict]:
        """
        레거시 DB에서 모든 문서 조회

        Returns:
            List[Dict]: 문서 목록
        """
        try:
            pool = await self.get_pool()
            async with pool.acquire() as conn:
                # 레거시 DB 스키마에 맞게 쿼리 (가정)
                rows = await conn.fetch("""
                    SELECT
                        id as legacy_id,
                        title,
                        content,
                        document_type,
                        updated_at
                    FROM documents
                    ORDER BY updated_at DESC
                """)

                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to fetch documents from legacy DB: {e}")
            return []

    async def fetch_document_by_id(self, legacy_id: str) -> Optional[Dict]:
        """
        레거시 DB에서 특정 문서 조회

        Args:
            legacy_id: 레거시 문서 ID

        Returns:
            Optional[Dict]: 문서 정보 또는 None
        """
        try:
            pool = await self.get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT
                        id as legacy_id,
                        title,
                        content,
                        document_type,
                        updated_at
                    FROM documents
                    WHERE id = $1
                """, legacy_id)

                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to fetch document {legacy_id} from legacy DB: {e}")
            return None

    async def close(self):
        """연결 풀 종료"""
        if self._pool:
            await self._pool.close()
            self._pool = None
