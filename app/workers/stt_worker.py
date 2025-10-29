"""
STT Background Worker
FastAPI BackgroundTasks를 사용한 배치 처리
"""
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stt import STTBatch, STTTranscription, STTSummary
from app.services.stt_client_service import STTClientService
from app.core.database import get_db


async def process_batch_background(
    batch_id: int,
    db_session: AsyncSession
):
    """
    배치 처리 백그라운드 작업

    Args:
        batch_id: 배치 ID
        db_session: 데이터베이스 세션

    Process:
        1. 배치 정보 조회
        2. source_path에서 오디오 파일 목록 스캔
        3. 각 파일을 ex-GPT-STT API에 제출
        4. 진행 상황 DB 업데이트
        5. 완료 시 이메일 발송 (선택)
    """
    try:
        # 1. 배치 조회
        from sqlalchemy import select
        result = await db_session.execute(
            select(STTBatch).where(STTBatch.id == batch_id)
        )
        batch = result.scalar_one_or_none()

        if not batch:
            print(f"❌ Batch {batch_id} not found")
            return

        # 배치 상태 업데이트: processing
        batch.status = "processing"
        batch.started_at = datetime.utcnow()
        await db_session.commit()

        print(f"🎤 Starting batch processing: {batch.name} (ID: {batch_id})")

        # 2. 오디오 파일 스캔 (실제 구현 시)
        # TODO: MinIO/S3에서 파일 목록 가져오기
        # For now, we'll simulate with a simple list
        audio_files = scan_audio_files(batch.source_path, batch.file_pattern)

        # 총 파일 수 업데이트
        batch.total_files = len(audio_files)
        await db_session.commit()

        print(f"📊 Found {len(audio_files)} audio files")

        # 3. STT Client 초기화
        stt_client = STTClientService(
            api_base_url="http://localhost:9200"  # ex-GPT-STT API (실제 포트)
        )

        # 4. Checkpoint/Resume: 이미 완료된 파일 스킵
        from sqlalchemy import select
        processed_result = await db_session.execute(
            select(STTTranscription.audio_file_path).where(
                STTTranscription.batch_id == batch_id,
                STTTranscription.status == "success"
            )
        )
        processed_files = {row[0] for row in processed_result.fetchall()}

        remaining_files = [f for f in audio_files if f not in processed_files]

        if processed_files:
            print(f"📝 Checkpoint: Skipping {len(processed_files)} already processed files")
            print(f"📊 Remaining: {len(remaining_files)} files to process")

        # 5. 각 파일 처리
        for idx, audio_file_path in enumerate(remaining_files):
            try:
                await process_single_file(
                    batch_id=batch_id,
                    audio_file_path=audio_file_path,
                    stt_client=stt_client,
                    db_session=db_session
                )

                # 진행 상황 업데이트 (전체 완료 수 = 이미 완료 + 방금 완료)
                batch.completed_files = len(processed_files) + idx + 1
                await db_session.commit()

                print(f"✅ Progress: {batch.completed_files}/{batch.total_files}")

            except Exception as e:
                print(f"❌ Failed to process {audio_file_path}: {e}")
                batch.failed_files = (batch.failed_files or 0) + 1
                await db_session.commit()

        # 6. 배치 완료
        batch.status = "completed"
        batch.completed_at = datetime.utcnow()
        await db_session.commit()

        print(f"🎉 Batch {batch_id} completed!")
        print(f"   Total: {batch.total_files}")
        print(f"   Completed: {batch.completed_files}")
        print(f"   Failed: {batch.failed_files}")

        # 7. 이메일 발송 (선택)
        # TODO: 배치 완료 이메일 발송
        # await send_batch_completion_email(batch)

    except Exception as e:
        print(f"❌ Batch {batch_id} processing failed: {e}")
        # 배치 상태를 failed로 업데이트
        if batch:
            batch.status = "failed"
            batch.error_message = str(e)
            await db_session.commit()


async def process_single_file(
    batch_id: int,
    audio_file_path: str,
    stt_client: STTClientService,
    db_session: AsyncSession
) -> None:
    """
    단일 오디오 파일 처리

    Args:
        batch_id: 배치 ID
        audio_file_path: 오디오 파일 경로
        stt_client: STT Client
        db_session: 데이터베이스 세션
    """
    import uuid

    # 1. ex-GPT-STT에 제출
    filename = Path(audio_file_path).stem
    result = await stt_client.submit_audio(
        audio_file_path=audio_file_path,
        meeting_title=filename,
        sender_name="Batch Processing"
    )

    task_id = result.get("task_id")
    if not task_id:
        raise Exception("No task_id returned from STT API")

    # 2. DB에 전사 레코드 생성 (처리 중)
    transcription = STTTranscription(
        batch_id=batch_id,
        audio_file_path=audio_file_path,
        transcription_text="",  # 나중에 업데이트
        status="processing",
        ex_gpt_task_id=task_id,
        processing_started_at=datetime.utcnow()
    )
    db_session.add(transcription)
    await db_session.commit()
    await db_session.refresh(transcription)

    # 3. 완료 대기 (타임아웃 30분)
    try:
        task_result = await stt_client.wait_for_completion(
            task_id=task_id,
            max_wait_time=1800  # 30분
        )

        # 4. txt 파일 다운로드 및 저장 (500만건 처리 핵심 기능)
        try:
            # 전사 결과 txt 파일 다운로드
            transcription_text = await stt_client.download_transcription_file(task_id)

            # 출력 디렉토리 구조: /data/stt-results/batch_{id}/
            output_dir = Path("/data/stt-results") / f"batch_{batch_id}"
            output_dir.mkdir(parents=True, exist_ok=True)

            # txt 파일 저장
            audio_filename = Path(audio_file_path).stem
            txt_file = output_dir / f"{audio_filename}.txt"
            txt_file.write_text(transcription_text, encoding="utf-8")

            print(f"✅ Saved txt file: {txt_file}")

            # 회의록도 다운로드 (옵션)
            try:
                minutes_text = await stt_client.download_minutes_file(task_id)
                minutes_file = output_dir / f"{audio_filename}_minutes.txt"
                minutes_file.write_text(minutes_text, encoding="utf-8")
                print(f"✅ Saved minutes file: {minutes_file}")
            except Exception as e:
                print(f"⚠️ Minutes file not available: {e}")
        except Exception as e:
            print(f"❌ Failed to download txt files: {e}")
            # txt 파일 다운로드 실패해도 DB에는 저장
            transcription_text = task_result.get("transcription", "")

        # 5. 결과 저장 (DB)
        transcription.transcription_text = transcription_text
        transcription.status = "success"
        transcription.processing_completed_at = datetime.utcnow()

        # 처리 시간 계산
        if transcription.processing_started_at:
            duration = (
                transcription.processing_completed_at -
                transcription.processing_started_at
            ).total_seconds()
            transcription.processing_duration = duration

        await db_session.commit()

        # 6. 회의록 저장 (있으면)
        meeting_minutes = task_result.get("meeting_minutes")
        if meeting_minutes:
            summary = STTSummary(
                transcription_id=transcription.id,
                summary_text=meeting_minutes,
                llm_model=task_result.get("llm_model", "unknown")
            )
            db_session.add(summary)
            await db_session.commit()

    except TimeoutError:
        transcription.status = "failed"
        transcription.error_message = "Processing timeout (30 minutes)"
        await db_session.commit()
        raise

    except Exception as e:
        transcription.status = "failed"
        transcription.error_message = str(e)
        await db_session.commit()
        raise


def scan_audio_files(source_path: str, file_pattern: str) -> List[str]:
    """
    오디오 파일 스캔 (시큐어 코딩 적용)

    Args:
        source_path: 소스 경로 (s3://, minio://, 또는 로컬)
        file_pattern: 파일 패턴 (예: *.mp3)

    Returns:
        List[str]: 오디오 파일 경로 목록

    Raises:
        ValueError: Path Traversal 공격 시도 감지

    Security:
        - Path Traversal 방지 (SER-001)
        - 허용된 경로만 접근 가능
    """
    import glob
    from app.services.stt_service import STTService

    # 시큐어 코딩: Path Traversal 방지 (SER-001 요구사항)
    if ".." in source_path or "/../" in source_path:
        raise ValueError(f"Invalid file path: '{source_path}' contains path traversal patterns")

    # 경로 검증 (STTService 재사용)
    stt_service = STTService()
    try:
        stt_service.validate_file_path(source_path)
    except ValueError as e:
        raise ValueError(f"Security validation failed: {e}")

    # MinIO/S3 파일 스캔
    if source_path.startswith("s3://") or source_path.startswith("minio://"):
        return scan_minio_files(source_path, file_pattern)

    # 로컬 파일 시스템
    pattern = f"{source_path}/{file_pattern}"
    files = glob.glob(pattern, recursive=False)  # recursive=False로 안전성 확보
    return sorted(files)  # 일관된 순서 보장


def scan_minio_files(source_path: str, file_pattern: str) -> List[str]:
    """
    MinIO/S3 파일 스캔

    Args:
        source_path: MinIO/S3 경로 (minio://bucket/prefix 또는 s3://bucket/prefix)
        file_pattern: 파일 패턴 (예: *.mp3)

    Returns:
        List[str]: 파일 경로 목록
    """
    try:
        from minio import Minio
        from urllib.parse import urlparse
        import os
        import fnmatch

        # URL 파싱
        parsed = urlparse(source_path)
        bucket_name = parsed.netloc
        prefix = parsed.path.lstrip("/")

        # MinIO 클라이언트 초기화
        minio_client = Minio(
            os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=False  # HTTP (내부망)
        )

        # 파일 목록 가져오기
        objects = minio_client.list_objects(bucket_name, prefix=prefix, recursive=True)

        # 패턴 매칭
        files = []
        for obj in objects:
            if fnmatch.fnmatch(obj.object_name, f"*{file_pattern.replace('*', '')}"):
                files.append(f"minio://{bucket_name}/{obj.object_name}")

        print(f"📦 MinIO: Found {len(files)} files in {bucket_name}/{prefix}")
        return sorted(files)

    except ImportError:
        print("⚠️ minio package not installed. Run: pip install minio")
        return []
    except Exception as e:
        print(f"❌ MinIO scanning failed: {e}")
        return []
