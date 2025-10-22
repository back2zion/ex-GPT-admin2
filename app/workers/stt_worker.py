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
            api_base_url="http://localhost:8001"  # ex-GPT-STT API
        )

        # 4. 각 파일 처리
        for idx, audio_file_path in enumerate(audio_files):
            try:
                await process_single_file(
                    batch_id=batch_id,
                    audio_file_path=audio_file_path,
                    stt_client=stt_client,
                    db_session=db_session
                )

                # 진행 상황 업데이트
                batch.completed_files = idx + 1
                await db_session.commit()

                print(f"✅ Progress: {batch.completed_files}/{batch.total_files}")

            except Exception as e:
                print(f"❌ Failed to process {audio_file_path}: {e}")
                batch.failed_files = (batch.failed_files or 0) + 1
                await db_session.commit()

        # 5. 배치 완료
        batch.status = "completed"
        batch.completed_at = datetime.utcnow()
        await db_session.commit()

        print(f"🎉 Batch {batch_id} completed!")
        print(f"   Total: {batch.total_files}")
        print(f"   Completed: {batch.completed_files}")
        print(f"   Failed: {batch.failed_files}")

        # 6. 이메일 발송 (선택)
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

        # 4. 결과 저장
        transcription.transcription_text = task_result.get("transcription", "")
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

        # 5. 회의록 저장 (있으면)
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
    오디오 파일 스캔

    Args:
        source_path: 소스 경로 (s3://, minio://, 또는 로컬)
        file_pattern: 파일 패턴 (예: *.mp3)

    Returns:
        List[str]: 오디오 파일 경로 목록

    TODO: MinIO/S3 연동 구현
    """
    # 임시 구현: 로컬 파일 시스템만 지원
    # 실제 구현 시 MinIO/S3 클라이언트 사용
    import glob

    if source_path.startswith("s3://") or source_path.startswith("minio://"):
        # TODO: MinIO/S3 파일 목록 가져오기
        print(f"⚠️ MinIO/S3 scanning not yet implemented: {source_path}")
        return []

    # 로컬 파일 시스템
    pattern = f"{source_path}/{file_pattern}"
    files = glob.glob(pattern)
    return files
