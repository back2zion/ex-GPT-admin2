"""
Documents API Router
학습데이터 관리 - 문서 CRUD API (Secure Coding Applied)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from typing import List, Optional
import os

from app.core.database import get_db
from app.models.document import Document, DocumentType, DocumentStatus
from app.models.document_vector import DocumentVector, VectorStatus
from app.models.category import Category
from app.schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
    DocumentVectorInfo,
    VectorStatusEnum,
    DocumentStatusEnum,
    DocumentTypeEnum
)

router = APIRouter(prefix="/api/v1/admin/documents", tags=["documents"])


async def get_vector_info(document_id: int, db: AsyncSession) -> DocumentVectorInfo:
    """
    문서의 벡터화 정보 집계
    Secure: Parameterized query
    """
    # Count vectors by status
    query = select(
        func.count(DocumentVector.id).label('total'),
        func.count(func.nullif(DocumentVector.status == VectorStatus.COMPLETED, False)).label('completed'),
        func.count(func.nullif(DocumentVector.status == VectorStatus.FAILED, False)).label('failed'),
        DocumentVector.vector_dimension,
        DocumentVector.embedding_model
    ).where(DocumentVector.document_id == document_id).group_by(
        DocumentVector.vector_dimension,
        DocumentVector.embedding_model
    )

    result = await db.execute(query)
    row = result.first()

    if not row or row.total == 0:
        return DocumentVectorInfo(
            total_chunks=0,
            completed_chunks=0,
            failed_chunks=0,
            status=VectorStatusEnum.PENDING
        )

    total = row.total or 0
    completed = row.completed or 0
    failed = row.failed or 0

    # Determine overall status
    if failed > 0:
        status = VectorStatusEnum.FAILED
    elif completed == total:
        status = VectorStatusEnum.COMPLETED
    elif completed > 0:
        status = VectorStatusEnum.PROCESSING
    else:
        status = VectorStatusEnum.PENDING

    return DocumentVectorInfo(
        total_chunks=total,
        completed_chunks=completed,
        failed_chunks=failed,
        status=status,
        vector_dimension=row.vector_dimension,
        embedding_model=row.embedding_model
    )


@router.post("", response_model=DocumentResponse, status_code=201)
async def create_document(
    document: DocumentCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    문서 메타데이터 생성
    Secure: Input validation via Pydantic, Unique constraint handling
    Note: 파일 업로드는 /upload 엔드포인트 사용
    """
    try:
        # Validate category exists if provided
        if document.category_id:
            category_query = select(Category).where(Category.id == document.category_id)
            category_result = await db.execute(category_query)
            category = category_result.scalar_one_or_none()
            if not category:
                raise HTTPException(status_code=400, detail="카테고리를 찾을 수 없습니다")

        # Create new document
        db_document = Document(
            document_id=document.document_id,
            title=document.title,
            document_type=document.document_type,
            status=document.status,
            category_id=document.category_id,
            content=document.content,
            summary=document.summary
        )

        db.add(db_document)
        await db.commit()
        await db.refresh(db_document)

        # Get vector info and category name
        vector_info = await get_vector_info(db_document.id, db)
        category_name = None
        if db_document.category_id:
            cat_query = select(Category.name).where(Category.id == db_document.category_id)
            cat_result = await db.execute(cat_query)
            category_name = cat_result.scalar_one_or_none()

        # Build response
        response_data = DocumentResponse.model_validate(db_document)
        response_data.vector_info = vector_info
        response_data.category_name = category_name

        return response_data

    except IntegrityError as e:
        await db.rollback()
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail=f"문서 ID '{document.document_id}'가 이미 존재합니다"
            )
        raise HTTPException(status_code=400, detail="문서 생성 실패")


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0, description="스킵할 항목 수"),
    limit: int = Query(50, ge=1, le=100, description="가져올 항목 수 (최대 100)"),
    category_id: Optional[int] = Query(None, description="카테고리 필터"),
    status: Optional[DocumentStatusEnum] = Query(None, description="상태 필터"),
    document_type: Optional[DocumentTypeEnum] = Query(None, description="문서 타입 필터"),
    search: Optional[str] = Query(None, max_length=200, description="제목 검색"),
    db: AsyncSession = Depends(get_db)
):
    """
    문서 목록 조회
    Secure: Parameterized query, Pagination limits to prevent DoS
    """
    # Build filter conditions
    conditions = []

    if category_id is not None:
        conditions.append(Document.category_id == category_id)

    if status is not None:
        conditions.append(Document.status == status)

    if document_type is not None:
        conditions.append(Document.document_type == document_type)

    if search:
        # Secure: Parameterized LIKE query
        search_pattern = f"%{search}%"
        conditions.append(or_(
            Document.title.ilike(search_pattern),
            Document.document_id.ilike(search_pattern)
        ))

    # Get total count
    count_query = select(func.count()).select_from(Document)
    if conditions:
        count_query = count_query.where(and_(*conditions))

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get documents with pagination
    query = select(Document).options(
        selectinload(Document.category)
    ).offset(skip).limit(limit).order_by(Document.created_at.desc())

    if conditions:
        query = query.where(and_(*conditions))

    result = await db.execute(query)
    documents = result.scalars().all()

    # Calculate page number
    page = (skip // limit) + 1 if limit > 0 else 1

    # Build response with vector info
    response_items = []
    for doc in documents:
        vector_info = await get_vector_info(doc.id, db)
        doc_response = DocumentResponse.model_validate(doc)
        doc_response.vector_info = vector_info
        doc_response.category_name = doc.category.name if doc.category else None
        response_items.append(doc_response)

    return DocumentListResponse(
        items=response_items,
        total=total or 0,
        page=page,
        limit=limit
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    ID로 문서 조회
    Secure: Parameterized query prevents SQL injection
    """
    query = select(Document).options(
        selectinload(Document.category)
    ).where(Document.id == document_id)

    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    # Get vector info
    vector_info = await get_vector_info(document.id, db)

    # Build response
    doc_response = DocumentResponse.model_validate(document)
    doc_response.vector_info = vector_info
    doc_response.category_name = document.category.name if document.category else None

    return doc_response


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    문서 수정
    Secure: Input validation, Parameterized query
    """
    # Find existing document
    query = select(Document).where(Document.id == document_id)
    result = await db.execute(query)
    db_document = result.scalar_one_or_none()

    if not db_document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    try:
        # Validate category if provided
        if document_update.category_id is not None:
            category_query = select(Category).where(Category.id == document_update.category_id)
            category_result = await db.execute(category_query)
            category = category_result.scalar_one_or_none()
            if not category:
                raise HTTPException(status_code=400, detail="카테고리를 찾을 수 없습니다")

        # Update fields (only non-None values)
        update_data = document_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_document, field, value)

        await db.commit()
        await db.refresh(db_document)

        # Get updated info
        vector_info = await get_vector_info(db_document.id, db)
        category_name = None
        if db_document.category_id:
            cat_query = select(Category.name).where(Category.id == db_document.category_id)
            cat_result = await db.execute(cat_query)
            category_name = cat_result.scalar_one_or_none()

        # Build response
        doc_response = DocumentResponse.model_validate(db_document)
        doc_response.vector_info = vector_info
        doc_response.category_name = category_name

        return doc_response

    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail="문서 수정 실패")


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    문서 삭제
    Secure: Cascade delete for vectors via relationship
    """
    # Find document
    query = select(Document).where(Document.id == document_id)
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    # Delete document (vectors will be cascade deleted)
    await db.delete(document)
    await db.commit()

    return None


@router.post("/{document_id}/revectorize", response_model=DocumentResponse)
async def revectorize_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    문서 재벡터화
    실패한 문서나 업데이트된 문서에 대해 벡터화를 다시 수행합니다.
    Secure: Parameterized query, Transaction safety
    """
    from app.services.vectorization_service import vectorization_service

    # Find document
    query = select(Document).options(
        selectinload(Document.category)
    ).where(Document.id == document_id)

    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    if not document.content:
        raise HTTPException(status_code=400, detail="문서 내용이 없어 벡터화할 수 없습니다")

    try:
        # Delete existing vectors
        delete_query = select(DocumentVector).where(DocumentVector.document_id == document_id)
        delete_result = await db.execute(delete_query)
        existing_vectors = delete_result.scalars().all()

        for vector in existing_vectors:
            await db.delete(vector)

        await db.commit()

        # Re-vectorize
        await vectorization_service.vectorize_document(
            document.id,
            document.content,
            db,
            metadata={
                "filename": document.file_name or "",
                "title": document.title,
                "file_type": document.file_name.split('.')[-1] if document.file_name and '.' in document.file_name else "",
                "mime_type": document.mime_type or ""
            }
        )

        # Get updated vector info
        vector_info = await get_vector_info(document.id, db)

        # Build response
        doc_response = DocumentResponse.model_validate(document)
        doc_response.vector_info = vector_info
        doc_response.category_name = document.category.name if document.category else None

        return doc_response

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"재벡터화 실패: {str(e)}")


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    document_type: DocumentTypeEnum = Form(...),
    category_id: Optional[int] = Form(None),
    status: DocumentStatusEnum = Form(DocumentStatusEnum.PENDING),
    db: AsyncSession = Depends(get_db)
):
    """
    문서 파일 업로드 및 자동 벡터화
    Secure: File type validation, Size limits, Filename sanitization
    """
    from app.services.minio_service import minio_service
    from app.services.vectorization_service import vectorization_service
    import uuid

    # Validate file type (Secure: File Type Validation)
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
        "text/plain",
        "application/x-hwp",  # HWP
        "application/haansofthwp",  # HWP (alternative)
        "application/vnd.hancom.hwpx",  # HWPX
        "application/vnd.ms-powerpoint",  # PPT
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # PPTX
        "application/octet-stream"  # Fallback for HWP files
    ]

    # Additional extension check for security
    allowed_extensions = ['.pdf', '.docx', '.txt', '.hwp', '.hwpx', '.ppt', '.pptx']
    file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''

    if file.content_type not in allowed_types and f'.{file_ext}' not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"지원되지 않는 파일 형식입니다. 허용: PDF, DOCX, TXT, HWP, HWPX, PPT, PPTX"
        )

    # Validate category
    if category_id:
        category_query = select(Category).where(Category.id == category_id)
        category_result = await db.execute(category_query)
        category = category_result.scalar_one_or_none()
        if not category:
            raise HTTPException(status_code=400, detail="카테고리를 찾을 수 없습니다")

    try:
        # Auto-generate title from filename if not provided
        if not title or not title.strip():
            # Remove extension and clean up filename
            title = os.path.splitext(file.filename)[0]
            # Replace underscores and dashes with spaces
            title = title.replace('_', ' ').replace('-', ' ')
            # Limit length
            if len(title) > 200:
                title = title[:200] + "..."

        # 1. Upload to MinIO
        file_path, file_size = minio_service.upload_file(
            file.file,
            file.filename,
            file.content_type
        )

        # 2. Create document record
        doc_id = f"DOC-{uuid.uuid4().hex[:12].upper()}"
        db_document = Document(
            document_id=doc_id,
            title=title.strip(),
            document_type=document_type,
            status=status,
            category_id=category_id,
            file_path=file_path,
            file_name=file.filename,
            file_size=file_size,
            mime_type=file.content_type
        )

        db.add(db_document)
        await db.commit()
        await db.refresh(db_document)

        # 3. Extract text from document
        from app.services.text_extraction_service import text_extraction_service

        # Reset file pointer for text extraction
        file.file.seek(0)
        extracted_text = text_extraction_service.extract_text(
            file.file,
            file.filename,
            file.content_type
        )

        # Store extracted text in document content field
        # Remove NULL bytes (PostgreSQL doesn't allow \x00 in UTF-8 text)
        cleaned_text = extracted_text.replace('\x00', '')
        db_document.content = cleaned_text[:1000000]  # Limit to 1MB
        await db.commit()
        await db.refresh(db_document)

        # 4. Vectorize in background
        try:
            await vectorization_service.vectorize_document(
                db_document.id,
                extracted_text,
                db,
                metadata={
                    "filename": file.filename,
                    "title": title,
                    "file_type": file_ext,
                    "mime_type": file.content_type
                }
            )
        except Exception as e:
            print(f"Vectorization warning: {e}")
            # Continue even if vectorization fails

        # 5. Get final state
        vector_info = await get_vector_info(db_document.id, db)
        category_name = None
        if db_document.category_id:
            cat_query = select(Category.name).where(Category.id == db_document.category_id)
            cat_result = await db.execute(cat_query)
            category_name = cat_result.scalar_one_or_none()

        # Build response
        response_data = DocumentResponse.model_validate(db_document)
        response_data.vector_info = vector_info
        response_data.category_name = category_name

        return response_data

    except ValueError as e:
        await db.rollback()
        print(f"[UPLOAD ERROR] ValueError: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        import traceback
        error_trace = traceback.format_exc()
        print(f"[UPLOAD ERROR] Exception: {str(e)}")
        print(f"[UPLOAD ERROR] Traceback:\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"업로드 실패: {str(e)}")
