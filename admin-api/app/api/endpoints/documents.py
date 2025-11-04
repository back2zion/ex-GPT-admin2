"""
문서 관리 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime
import hashlib
import io
import uuid

from app.models.document import Document
from app.models.approval import DocumentChangeRequest
from app.core.database import get_db
from app.core.config import settings
from app.dependencies import get_principal
from app.services.storage import StorageService
from app.services.vector_store import VectorStoreService
from cerbos.sdk.model import Principal

router = APIRouter()

# MinIO와 Qdrant 서비스 초기화 (환경 변수 직접 사용)
import os

storage_service = StorageService(
    endpoint=os.getenv("MINIO_ENDPOINT", settings.MINIO_ENDPOINT),
    access_key=os.getenv("MINIO_ACCESS_KEY", settings.MINIO_ACCESS_KEY),
    secret_key=os.getenv("MINIO_SECRET_KEY", settings.MINIO_SECRET_KEY),
    secure=os.getenv("MINIO_SECURE", "false").lower() == "true"
)

vector_store_service = VectorStoreService(
    host=os.getenv("QDRANT_HOST", settings.QDRANT_HOST),
    port=int(os.getenv("QDRANT_PORT", str(settings.QDRANT_PORT)))
)


@router.get("/")
async def list_documents(
    skip: int = Query(0, ge=0, description="오프셋"),
    limit: int = Query(100, le=1000, description="최대 개수"),
    document_type: Optional[str] = Query(None, description="문서 타입 (law/regulation/standard)"),
    status: Optional[str] = Query(None, description="상태 (active/inactive/pending)"),
    search: Optional[str] = Query(None, description="검색어 (제목/내용)"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    문서 목록 조회

    - 문서 타입, 상태로 필터링 가능
    - 제목/내용 검색 지원
    - 페이지네이션 지원
    """
    query = select(Document)

    # 필터링
    if document_type:
        query = query.filter(Document.document_type == document_type)
    if status:
        query = query.filter(Document.status == status)
    if search:
        query = query.filter(
            (Document.title.contains(search)) |
            (Document.content.contains(search))
        )

    # 총 개수
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 페이지네이션
    query = query.order_by(Document.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    documents = result.scalars().all()

    return {
        "total": total,
        "items": [
            {
                "id": doc.id,
                "document_id": doc.document_id,
                "title": doc.title,
                "document_type": doc.document_type,
                "status": doc.status,
                "version": doc.current_version or "1.0",
                "legacy_id": doc.legacy_id,
                "file_name": doc.file_name,
                "file_size": doc.file_size,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                "created_at": doc.created_at.isoformat() if doc.created_at else None
            }
            for doc in documents
        ],
        "skip": skip,
        "limit": limit
    }


@router.get("/stats")
async def get_document_stats(
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    문서 통계 조회 (대시보드용)

    - 문서 타입별 개수
    - 상태별 개수
    - 파일 확장자별 개수
    - 총 문서 수

    빠른 응답을 위해 SQL GROUP BY 사용
    """
    from sqlalchemy import case
    import os

    # 타입별 카운트
    type_query = select(
        Document.document_type,
        func.count(Document.id).label('count')
    ).group_by(Document.document_type)

    type_result = await db.execute(type_query)
    by_type = {row.document_type: row.count for row in type_result}

    # 상태별 카운트
    status_query = select(
        Document.status,
        func.count(Document.id).label('count')
    ).group_by(Document.status)

    status_result = await db.execute(status_query)
    by_status = {row.status: row.count for row in status_result}

    # 파일 확장자별 카운트 (file_name에서 추출)
    # 모든 문서의 file_name을 가져와서 확장자 집계
    file_query = select(Document.file_name).filter(Document.file_name.isnot(None))
    file_result = await db.execute(file_query)
    file_names = [row[0] for row in file_result]

    by_extension = {}
    for file_name in file_names:
        if file_name:
            ext = os.path.splitext(file_name)[1].lower().lstrip('.')
            if ext:
                by_extension[ext] = by_extension.get(ext, 0) + 1

    # 총 개수
    total_query = select(func.count(Document.id))
    total_result = await db.execute(total_query)
    total = total_result.scalar()

    return {
        "total": total,
        "by_type": by_type,
        "by_status": by_status,
        "by_extension": by_extension
    }


@router.get("/changes")
async def get_document_changes(
    since: Optional[str] = Query(None, description="이 시각 이후 변경사항 (ISO 8601)"),
    status: Optional[str] = Query(None, description="변경 요청 상태"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    문서 변경 이력 조회 (승인 대기 목록)

    - 레거시 시스템에서 감지된 변경사항
    - 승인/반려 상태로 필터링 가능
    """
    query = select(DocumentChangeRequest)

    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            query = query.filter(DocumentChangeRequest.created_at >= since_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="잘못된 날짜 형식입니다")

    if status:
        query = query.filter(DocumentChangeRequest.status == status)

    query = query.order_by(DocumentChangeRequest.created_at.desc()).limit(100)
    result = await db.execute(query)
    changes = result.scalars().all()

    last_sync = None
    if changes:
        last_sync = max(c.created_at for c in changes).isoformat()

    return {
        "changes": [
            {
                "id": change.id,
                "document_id": change.document_id,
                "legacy_id": change.legacy_id,
                "change_type": change.change_type,
                "status": change.status,
                "diff_summary": change.diff_summary,
                "created_at": change.created_at.isoformat() if change.created_at else None,
                "approved_at": change.approved_at
            }
            for change in changes
        ],
        "last_sync": last_sync
    }


@router.post("/sync")
async def sync_documents(
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    레거시 시스템과 문서 동기화 (수동 트리거)

    - 레거시 DB에서 문서 조회
    - 변경사항 감지
    - 승인 대기 목록 생성
    """
    try:
        from app.services.scheduler import DocumentSyncScheduler

        scheduler = DocumentSyncScheduler()
        result = await scheduler.run_sync_job(db)

        return {
            "status": "success",
            "synced_count": result.get("change_requests_created", 0),
            "details": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"동기화 실패: {str(e)}"
        )


@router.post("/sync-from-minio")
async def sync_from_minio(
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    MinIO와 Qdrant에서 문서 동기화

    - MinIO gov-audit 버킷에서 문서 메타데이터 조회
    - Qdrant ga_collection에서 벡터 데이터 확인
    - Admin DB에 문서 정보 저장
    """
    try:
        import json
        from minio import Minio
        from app.models.document import DocumentType, DocumentStatus

        # MinIO 클라이언트 설정 (ex-gpt 컨테이너)
        # admin-api가 exgpt_net에 연결되어 있어서 컨테이너 이름으로 직접 접근 가능
        minio_endpoint = os.getenv("EX_GPT_MINIO_ENDPOINT", "minio:9000")

        minio_client = Minio(
            minio_endpoint,
            access_key="neoali",
            secret_key="exgpt2025",
            secure=False
        )

        # Qdrant 클라이언트 설정 (ex-gpt 컨테이너)
        from qdrant_client import QdrantClient
        qdrant_host = os.getenv("EX_GPT_QDRANT_HOST", "qdrant")
        qdrant_port = int(os.getenv("EX_GPT_QDRANT_PORT", "6333"))
        qdrant_api_key = os.getenv("EX_GPT_QDRANT_API_KEY", "QFy9YlRTm0Y1yo6D")

        qdrant_client = QdrantClient(
            host=qdrant_host,
            port=qdrant_port,
            api_key=qdrant_api_key
        )

        synced_count = 0
        errors = []

        # processed 버킷의 모든 문서 폴더 나열 (3,000개 이상의 문서)
        bucket_name = "processed"
        objects = minio_client.list_objects(bucket_name, prefix="", recursive=False)

        for obj in objects:
            if not obj.is_dir:
                continue

            document_id = obj.object_name.rstrip('/')

            try:
                # metadata.json 파일 읽기
                metadata_path = f"{document_id}/metadata.json"
                response = minio_client.get_object(bucket_name, metadata_path)
                metadata = json.loads(response.read().decode('utf-8'))
                response.close()
                response.release_conn()

                # 이미 DB에 있는지 확인
                existing_query = select(Document).filter(Document.document_id == document_id)
                existing_result = await db.execute(existing_query)
                existing_doc = existing_result.scalar_one_or_none()

                if existing_doc:
                    # 이미 존재하면 스킵
                    continue

                # 문서 타입 결정 (제목 기반 간단한 추론)
                title = metadata.get("name", "")
                doc_type = DocumentType.OTHER
                if "법" in title or "규정" in title:
                    doc_type = DocumentType.REGULATION
                elif "기준" in title or "표준" in title:
                    doc_type = DocumentType.STANDARD
                elif "매뉴얼" in title or "지침" in title:
                    doc_type = DocumentType.MANUAL

                # 파일 크기 가져오기
                raw_uri = metadata.get("artifacts", {}).get("raw_file_uri", "")
                file_path = ""
                file_size = 0

                # s3://raw/... 또는 s3://processed/... 형식에서 버킷과 경로 추출
                if raw_uri.startswith("s3://"):
                    parts = raw_uri.replace("s3://", "").split("/", 1)
                    if len(parts) == 2:
                        file_bucket, file_path = parts
                        try:
                            file_stat = minio_client.stat_object(file_bucket, file_path)
                            file_size = file_stat.size
                        except:
                            pass

                # 실제 파일 확장자 추출
                actual_file_ext = ""
                if file_path:
                    # file_path에서 확장자 추출 (예: "00356dd6254d6cac/file.hwp" -> ".hwp")
                    import os as os_module
                    actual_file_ext = os_module.path.splitext(file_path)[1]

                # file_name 결정: 실제 파일 확장자 사용
                if actual_file_ext:
                    file_name = title + actual_file_ext
                else:
                    file_name = title + ".pdf" if ".pdf" not in title else title

                # MIME 타입 결정
                mime_type_map = {
                    ".pdf": "application/pdf",
                    ".hwp": "application/x-hwp",
                    ".hwpx": "application/x-hwp",
                    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                }
                mime_type = mime_type_map.get(actual_file_ext.lower(), "application/octet-stream")

                # 문서 레코드 생성
                new_doc = Document(
                    document_id=document_id,
                    title=title,
                    document_type=doc_type,
                    status=DocumentStatus.ACTIVE if metadata.get("status") == "ready" else DocumentStatus.PENDING,
                    legacy_id=metadata.get("id"),
                    legacy_updated_at=metadata.get("date_updated_utc"),
                    content=None,  # content.md를 읽어서 저장할 수도 있음
                    summary=None,
                    doc_metadata=metadata,
                    current_version=metadata.get("version", "1.0"),
                    file_path=file_path,
                    file_name=file_name,
                    file_size=file_size,
                    mime_type=mime_type
                )

                db.add(new_doc)
                synced_count += 1

            except Exception as e:
                errors.append(f"{document_id}: {str(e)}")
                continue

        await db.commit()

        return {
            "status": "success",
            "synced_count": synced_count,
            "total_processed": synced_count + len(errors),
            "errors": errors[:10]  # 최대 10개 에러만 반환
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"MinIO 동기화 실패: {str(e)}"
        )


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    특정 문서 상세 조회

    - document_id 또는 legacy_id로 조회 가능
    """
    # document_id로 먼저 시도
    query = select(Document).filter(Document.document_id == document_id)
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    # 없으면 legacy_id로 시도
    if not document:
        query = select(Document).filter(Document.legacy_id == document_id)
        result = await db.execute(query)
        document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    return {
        "id": document.id,
        "document_id": document.document_id,
        "title": document.title,
        "content": document.content,
        "document_type": document.document_type,
        "status": document.status,
        "version": document.current_version or "1.0",
        "legacy_id": document.legacy_id,
        "file_name": document.file_name,
        "file_path": document.file_path,
        "legacy_updated_at": document.legacy_updated_at,
        "created_at": document.created_at.isoformat() if document.created_at else None,
        "updated_at": document.updated_at.isoformat() if document.updated_at else None
    }


@router.post("/{change_request_id}/approve")
async def approve_document_change(
    change_request_id: int,
    comment: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    문서 변경 승인

    - 승인 완료 시 자동으로 Document 테이블 업데이트
    - 벡터 DB 재색인 트리거 (TODO: ds-api 연동)
    """
    try:
        from app.services.approval_workflow import ApprovalWorkflowService

        approval_service = ApprovalWorkflowService(db)

        # 변경 요청 조회
        change_request = await db.get(DocumentChangeRequest, change_request_id)
        if not change_request:
            raise HTTPException(status_code=404, detail="변경 요청을 찾을 수 없습니다")

        # 승인 프로세스 시작 (간단한 1단계 승인)
        await approval_service.initiate_approval(
            change_request_id=change_request_id,
            approvers=[{"level": 1, "user_id": 1, "name": principal.id}]  # 현재 사용자
        )

        # 승인 처리
        await approval_service.approve(
            change_request_id=change_request_id,
            approver_id=1,  # TODO: 실제 사용자 ID
            level=1,
            comment=comment or "승인"
        )

        # 변경사항 적용
        applied = await approval_service.apply_changes(change_request_id)

        await db.commit()

        return {
            "message": "문서 변경이 승인되었습니다",
            "change_request_id": change_request_id,
            "applied": applied
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"승인 실패: {str(e)}"
        )


@router.post("/{change_request_id}/reject")
async def reject_document_change(
    change_request_id: int,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """문서 변경 반려"""
    try:
        from app.services.approval_workflow import ApprovalWorkflowService

        approval_service = ApprovalWorkflowService(db)

        # 변경 요청 조회
        change_request = await db.get(DocumentChangeRequest, change_request_id)
        if not change_request:
            raise HTTPException(status_code=404, detail="변경 요청을 찾을 수 없습니다")

        # 반려 처리
        await approval_service.reject(
            change_request_id=change_request_id,
            approver_id=1,  # TODO: 실제 사용자 ID
            level=1,
            comment=reason or "반려"
        )

        await db.commit()

        return {
            "message": "문서 변경이 반려되었습니다",
            "change_request_id": change_request_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"반려 실패: {str(e)}"
        )


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Query("general", description="문서 타입"),
    title: Optional[str] = Query(None, description="문서 제목"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    문서 업로드

    - 파일을 MinIO에 저장
    - 메타데이터를 PostgreSQL에 저장
    - Qdrant에 벡터 인덱싱 (텍스트 추출 + 임베딩 생성)
    """
    try:
        # 파일 읽기
        file_content = await file.read()
        file_size = len(file_content)

        # 파일 해시 생성 (document_id로 사용)
        file_hash = hashlib.sha256(file_content).hexdigest()

        # MinIO에 파일 업로드
        object_name = f"{file_hash}/{file.filename}"
        data_stream = io.BytesIO(file_content)

        etag = storage_service.put_object(
            bucket_name=settings.MINIO_BUCKET,
            object_name=object_name,
            data=data_stream,
            length=file_size,
            content_type=file.content_type or "application/octet-stream"
        )

        if not etag:
            raise HTTPException(status_code=500, detail="파일 업로드 실패")

        # Qdrant 인덱싱 시도 (비동기, 실패해도 업로드는 성공으로 처리)
        indexed = False
        extracted_text = None
        try:
            from app.services.document_processor import DocumentProcessor

            processor = DocumentProcessor(
                embedding_endpoint=os.getenv("EMBEDDING_MODEL_ENDPOINT", "http://vllm-embeddings:8000/v1")
            )

            # 메타데이터 준비
            metadata = {
                "title": title or file.filename,
                "document_type": document_type,
                "file_size": file_size,
                "mime_type": file.content_type
            }

            # 문서 처리 (텍스트 추출 + 청킹 + 임베딩)
            extracted_text, chunk_data = await processor.process_document(
                file_content=file_content,
                filename=file.filename,
                document_id=file_hash,
                metadata=metadata
            )

            # Qdrant에 저장
            if chunk_data:
                qdrant_collection = os.getenv("QDRANT_COLLECTION", "documents")
                success = await vector_store_service.upsert_points(
                    collection_name=qdrant_collection,
                    points=chunk_data
                )
                if success:
                    indexed = True
                    logger.info(f"✅ Document indexed in Qdrant: {file_hash} ({len(chunk_data)} chunks)")
                else:
                    logger.warning(f"⚠️ Failed to index document in Qdrant: {file_hash}")
            else:
                logger.warning(f"⚠️ No chunks generated for document: {file_hash}")

        except Exception as e:
            logger.error(f"❌ Qdrant indexing failed for {file_hash}: {e}")
            # 인덱싱 실패해도 파일 업로드는 성공으로 처리

        # PostgreSQL에 메타데이터 저장
        document = Document(
            document_id=file_hash,
            title=title or file.filename,
            content=extracted_text[:5000] if extracted_text else f"파일: {file.filename} (크기: {file_size} bytes)",
            document_type=document_type,
            status="active",
            current_version="1.0",
            file_path=object_name,
            file_size=file_size,
            file_name=file.filename,
            mime_type=file.content_type
        )

        db.add(document)
        await db.commit()
        await db.refresh(document)

        return {
            "message": "파일 업로드 성공" + (" (Qdrant 인덱싱 완료)" if indexed else " (Qdrant 인덱싱 실패)"),
            "document_id": file_hash,
            "file_name": file.filename,
            "file_size": file_size,
            "object_name": object_name,
            "etag": etag,
            "indexed": indexed,
            "chunks_indexed": len(chunk_data) if chunk_data else 0
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"업로드 실패: {str(e)}"
        )


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    문서 다운로드

    - PostgreSQL에서 메타데이터 조회
    - MinIO에서 파일 다운로드
    """
    # 문서 조회
    query = select(Document).filter(Document.document_id == document_id)
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    if not document.file_path:
        raise HTTPException(status_code=404, detail="파일 경로가 없습니다")

    # 버킷과 파일 경로 결정
    # file_path 형식: "ga-xxx/file.pdf" 또는 "00356dd6254d6cac/file.hwp"
    bucket_name = None
    object_name = document.file_path

    # ga- 접두사면 gov-audit 버킷
    if document.file_path.startswith("ga-"):
        bucket_name = "gov-audit"
    else:
        # 기본적으로 documents 버킷 시도 (새 업로드용)
        bucket_name = "documents"

    # MinIO 클라이언트 설정
    from minio import Minio
    minio_endpoint = os.getenv("EX_GPT_MINIO_ENDPOINT", "minio:9000")
    minio_client = Minio(
        minio_endpoint,
        access_key="neoali",
        secret_key="exgpt2025",
        secure=False
    )

    # MinIO에서 파일 다운로드 (여러 버킷 시도)
    file_data = None
    tried_buckets = []

    # 우선순위: documents -> raw -> processed (ga- 파일이 아닌 경우)
    buckets_to_try = ["documents", "raw", "processed"] if bucket_name == "documents" else [bucket_name]

    for bucket in buckets_to_try:
        try:
            tried_buckets.append(bucket)
            response = minio_client.get_object(bucket, object_name)
            file_data = response.read()
            response.close()
            response.release_conn()
            break  # 성공하면 루프 종료
        except Exception as e:
            continue  # 다음 버킷 시도

    if not file_data:
        raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {bucket_name}/{object_name}")

    # 파일 스트리밍 응답
    # 한글 파일명을 URL 인코딩
    from urllib.parse import quote
    filename_encoded = quote(document.file_name.encode('utf-8'))

    return StreamingResponse(
        io.BytesIO(file_data),
        media_type=document.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"
        }
    )


@router.get("/search")
async def search_documents(
    query: str = Query(..., description="검색어"),
    limit: int = Query(10, le=100, description="최대 결과 수"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    문서 검색 (텍스트 기반)

    - PostgreSQL에서 제목/내용 검색
    - 향후 Qdrant 벡터 검색 추가 예정
    """
    # 텍스트 검색
    search_query = select(Document).filter(
        (Document.title.contains(query)) |
        (Document.content.contains(query)) |
        (Document.file_name.contains(query))
    ).limit(limit)

    result = await db.execute(search_query)
    documents = result.scalars().all()

    return {
        "query": query,
        "total": len(documents),
        "items": [
            {
                "id": doc.id,
                "document_id": doc.document_id,
                "title": doc.title,
                "file_name": doc.file_name,
                "document_type": doc.document_type,
                "status": doc.status,
                "created_at": doc.created_at.isoformat() if doc.created_at else None
            }
            for doc in documents
        ]
    }
