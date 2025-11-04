"""
STT Client Service 테스트 (TDD Red Phase)
ex-GPT-STT API와 통신하는 HTTP 클라이언트 서비스
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.stt_client_service import STTClientService


class TestSTTClientService:
    """STT Client Service 테스트"""

    @pytest.mark.asyncio
    async def test_submit_audio_success(self):
        """
        오디오 파일 제출 성공 테스트

        Given: 유효한 오디오 파일 경로
        When: submit_audio() 호출
        Then: task_id 반환
        """
        # Given
        client = STTClientService(api_base_url="http://localhost:8001")
        audio_path = "s3://test/meeting.mp3"
        meeting_title = "테스트 회의"

        # Mock httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "task_id": "task_12345",
            "message": "Audio processing started"
        }

        # When
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            result = await client.submit_audio(
                audio_file_path=audio_path,
                meeting_title=meeting_title,
                sender_name="Admin"
            )

        # Then
        assert result["success"] is True
        assert result["task_id"] == "task_12345"

    @pytest.mark.asyncio
    async def test_submit_audio_failure(self):
        """
        오디오 파일 제출 실패 테스트 (ex-GPT-STT 서버 오류)

        Given: ex-GPT-STT 서버 오류
        When: submit_audio() 호출
        Then: Exception 발생
        """
        # Given
        client = STTClientService(api_base_url="http://localhost:8001")

        # Mock httpx error response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = Exception("HTTP 500")

        # When/Then
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            with pytest.raises(Exception):
                await client.submit_audio(
                    audio_file_path="s3://test/file.mp3",
                    meeting_title="Test",
                    sender_name="Admin"
                )

    @pytest.mark.asyncio
    async def test_get_task_status_processing(self):
        """
        작업 상태 조회 테스트 (처리 중)

        Given: 처리 중인 task_id
        When: get_task_status() 호출
        Then: "processing" 상태 반환
        """
        # Given
        client = STTClientService(api_base_url="http://localhost:8001")
        task_id = "task_12345"

        # Mock httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "task_id": task_id,
            "status": "processing",
            "progress": 45.0
        }

        # When
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            result = await client.get_task_status(task_id)

        # Then
        assert result["status"] == "processing"
        assert result["progress"] == 45.0

    @pytest.mark.asyncio
    async def test_get_task_status_completed(self):
        """
        작업 상태 조회 테스트 (완료)

        Given: 완료된 task_id
        When: get_task_status() 호출
        Then: "completed" 상태 반환
        """
        # Given
        client = STTClientService(api_base_url="http://localhost:8001")
        task_id = "task_12345"

        # Mock httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "task_id": task_id,
            "status": "completed",
            "progress": 100.0
        }

        # When
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            result = await client.get_task_status(task_id)

        # Then
        assert result["status"] == "completed"
        assert result["progress"] == 100.0

    @pytest.mark.asyncio
    async def test_get_task_result_success(self):
        """
        작업 결과 조회 테스트 (성공)

        Given: 완료된 task_id
        When: get_task_result() 호출
        Then: 전사 결과 및 회의록 반환
        """
        # Given
        client = STTClientService(api_base_url="http://localhost:8001")
        task_id = "task_12345"

        # Mock httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "task_id": task_id,
            "success": True,
            "status": "completed",
            "transcription": "안녕하세요. 오늘 회의를 시작하겠습니다.",
            "meeting_minutes": "1. 회의 개요\n2. 주요 논의 사항\n3. 결정 사항",
            "duration": 600.0,
            "language": "ko",
            "segment_count": 50
        }

        # When
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            result = await client.get_task_result(task_id)

        # Then
        assert result["success"] is True
        assert result["status"] == "completed"
        assert "안녕하세요" in result["transcription"]
        assert "회의 개요" in result["meeting_minutes"]
        assert result["duration"] == 600.0
        assert result["language"] == "ko"

    @pytest.mark.asyncio
    async def test_get_task_result_not_ready(self):
        """
        작업 결과 조회 테스트 (아직 준비 안됨)

        Given: 처리 중인 task_id
        When: get_task_result() 호출
        Then: "processing" 상태 반환
        """
        # Given
        client = STTClientService(api_base_url="http://localhost:8001")
        task_id = "task_12345"

        # Mock httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "task_id": task_id,
            "success": False,
            "status": "processing",
            "error_message": "Task is still processing"
        }

        # When
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            result = await client.get_task_result(task_id)

        # Then
        assert result["success"] is False
        assert result["status"] == "processing"

    @pytest.mark.asyncio
    async def test_wait_for_completion(self):
        """
        작업 완료 대기 테스트

        Given: 처리 중인 task_id
        When: wait_for_completion() 호출
        Then: 완료될 때까지 폴링 후 결과 반환
        """
        # Given
        client = STTClientService(
            api_base_url="http://localhost:8001",
            poll_interval=0.1  # 테스트용 짧은 간격
        )
        task_id = "task_12345"

        # Mock httpx responses (처리 중 → 처리 중 → 완료)
        mock_status_responses = [
            MagicMock(status_code=200, json=lambda: {"status": "processing"}),
            MagicMock(status_code=200, json=lambda: {"status": "processing"}),
            MagicMock(status_code=200, json=lambda: {"status": "completed"}),
        ]

        mock_result_response = MagicMock()
        mock_result_response.status_code = 200
        mock_result_response.json.return_value = {
            "success": True,
            "status": "completed",
            "transcription": "전사 결과",
            "meeting_minutes": "회의록"
        }

        # When
        with patch('httpx.AsyncClient.get', side_effect=mock_status_responses + [mock_result_response]):
            result = await client.wait_for_completion(task_id, max_wait_time=10)

        # Then
        assert result["success"] is True
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_wait_for_completion_timeout(self):
        """
        작업 완료 대기 타임아웃 테스트

        Given: 계속 처리 중인 task_id
        When: wait_for_completion() 호출 (짧은 timeout)
        Then: TimeoutError 발생
        """
        # Given
        client = STTClientService(
            api_base_url="http://localhost:8001",
            poll_interval=0.1
        )
        task_id = "task_12345"

        # Mock httpx response (계속 processing)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "processing"}

        # When/Then
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            with pytest.raises(TimeoutError):
                await client.wait_for_completion(task_id, max_wait_time=0.5)

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """
        ex-GPT-STT API 헬스체크 테스트

        Given: ex-GPT-STT API 서버 정상
        When: health_check() 호출
        Then: True 반환
        """
        # Given
        client = STTClientService(api_base_url="http://localhost:8001")

        # Mock httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}

        # When
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            result = await client.health_check()

        # Then
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """
        ex-GPT-STT API 헬스체크 실패 테스트

        Given: ex-GPT-STT API 서버 오류
        When: health_check() 호출
        Then: False 반환
        """
        # Given
        client = STTClientService(api_base_url="http://localhost:8001")

        # Mock httpx error
        with patch('httpx.AsyncClient.get', side_effect=Exception("Connection refused")):
            result = await client.health_check()

        # Then
        assert result is False


class TestSTTClientServiceSecurity:
    """STT Client Service 보안 테스트"""

    @pytest.mark.asyncio
    async def test_path_traversal_in_audio_path(self):
        """
        오디오 파일 경로에서 Path Traversal 시도 차단

        Given: Path Traversal 시도 경로
        When: submit_audio() 호출
        Then: ValueError 발생
        """
        # Given
        client = STTClientService(api_base_url="http://localhost:8001")
        malicious_path = "../../etc/passwd"

        # When/Then
        with pytest.raises(ValueError, match="Invalid file path"):
            await client.submit_audio(
                audio_file_path=malicious_path,
                meeting_title="Test",
                sender_name="Admin"
            )

    @pytest.mark.asyncio
    async def test_injection_in_meeting_title(self):
        """
        회의 제목에서 특수문자 제거

        Given: 특수문자가 포함된 회의 제목
        When: submit_audio() 호출
        Then: 특수문자 제거 후 제출
        """
        # Given
        client = STTClientService(api_base_url="http://localhost:8001")
        malicious_title = "테스트<script>alert('xss')</script>"

        # Mock httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "task_id": "task_12345"
        }

        # When
        with patch('httpx.AsyncClient.post', return_value=mock_response) as mock_post:
            await client.submit_audio(
                audio_file_path="s3://test/file.mp3",
                meeting_title=malicious_title,
                sender_name="Admin"
            )

            # Then: 특수문자가 제거되었는지 확인
            call_args = mock_post.call_args
            # 실제 전송된 데이터에서 <script> 태그가 없어야 함
            assert "<script>" not in str(call_args)
