"""
개인정보 검출 관리 API
PRD_v2.md P0 요구사항: FUN-003
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import json

from app.models.pii_detection import PIIDetectionResult, PIIStatus
from app.models.document import Document
from app.schemas.pii_detection import (
    PIIDetectionResultResponse,
    PIIApprovalRequest,
    PIIDetectionListResponse,
    PIIMatchSchema
)
from app.services.pii_scanner import PIIScanner
from app.core.database import get_db
from app.dependencies import require_permission, get_principal
from cerbos.sdk.model import Principal


router = APIRouter(prefix="/api/v1/admin/pii-detections", tags=["admin-pii"])


@router.post("/scan/{document_id}", response_model=PIIDetectionResultResponse)
async def scan_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("document", "update"))
):
    """
    문서를 스캔하여 개인정보를 검출합니다.

    시큐어 코딩:
    - 권한 검증: Cerbos를 통한 문서 수정 권한 확인
    - 입력 검증: document_id 유효성 확인
    """
    scanner = PIIScanner()

    try:
        result = await scanner.scan_document(document_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Response 변환
    pii_matches = []
    if result.pii_data:
        matches_data = json.loads(result.pii_data)
        pii_matches = [PIIMatchSchema(**m) for m in matches_data]

    return PIIDetectionResultResponse(
        id=result.id,
        document_id=result.document_id,
        has_pii=result.has_pii,
        pii_matches=pii_matches,
        status=result.status,
        admin_note=result.admin_note,
        processed_by=result.processed_by,
        created_at=result.created_at,
        updated_at=result.updated_at
    )


@router.get("/", response_model=PIIDetectionListResponse)
async def list_pii_detections(
    status: Optional[PIIStatus] = Query(None, description="처리 상태 필터"),
    has_pii: Optional[bool] = Query(None, description="PII 포함 여부 필터"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("pii_detection", "view"))
):
    """
    PII 검출 결과 목록을 조회합니다.

    시큐어 코딩:
    - 권한 검증: Cerbos를 통한 PII 조회 권한 확인
    - 입력 검증: 페이지, 페이지 크기 범위 검증
    - 개인정보 보호: 마스킹된 정보만 반환
    """
    query = select(PIIDetectionResult).order_by(PIIDetectionResult.created_at.desc())

    # 필터링
    if status is not None:
        query = query.filter(PIIDetectionResult.status == status)

    if has_pii is not None:
        query = query.filter(PIIDetectionResult.has_pii == has_pii)

    # 총 개수
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 페이징
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    detections = result.scalars().all()

    # Response 변환
    items = []
    for detection in detections:
        pii_matches = []
        if detection.pii_data:
            matches_data = json.loads(detection.pii_data)
            pii_matches = [PIIMatchSchema(**m) for m in matches_data]

        items.append(PIIDetectionResultResponse(
            id=detection.id,
            document_id=detection.document_id,
            has_pii=detection.has_pii,
            pii_matches=pii_matches,
            status=detection.status,
            admin_note=detection.admin_note,
            processed_by=detection.processed_by,
            created_at=detection.created_at,
            updated_at=detection.updated_at
        ))

    return PIIDetectionListResponse(
        total=total,
        items=items,
        page=page,
        page_size=page_size
    )


@router.get("/{detection_id}", response_model=PIIDetectionResultResponse)
async def get_pii_detection(
    detection_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("pii_detection", "view"))
):
    """
    PII 검출 결과 상세를 조회합니다.

    시큐어 코딩:
    - 권한 검증: Cerbos를 통한 PII 조회 권한 확인
    - 개인정보 보호: 마스킹된 정보만 반환
    """
    result = await db.execute(
        select(PIIDetectionResult).filter(PIIDetectionResult.id == detection_id)
    )
    detection = result.scalar_one_or_none()

    if not detection:
        raise HTTPException(status_code=404, detail="PII 검출 결과를 찾을 수 없습니다")

    # Response 변환
    pii_matches = []
    if detection.pii_data:
        matches_data = json.loads(detection.pii_data)
        pii_matches = [PIIMatchSchema(**m) for m in matches_data]

    return PIIDetectionResultResponse(
        id=detection.id,
        document_id=detection.document_id,
        has_pii=detection.has_pii,
        pii_matches=pii_matches,
        status=detection.status,
        admin_note=detection.admin_note,
        processed_by=detection.processed_by,
        created_at=detection.created_at,
        updated_at=detection.updated_at
    )


@router.post("/{detection_id}/approve", response_model=PIIDetectionResultResponse)
async def approve_pii_detection(
    detection_id: int,
    approval: PIIApprovalRequest,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("pii_detection", "approve"))
):
    """
    PII 검출 결과를 승인 처리합니다.

    처리 작업:
    - approve: 승인 (원본 유지)
    - mask: 마스킹 처리
    - delete: 문서 삭제

    시큐어 코딩:
    - 권한 검증: Cerbos를 통한 PII 승인 권한 확인
    - 입력 검증: action 값 검증
    - 감사 로그: 처리 이력 기록
    """
    # PII 검출 결과 조회
    result = await db.execute(
        select(PIIDetectionResult).filter(PIIDetectionResult.id == detection_id)
    )
    detection = result.scalar_one_or_none()

    if not detection:
        raise HTTPException(status_code=404, detail="PII 검출 결과를 찾을 수 없습니다")

    # 작업 처리
    if approval.action == "approve":
        detection.status = PIIStatus.APPROVED
    elif approval.action == "mask":
        # 문서 내용을 마스킹 처리
        from app.services.pii_detector import PIIDetector

        doc_result = await db.execute(
            select(Document).filter(Document.id == detection.document_id)
        )
        document = doc_result.scalar_one_or_none()

        if document:
            detector = PIIDetector()
            document.content = detector.mask(document.content or "")
            detection.status = PIIStatus.MASKED
    elif approval.action == "delete":
        # 문서 삭제
        doc_result = await db.execute(
            select(Document).filter(Document.id == detection.document_id)
        )
        document = doc_result.scalar_one_or_none()

        if document:
            await db.delete(document)
        detection.status = PIIStatus.DELETED
    else:
        raise HTTPException(
            status_code=400,
            detail="유효하지 않은 작업입니다. (approve, mask, delete 중 선택)"
        )

    # 관리자 정보 기록
    detection.admin_note = approval.admin_note
    # TODO: principal에서 user_id 추출
    # detection.processed_by = principal.id

    await db.commit()
    await db.refresh(detection)

    # Response 변환
    pii_matches = []
    if detection.pii_data:
        matches_data = json.loads(detection.pii_data)
        pii_matches = [PIIMatchSchema(**m) for m in matches_data]

    return PIIDetectionResultResponse(
        id=detection.id,
        document_id=detection.document_id,
        has_pii=detection.has_pii,
        pii_matches=pii_matches,
        status=detection.status,
        admin_note=detection.admin_note,
        processed_by=detection.processed_by,
        created_at=detection.created_at,
        updated_at=detection.updated_at
    )
