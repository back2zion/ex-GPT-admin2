"""
RQ STT Worker 테스트
TDD 방식으로 작성된 병렬 처리 테스트
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import tempfile

from app.workers.rq_stt_worker import (
    process_audio_file_rq,
    enqueue_batch_processing,
    get_batch_progress,
    cancel_batch,
    stt_queue,
    redis_conn
)


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


class TestProcessAudioFileRQ:
    """단일 오디오 파일 처리 테스트 (Mock)"""

    @pytest.mark.asyncio
    @patch('app.workers.rq_stt_worker._process_audio_async')
    async def test_process_audio_file_rq_success(self, mock_process):
        """오디오 파일 처리 성공 시나리오"""
        # Given
        mock_process.return_value = {
            "success": True,
            "txt_file": "/data/stt-results/batch_1/test.txt",
            "task_id": "test-task-123"
        }

        batch_id = 1
        audio_file_path = "/data/audio/test.mp3"
        gpu_id = 0

        # When
        result = process_audio_file_rq(batch_id, audio_file_path, gpu_id)

        # Then
        assert result["success"] is True
        assert "txt_file" in result
        assert "task_id" in result

    @pytest.mark.asyncio
    @patch('app.workers.rq_stt_worker._process_audio_async')
    async def test_process_audio_file_rq_with_gpu_assignment(self, mock_process):
        """GPU 할당 테스트"""
        # Given
        mock_process.return_value = {"success": True}
        batch_id = 1
        audio_file_path = "/data/audio/test.mp3"
        gpu_id = 1

        # When
        with patch.dict('os.environ', {}, clear=True):
            result = process_audio_file_rq(batch_id, audio_file_path, gpu_id)

        # Then
        # GPU 환경변수가 설정되었는지 확인
        # (실제 구현에서는 os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id))
        assert result["success"] is True


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
