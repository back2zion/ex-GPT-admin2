"""
RQ (Redis Queue) 기반 STT 병렬 Worker
H100 2대를 활용한 병렬 처리

Architecture:
- GPU 0: Worker 1, 2 (2개 프로세스)
- GPU 1: Worker 3, 4 (2개 프로세스)
- 총 4개 Worker 동시 처리

Usage:
    # Worker 시작 (터미널 1)
    rq worker stt-queue --with-scheduler

    # Worker 시작 (터미널 2)
    rq worker stt-queue --with-scheduler

    # Worker 시작 (터미널 3)
    rq worker stt-queue --with-scheduler

    # Worker 시작 (터미널 4)
    rq worker stt-queue --with-scheduler
"""
import os
import asyncio
from pathlib import Path
from typing import Optional
from redis import Redis
from rq import Queue, Worker
from rq.job import Job

# Redis 연결 (기존 admin-api Redis 재사용)
redis_conn = Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=int(os.getenv("REDIS_DB", "0")),
    decode_responses=False  # bytes 모드 (성능)
)

# STT 작업 큐
stt_queue = Queue("stt-queue", connection=redis_conn)


def process_audio_file_rq(
    batch_id: int,
    audio_file_path: str,
    gpu_id: Optional[int] = None
) -> dict:
    """
    RQ Job: 단일 오디오 파일 STT 처리

    Args:
        batch_id: 배치 ID
        audio_file_path: 오디오 파일 경로
        gpu_id: GPU ID (0 또는 1)

    Returns:
        dict: 처리 결과 {"success": bool, "txt_file": str}

    이 함수는 RQ Worker에서 동기적으로 실행됩니다.
    """
    # GPU 설정
    if gpu_id is not None:
        os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
        print(f"🎮 Using GPU {gpu_id}")

    # 비동기 함수를 동기 방식으로 실행
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(
            _process_audio_async(batch_id, audio_file_path)
        )
        return result
    finally:
        loop.close()


async def _process_audio_async(batch_id: int, audio_file_path: str) -> dict:
    """
    비동기 STT 처리 로직 (내부 함수)
    """
    from app.services.stt_client_service import STTClientService
    from app.core.database import get_async_session
    from app.models.stt import STTTranscription
    from datetime import datetime
    import httpx

    print(f"🎤 Processing: {audio_file_path}")

    stt_client = STTClientService(api_base_url="http://localhost:9200")
    filename = Path(audio_file_path).stem
    task_id = None
    transcription_text = ""
    txt_file = None
    status = "failed"
    error_message = None
    processing_started_at = datetime.utcnow()
    processing_completed_at = None

    try:
        # 1. ex-GPT-STT에 제출
        print(f"📤 Submitting audio file to ex-GPT-STT: {audio_file_path}")
        submit_result = await stt_client.submit_audio(
            audio_file_path=audio_file_path,
            meeting_title=filename,
            sender_name="RQ Worker"
        )
        task_id = submit_result.get("task_id")
        if not task_id:
            raise ValueError("No task_id returned from STT API after submission.")
        print(f"✅ Audio submitted. Task ID: {task_id}")

        # 2. 완료 대기
        print(f"⏳ Waiting for task {task_id} completion...")
        task_result = await stt_client.wait_for_completion(
            task_id=task_id,
            max_wait_time=1800  # 30분
        )
        print(f"✅ Task {task_id} completed. Status: {task_result.get('status')}")

        # 3. txt 파일 다운로드 및 저장
        transcription_text = await stt_client.download_transcription_file(task_id)
        output_dir = Path("/data/stt-results") / f"batch_{batch_id}"
        output_dir.mkdir(parents=True, exist_ok=True)
        txt_file = output_dir / f"{filename}.txt"
        txt_file.write_text(transcription_text, encoding="utf-8")
        print(f"✅ Transcription saved to: {txt_file}")

        status = "success"
        processing_completed_at = datetime.utcnow()

    except httpx.HTTPStatusError as e:
        error_message = f"HTTP Status Error from STT API: {e.response.status_code} - {e.response.text}"
        print(f"❌ {error_message}")
    except httpx.RequestError as e:
        error_message = f"Network/Request Error connecting to STT API: {e}"
        print(f"❌ {error_message}")
    except asyncio.TimeoutError:
        error_message = f"STT task {task_id} timed out after 1800 seconds."
        print(f"❌ {error_message}")
    except ValueError as e:
        error_message = f"Configuration/Value Error: {e}"
        print(f"❌ {error_message}")
    except Exception as e:
        error_message = f"An unexpected error occurred during STT processing: {e}"
        print(f"❌ {error_message}")
    finally:
        processing_completed_at = processing_completed_at or datetime.utcnow()
        # 4. DB 저장
        async for db in get_async_session():
            transcription = STTTranscription(
                batch_id=batch_id,
                audio_file_path=audio_file_path,
                transcription_text=transcription_text,
                status=status,
                ex_gpt_task_id=task_id,
                processing_started_at=processing_started_at,
                processing_completed_at=processing_completed_at,
                error_message=error_message
            )
            db.add(transcription)
            await db.commit()
            break

    return {
        "success": status == "success",
        "txt_file": str(txt_file) if txt_file else None,
        "task_id": task_id,
        "status": status,
        "error_message": error_message
    }


def enqueue_batch_processing(batch_id: int, audio_files: list) -> list:
    """
    배치 처리 작업을 RQ 큐에 등록 (GPU 분산)

    Args:
        batch_id: 배치 ID
        audio_files: 오디오 파일 경로 목록

    Returns:
        list: RQ Job ID 목록
    """
    jobs = []

    # H100 2대에 분산 (라운드 로빈)
    for idx, audio_file in enumerate(audio_files):
        gpu_id = idx % 2  # GPU 0, 1 번갈아 사용

        job = stt_queue.enqueue(
            process_audio_file_rq,
            batch_id=batch_id,
            audio_file_path=audio_file,
            gpu_id=gpu_id,
            job_timeout="2h",  # 최대 2시간
            result_ttl=86400,  # 결과 보관 24시간
            failure_ttl=604800,  # 실패 로그 보관 7일
            meta={
                "batch_id": batch_id,
                "filename": Path(audio_file).name,
                "gpu_id": gpu_id
            }
        )

        jobs.append(job.id)
        print(f"📤 Enqueued: {Path(audio_file).name} → GPU {gpu_id} (Job: {job.id[:8]})")

    return jobs


def get_batch_progress(batch_id: int) -> dict:
    """
    배치 진행 상황 조회 (RQ 기반)

    Args:
        batch_id: 배치 ID

    Returns:
        dict: {
            "total": int,
            "queued": int,
            "started": int,
            "finished": int,
            "failed": int
        }
    """
    # 큐에서 모든 작업 조회
    registry = stt_queue.started_job_registry
    failed_registry = stt_queue.failed_job_registry
    finished_registry = stt_queue.finished_job_registry

    # 배치 관련 작업만 필터링
    queued_jobs = [j for j in stt_queue.jobs if j.meta.get("batch_id") == batch_id]
    started_jobs = [j for j in registry.get_job_ids() if Job.fetch(j, connection=redis_conn).meta.get("batch_id") == batch_id]
    finished_jobs = [j for j in finished_registry.get_job_ids() if Job.fetch(j, connection=redis_conn).meta.get("batch_id") == batch_id]
    failed_jobs = [j for j in failed_registry.get_job_ids() if Job.fetch(j, connection=redis_conn).meta.get("batch_id") == batch_id]

    total = len(queued_jobs) + len(started_jobs) + len(finished_jobs) + len(failed_jobs)

    return {
        "total": total,
        "queued": len(queued_jobs),
        "started": len(started_jobs),
        "finished": len(finished_jobs),
        "failed": len(failed_jobs),
        "progress_percentage": (len(finished_jobs) / total * 100) if total > 0 else 0
    }


def cancel_batch(batch_id: int) -> int:
    """
    배치 작업 취소

    Args:
        batch_id: 배치 ID

    Returns:
        int: 취소된 작업 수
    """
    cancelled_count = 0

    # 대기 중인 작업 취소
    for job in stt_queue.jobs:
        if job.meta.get("batch_id") == batch_id:
            job.cancel()
            job.delete()
            cancelled_count += 1

    print(f"🚫 Cancelled {cancelled_count} jobs for batch {batch_id}")
    return cancelled_count


# Worker 시작 스크립트 (별도 파일로 실행)
if __name__ == "__main__":
    """
    Usage:
        python -m app.workers.rq_stt_worker

    또는 rq CLI:
        rq worker stt-queue --url redis://localhost:6379/0
    """
    import sys

    # GPU ID를 명령줄 인자로 받기
    gpu_id = int(sys.argv[1]) if len(sys.argv) > 1 else None

    if gpu_id is not None:
        os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
        print(f"🎮 Worker assigned to GPU {gpu_id}")

    # RQ Worker 시작
    worker = Worker([stt_queue], connection=redis_conn)
    worker.work(with_scheduler=True)
