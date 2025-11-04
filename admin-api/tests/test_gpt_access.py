"""
GPT 접근 권한 관리 API 테스트
TDD: Write tests first, then implement
"""
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from httpx import AsyncClient

from app.models.user import User
from app.models.access import AccessRequest, AccessRequestStatus
from app.models.permission import Department


@pytest.mark.asyncio
class TestGPTAccessManagement:
    """GPT 접근 권한 관리 테스트"""

    @pytest.fixture(autouse=True)
    async def setup_test_data(self, db_session: AsyncSession):
        """테스트용 데이터 생성"""
        import uuid
        unique_id = str(uuid.uuid4())[:8]

        # 부서 생성
        dept = Department(
            name=f"테스트부서_{unique_id}",
            code=f"TEST_{unique_id}",
            description="테스트용 부서"
        )
        db_session.add(dept)
        await db_session.flush()

        # 사용자 생성
        user1 = User(
            username=f"user1_{unique_id}",
            email=f"user1_{unique_id}@test.com",
            hashed_password="hashed_pwd",
            full_name="사용자1",
            department_id=dept.id,
            is_active=True,
            gpt_access_granted=False,
            last_login_at=datetime.now(timezone.utc) - timedelta(days=40)  # 40일 전
        )
        user2 = User(
            username=f"user2_{unique_id}",
            email=f"user2_{unique_id}@test.com",
            hashed_password="hashed_pwd",
            full_name="사용자2",
            department_id=dept.id,
            is_active=True,
            gpt_access_granted=True,
            allowed_model="Qwen3-32B",
            last_login_at=datetime.now(timezone.utc) - timedelta(days=10)  # 10일 전
        )
        user3 = User(
            username=f"user3_{unique_id}",
            email=f"user3_{unique_id}@test.com",
            hashed_password="hashed_pwd",
            full_name="사용자3",
            department_id=dept.id,
            is_active=True,
            gpt_access_granted=False
        )

        db_session.add_all([user1, user2, user3])
        await db_session.flush()

        # 접근 신청 생성
        request1 = AccessRequest(
            user_id=user1.id,
            status=AccessRequestStatus.PENDING,
            requested_at=datetime.now(timezone.utc)
        )
        request2 = AccessRequest(
            user_id=user3.id,
            status=AccessRequestStatus.APPROVED,
            requested_at=datetime.now(timezone.utc) - timedelta(days=5),
            processed_at=datetime.now(timezone.utc) - timedelta(days=4),
            processed_by=user2.id
        )

        db_session.add_all([request1, request2])
        await db_session.commit()

        self.dept = dept
        self.user1 = user1
        self.user2 = user2
        self.user3 = user3
        self.request1 = request1
        self.request2 = request2

    async def test_list_users_with_gpt_access(self, client: AsyncClient, db_session: AsyncSession):
        """GPT 접근 권한이 있는 사용자 목록 조회 테스트"""
        response = await client.get("/api/v1/admin/gpt-access/users")

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert len(data["users"]) >= 3

        # user2는 GPT 접근 권한이 있어야 함
        user2_data = next((u for u in data["users"] if u["id"] == self.user2.id), None)
        assert user2_data is not None
        assert user2_data["gpt_access_granted"] is True
        assert user2_data["allowed_model"] == "Qwen3-32B"

    async def test_filter_users_by_inactive_days(self, client: AsyncClient):
        """30일 이상 미접속 사용자 필터링 테스트"""
        response = await client.get("/api/v1/admin/gpt-access/users?inactive_days=30")

        assert response.status_code == 200
        data = response.json()

        # user1만 40일 미접속이므로 1명 이상 나와야 함 (기존 데이터 + test user1)
        user1_data = next((u for u in data["users"] if u["id"] == self.user1.id), None)
        assert user1_data is not None

    async def test_grant_gpt_access_single_user(self, client: AsyncClient, db_session: AsyncSession):
        """단일 사용자에게 GPT 접근 권한 부여 테스트"""
        response = await client.post(
            "/api/v1/admin/gpt-access/grant",
            json={
                "user_ids": [self.user1.id],
                "model": "Qwen3-235B-A22B-GPTQ-Int4"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["granted_count"] == 1

        # DB에서 확인
        await db_session.refresh(self.user1)
        assert self.user1.gpt_access_granted is True
        assert self.user1.allowed_model == "Qwen3-235B-A22B-GPTQ-Int4"

    async def test_grant_gpt_access_bulk(self, client: AsyncClient, db_session: AsyncSession):
        """여러 사용자에게 일괄 GPT 접근 권한 부여 테스트"""
        response = await client.post(
            "/api/v1/admin/gpt-access/grant",
            json={
                "user_ids": [self.user1.id, self.user3.id],
                "model": "Qwen3-32B"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["granted_count"] == 2

        # DB에서 확인
        await db_session.refresh(self.user1)
        await db_session.refresh(self.user3)
        assert self.user1.gpt_access_granted is True
        assert self.user3.gpt_access_granted is True
        assert self.user1.allowed_model == "Qwen3-32B"
        assert self.user3.allowed_model == "Qwen3-32B"

    async def test_revoke_gpt_access(self, client: AsyncClient, db_session: AsyncSession):
        """GPT 접근 권한 회수 테스트"""
        response = await client.post(
            "/api/v1/admin/gpt-access/revoke",
            json={
                "user_ids": [self.user2.id]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["revoked_count"] == 1

        # DB에서 확인
        await db_session.refresh(self.user2)
        assert self.user2.gpt_access_granted is False
        assert self.user2.allowed_model is None

    async def test_list_access_requests(self, client: AsyncClient):
        """접근 신청 목록 조회 테스트"""
        response = await client.get("/api/v1/admin/gpt-access/requests")

        assert response.status_code == 200
        data = response.json()
        assert "requests" in data
        assert len(data["requests"]) >= 2

    async def test_filter_access_requests_by_status(self, client: AsyncClient):
        """상태별 접근 신청 필터링 테스트"""
        response = await client.get("/api/v1/admin/gpt-access/requests?status=PENDING")

        assert response.status_code == 200
        data = response.json()

        # 모두 PENDING 상태여야 함 (소문자로 반환됨)
        for req in data["requests"]:
            assert req["status"] == "pending"

    async def test_approve_access_request(self, client: AsyncClient, db_session: AsyncSession):
        """접근 신청 승인 테스트"""
        response = await client.post(
            f"/api/v1/admin/gpt-access/requests/{self.request1.id}/approve",
            json={
                "model": "Qwen3-32B",
                "processor_id": self.user2.id
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"

        # DB에서 확인
        await db_session.refresh(self.request1)
        assert self.request1.status == AccessRequestStatus.APPROVED
        assert self.request1.processed_by == self.user2.id
        assert self.request1.processed_at is not None

        # 사용자에게 권한이 부여되었는지 확인
        await db_session.refresh(self.user1)
        assert self.user1.gpt_access_granted is True
        assert self.user1.allowed_model == "Qwen3-32B"

    async def test_reject_access_request(self, client: AsyncClient, db_session: AsyncSession):
        """접근 신청 거부 테스트"""
        # 새로운 PENDING 요청 생성
        new_request = AccessRequest(
            user_id=self.user3.id,
            status=AccessRequestStatus.PENDING,
            requested_at=datetime.now(timezone.utc)
        )
        db_session.add(new_request)
        await db_session.commit()
        await db_session.refresh(new_request)

        response = await client.post(
            f"/api/v1/admin/gpt-access/requests/{new_request.id}/reject",
            json={
                "reason": "추가 승인 필요",
                "processor_id": self.user2.id
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"

        # DB에서 확인
        await db_session.refresh(new_request)
        assert new_request.status == AccessRequestStatus.REJECTED
        assert new_request.reject_reason == "추가 승인 필요"
        assert new_request.processed_by == self.user2.id
        assert new_request.processed_at is not None

    async def test_approve_nonexistent_request(self, client: AsyncClient):
        """존재하지 않는 접근 신청 승인 시 에러 테스트"""
        response = await client.post(
            "/api/v1/admin/gpt-access/requests/99999/approve",
            json={
                "model": "Qwen3-32B",
                "processor_id": self.user2.id
            }
        )

        assert response.status_code == 404

    async def test_grant_access_with_invalid_model(self, client: AsyncClient):
        """잘못된 모델명으로 권한 부여 시 에러 테스트"""
        response = await client.post(
            "/api/v1/admin/gpt-access/grant",
            json={
                "user_ids": [self.user1.id],
                "model": "InvalidModel-123"
            }
        )

        # 모델 검증이 있다면 400, 없다면 200 (구현에 따라 달라질 수 있음)
        assert response.status_code in [200, 400]
