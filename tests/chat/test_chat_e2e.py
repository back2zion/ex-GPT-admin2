"""
Chat System E2E Tests

Complete end-to-end tests for chat functionality:
- New conversation creation
- Message continuity
- SSE streaming
- File upload integration
- History retrieval
- Security validation

Test Strategy: TDD with secure coding
"""

import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.core.database import get_db
from app.models.base import Base
from unittest.mock import patch, AsyncMock
import json
import uuid


@pytest_asyncio.fixture
async def authenticated_client(db_session: AsyncSession) -> AsyncClient:
    """E2E 테스트용 인증된 클라이언트 (실제 AI 서비스 연동)"""
    from app.utils.auth import get_current_user_from_session
    from httpx import ASGITransport

    async def override_get_db():
        yield db_session

    async def override_auth():
        return {
            "user_id": "test_user_e2e",
            "department": "TEST_DEPT",
            "name": "E2E 테스트 사용자"
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


@pytest.fixture
def test_user():
    """Test user credentials"""
    return {
        "user_id": "test_user_e2e",
        "session_id": f"session_{uuid.uuid4().hex[:8]}"
    }


class TestChatE2E:
    """Complete chat workflow E2E tests"""

    @pytest.mark.asyncio
    async def test_new_conversation_flow(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user):
        """
        E2E Test: New conversation creation

        Scenario:
        1. User sends first message
        2. System creates new room_id
        3. System saves question to DB
        4. System generates answer
        5. System saves answer to DB
        6. System returns SSE stream

        Security:
        - Input validation (XSS prevention)
        - SQL injection prevention
        - Room ID format validation
        """
        # Arrange
        user_message = "안녕하세요. 법인카드 사용 제한 업종이 무엇인가요?"

        # Mock AI service
        with patch("app.services.chat_service.ai_service") as mock_ai:
            mock_ai.generate_answer = AsyncMock(return_value={
                "answer": "법인카드 사용이 제한되는 업종은 다음과 같습니다: 유흥업소, 도박, 사행성 게임 등입니다.",
                "metadata": {"tokens_used": 50, "response_time_ms": 1000}
            })

            # Act - Send first message (no room_id)
            response = await authenticated_client.post(
                "/api/v1/chat/send",
                json={
                    "cnvs_idt_id": "",  # New conversation (empty string)
                    "message": user_message,
                    "stream": False,  # JSON response for testing
                    "temperature": 0.7
                }
            )

        # Assert - Response
        assert response.status_code == 200
        data = response.json()

        # Verify room_id created
        assert "room_id" in data or "cnvs_idt_id" in data
        room_id = data.get("room_id") or data.get("cnvs_idt_id")
        assert room_id is not None
        assert len(room_id) > 0

        # Verify room_id format (user_id_timestamp)
        assert "_" in room_id

        # Verify response content
        assert "content" in data or "response" in data
        response_text = data.get("content", {}).get("response") or data.get("response")
        assert response_text is not None
        assert len(response_text) > 0

        # Assert - Database verification
        # Check conversation summary created
        result = await db_session.execute(
            text("""
                SELECT "CNVS_IDT_ID", "CNVS_SMRY_TXT", "USE_YN"
                FROM "USR_CNVS_SMRY"
                WHERE "CNVS_IDT_ID" = :room_id
            """),
            {"room_id": room_id}
        )
        summary = result.fetchone()
        assert summary is not None
        assert summary[0] == room_id  # CNVS_IDT_ID
        assert summary[2] == 'Y'  # USE_YN

        # Check message saved
        result = await db_session.execute(
            text("""
                SELECT "QUES_TXT", "ANS_TXT", "USE_YN"
                FROM "USR_CNVS"
                WHERE "CNVS_IDT_ID" = :room_id
            """),
            {"room_id": room_id}
        )
        message = result.fetchone()
        assert message is not None
        assert message[0] == user_message  # QUES_TXT
        assert message[1] is not None  # ANS_TXT
        assert message[2] == 'Y'  # USE_YN

        return room_id  # For next test

    @pytest.mark.asyncio
    async def test_conversation_continuity(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user):
        """
        E2E Test: Message continuity in existing conversation

        Scenario:
        1. Create new conversation (first message)
        2. Send follow-up message with room_id
        3. Verify both messages in same conversation
        4. Verify conversation context maintained

        Security:
        - Room ID ownership validation
        - Message ordering integrity
        """
        # Arrange - Create first conversation
        first_message = "첫 번째 질문입니다"
        response1 = await authenticated_client.post(
            "/api/v1/chat/send",
            json={
                "cnvs_idt_id": None,
                "message": first_message,
                "stream": False
            }
        )
        assert response1.status_code == 200
        room_id = response1.json().get("room_id") or response1.json().get("cnvs_idt_id")

        # Act - Send follow-up message
        second_message = "두 번째 질문입니다"
        response2 = await authenticated_client.post(
            "/api/v1/chat/send",
            json={
                "cnvs_idt_id": room_id,
                "message": second_message,
                "stream": False
            }
        )

        # Assert - Response
        assert response2.status_code == 200
        data2 = response2.json()
        returned_room_id = data2.get("room_id") or data2.get("cnvs_idt_id")
        assert returned_room_id == room_id  # Same room

        # Assert - Database verification
        result = await db_session.execute(
            text("""
                SELECT "CNVS_ID", "QUES_TXT", "REG_DT"
                FROM "USR_CNVS"
                WHERE "CNVS_IDT_ID" = :room_id
                ORDER BY "REG_DT" ASC
            """),
            {"room_id": room_id}
        )
        messages = result.fetchall()

        assert len(messages) == 2
        assert messages[0][1] == first_message
        assert messages[1][1] == second_message
        # Verify timestamp ordering
        assert messages[0][2] < messages[1][2]

    @pytest.mark.asyncio
    async def test_sse_streaming(self, authenticated_client: AsyncClient, test_user):
        """
        E2E Test: SSE streaming functionality

        Scenario:
        1. Send message with stream=true
        2. Receive SSE events
        3. Verify event types (room_created, token, metadata)
        4. Verify [DONE] signal

        Security:
        - Stream timeout handling
        - Connection cleanup
        """
        # Arrange
        user_message = "간단한 질문"

        # Act - Send with streaming
        response = await authenticated_client.post(
            "/api/v1/chat/send",
            json={
                "cnvs_idt_id": None,
                "message": user_message,
                "stream": True
            }
        )

        # Assert - Response type
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"

        # Read SSE stream
        events = []
        room_id_created = None

        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = line[6:]  # Remove "data: " prefix

                if data == "[DONE]":
                    break

                try:
                    parsed = json.loads(data)
                    events.append(parsed)

                    # Capture room_id from room_created event
                    if parsed.get("type") == "room_created":
                        room_id_created = parsed.get("room_id")
                except json.JSONDecodeError:
                    pass

        # Assert - Events received
        assert len(events) > 0

        # Assert - room_created event
        assert room_id_created is not None
        assert len(room_id_created) > 0

    @pytest.mark.asyncio
    async def test_file_upload_integration(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user):
        """
        E2E Test: File upload + chat integration

        Scenario:
        1. Create conversation
        2. Upload file
        3. Send message with file_id
        4. Verify file reference in DB

        Security:
        - File type validation
        - File size limits
        - Path traversal prevention
        """
        # Arrange - Create conversation
        response1 = await authenticated_client.post(
            "/api/v1/chat/send",
            json={
                "cnvs_idt_id": None,
                "message": "파일 업로드 테스트",
                "stream": False
            }
        )
        room_id = response1.json().get("room_id") or response1.json().get("cnvs_idt_id")

        # Act - Upload file
        file_content = b"Test PDF content"
        files = {
            "file": ("test.pdf", file_content, "application/pdf")
        }
        data = {
            "room_id": room_id
        }

        upload_response = await authenticated_client.post(
            "/api/v1/files/upload",
            files=files,
            data=data
        )

        # Assert - Upload success
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert "file_id" in upload_data
        file_id = upload_data["file_id"]

        # Assert - Database verification
        result = await db_session.execute(
            text("""
                SELECT "FILE_ID", "CNVS_IDT_ID", "FILE_NM", "FILE_SIZE"
                FROM "USR_UPLD_DOC_MNG"
                WHERE "FILE_ID" = :file_id
            """),
            {"file_id": file_id}
        )
        file_record = result.fetchone()
        assert file_record is not None
        assert file_record[1] == room_id  # CNVS_IDT_ID
        assert file_record[2] == "test.pdf"

    @pytest.mark.asyncio
    async def test_history_retrieval(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user):
        """
        E2E Test: Conversation history retrieval

        Scenario:
        1. Create conversation with multiple messages
        2. Retrieve conversation list
        3. Retrieve conversation detail
        4. Verify data integrity

        Security:
        - User-based access control
        - Pagination validation
        """
        # Arrange - Create conversation with 3 messages
        messages_sent = []
        room_id = None

        for i in range(3):
            msg = f"테스트 메시지 {i+1}"
            messages_sent.append(msg)

            response = await authenticated_client.post(
                "/api/v1/chat/send",
                json={
                    "cnvs_idt_id": room_id,
                    "message": msg,
                    "stream": False
                }
            )

            if room_id is None:
                room_id = response.json().get("room_id") or response.json().get("cnvs_idt_id")

        # Act - Get conversation list
        list_response = await authenticated_client.post(
            "/api/v1/history/list",
            json={"page": 1, "page_size": 10}
        )

        # Assert - List response
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert "items" in list_data
        assert len(list_data["items"]) > 0

        # Find our conversation
        our_conv = None
        for item in list_data["items"]:
            if item["cnvs_idt_id"] == room_id:
                our_conv = item
                break

        assert our_conv is not None

        # Act - Get conversation detail
        detail_response = await authenticated_client.get(
            f"/api/v1/history/{room_id}"
        )

        # Assert - Detail response
        assert detail_response.status_code == 200
        detail_data = detail_response.json()
        assert "messages" in detail_data
        assert len(detail_data["messages"]) == 3

        # Verify message order
        for i, msg_data in enumerate(detail_data["messages"]):
            assert msg_data["ques_txt"] == messages_sent[i]

    @pytest.mark.asyncio
    async def test_security_xss_prevention(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user):
        """
        Security Test: XSS prevention in chat messages

        Scenario:
        1. Send message with XSS payload
        2. Verify payload is sanitized/escaped
        3. Verify stored data is safe

        Security Focus:
        - <script> tag filtering
        - Event handler filtering
        - HTML entity encoding
        """
        # Arrange - XSS payloads
        xss_payloads = [
            '<script>alert("XSS")</script>',
            '<img src=x onerror="alert(1)">',
            'javascript:alert("XSS")',
            '<iframe src="evil.com"></iframe>',
            '<svg onload="alert(1)">'
        ]

        for payload in xss_payloads:
            # Act - Send XSS payload
            response = await authenticated_client.post(
                "/api/v1/chat/send",
                json={
                    "cnvs_idt_id": None,
                    "message": payload,
                    "stream": False
                }
            )

            # Assert - Request not rejected (sanitization, not blocking)
            assert response.status_code == 200

            room_id = response.json().get("room_id") or response.json().get("cnvs_idt_id")

            # Assert - Database check
            result = await db_session.execute(
                text("""
                    SELECT "QUES_TXT"
                    FROM "USR_CNVS"
                    WHERE "CNVS_IDT_ID" = :room_id
                """),
                {"room_id": room_id}
            )
            stored_message = result.fetchone()[0]

            # Verify dangerous patterns removed/escaped
            assert "<script" not in stored_message.lower()
            assert "onerror" not in stored_message.lower()
            assert "javascript:" not in stored_message.lower()

    @pytest.mark.asyncio
    async def test_security_sql_injection(self, authenticated_client: AsyncClient, test_user):
        """
        Security Test: SQL injection prevention

        Scenario:
        1. Send SQL injection payload in message
        2. Send SQL injection in room_id
        3. Verify queries are parameterized

        Security Focus:
        - Parameterized queries
        - Input validation
        - No direct string concatenation
        """
        # Arrange - SQL injection payloads
        sql_payloads = [
            "'; DROP TABLE USR_CNVS; --",
            "' OR '1'='1",
            "1'; UPDATE USR_CNVS SET ANS_TXT='hacked'; --"
        ]

        for payload in sql_payloads:
            # Act - Try SQL injection in message
            response = await authenticated_client.post(
                "/api/v1/chat/send",
                json={
                    "cnvs_idt_id": None,
                    "message": payload,
                    "stream": False
                }
            )

            # Assert - No SQL error, query executed safely
            assert response.status_code == 200

        # Act - Try SQL injection in room_id
        malicious_room_id = "' OR '1'='1"
        response = await authenticated_client.get(
            f"/api/v1/history/{malicious_room_id}"
        )

        # Assert - 404 (not found) or 400 (bad request), not 500 (SQL error)
        assert response.status_code in [400, 404]

    @pytest.mark.asyncio
    async def test_performance_response_time(self, authenticated_client: AsyncClient, test_user):
        """
        Performance Test: Response time < 2s

        Scenario:
        1. Send message
        2. Measure response time
        3. Verify < 2000ms

        Performance Target:
        - P50: < 1000ms
        - P95: < 2000ms
        """
        import time

        # Act - Measure 10 requests
        response_times = []

        for i in range(10):
            start = time.time()

            response = await authenticated_client.post(
                "/api/v1/chat/send",
                json={
                    "cnvs_idt_id": None,
                    "message": f"성능 테스트 {i+1}",
                    "stream": False
                }
            )

            end = time.time()
            response_time_ms = (end - start) * 1000
            response_times.append(response_time_ms)

            assert response.status_code == 200

        # Assert - Performance metrics
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)

        print(f"\nPerformance Metrics:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Min: {min_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")

        # Verify P95 < 2000ms
        sorted_times = sorted(response_times)
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        assert p95 < 2000, f"P95 response time {p95:.2f}ms exceeds 2000ms"

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, authenticated_client: AsyncClient, test_user):
        """
        Load Test: Concurrent requests handling

        Scenario:
        1. Send 10 concurrent requests
        2. Verify all succeed
        3. Verify no race conditions

        Concurrency:
        - Test thread safety
        - Test database connection pool
        """
        # Act - Send 10 concurrent requests
        tasks = []
        for i in range(10):
            task = authenticated_client.post(
                "/api/v1/chat/send",
                json={
                    "cnvs_idt_id": None,
                    "message": f"동시 요청 {i+1}",
                    "stream": False
                }
            )
            tasks.append(task)

        # Wait for all requests
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert - All requests succeeded
        success_count = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
        assert success_count == 10, f"Only {success_count}/10 requests succeeded"

        # Verify unique room IDs
        room_ids = set()
        for r in responses:
            if not isinstance(r, Exception):
                data = r.json()
                room_id = data.get("room_id") or data.get("cnvs_idt_id")
                room_ids.add(room_id)

        assert len(room_ids) == 10, "Room IDs are not unique (race condition)"
