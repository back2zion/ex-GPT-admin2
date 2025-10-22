"""
레거시 시스템 연계 API
PRD_v2.md P0: 레거시 시스템 연계
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.dependencies import get_principal
from app.models.approval import DocumentChangeRequest
from app.models.document import Document
from app.schemas.document_change import (
    DocumentChangeRequestCreate,
    DocumentChangeRequestResponse,
    DocumentChangeRequestListResponse,
    ApproveChangeRequest,
    RejectChangeRequest,
    DetectChangesResponse
)
from cerbos.sdk.model import Principal

router = APIRouter(prefix="/api/v1/admin/legacy-sync", tags=["admin-legacy-sync"])


@router.get("/detect-changes", response_model=DetectChangesResponse)
async def detect_changes(
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    레거시 DB에서 변경된 문서 감지

    TODO: 실제 레거시 DB 연결 구현
    """
    # TODO: 레거시 DB와 비교하여 변경 감지
    # 현재는 Mock 응답
    total_result = await db.execute(select(func.count()).select_from(Document))
    total = total_result.scalar()

    return DetectChangesResponse(
        changes=0,
        total=total
    )


@router.get("/change-requests", response_model=DocumentChangeRequestListResponse)
async def list_change_requests(
    status: Optional[str] = Query(None, description="상태 필터 (pending, approved, rejected, completed)"),
    skip: int = Query(0, ge=0, description="오프셋"),
    limit: int = Query(100, le=1000, description="최대 개수"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    변경 요청 목록 조회
    """
    query = select(DocumentChangeRequest)

    # 상태 필터
    if status:
        query = query.where(DocumentChangeRequest.status == status)

    # 전체 개수
    count_query = select(func.count()).select_from(DocumentChangeRequest)
    if status:
        count_query = count_query.where(DocumentChangeRequest.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 정렬 및 페이징
    query = query.order_by(DocumentChangeRequest.created_at.desc())
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()

    return DocumentChangeRequestListResponse(
        items=items,
        total=total
    )


@router.get("/change-requests/{change_id}", response_model=DocumentChangeRequestResponse)
async def get_change_request(
    change_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    변경 요청 상세 조회
    """
    result = await db.execute(
        select(DocumentChangeRequest).where(DocumentChangeRequest.id == change_id)
    )
    change_request = result.scalar_one_or_none()

    if not change_request:
        raise HTTPException(status_code=404, detail="변경 요청을 찾을 수 없습니다")

    return change_request


@router.post("/change-requests", response_model=DocumentChangeRequestResponse, status_code=201)
async def create_change_request(
    change_data: DocumentChangeRequestCreate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    변경 요청 생성
    """
    # 문서 존재 확인
    doc_result = await db.execute(
        select(Document).where(Document.id == change_data.document_id)
    )
    document = doc_result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    # 변경 요청 생성
    change_request = DocumentChangeRequest(
        document_id=change_data.document_id,
        legacy_id=change_data.legacy_id,
        change_type=change_data.change_type,
        old_data=change_data.old_data,
        new_data=change_data.new_data,
        diff_summary=change_data.diff_summary,
        status="pending"
    )

    db.add(change_request)
    await db.commit()
    await db.refresh(change_request)

    return change_request


@router.post("/change-requests/{change_id}/approve", response_model=DocumentChangeRequestResponse)
async def approve_change_request(
    change_id: int,
    approve_data: Optional[ApproveChangeRequest] = None,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    변경 요청 승인

    - 상태를 approved로 변경
    - apply_immediately=True면 문서에 즉시 반영
    """
    # 변경 요청 조회
    result = await db.execute(
        select(DocumentChangeRequest).where(DocumentChangeRequest.id == change_id)
    )
    change_request = result.scalar_one_or_none()

    if not change_request:
        raise HTTPException(status_code=404, detail="변경 요청을 찾을 수 없습니다")

    if change_request.status != "pending":
        raise HTTPException(status_code=400, detail="이미 처리된 요청입니다")

    # 승인 처리
    change_request.status = "approved"
    change_request.approved_at = datetime.utcnow().isoformat()

    # 즉시 적용
    if approve_data and approve_data.apply_immediately:
        # 문서 업데이트
        doc_result = await db.execute(
            select(Document).where(Document.id == change_request.document_id)
        )
        document = doc_result.scalar_one_or_none()

        if document and change_request.new_data:
            # 새 데이터 적용
            if "title" in change_request.new_data:
                document.title = change_request.new_data["title"]
            if "content" in change_request.new_data:
                document.content = change_request.new_data["content"]

            change_request.status = "completed"
            change_request.applied_at = datetime.utcnow().isoformat()

    await db.commit()
    await db.refresh(change_request)

    return change_request


@router.post("/change-requests/{change_id}/reject", response_model=DocumentChangeRequestResponse)
async def reject_change_request(
    change_id: int,
    reject_data: RejectChangeRequest,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    변경 요청 반려
    """
    # 변경 요청 조회
    result = await db.execute(
        select(DocumentChangeRequest).where(DocumentChangeRequest.id == change_id)
    )
    change_request = result.scalar_one_or_none()

    if not change_request:
        raise HTTPException(status_code=404, detail="변경 요청을 찾을 수 없습니다")

    if change_request.status != "pending":
        raise HTTPException(status_code=400, detail="이미 처리된 요청입니다")

    # 반려 처리
    change_request.status = "rejected"

    # diff_summary에 반려 사유 추가
    if change_request.diff_summary:
        change_request.diff_summary += f"\n[반려 사유] {reject_data.reason}"
    else:
        change_request.diff_summary = f"[반려 사유] {reject_data.reason}"

    await db.commit()
    await db.refresh(change_request)

    return change_request
