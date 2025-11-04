"""
부서별 GPT 통계 API 테스트
TDD: Write tests first, then implement
"""
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from httpx import AsyncClient

from app.models.user import User
from app.models.permission import Department


@pytest.mark.asyncio
class TestGPTStatistics:
    """부서별 GPT 접근 권한 통계 테스트"""

    @pytest.fixture(autouse=True)
    async def setup_test_data(self, db_session: AsyncSession):
        """테스트용 데이터 생성"""
        import uuid
        unique_id = str(uuid.uuid4())[:8]

        # 부서 생성
        dept1 = Department(
            name=f"기획조정실_{unique_id}",
            code=f"PLAN_{unique_id}",
            description="기획 담당"
        )
        dept2 = Department(
            name=f"건설처_{unique_id}",
            code=f"CONST_{unique_id}",
            description="건설 담당"
        )
        dept3 = Department(
            name=f"인사처_{unique_id}",
            code=f"HR_{unique_id}",
            description="인사 담당"
        )
        db_session.add_all([dept1, dept2, dept3])
        await db_session.flush()

        # 사용자 생성 (부서별)
        # 기획조정실: 3명 (GPT 권한: 2명)
        user1 = User(
            username=f"plan1_{unique_id}",
            email=f"plan1_{unique_id}@test.com",
            hashed_password="hashed",
            full_name="기획1",
            department_id=dept1.id,
            is_active=True,
            gpt_access_granted=True,
            allowed_model="Qwen3-32B"
        )
        user2 = User(
            username=f"plan2_{unique_id}",
            email=f"plan2_{unique_id}@test.com",
            hashed_password="hashed",
            full_name="기획2",
            department_id=dept1.id,
            is_active=True,
            gpt_access_granted=True,
            allowed_model="Qwen3-235B-A22B-GPTQ-Int4"
        )
        user3 = User(
            username=f"plan3_{unique_id}",
            email=f"plan3_{unique_id}@test.com",
            hashed_password="hashed",
            full_name="기획3",
            department_id=dept1.id,
            is_active=True,
            gpt_access_granted=False
        )

        # 건설처: 2명 (GPT 권한: 1명)
        user4 = User(
            username=f"const1_{unique_id}",
            email=f"const1_{unique_id}@test.com",
            hashed_password="hashed",
            full_name="건설1",
            department_id=dept2.id,
            is_active=True,
            gpt_access_granted=True,
            allowed_model="Qwen3-32B"
        )
        user5 = User(
            username=f"const2_{unique_id}",
            email=f"const2_{unique_id}@test.com",
            hashed_password="hashed",
            full_name="건설2",
            department_id=dept2.id,
            is_active=True,
            gpt_access_granted=False
        )

        # 인사처: 1명 (GPT 권한: 0명)
        user6 = User(
            username=f"hr1_{unique_id}",
            email=f"hr1_{unique_id}@test.com",
            hashed_password="hashed",
            full_name="인사1",
            department_id=dept3.id,
            is_active=True,
            gpt_access_granted=False
        )

        db_session.add_all([user1, user2, user3, user4, user5, user6])
        await db_session.commit()

        self.dept1 = dept1
        self.dept2 = dept2
        self.dept3 = dept3
        self.unique_id = unique_id

    async def test_get_department_stats(self, client: AsyncClient, db_session: AsyncSession):
        """부서별 GPT 접근 권한 통계 조회 테스트"""
        response = await client.get("/api/v1/admin/gpt-access/stats/departments")

        assert response.status_code == 200
        data = response.json()
        assert "departments" in data
        assert isinstance(data["departments"], list)

        # 테스트 데이터 검증
        test_depts = [d for d in data["departments"] if self.unique_id in d["name"]]
        assert len(test_depts) == 3

        # 기획조정실: 3명 중 2명
        plan_dept = next((d for d in test_depts if "기획조정실" in d["name"]), None)
        assert plan_dept is not None
        assert plan_dept["total_users"] == 3
        assert plan_dept["users_with_gpt_access"] == 2

        # 건설처: 2명 중 1명
        const_dept = next((d for d in test_depts if "건설처" in d["name"]), None)
        assert const_dept is not None
        assert const_dept["total_users"] == 2
        assert const_dept["users_with_gpt_access"] == 1

        # 인사처: 1명 중 0명
        hr_dept = next((d for d in test_depts if "인사처" in d["name"]), None)
        assert hr_dept is not None
        assert hr_dept["total_users"] == 1
        assert hr_dept["users_with_gpt_access"] == 0

    async def test_get_department_stats_with_filter(self, client: AsyncClient):
        """특정 부서만 필터링하여 통계 조회 테스트"""
        response = await client.get(f"/api/v1/admin/gpt-access/stats/departments?department_id={self.dept1.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["departments"]) == 1
        assert data["departments"][0]["name"] == self.dept1.name
        assert data["departments"][0]["users_with_gpt_access"] == 2

    async def test_get_model_distribution(self, client: AsyncClient):
        """모델별 사용자 분포 통계 테스트"""
        response = await client.get("/api/v1/admin/gpt-access/stats/models")

        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert isinstance(data["models"], list)

        # Qwen3-32B 사용자가 있어야 함
        qwen32b = next((m for m in data["models"] if m["model"] == "Qwen3-32B"), None)
        assert qwen32b is not None
        assert qwen32b["user_count"] >= 2
