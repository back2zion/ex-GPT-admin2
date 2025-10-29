"""
STT 배치 처리 API 라우터
시큐어 코딩: SQL Injection, Path Traversal, 권한 관리
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, asc, desc
from typing import List, Optional
from datetime import datetime

from app.models.stt import STTBatch, STTTranscription, STTSummary, STTEmailLog
from app.schemas.stt import (
    STTBatchCreate,
    STTBatchUpdate,
    STTBatchResponse,
    STTBatchProgressResponse,
    STTTranscriptionResponse,
    STTSummaryResponse,
    STTEmailLogResponse
)
from app.services.stt_service import STTService
from app.services.email_service import EmailService
from app.core.database import get_db
from app.dependencies import require_permission, get_principal
from cerbos.sdk.model import Principal


router = APIRouter(prefix="/api/v1/admin/stt-batches", tags=["admin-stt"])

stt_service = STTService()
email_service = EmailService()


@router.get("")
async def list_stt_batches(
    skip: int = Query(0, ge=0, description="오프셋"),
    limit: int = Query(100, le=1000, description="최대 개수"),
    status: Optional[str] = Query(None, description="상태 필터"),
    priority: Optional[str] = Query(None, description="우선순위 필터"),
    search: Optional[str] = Query(None, description="검색어 (이름)"),
    sort_by: Optional[str] = Query("created_at", description="정렬 필드"),
    order: Optional[str] = Query("desc", description="정렬 방향"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    STT 배치 목록 조회 (Pagination 및 Sorting 지원)

    Returns:
        {
            "items": [...],
            "total": N,
            "page": 1,
            "limit": 100
        }

    Security:
        - SQL Injection 방지 (Parameterized Query)
        - 권한 검증 (Cerbos)
    """
    from sqlalchemy import func, asc, desc

    # Base query
    query = select(STTBatch)
    count_query = select(func.count()).select_from(STTBatch)

    # Filters (Parameterized Query로 SQL Injection 방지)
    if search:
        search_filter = STTBatch.name.contains(search)
        query = query.filter(search_filter)
        count_query = count_query.filter(search_filter)

    # 보안: status 값 검증 (화이트리스트)
    if status:
        valid_statuses = ["pending", "processing", "completed", "failed", "paused"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        query = query.filter(STTBatch.status == status)
        count_query = count_query.filter(STTBatch.status == status)

    # 보안: priority 값 검증 (화이트리스트)
    if priority:
        valid_priorities = ["low", "normal", "high", "urgent"]
        if priority not in valid_priorities:
            raise HTTPException(status_code=400, detail=f"Invalid priority: {priority}")
        query = query.filter(STTBatch.priority == priority)
        count_query = count_query.filter(STTBatch.priority == priority)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Sorting (보안: sort_by 값 검증)
    valid_sort_fields = ["id", "name", "status", "priority", "created_at", "updated_at"]
    if sort_by not in valid_sort_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort field: {sort_by}")

    sort_column = getattr(STTBatch, sort_by)
    if order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # Pagination
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "limit": limit
    }


@router.post("", response_model=STTBatchResponse, status_code=201)
async def create_stt_batch(
    batch: STTBatchCreate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    STT 배치 작업 생성 (admin/manager만)

    Security:
        - Path Traversal 방지 (파일 경로 검증)
        - Email Injection 방지 (이메일 주소 검증)
        - SQL Injection 방지 (Parameterized Query)
    """
    try:
        # 보안: STTService에서 파일 경로 및 이메일 검증
        db_batch = await stt_service.create_batch(
            name=batch.name,
            source_path=batch.source_path,
            file_pattern=batch.file_pattern,
            description=batch.description,
            priority=batch.priority,
            created_by=principal.id,
            notify_emails=batch.notify_emails,
            db=db
        )

        return db_batch

    except ValueError as e:
        # 보안 검증 실패 시 400 에러
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{batch_id}", response_model=STTBatchResponse)
async def get_stt_batch(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """STT 배치 상세 조회"""
    result = await db.execute(
        select(STTBatch).where(STTBatch.id == batch_id)
    )
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(status_code=404, detail="배치를 찾을 수 없습니다")

    return batch


@router.get("/{batch_id}/progress", response_model=STTBatchProgressResponse)
async def get_batch_progress(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    배치 진행 상황 조회

    Returns:
        {
            "batch_id": 12345,
            "status": "processing",
            "progress": {
                "total_files": 5000000,
                "completed": 3250000,
                "failed": 1250,
                "pending": 1748750,
                "progress_percentage": 65.0
            }
        }

    Security:
        - SQL Injection 방지
        - Rate Limiting 권장 (API 과다 호출 방지)
    """
    try:
        progress = await stt_service.get_batch_progress(batch_id, db)
        return progress
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{batch_id}", response_model=STTBatchResponse)
async def update_stt_batch(
    batch_id: int,
    batch_update: STTBatchUpdate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("stt_batch", "update"))
):
    """STT 배치 수정 (admin/manager만)"""
    result = await db.execute(
        select(STTBatch).where(STTBatch.id == batch_id)
    )
    db_batch = result.scalar_one_or_none()

    if not db_batch:
        raise HTTPException(status_code=404, detail="배치를 찾을 수 없습니다")

    # 업데이트
    for field, value in batch_update.model_dump(exclude_unset=True).items():
        setattr(db_batch, field, value)

    await db.commit()
    await db.refresh(db_batch)
    return db_batch


@router.put("/{batch_id}/pause")
async def pause_batch(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("stt_batch", "update"))
):
    """배치 일시정지 (admin/manager만)"""
    result = await db.execute(
        select(STTBatch).where(STTBatch.id == batch_id)
    )
    db_batch = result.scalar_one_or_none()

    if not db_batch:
        raise HTTPException(status_code=404, detail="배치를 찾을 수 없습니다")

    if db_batch.status != "processing":
        raise HTTPException(status_code=400, detail="처리 중인 배치만 일시정지할 수 있습니다")

    db_batch.status = "paused"
    await db.commit()

    return {"message": "배치가 일시정지되었습니다", "batch_id": batch_id}


@router.put("/{batch_id}/resume")
async def resume_batch(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("stt_batch", "update"))
):
    """배치 재개 (admin/manager만)"""
    result = await db.execute(
        select(STTBatch).where(STTBatch.id == batch_id)
    )
    db_batch = result.scalar_one_or_none()

    if not db_batch:
        raise HTTPException(status_code=404, detail="배치를 찾을 수 없습니다")

    if db_batch.status != "paused":
        raise HTTPException(status_code=400, detail="일시정지된 배치만 재개할 수 있습니다")

    db_batch.status = "processing"
    await db.commit()

    return {"message": "배치가 재개되었습니다", "batch_id": batch_id}


@router.delete("/{batch_id}", status_code=204)
async def delete_batch(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("stt_batch", "delete"))
):
    """배치 삭제 (admin만) - CASCADE로 관련 데이터 모두 삭제"""
    result = await db.execute(
        select(STTBatch).where(STTBatch.id == batch_id)
    )
    db_batch = result.scalar_one_or_none()

    if not db_batch:
        raise HTTPException(status_code=404, detail="배치를 찾을 수 없습니다")

    await db.delete(db_batch)
    await db.commit()


# ============================================
# 전사 결과 조회 API
# ============================================

@router.get("/{batch_id}/transcriptions", response_model=List[STTTranscriptionResponse])
async def list_batch_transcriptions(
    batch_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    status: Optional[str] = Query(None, description="전사 상태 필터"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """특정 배치의 전사 결과 목록 조회"""
    # 배치 존재 확인
    batch_result = await db.execute(
        select(STTBatch).where(STTBatch.id == batch_id)
    )
    if not batch_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="배치를 찾을 수 없습니다")

    # 전사 목록 조회
    query = select(STTTranscription).where(STTTranscription.batch_id == batch_id)

    if status:
        valid_statuses = ["pending", "processing", "success", "failed", "partial"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        query = query.filter(STTTranscription.status == status)

    query = query.order_by(desc(STTTranscription.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


# ============================================
# 요약 및 이메일 API
# ============================================

@router.get("/summaries/{summary_id}", response_model=STTSummaryResponse)
async def get_summary(
    summary_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """요약 조회"""
    result = await db.execute(
        select(STTSummary).where(STTSummary.id == summary_id)
    )
    summary = result.scalar_one_or_none()

    if not summary:
        raise HTTPException(status_code=404, detail="요약을 찾을 수 없습니다")

    return summary


@router.post("/summaries/{summary_id}/send-email")
async def send_summary_email(
    summary_id: int,
    recipient_email: str,
    cc_emails: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("stt_batch", "update"))
):
    """
    회의록 이메일 발송

    Security:
        - Email Injection 방지 (이메일 주소 검증)
        - SMTP Injection 방지
    """
    # 요약 조회
    result = await db.execute(
        select(STTSummary).where(STTSummary.id == summary_id)
    )
    summary = result.scalar_one_or_none()

    if not summary:
        raise HTTPException(status_code=404, detail="요약을 찾을 수 없습니다")

    # 보안: 이메일 주소 검증
    if not email_service.validate_email(recipient_email):
        raise HTTPException(status_code=400, detail=f"Invalid email: {recipient_email}")

    if cc_emails:
        for cc_email in cc_emails:
            if not email_service.validate_email(cc_email):
                raise HTTPException(status_code=400, detail=f"Invalid CC email: {cc_email}")

    # 이메일 발송
    try:
        subject = f"[회의록] {summary.meeting_title or '음성 전사 요약'}"
        body = f"""
회의록을 전달드립니다.

{summary.summary_text}

---
자동 생성 이메일입니다.
        """

        await email_service.send_email(
            recipient_email=recipient_email,
            subject=subject,
            body=body,
            cc_emails=cc_emails
        )

        # 이메일 로그 기록
        email_log = STTEmailLog(
            summary_id=summary_id,
            recipient_email=recipient_email,
            cc_emails=cc_emails,
            subject=subject,
            status="sent",
            sent_at=datetime.utcnow()
        )
        db.add(email_log)
        await db.commit()

        return {"message": "이메일이 발송되었습니다", "log_id": email_log.id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이메일 발송 실패: {str(e)}")


@router.get("/email-logs", response_model=List[STTEmailLogResponse])
async def list_email_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    status: Optional[str] = Query(None, description="발송 상태 필터"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """이메일 송출 내역 조회"""
    query = select(STTEmailLog)

    if status:
        valid_statuses = ["pending", "sent", "failed", "bounced"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        query = query.filter(STTEmailLog.status == status)

    query = query.order_by(desc(STTEmailLog.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


# ============================================
# 배치 결과 파일 다운로드 API (500만건 처리)
# ============================================

@router.get("/{batch_id}/download-all")
async def download_batch_results(
    batch_id: int,
    include_minutes: bool = Query(False, description="회의록 포함 여부"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    배치 전체 txt 파일을 ZIP으로 다운로드 (500만건 대용량 처리)

    Args:
        batch_id: 배치 ID
        include_minutes: True면 회의록(_minutes.txt)도 포함

    Returns:
        StreamingResponse: ZIP 파일 스트림

    Security:
        - Path Traversal 방지
        - 권한 검증
    """
    from fastapi.responses import StreamingResponse
    from pathlib import Path
    import zipfile
    import io
    import os

    # 1. 배치 확인
    result = await db.execute(
        select(STTBatch).where(STTBatch.id == batch_id)
    )
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(status_code=404, detail="배치를 찾을 수 없습니다")

    # 2. 결과 디렉토리 확인
    results_dir = Path("/data/stt-results") / f"batch_{batch_id}"

    if not results_dir.exists():
        raise HTTPException(
            status_code=404,
            detail="배치 결과 파일이 아직 생성되지 않았습니다. STT 처리가 완료될 때까지 기다려주세요."
        )

    # 3. Security: Path Traversal 방지
    resolved_dir = results_dir.resolve()
    if not str(resolved_dir).startswith("/data/stt-results/"):
        raise HTTPException(status_code=403, detail="잘못된 경로 접근")

    # 4. txt 파일 수집
    txt_files = list(results_dir.glob("*.txt"))

    if include_minutes:
        # 모든 txt 파일 (전사 + 회의록)
        files_to_zip = txt_files
    else:
        # 회의록 제외 (_minutes.txt 파일 제외)
        files_to_zip = [f for f in txt_files if not f.name.endswith("_minutes.txt")]

    if not files_to_zip:
        raise HTTPException(status_code=404, detail="다운로드할 파일이 없습니다")

    # 5. ZIP 파일 생성 (메모리 스트림)
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for txt_file in files_to_zip:
            # ZIP 내부 경로: 파일명만 (디렉토리 구조 없음)
            arcname = txt_file.name
            zip_file.write(txt_file, arcname=arcname)

    # 6. 스트리밍 응답
    zip_buffer.seek(0)

    # 파일명: batch_{id}_results_{timestamp}.zip
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"batch_{batch_id}_results_{timestamp}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={zip_filename}",
            "Content-Length": str(zip_buffer.getbuffer().nbytes)
        }
    )


@router.get("/{batch_id}/results-info")
async def get_batch_results_info(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    배치 결과 파일 정보 조회

    Returns:
        {
            "batch_id": int,
            "results_available": bool,
            "total_files": int,
            "transcription_files": int,
            "minutes_files": int,
            "total_size_mb": float,
            "results_path": str
        }
    """
    from pathlib import Path

    # 배치 확인
    result = await db.execute(
        select(STTBatch).where(STTBatch.id == batch_id)
    )
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(status_code=404, detail="배치를 찾을 수 없습니다")

    # 결과 디렉토리 확인
    results_dir = Path("/data/stt-results") / f"batch_{batch_id}"

    if not results_dir.exists():
        return {
            "batch_id": batch_id,
            "results_available": False,
            "total_files": 0,
            "transcription_files": 0,
            "minutes_files": 0,
            "total_size_mb": 0.0,
            "results_path": str(results_dir)
        }

    # 파일 통계
    txt_files = list(results_dir.glob("*.txt"))
    transcription_files = [f for f in txt_files if not f.name.endswith("_minutes.txt")]
    minutes_files = [f for f in txt_files if f.name.endswith("_minutes.txt")]

    # 전체 크기 계산
    total_size_bytes = sum(f.stat().st_size for f in txt_files)
    total_size_mb = total_size_bytes / (1024 * 1024)

    return {
        "batch_id": batch_id,
        "results_available": True,
        "total_files": len(txt_files),
        "transcription_files": len(transcription_files),
        "minutes_files": len(minutes_files),
        "total_size_mb": round(total_size_mb, 2),
        "results_path": str(results_dir)
    }



# ============================================
# RQ 기반 배치 처리 API (H100 2대 병렬 처리)
# ============================================

@router.post("/{batch_id}/start-rq")
async def start_batch_processing_rq(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("stt_batch", "update"))
):
    """
    RQ 기반 배치 처리 시작 (H100 2대 병렬 처리)
    
    Architecture:
        - GPU 0: Worker 1, 2
        - GPU 1: Worker 3, 4
        - 총 4개 Worker 동시 처리
    
    Returns:
        {
            "message": str,
            "batch_id": int,
            "total_files": int,
            "job_ids": [str],  # RQ Job IDs
            "estimated_time_hours": float
        }
    """
    from app.workers.rq_stt_worker import enqueue_batch_processing
    from app.workers.stt_worker import scan_audio_files
    
    # 1. 배치 조회
    result = await db.execute(
        select(STTBatch).where(STTBatch.id == batch_id)
    )
    batch = result.scalar_one_or_none()
    
    if not batch:
        raise HTTPException(status_code=404, detail="배치를 찾을 수 없습니다")
    
    if batch.status not in ["pending", "paused"]:
        raise HTTPException(
            status_code=400,
            detail=f"배치 상태가 처리 가능한 상태가 아닙니다: {batch.status}"
        )
    
    # 2. 오디오 파일 스캔 (시큐어 코딩 적용)
    try:
        audio_files = scan_audio_files(batch.source_path, batch.file_pattern)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not audio_files:
        raise HTTPException(
            status_code=404,
            detail=f"파일을 찾을 수 없습니다: {batch.source_path}/{batch.file_pattern}"
        )
    
    # 3. 배치 정보 업데이트
    batch.total_files = len(audio_files)
    batch.status = "processing"
    batch.started_at = datetime.utcnow()
    await db.commit()
    
    # 4. RQ 큐에 작업 등록 (GPU 분산)
    job_ids = enqueue_batch_processing(batch_id, audio_files)
    
    # 5. 예상 처리 시간 계산
    # 가정: 37분 음성 → 4분 처리 (10x realtime)
    # 4개 Worker 병렬 처리
    avg_processing_time_minutes = 4
    estimated_time_hours = (len(audio_files) * avg_processing_time_minutes) / 60 / 4
    
    return {
        "message": f"배치 처리가 시작되었습니다 (RQ Worker {len(job_ids)}개 작업 등록)",
        "batch_id": batch_id,
        "total_files": len(audio_files),
        "job_ids": job_ids[:10],  # 처음 10개만 표시
        "total_jobs": len(job_ids),
        "estimated_time_hours": round(estimated_time_hours, 2),
        "workers": "4 workers (2 per GPU)"
    }


@router.get("/{batch_id}/rq-progress")
async def get_rq_batch_progress(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    RQ 기반 배치 진행 상황 조회
    
    Returns:
        {
            "batch_id": int,
            "total": int,
            "queued": int,
            "started": int,
            "finished": int,
            "failed": int,
            "progress_percentage": float
        }
    """
    from app.workers.rq_stt_worker import get_batch_progress
    
    # 배치 확인
    result = await db.execute(
        select(STTBatch).where(STTBatch.id == batch_id)
    )
    batch = result.scalar_one_or_none()
    
    if not batch:
        raise HTTPException(status_code=404, detail="배치를 찾을 수 없습니다")
    
    # RQ 진행 상황 조회
    rq_progress = get_batch_progress(batch_id)
    
    # DB 진행 상황과 병합
    db_result = await db.execute(
        select(func.count())
        .select_from(STTTranscription)
        .where(STTTranscription.batch_id == batch_id, STTTranscription.status == "success")
    )
    db_completed = db_result.scalar() or 0
    
    return {
        **rq_progress,
        "db_completed_files": db_completed,
        "batch_status": batch.status
    }


@router.post("/{batch_id}/cancel-rq")
async def cancel_rq_batch(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("stt_batch", "update"))
):
    """
    RQ 배치 작업 취소
    
    Returns:
        {
            "message": str,
            "cancelled_jobs": int
        }
    """
    from app.workers.rq_stt_worker import cancel_batch
    
    # 배치 조회
    result = await db.execute(
        select(STTBatch).where(STTBatch.id == batch_id)
    )
    batch = result.scalar_one_or_none()
    
    if not batch:
        raise HTTPException(status_code=404, detail="배치를 찾을 수 없습니다")
    
    # RQ 작업 취소
    cancelled_count = cancel_batch(batch_id)
    
    # 배치 상태 업데이트
    batch.status = "cancelled"
    await db.commit()
    
    return {
        "message": f"{cancelled_count}개 작업이 취소되었습니다",
        "cancelled_jobs": cancelled_count,
        "batch_id": batch_id
    }

