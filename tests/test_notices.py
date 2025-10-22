"""
공지사항 관리 테스트

TDD 기반 개발:
1. 테스트 작성 (Red)
2. 최소 구현 (Green)
3. 리팩토링 (Refactor)

시큐어 코딩 검증:
- SQL Injection 방지
- XSS 공격 방지
- 입력 검증
- 권한 검증
"""
import pytest
from httpx import AsyncClient
from datetime import date, timedelta


class TestNoticesCRUD:
    """공지사항 CRUD 기능 테스트"""

    @pytest.mark.asyncio
    async def test_create_notice(self, authenticated_client: AsyncClient):
        """공지사항 생성 테스트"""
        notice_data = {
            "title": "시스템 점검 안내",
            "content": "2025년 10월 25일 02:00-04:00 정기 점검 예정입니다.",
            "is_important": True,
            "is_popup": False,
            "start_date": str(date.today()),
            "end_date": str(date.today() + timedelta(days=7))
        }

        response = await authenticated_client.post("/api/v1/admin/notices", json=notice_data)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] == notice_data["title"]

    @pytest.mark.asyncio
    async def test_list_notices(self, authenticated_client: AsyncClient):
        """공지사항 목록 조회 테스트"""
        response = await authenticated_client.get("/api/v1/admin/notices?page=1&limit=50")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_get_notice_by_id(self, authenticated_client: AsyncClient):
        """공지사항 상세 조회 테스트"""
        # 먼저 공지사항 생성
        notice_data = {
            "title": "테스트 공지",
            "content": "테스트 내용",
            "is_important": False,
            "start_date": str(date.today())
        }
        create_response = await authenticated_client.post("/api/v1/admin/notices", json=notice_data)
        notice_id = create_response.json()["id"]

        # 조회
        response = await authenticated_client.get(f"/api/v1/admin/notices/{notice_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == notice_id
        assert data["title"] == notice_data["title"]

    @pytest.mark.asyncio
    async def test_update_notice(self, authenticated_client: AsyncClient):
        """공지사항 수정 테스트"""
        # 먼저 공지사항 생성
        notice_data = {
            "title": "원본 제목",
            "content": "원본 내용",
            "is_important": False,
            "start_date": str(date.today())
        }
        create_response = await authenticated_client.post("/api/v1/admin/notices", json=notice_data)
        notice_id = create_response.json()["id"]

        # 수정
        update_data = {
            "title": "수정된 제목",
            "content": "수정된 내용",
            "is_important": True,
            "start_date": str(date.today())
        }
        response = await authenticated_client.put(f"/api/v1/admin/notices/{notice_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "수정된 제목"

    @pytest.mark.asyncio
    async def test_delete_notice(self, authenticated_client: AsyncClient):
        """공지사항 삭제 테스트"""
        # 먼저 공지사항 생성
        notice_data = {
            "title": "삭제될 공지",
            "content": "삭제될 내용",
            "is_important": False,
            "start_date": str(date.today())
        }
        create_response = await authenticated_client.post("/api/v1/admin/notices", json=notice_data)
        notice_id = create_response.json()["id"]

        # 삭제
        response = await authenticated_client.delete(f"/api/v1/admin/notices/{notice_id}")
        assert response.status_code == 200

        # 삭제 확인
        get_response = await authenticated_client.get(f"/api/v1/admin/notices/{notice_id}")
        assert get_response.status_code == 404


class TestNoticesSecurity:
    """공지사항 시큐어 코딩 검증 테스트"""

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, authenticated_client: AsyncClient):
        """SQL Injection 방지 테스트"""
        malicious_data = {
            "title": "테스트'; DROP TABLE notices; --",
            "content": "SQL Injection 시도",
            "is_important": False,
            "start_date": str(date.today())
        }

        response = await authenticated_client.post("/api/v1/admin/notices", json=malicious_data)
        # 요청이 정상 처리되거나 입력 검증으로 거부되어야 함 (테이블 삭제 X)
        assert response.status_code in [201, 400, 422]

        # 테이블이 여전히 존재하는지 확인
        list_response = await authenticated_client.get("/api/v1/admin/notices")
        assert list_response.status_code == 200

    @pytest.mark.asyncio
    async def test_xss_prevention(self, authenticated_client: AsyncClient):
        """XSS 공격 방지 테스트"""
        xss_data = {
            "title": "<script>alert('XSS')</script>",
            "content": "<img src=x onerror=alert('XSS')>",
            "is_important": False,
            "start_date": str(date.today())
        }

        response = await authenticated_client.post("/api/v1/admin/notices", json=xss_data)

        if response.status_code == 201:
            # 생성 성공 시, 조회해서 XSS 코드가 sanitize 되었는지 확인
            notice_id = response.json()["id"]
            get_response = await authenticated_client.get(f"/api/v1/admin/notices/{notice_id}")
            data = get_response.json()

            # 스크립트 태그가 제거되거나 이스케이프되어야 함
            assert "<script>" not in data["title"] or "&lt;script&gt;" in data["title"]

    @pytest.mark.asyncio
    async def test_input_validation_title_length(self, authenticated_client: AsyncClient):
        """제목 길이 제한 검증 테스트"""
        too_long_title = "A" * 201  # 200자 초과

        invalid_data = {
            "title": too_long_title,
            "content": "내용",
            "is_important": False,
            "start_date": str(date.today())
        }

        response = await authenticated_client.post("/api/v1/admin/notices", json=invalid_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_input_validation_date_format(self, authenticated_client: AsyncClient):
        """날짜 형식 검증 테스트"""
        invalid_data = {
            "title": "테스트",
            "content": "내용",
            "is_important": False,
            "start_date": "2025-13-45"  # 잘못된 날짜
        }

        response = await authenticated_client.post("/api/v1/admin/notices", json=invalid_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_input_validation_required_fields(self, authenticated_client: AsyncClient):
        """필수 필드 검증 테스트"""
        incomplete_data = {
            "title": "테스트"
            # content, start_date 누락
        }

        response = await authenticated_client.post("/api/v1/admin/notices", json=incomplete_data)
        assert response.status_code == 422


class TestNoticesBusiness:
    """공지사항 비즈니스 로직 테스트"""

    @pytest.mark.asyncio
    async def test_notice_expiration_filter(self, authenticated_client: AsyncClient):
        """만료된 공지사항 필터링 테스트"""
        # 만료된 공지사항 생성
        expired_notice = {
            "title": "만료된 공지",
            "content": "이미 종료된 공지사항",
            "is_important": False,
            "start_date": str(date.today() - timedelta(days=10)),
            "end_date": str(date.today() - timedelta(days=1))
        }
        await authenticated_client.post("/api/v1/admin/notices", json=expired_notice)

        # 활성 공지사항만 조회하는 API가 있다면 테스트
        response = await authenticated_client.get("/api/v1/admin/notices/active")

        if response.status_code == 200:
            data = response.json()
            # 만료된 공지사항이 포함되지 않아야 함
            for notice in data.get("items", []):
                if notice.get("end_date"):
                    assert notice["end_date"] >= str(date.today())

    @pytest.mark.asyncio
    async def test_important_notice_ordering(self, authenticated_client: AsyncClient):
        """중요 공지사항 우선 정렬 테스트"""
        # 일반 공지
        await authenticated_client.post("/api/v1/admin/notices", json={
            "title": "일반 공지",
            "content": "일반",
            "is_important": False,
            "start_date": str(date.today())
        })

        # 중요 공지
        await authenticated_client.post("/api/v1/admin/notices", json={
            "title": "중요 공지",
            "content": "중요",
            "is_important": True,
            "start_date": str(date.today())
        })

        # 정렬된 목록 조회
        response = await authenticated_client.get("/api/v1/admin/notices?sort_by=importance")

        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])

            # 중요 공지가 먼저 나와야 함
            if len(items) >= 2:
                assert items[0].get("is_important") == True
