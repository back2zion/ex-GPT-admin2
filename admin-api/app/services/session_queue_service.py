"""
PER-002 구현: 세션 및 대기열 관리 서비스
- 최대 20개 세션 유지
- 동시 10개 질의 처리
- 초과 시 대기열 관리
"""
import asyncio
import time
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
import json
import logging

import redis.asyncio as aioredis
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class SessionQueueService:
    """세션 및 대기열 관리 서비스"""

    # PER-002 요구사항
    MAX_CONCURRENT_REQUESTS = 10  # 동시 처리 질의 수
    MAX_ACTIVE_SESSIONS = 20       # 최대 활성 세션 수

    # Redis Keys
    ACTIVE_SESSIONS_KEY = "ex_gpt:active_sessions"
    SESSION_QUEUE_KEY = "ex_gpt:session_queue"
    SESSION_DATA_PREFIX = "ex_gpt:session:"
    REQUEST_SEMAPHORE_KEY = "ex_gpt:request_semaphore"

    # Timeouts
    SESSION_TIMEOUT = 1800  # 30분 (초 단위)
    QUEUE_POSITION_TTL = 600  # 대기열 위치 TTL 10분

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self._redis: Optional[aioredis.Redis] = None
        self._request_semaphore: Optional[asyncio.Semaphore] = None

    async def get_redis(self) -> aioredis.Redis:
        """Redis 클라이언트 가져오기"""
        if self._redis is None:
            self._redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self._redis

    async def close(self):
        """Redis 연결 종료"""
        if self._redis:
            await self._redis.close()
            self._redis = None

    def get_request_semaphore(self) -> asyncio.Semaphore:
        """요청 처리 Semaphore 가져오기"""
        if self._request_semaphore is None:
            self._request_semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_REQUESTS)
        return self._request_semaphore

    async def create_session(self, user_id: str, session_id: str) -> Dict:
        """
        새 세션 생성

        Returns:
            세션 정보 또는 대기열 정보
        """
        redis = await self.get_redis()

        # 이미 활성 세션이 있는지 확인
        existing_session = await redis.hget(self.ACTIVE_SESSIONS_KEY, user_id)
        if existing_session:
            session_data = json.loads(existing_session)
            return {
                "status": "active",
                "session_id": session_data["session_id"],
                "created_at": session_data["created_at"]
            }

        # 현재 활성 세션 수 확인
        active_count = await redis.hlen(self.ACTIVE_SESSIONS_KEY)

        if active_count < self.MAX_ACTIVE_SESSIONS:
            # 세션 생성 가능
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat()
            }

            # 세션 저장
            await redis.hset(
                self.ACTIVE_SESSIONS_KEY,
                user_id,
                json.dumps(session_data)
            )

            # 세션 만료 시간 설정 (개별 키)
            session_key = f"{self.SESSION_DATA_PREFIX}{session_id}"
            await redis.setex(
                session_key,
                self.SESSION_TIMEOUT,
                json.dumps(session_data)
            )

            logger.info(f"세션 생성: user_id={user_id}, session_id={session_id}, active={active_count + 1}/{self.MAX_ACTIVE_SESSIONS}")

            return {
                "status": "active",
                "session_id": session_id,
                "created_at": session_data["created_at"]
            }
        else:
            # 대기열에 추가
            queue_entry = {
                "user_id": user_id,
                "session_id": session_id,
                "queued_at": datetime.utcnow().isoformat()
            }

            # 대기열에 추가 (FIFO)
            await redis.rpush(self.SESSION_QUEUE_KEY, json.dumps(queue_entry))

            # 대기 순번 계산
            queue_length = await redis.llen(self.SESSION_QUEUE_KEY)
            position = queue_length

            # 예상 대기 시간 계산 (평균 세션 시간 5분 가정)
            estimated_wait_minutes = (position * 5) // self.MAX_ACTIVE_SESSIONS

            logger.info(f"대기열 추가: user_id={user_id}, position={position}, active={active_count}/{self.MAX_ACTIVE_SESSIONS}")

            return {
                "status": "queued",
                "position": position,
                "estimated_wait_minutes": estimated_wait_minutes,
                "active_sessions": active_count,
                "max_sessions": self.MAX_ACTIVE_SESSIONS
            }

    async def close_session(self, user_id: str):
        """세션 종료"""
        redis = await self.get_redis()

        # 활성 세션에서 제거
        session_data_str = await redis.hget(self.ACTIVE_SESSIONS_KEY, user_id)
        if session_data_str:
            session_data = json.loads(session_data_str)
            session_id = session_data.get("session_id")

            # 활성 세션 목록에서 제거
            await redis.hdel(self.ACTIVE_SESSIONS_KEY, user_id)

            # 개별 세션 데이터 삭제
            if session_id:
                session_key = f"{self.SESSION_DATA_PREFIX}{session_id}"
                await redis.delete(session_key)

            logger.info(f"세션 종료: user_id={user_id}, session_id={session_id}")

            # 대기열에서 다음 사용자 처리
            await self._process_queue()

    async def _process_queue(self):
        """대기열에서 다음 사용자 처리"""
        redis = await self.get_redis()

        # 대기열에서 첫 번째 항목 가져오기
        queue_entry_str = await redis.lpop(self.SESSION_QUEUE_KEY)
        if queue_entry_str:
            queue_entry = json.loads(queue_entry_str)
            user_id = queue_entry["user_id"]
            session_id = queue_entry["session_id"]

            # 새 세션 생성
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat(),
                "promoted_from_queue": True
            }

            await redis.hset(
                self.ACTIVE_SESSIONS_KEY,
                user_id,
                json.dumps(session_data)
            )

            session_key = f"{self.SESSION_DATA_PREFIX}{session_id}"
            await redis.setex(
                session_key,
                self.SESSION_TIMEOUT,
                json.dumps(session_data)
            )

            logger.info(f"대기열에서 세션 활성화: user_id={user_id}, session_id={session_id}")

    async def update_session_activity(self, user_id: str):
        """세션 활동 시간 업데이트"""
        redis = await self.get_redis()

        session_data_str = await redis.hget(self.ACTIVE_SESSIONS_KEY, user_id)
        if session_data_str:
            session_data = json.loads(session_data_str)
            session_data["last_activity"] = datetime.utcnow().isoformat()

            await redis.hset(
                self.ACTIVE_SESSIONS_KEY,
                user_id,
                json.dumps(session_data)
            )

            # 개별 세션 TTL 갱신
            session_id = session_data.get("session_id")
            if session_id:
                session_key = f"{self.SESSION_DATA_PREFIX}{session_id}"
                await redis.expire(session_key, self.SESSION_TIMEOUT)

    async def get_queue_status(self) -> Dict:
        """대기열 상태 조회"""
        redis = await self.get_redis()

        active_count = await redis.hlen(self.ACTIVE_SESSIONS_KEY)
        queue_length = await redis.llen(self.SESSION_QUEUE_KEY)

        return {
            "active_sessions": active_count,
            "max_sessions": self.MAX_ACTIVE_SESSIONS,
            "queue_length": queue_length,
            "available_slots": max(0, self.MAX_ACTIVE_SESSIONS - active_count)
        }

    async def get_user_queue_position(self, user_id: str) -> Optional[int]:
        """사용자의 대기열 위치 확인"""
        redis = await self.get_redis()

        # 활성 세션인지 먼저 확인
        if await redis.hexists(self.ACTIVE_SESSIONS_KEY, user_id):
            return 0  # 이미 활성 세션

        # 대기열에서 위치 찾기
        queue = await redis.lrange(self.SESSION_QUEUE_KEY, 0, -1)
        for i, entry_str in enumerate(queue):
            entry = json.loads(entry_str)
            if entry["user_id"] == user_id:
                return i + 1

        return None

    async def cleanup_expired_sessions(self):
        """만료된 세션 정리"""
        redis = await self.get_redis()

        # 활성 세션 목록 조회
        active_sessions = await redis.hgetall(self.ACTIVE_SESSIONS_KEY)

        now = datetime.utcnow()
        expired_users = []

        for user_id, session_data_str in active_sessions.items():
            session_data = json.loads(session_data_str)
            last_activity = datetime.fromisoformat(session_data["last_activity"])

            # 30분 이상 활동 없으면 만료
            if (now - last_activity).total_seconds() > self.SESSION_TIMEOUT:
                expired_users.append(user_id)

        # 만료된 세션 제거
        for user_id in expired_users:
            await self.close_session(user_id)
            logger.info(f"만료된 세션 제거: user_id={user_id}")

    async def process_request_with_limit(self, user_id: str, request_func):
        """
        동시 처리 제한을 적용하여 요청 처리

        Args:
            user_id: 사용자 ID
            request_func: 실행할 비동기 함수
        """
        # 세션 활동 업데이트
        await self.update_session_activity(user_id)

        # Semaphore로 동시 처리 제한
        semaphore = self.get_request_semaphore()

        async with semaphore:
            logger.debug(f"요청 처리 시작: user_id={user_id}, active_requests={self.MAX_CONCURRENT_REQUESTS - semaphore._value}")
            result = await request_func()
            logger.debug(f"요청 처리 완료: user_id={user_id}")
            return result


# 싱글톤 인스턴스
_session_queue_service: Optional[SessionQueueService] = None


async def get_session_queue_service(redis_url: str = "redis://localhost:6379") -> SessionQueueService:
    """SessionQueueService 싱글톤 가져오기"""
    global _session_queue_service
    if _session_queue_service is None:
        _session_queue_service = SessionQueueService(redis_url)
    return _session_queue_service
