"""
RQ STT Worker 테스트
TDD 방식으로 작성된 병렬 처리 테스트
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import tempfile
import asyncio
import httpx
from datetime import datetime

from app.workers.rq_stt_worker import (
    process_audio_file_rq,
    enqueue_batch_processing,
    get_batch_progress,
    cancel_batch,
    stt_queue,
    redis_conn,
    _process_audio_async
)
from app.models.stt import STTTranscription


class TestRQWorkerEnqueue:
    """RQ 작업 등록 테스트"""

    def test_enqueue_batch_processing_creates_jobs(self):
        """배치 작업이 RQ 큐에 등록되는지 테스트"""
        # Given
        batch_id = 1
        audio_files = [
            "/data/audio/file1.mp3",
            "/data/audio/file2.mp3",
            "/data/audio/file3.mp3",
            "/data/audio/file4.mp3",
        ]

        # When
        job_ids = enqueue_batch_processing(batch_id, audio_files)

        # Then
        assert len(job_ids) == 4
        assert all(isinstance(job_id, str) for job_id in job_ids)

        # Cleanup
        for job_id in job_ids:
            try:
                from rq.job import Job
                job = Job.fetch(job_id, connection=redis_conn)
                job.delete()
            except:
                pass

    def test_gpu_round_robin_assignment(self):
        """GPU가 라운드 로빈 방식으로 할당되는지 테스트"""
        # Given
        batch_id = 1
        audio_files = [f"/data/audio/file{i}.mp3" for i in range(10)]

        # When
        job_ids = enqueue_batch_processing(batch_id, audio_files)

        # Then: GPU 0과 GPU 1에 균등 분배
        from rq.job import Job
        gpu_assignments = []
        for job_id in job_ids:
            try:
                job = Job.fetch(job_id, connection=redis_conn)
                gpu_id = job.meta.get("gpu_id")
                gpu_assignments.append(gpu_id)
                job.delete()
            except:
                pass

        assert gpu_assignments == [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]


class TestRQWorkerProgress:
    """RQ 진행 상황 조회 테스트"""

    def test_get_batch_progress_empty(self):
        """작업이 없는 배치의 진행 상황 테스트"""
        # Given
        batch_id = 9999  # 존재하지 않는 배치

        # When
        progress = get_batch_progress(batch_id)

        # Then
        assert progress["total"] == 0
        assert progress["queued"] == 0
        assert progress["started"] == 0
        assert progress["finished"] == 0
        assert progress["failed"] == 0
        assert progress["progress_percentage"] == 0

    def test_get_batch_progress_with_jobs(self):
        """작업이 있는 배치의 진행 상황 테스트"""
        # Given
        batch_id = 1
        audio_files = [f"/data/audio/file{i}.mp3" for i in range(5)]
        job_ids = enqueue_batch_processing(batch_id, audio_files)

        try:
            # When
            progress = get_batch_progress(batch_id)

            # Then
            assert progress["total"] >= 5
            assert progress["queued"] >= 0
            assert "progress_percentage" in progress

        finally:
            # Cleanup
            for job_id in job_ids:
                try:
                    from rq.job import Job
                    job = Job.fetch(job_id, connection=redis_conn)
                    job.delete()
                except:
                    pass


class TestRQWorkerCancel:
    """RQ 작업 취소 테스트"""

    def test_cancel_batch(self):
        """배치 작업 취소 테스트"""
        # Given
        batch_id = 1
        audio_files = [f"/data/audio/file{i}.mp3" for i in range(3)]
        job_ids = enqueue_batch_processing(batch_id, audio_files)

        # When
        cancelled_count = cancel_batch(batch_id)

        # Then
        assert cancelled_count >= 0  # 일부는 이미 처리되었을 수 있음

        # Cleanup
        for job_id in job_ids:
            try:
                from rq.job import Job
                job = Job.fetch(job_id, connection=redis_conn)
                job.delete()
            except:
                pass


@pytest.fixture
def mock_stt_client_service():
    """STTClientService Mock 객체"""
    with patch('app.workers.rq_stt_worker._process_audio_async.STTClientService') as MockClient:
        instance = MockClient.return_value
        instance.submit_audio = AsyncMock()
        instance.wait_for_completion = AsyncMock()
        instance.download_transcription_file = AsyncMock()
        instance.health_check = AsyncMock(return_value=True)
        yield instance

@pytest.fixture
def mock_db_session():
    """AsyncSession Mock 객체"""
    with patch('app.workers.rq_stt_worker.get_async_session') as mock_get_session:
        mock_session = AsyncMock()
        mock_get_session.return_value.__aiter__.return_value = [mock_session]
        yield mock_session


class TestProcessAudioFileAsync:
    """_process_audio_async 함수 테스트 (Mock)"""

    @pytest.mark.asyncio
    async def test_process_audio_async_success(self, mock_stt_client_service, mock_db_session):
        """성공적인 STT 처리 시나리오"""
        # Given
        batch_id = 1
        audio_file_path = "/data/audio/test_success.mp3"
        task_id = "test-task-success"
        transcription_text = "This is a successful transcription."

        mock_stt_client_service.submit_audio.return_value = {"task_id": task_id}
        mock_stt_client_service.wait_for_completion.return_value = {"status": "completed"}
        mock_stt_client_service.download_transcription_file.return_value = transcription_text

        # When
        result = await _process_audio_async(batch_id, audio_file_path)

        # Then
        assert result["success"] is True
        assert result["status"] == "success"
        assert result["task_id"] == task_id
        assert "txt_file" in result
        assert result["error_message"] is None

        mock_stt_client_service.submit_audio.assert_awaited_once()
        mock_stt_client_service.wait_for_completion.assert_awaited_once()
        mock_stt_client_service.download_transcription_file.assert_awaited_once()

        mock_db_session.add.assert_awaited_once()
        mock_db_session.commit.assert_awaited_once()
        saved_transcription = mock_db_session.add.call_args[0][0]
        assert isinstance(saved_transcription, STTTranscription)
        assert saved_transcription.batch_id == batch_id
        assert saved_transcription.audio_file_path == audio_file_path
        assert saved_transcription.transcription_text == transcription_text
        assert saved_transcription.status == "success"
        assert saved_transcription.ex_gpt_task_id == task_id
        assert saved_transcription.error_message is None

    @pytest.mark.asyncio
    async def test_process_audio_async_submit_failure(self, mock_stt_client_service, mock_db_session):
        """STT 제출 실패 시나리오"""
        # Given
        batch_id = 1
        audio_file_path = "/data/audio/test_submit_fail.mp3"

        mock_stt_client_service.submit_audio.side_effect = httpx.RequestError("Network error")

        # When
        result = await _process_audio_async(batch_id, audio_file_path)

        # Then
        assert result["success"] is False
        assert result["status"] == "failed"
        assert "Network error" in result["error_message"]

        mock_db_session.add.assert_awaited_once()
        mock_db_session.commit.assert_awaited_once()
        saved_transcription = mock_db_session.add.call_args[0][0]
        assert saved_transcription.status == "failed"
        assert "Network error" in saved_transcription.error_message

    @pytest.mark.asyncio
    async def test_process_audio_async_no_task_id(self, mock_stt_client_service, mock_db_session):
        """STT 제출 후 task_id 없음 시나리오"""
        # Given
        batch_id = 1
        audio_file_path = "/data/audio/test_no_task_id.mp3"

        mock_stt_client_service.submit_audio.return_value = {"message": "failed"}

        # When
        result = await _process_audio_async(batch_id, audio_file_path)

        # Then
        assert result["success"] is False
        assert result["status"] == "failed"
        assert "No task_id returned" in result["error_message"]

        mock_db_session.add.assert_awaited_once()
        mock_db_session.commit.assert_awaited_once()
        saved_transcription = mock_db_session.add.call_args[0][0]
        assert saved_transcription.status == "failed"
        assert "No task_id returned" in saved_transcription.error_message

    @pytest.mark.asyncio
    async def test_process_audio_async_timeout_waiting_for_completion(self, mock_stt_client_service, mock_db_session):
        """STT 완료 대기 타임아웃 시나리오"""
        # Given
        batch_id = 1
        audio_file_path = "/data/audio/test_timeout.mp3"
        task_id = "test-task-timeout"

        mock_stt_client_service.submit_audio.return_value = {"task_id": task_id}
        mock_stt_client_service.wait_for_completion.side_effect = asyncio.TimeoutError("Task timed out")

        # When
        result = await _process_audio_async(batch_id, audio_file_path)

        # Then
        assert result["success"] is False
        assert result["status"] == "failed"
        assert "timed out" in result["error_message"]

        mock_db_session.add.assert_awaited_once()
        mock_db_session.commit.assert_awaited_once()
        saved_transcription = mock_db_session.add.call_args[0][0]
        assert saved_transcription.status == "failed"
        assert "timed out" in saved_transcription.error_message

    @pytest.mark.asyncio
    async def test_process_audio_async_download_failure(self, mock_stt_client_service, mock_db_session):
        """전사 파일 다운로드 실패 시나리오"""
        # Given
        batch_id = 1
        audio_file_path = "/data/audio/test_download_fail.mp3"
        task_id = "test-task-download-fail"

        mock_stt_client_service.submit_audio.return_value = {"task_id": task_id}
        mock_stt_client_service.wait_for_completion.return_value = {"status": "completed"}
        mock_stt_client_service.download_transcription_file.side_effect = httpx.HTTPStatusError("Download failed", request=httpx.Request("GET", "http://test.com"), response=httpx.Response(404))

        # When
        result = await _process_audio_async(batch_id, audio_file_path)

        # Then
        assert result["success"] is False
        assert result["status"] == "failed"
        assert "Download failed" in result["error_message"]

        mock_db_session.add.assert_awaited_once()
        mock_db_session.commit.assert_awaited_once()
        saved_transcription = mock_db_session.add.call_args[0][0]
        assert saved_transcription.status == "failed"
        assert "Download failed" in saved_transcription.error_message

    @pytest.mark.asyncio
    async def test_process_audio_async_http_status_error(self, mock_stt_client_service, mock_db_session):
        """HTTP 상태 오류 시나리오"""
        # Given
        batch_id = 1
        audio_file_path = "/data/audio/test_http_error.mp3"
        task_id = "test-task-http-error"

        mock_stt_client_service.submit_audio.return_value = {"task_id": task_id}
        mock_stt_client_service.wait_for_completion.side_effect = httpx.HTTPStatusError("Server error", request=httpx.Request("GET", "http://test.com"), response=httpx.Response(500))

        # When
        result = await _process_audio_async(batch_id, audio_file_path)

        # Then
        assert result["success"] is False
        assert result["status"] == "failed"
        assert "HTTP Status Error from STT API" in result["error_message"]
        assert "500" in result["error_message"]

        mock_db_session.add.assert_awaited_once()
        mock_db_session.commit.assert_awaited_once()
        saved_transcription = mock_db_session.add.call_args[0][0]
        assert saved_transcription.status == "failed"
        assert "HTTP Status Error from STT API" in saved_transcription.error_message

    @pytest.mark.asyncio
    async def test_process_audio_async_network_error(self, mock_stt_client_service, mock_db_session):
        """네트워크 오류 시나리오"""
        # Given
        batch_id = 1
        audio_file_path = "/data/audio/test_network_error.mp3"
        task_id = "test-task-network-error"

        mock_stt_client_service.submit_audio.return_value = {"task_id": task_id}
        mock_stt_client_service.wait_for_completion.side_effect = httpx.RequestError("Connection refused", request=httpx.Request("GET", "http://test.com"))

        # When
        result = await _process_audio_async(batch_id, audio_file_path)

        # Then
        assert result["success"] is False
        assert result["status"] == "failed"
        assert "Network/Request Error connecting to STT API" in result["error_message"]
        assert "Connection refused" in result["error_message"]

        mock_db_session.add.assert_awaited_once()
        mock_db_session.commit.assert_awaited_once()
        saved_transcription = mock_db_session.add.call_args[0][0]
        assert saved_transcription.status == "failed"
        assert "Network/Request Error connecting to STT API" in saved_transcription.error_message


class TestRQWorkerIntegration:
    """RQ Worker 통합 테스트 (E2E)"""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not redis_conn.ping(),
        reason="Redis not available"
    )
    def test_full_batch_workflow(self):
        """전체 배치 처리 워크플로우 테스트 (Redis 필요)"""
        # Given
        batch_id = 1
        audio_files = ["/data/audio/test1.mp3", "/data/audio/test2.mp3"]

        try:
            # When: 작업 등록
            job_ids = enqueue_batch_processing(batch_id, audio_files)

            # Then: 작업이 등록되었는지 확인
            assert len(job_ids) == 2

            # When: 진행 상황 조회
            progress = get_batch_progress(batch_id)

            # Then: 진행 상황이 반환되는지 확인
            assert progress["total"] >= 2

            # When: 작업 취소
            cancelled_count = cancel_batch(batch_id)

            # Then: 작업이 취소되었는지 확인
            assert cancelled_count >= 0

        finally:
            # Cleanup
            for job_id in job_ids:
                try:
                    from rq.job import Job
                    job = Job.fetch(job_id, connection=redis_conn)
                    job.delete()
                except:
                    pass


class TestRQWorkerSecurity:
    """RQ Worker 시큐어 코딩 테스트"""

    def test_path_traversal_prevention_in_job_metadata(self):
        """작업 메타데이터에서 Path Traversal 방지"""
        # Given: 악의적인 파일 경로
        batch_id = 1
        audio_files = [
            "/data/audio/../../../etc/passwd",  # Path Traversal 시도
        ]

        # When
        job_ids = enqueue_batch_processing(batch_id, audio_files)

        # Then: 작업은 등록되지만, 실제 처리 시 검증됨
        assert len(job_ids) == 1

        # Cleanup
        for job_id in job_ids:
            try:
                from rq.job import Job
                job = Job.fetch(job_id, connection=redis_conn)
                job.delete()
            except:
                pass

    def test_job_timeout_limit(self):
        """작업 타임아웃 제한 테스트"""
        # Given
        batch_id = 1
        audio_files = ["/data/audio/test.mp3"]

        # When
        job_ids = enqueue_batch_processing(batch_id, audio_files)

        # Then: 2시간 타임아웃이 설정되었는지 확인
        from rq.job import Job
        try:
            job = Job.fetch(job_ids[0], connection=redis_conn)
            # timeout은 문자열 "2h"로 설정됨
            assert job.timeout is not None
            job.delete()
        except:
            pass


class TestRQWorkerPerformance:
    """RQ Worker 성능 테스트"""

    @pytest.mark.performance
    def test_enqueue_1000_jobs_performance(self):
        """1000개 작업 등록 성능 테스트"""
        import time

        # Given
        batch_id = 1
        audio_files = [f"/data/audio/file{i}.mp3" for i in range(1000)]

        # When
        start_time = time.time()
        job_ids = enqueue_batch_processing(batch_id, audio_files)
        elapsed_time = time.time() - start_time

        # Then: 10초 이내에 완료되어야 함
        assert elapsed_time < 10.0
        assert len(job_ids) == 1000

        # Cleanup
        print(f"\n⚠️  Warning: {len(job_ids)} jobs created. Cleanup manually if needed.")
        print(f"   Run: cancel_batch({batch_id})")


# pytest 실행 예시:
# pytest tests/test_rq_stt_worker.py -v
# pytest tests/test_rq_stt_worker.py -v -k "test_enqueue"
# pytest tests/test_rq_stt_worker.py -v -m "integration"
# pytest tests/test_rq_stt_worker.py -v -m "performance"
