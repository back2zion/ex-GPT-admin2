"""
Tests for chat API endpoints
채팅 API 통합 테스트
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch, MagicMock
from app.utils.room_id_generator import generate_room_id


@pytest_asyncio.fixture
async def mock_authenticated_client(db_session: AsyncSession) -> AsyncClient:
    """인증된 테스트 클라이언트 (Redis 세션 모킹)"""
    from app.main import app
    from app.core.database import get_db
    from app.utils.auth import get_current_user_from_session
    from httpx import ASGITransport

    async def override_get_db():
        yield db_session

    async def override_auth():
        return {
            "user_id": "test_user_api",
            "department": "TEST_DEPT",
            "name": "테스트 사용자"
        }

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_from_session] = override_auth

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=True
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_room_for_api(db_session: AsyncSession):
    """API 테스트용 대화방"""
    from app.services.chat_service import create_room

    user_id = "test_user_api"
    room_id = generate_room_id(user_id)
    await create_room(db_session, room_id, user_id, "API 테스트 대화")
    await db_session.commit()

    yield room_id


class TestChatSendAPI:
    """채팅 메시지 전송 API 테스트"""

    @pytest.mark.asyncio
    async def test_send_chat_new_conversation(self, mock_authenticated_client: AsyncClient):
        """새 대화 시작 테스트"""
        # AI 서비스 모킹
        with patch("app.services.chat_service.ai_service") as mock_ai:
            # SSE 스트림 모킹
            async def mock_stream(*args, **kwargs):
                yield "안녕하세요! "
                yield "무엇을 도와드릴까요?"

            mock_ai.stream_chat = mock_stream

            # 요청
            response = await mock_authenticated_client.post(
                "/api/v1/chat/send",
                json={
                    "cnvs_idt_id": "",
                    "message": "안녕하세요",
                    "stream": True
                }
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

            # SSE 응답 파싱
            content = response.text
            assert "data:" in content
            assert "[DONE]" in content

    @pytest.mark.asyncio
    async def test_send_chat_continue_conversation(
        self, mock_authenticated_client: AsyncClient, test_room_for_api
    ):
        """기존 대화 이어가기 테스트"""
        room_id = test_room_for_api

        with patch("app.services.chat_service.ai_service") as mock_ai:
            async def mock_stream(*args, **kwargs):
                yield "이어서 답변드립니다."

            mock_ai.stream_chat = mock_stream

            response = await mock_authenticated_client.post(
                "/api/v1/chat/send",
                json={
                    "cnvs_idt_id": room_id,
                    "message": "두 번째 질문입니다",
                    "stream": True
                }
            )

            assert response.status_code == 200
            content = response.text
            assert "data:" in content

    @pytest.mark.asyncio
    async def test_send_chat_invalid_room_id(self, mock_authenticated_client: AsyncClient):
        """유효하지 않은 Room ID로 메시지 전송 시도 테스트"""
        with patch("app.services.chat_service.ai_service") as mock_ai:
            async def mock_stream(*args, **kwargs):
                yield "응답"

            mock_ai.stream_chat = mock_stream

            response = await mock_authenticated_client.post(
                "/api/v1/chat/send",
                json={
                    "cnvs_idt_id": "invalid_room_id",
                    "message": "질문",
                    "stream": True
                }
            )

            # 에러 메시지가 SSE로 전송됨
            assert response.status_code == 200
            content = response.text
            assert "error" in content or "유효하지 않은" in content


class TestRoomsAPI:
    """대화방 관리 API 테스트"""

    @pytest.mark.asyncio
    async def test_update_room_name(
        self, mock_authenticated_client: AsyncClient, test_room_for_api
    ):
        """대화방 이름 변경 테스트"""
        room_id = test_room_for_api

        response = await mock_authenticated_client.patch(
            f"/api/v1/rooms/{room_id}/name",
            json={"name": "변경된 대화명"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_update_room_name_invalid_room(
        self, mock_authenticated_client: AsyncClient
    ):
        """존재하지 않는 대화방 이름 변경 시도 테스트"""
        response = await mock_authenticated_client.patch(
            "/api/v1/rooms/invalid_room/name",
            json={"name": "변경 시도"}
        )

        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_delete_room(
        self, mock_authenticated_client: AsyncClient, test_room_for_api
    ):
        """대화방 삭제 테스트"""
        room_id = test_room_for_api

        response = await mock_authenticated_client.delete(
            f"/api/v1/rooms/{room_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_delete_room_invalid_room(
        self, mock_authenticated_client: AsyncClient
    ):
        """존재하지 않는 대화방 삭제 시도 테스트"""
        response = await mock_authenticated_client.delete(
            "/api/v1/rooms/invalid_room"
        )

        assert response.status_code in [403, 404]


class TestHistoryAPI:
    """대화 이력 API 테스트"""

    @pytest.mark.asyncio
    async def test_get_conversation_list(
        self, mock_authenticated_client: AsyncClient, test_room_for_api, db_session: AsyncSession
    ):
        """대화 목록 조회 테스트"""
        # 추가 대화방 생성
        from app.services.chat_service import create_room

        room_id2 = generate_room_id("test_user_api")
        await create_room(db_session, room_id2, "test_user_api", "두 번째 대화")
        await db_session.commit()

        response = await mock_authenticated_client.post(
            "/api/v1/history/list",
            json={"page": 1, "page_size": 10}
        )

        assert response.status_code == 200
        data = response.json()

        assert "conversations" in data
        assert "total" in data
        assert isinstance(data["conversations"], list)
        assert data["total"] >= 2

    @pytest.mark.asyncio
    async def test_get_conversation_list_pagination(
        self, mock_authenticated_client: AsyncClient
    ):
        """대화 목록 페이지네이션 테스트"""
        response = await mock_authenticated_client.post(
            "/api/v1/history/list",
            json={"page": 1, "page_size": 5}
        )

        assert response.status_code == 200
        data = response.json()

        # 페이지 크기 제한 확인
        assert len(data["conversations"]) <= 5

    @pytest.mark.asyncio
    async def test_get_conversation_detail(
        self, mock_authenticated_client: AsyncClient, test_room_for_api, db_session: AsyncSession
    ):
        """대화 상세 조회 테스트"""
        room_id = test_room_for_api

        # 질문-답변 추가
        from app.services.chat_service import save_question, save_answer

        cnvs_id = await save_question(db_session, room_id, "테스트 질문")
        await save_answer(db_session, cnvs_id, "테스트 답변", 100, 1000)
        await db_session.commit()

        response = await mock_authenticated_client.get(
            f"/api/v1/history/{room_id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert "cnvs_idt_id" in data
        assert "messages" in data
        assert "total_messages" in data
        assert data["cnvs_idt_id"] == room_id
        assert len(data["messages"]) > 0

    @pytest.mark.asyncio
    async def test_get_conversation_detail_invalid_room(
        self, mock_authenticated_client: AsyncClient
    ):
        """존재하지 않는 대화 상세 조회 시도 테스트"""
        response = await mock_authenticated_client.get(
            "/api/v1/history/invalid_room"
        )

        assert response.status_code in [403, 404]


class TestFilesAPI:
    """파일 업로드 API 테스트"""

    @pytest.mark.asyncio
    async def test_upload_file_success(
        self, mock_authenticated_client: AsyncClient, test_room_for_api
    ):
        """파일 업로드 성공 테스트"""
        room_id = test_room_for_api

        # MinIO 서비스 모킹
        with patch("app.services.minio_service.minio_service") as mock_minio:
            mock_minio.upload_file.return_value = ("documents/test.pdf", 1024)
            mock_minio.get_file_url.return_value = "http://minio/documents/test.pdf"

            # 파일 업로드
            files = {"file": ("test.pdf", b"PDF content", "application/pdf")}
            data = {"room_id": room_id}

            response = await mock_authenticated_client.post(
                "/api/v1/files/upload",
                files=files,
                data=data
            )

            assert response.status_code == 200
            result = response.json()

            assert result["success"] is True
            assert "file_uid" in result
            assert "download_url" in result

    @pytest.mark.asyncio
    async def test_upload_file_invalid_type(
        self, mock_authenticated_client: AsyncClient, test_room_for_api
    ):
        """허용되지 않은 파일 타입 업로드 시도 테스트"""
        room_id = test_room_for_api

        files = {"file": ("virus.exe", b"EXE content", "application/x-exe")}
        data = {"room_id": room_id}

        response = await mock_authenticated_client.post(
            "/api/v1/files/upload",
            files=files,
            data=data
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_file_invalid_room(
        self, mock_authenticated_client: AsyncClient
    ):
        """유효하지 않은 Room ID로 파일 업로드 시도 테스트"""
        files = {"file": ("test.pdf", b"PDF content", "application/pdf")}
        data = {"room_id": "invalid_room"}

        response = await mock_authenticated_client.post(
            "/api/v1/files/upload",
            files=files,
            data=data
        )

        assert response.status_code == 403


class TestChatAPIAuthentication:
    """채팅 API 인증 테스트"""

    @pytest.mark.asyncio
    async def test_chat_without_authentication(self, client: AsyncClient):
        """인증 없이 채팅 API 호출 시도 테스트"""
        response = await client.post(
            "/api/v1/chat/send",
            json={"message": "테스트"}
        )

        # 401 Unauthorized
        assert response.status_code == 401
