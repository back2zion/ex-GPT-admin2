"""
STT 배치 생성 프론트엔드 통합 테스트 (TDD)
실패 시나리오를 먼저 작성하고 수정
"""
import pytest
from httpx import AsyncClient
from app.main import app


class TestSTTBatchCreateFrontend:
    """프론트엔드에서 발생하는 배치 생성 에러 테스트"""

    @pytest.mark.asyncio
    async def test_create_batch_without_auth_cookie(self):
        """
        GIVEN: 인증 쿠키 없이 배치 생성 시도
        WHEN: POST /api/v1/admin/stt-batches
        THEN: 401 Unauthorized 또는 적절한 에러 메시지
        """
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/admin/stt-batches",
                json={
                    "name": "테스트 배치",
                    "source_path": "/data/audio",
                    "file_pattern": "*.mp3",
                    "priority": "normal"
                }
            )

            # 인증 없이는 401 에러 예상
            assert response.status_code == 401
            assert "인증" in response.json().get("detail", "")

    @pytest.mark.asyncio
    async def test_create_batch_with_invalid_session(self):
        """
        GIVEN: 유효하지 않은 세션 쿠키
        WHEN: POST /api/v1/admin/stt-batches
        THEN: Spring Boot 인증 실패 또는 적절한 폴백
        """
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/admin/stt-batches",
                json={
                    "name": "테스트 배치",
                    "source_path": "/data/audio",
                    "file_pattern": "*.mp3",
                    "priority": "normal"
                },
                cookies={"JSESSIONID": "invalid-session-123"}
            )

            # Spring Boot 인증 실패 시 401 반환 (시큐어 코딩)
            assert response.status_code == 401
            detail = response.json().get("detail", "")
            # 인증 실패 메시지 검증 (한글 또는 영문)
            assert "인증" in detail or "Session" in detail or "invalid" in detail

    @pytest.mark.asyncio
    async def test_create_batch_with_test_auth_header(self):
        """
        GIVEN: X-Test-Auth 헤더로 테스트 인증
        WHEN: POST /api/v1/admin/stt-batches
        THEN: 201 Created, 배치 생성 성공
        """
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/admin/stt-batches",
                json={
                    "name": "테스트 배치",
                    "source_path": "/data/audio",
                    "file_pattern": "*.mp3",
                    "priority": "normal"
                },
                headers={"X-Test-Auth": "admin"}
            )

            # 성공 시나리오
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "테스트 배치"
            assert data["source_path"] == "/data/audio"

    @pytest.mark.asyncio
    async def test_create_batch_with_missing_required_fields(self):
        """
        GIVEN: 필수 필드 누락
        WHEN: POST /api/v1/admin/stt-batches
        THEN: 422 Validation Error
        """
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/admin/stt-batches",
                json={
                    "name": "테스트 배치"
                    # source_path, file_pattern 누락
                },
                headers={"X-Test-Auth": "admin"}
            )

            # 필수 필드 누락 시 422 에러
            assert response.status_code == 422
            detail = response.json().get("detail", [])
            assert len(detail) > 0

    @pytest.mark.asyncio
    async def test_create_batch_with_invalid_path(self):
        """
        GIVEN: Path Traversal 공격 시도
        WHEN: POST /api/v1/admin/stt-batches
        THEN: 400 Bad Request (시큐어 코딩)
        """
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/admin/stt-batches",
                json={
                    "name": "악의적 배치",
                    "source_path": "/data/../../../etc/passwd",  # Path Traversal
                    "file_pattern": "*.mp3",
                    "priority": "normal"
                },
                headers={"X-Test-Auth": "admin"}
            )

            # 시큐어 코딩: Path Traversal 차단
            assert response.status_code == 400
            assert "Invalid" in response.json().get("detail", "") or "path" in response.json().get("detail", "").lower()


# 통합 테스트 (실제 브라우저 시나리오)
class TestSTTBatchCreateBrowserFlow:
    """브라우저에서 실제 발생하는 시나리오 테스트"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_browser_create_batch_flow(self):
        """
        브라우저에서 배치 생성 전체 플로우

        1. 페이지 로드 (GET /admin/#/stt-batches/create)
        2. 폼 데이터 입력
        3. POST /api/v1/admin/stt-batches
        4. 성공 시 목록 페이지로 리다이렉트
        """
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Step 1: OPTIONS 요청 (CORS preflight)
            options_response = await client.options(
                "/api/v1/admin/stt-batches",
                headers={
                    "Origin": "https://ui.datastreams.co.kr:20443",
                    "Access-Control-Request-Method": "POST"
                }
            )
            # CORS preflight는 허용되어야 함
            assert options_response.status_code in [200, 204]

            # Step 2: POST 요청 (실제 배치 생성)
            post_response = await client.post(
                "/api/v1/admin/stt-batches",
                json={
                    "name": "브라우저 테스트 배치",
                    "source_path": "/data/audio",
                    "file_pattern": "*.mp3",
                    "priority": "normal"
                },
                headers={"X-Test-Auth": "admin"}
            )

            # 생성 성공
            assert post_response.status_code == 201
            data = post_response.json()
            assert "id" in data
            assert data["name"] == "브라우저 테스트 배치"
