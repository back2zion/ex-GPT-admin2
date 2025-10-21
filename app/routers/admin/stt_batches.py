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


@router.get("/")
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


@router.post("/", response_model=STTBatchResponse, status_code=201)
async def create_stt_batch(
    batch: STTBatchCreate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("stt_batch", "create"))
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
