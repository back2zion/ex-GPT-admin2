"""
Files API Router
채팅 파일 업로드 API
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.services.minio_service import minio_service
from app.utils.auth import get_optional_current_user_from_session
from app.services.chat_service import validate_room_id
from pathlib import Path
from typing import Optional
import logging

router = APIRouter(prefix="/api/v1/files", tags=["chat-files"])
logger = logging.getLogger(__name__)

# 허용된 파일 확장자
ALLOWED_EXTENSIONS = {
    # Documents
    '.pdf',
    '.doc', '.docx',   # MS Word
    '.xls', '.xlsx',   # MS Excel
    '.ppt', '.pptx',   # MS PowerPoint
    '.hwp', '.hwpx',   # Hangul (한글)
    '.txt',            # Text
    # Images
    '.png', '.jpg', '.jpeg'
}

# 파일 크기 제한 (200MB)
MAX_FILE_SIZE = 200 * 1024 * 1024


@router.post("/upload")
async def upload_chat_file(
    file: UploadFile = File(...),
    room_id: str = Form(...),
    current_user: Optional[dict] = Depends(get_optional_current_user_from_session),
    db: AsyncSession = Depends(get_db)
):
    """
    채팅 파일 업로드 (MinIO + DB)

    Args:
        file: 업로드할 파일
        room_id: 대화방 ID
        current_user: 인증된 사용자 (Optional - 없으면 room_id에서 추출)
        db: 데이터베이스 세션

    Returns:
        dict: 업로드 결과

    Security:
        - 파일 타입 검증 (PDF, DOCX, XLSX, TXT, PNG, JPG)
        - 파일 크기 제한 (200MB)
        - Path Traversal 방지
        - Room ID 소유권 검증
    """
    # user_id 추출: 세션에서 또는 room_id에서
    if current_user:
        user_id = current_user["user_id"]
    else:
        # room_id 형식: {user_id}_{timestamp}
        if "_" in room_id:
            user_id = room_id.split("_")[0]
        else:
            user_id = "anonymous"
        logger.info(f"No session - extracted user_id from room_id: {user_id}")

    # 1. Room ID 검증 및 자동 생성
    is_valid = await validate_room_id(room_id, user_id, db)
    if not is_valid:
        # Room이 DB에 없으면 자동 생성 (첫 파일 업로드 시)
        logger.info(f"Creating new room - room_id: {room_id}, user_id: {user_id}")
        await db.execute(
            text("""
            INSERT INTO "USR_CNVS_SMRY" (
                "CNVS_IDT_ID", "USR_ID", "CNVS_SMRY_TXT",
                "USE_YN", "REG_DT"
            ) VALUES (
                :room_id, :user_id, :summary,
                'Y', CURRENT_TIMESTAMP
            )
            ON CONFLICT ("CNVS_IDT_ID") DO NOTHING
            """),
            {
                "room_id": room_id,
                "user_id": user_id,
                "summary": f"파일 업로드 대화방"
            }
        )
        await db.commit()
        logger.info(f"Room created successfully - room_id: {room_id}")

    # 2. 파일 타입 검증
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"허용되지 않은 파일 형식입니다: {file_ext}"
        )

    # 3. 파일 크기 확인
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="파일 크기가 200MB를 초과합니다."
        )

    # 4. MinIO 업로드
    try:
        object_name, uploaded_size = minio_service.upload_file(
            file.file,
            file.filename,
            file.content_type
        )
    except Exception as e:
        logger.error(f"MinIO upload error: {e}")
        raise HTTPException(
            status_code=500,
            detail="파일 업로드 실패"
        )

    # 5. DB에 메타데이터 저장 (USR_UPLD_DOC_MNG)
    file_uid = object_name  # "documents/uuid.pdf"
    file_download_url = minio_service.get_file_url(object_name)

    await db.execute(
        text("""
        INSERT INTO "USR_UPLD_DOC_MNG" (
            "CNVS_IDT_ID", "FILE_NM", "FILE_UID", "FILE_DOWN_URL",
            "FILE_SIZE", "FILE_TYP_CD", "USR_ID", "REG_DT"
        ) VALUES (
            :room_id, :filename, :file_uid, :file_url,
            :file_size, :file_type, :user_id, CURRENT_TIMESTAMP
        )
        """),
        {
            "room_id": room_id,
            "filename": file.filename,
            "file_uid": file_uid,
            "file_url": file_download_url,
            "file_size": uploaded_size,
            "file_type": file_ext[1:],  # ".pdf" -> "pdf"
            "user_id": user_id
        }
    )
    await db.commit()

    logger.info(f"File uploaded - room_id: {room_id}, file: {file.filename}, size: {uploaded_size}")

    # 벡터화 트리거 (백그라운드 작업)
    from app.services.text_extraction_service import text_extraction_service
    from app.services.vectorization_service import VectorizationService
    import asyncio

    async def vectorize_personal_file():
        """개인 파일 벡터화 (백그라운드) - session_collection-v2에 저장"""
        try:
            logger.info(f"Starting vectorization for {file_uid} in session_collection-v2")

            # 1. MinIO에서 파일 다운로드
            file_bytes = minio_service.get_file(object_name)
            if not file_bytes:
                logger.error(f"Failed to download file from MinIO: {object_name}")
                return

            # 2. 텍스트 추출
            from io import BytesIO
            file_obj = BytesIO(file_bytes)
            text = text_extraction_service.extract_text(file_obj, file.filename, file.content_type or 'application/octet-stream')

            if not text or len(text.strip()) < 10:
                logger.warning(f"No text extracted from {file.filename}")
                return

            logger.info(f"Extracted {len(text)} characters from {file.filename}")

            # 3. 벡터화 및 Qdrant 저장 (session_collection-v2 사용)
            metadata = {
                "filename": file.filename,
                "file_uid": file_uid,
                "session_id": room_id,  # ex-gpt-api expects "session_id" key
                "room_id": room_id,      # Keep for compatibility
                "user_id": user_id,
                "file_type": file_ext[1:],
                "file_size": uploaded_size,
                "upload_time": "now",
                "source": "personal_upload"  # ex-gpt-api uses "source" field
            }

            # Use session collection for personal files
            session_vectorization_service = VectorizationService(collection_name="session_collection-v2")

            # Use a temporary document_id (negative to avoid collision with admin docs)
            # Personal files don't go to doc_bas_lst table
            temp_doc_id = hash(file_uid) % 1000000  # Pseudo document ID

            await session_vectorization_service.vectorize_document(
                document_id=temp_doc_id,
                text=text,
                db=db,
                metadata=metadata
            )

            logger.info(f"✅ Vectorization completed for {file.filename} → session_collection-v2")

        except Exception as e:
            logger.error(f"Vectorization failed for {file_uid}: {e}", exc_info=True)

    # 백그라운드 실행 (응답 차단하지 않음)
    asyncio.create_task(vectorize_personal_file())

    return {
        "success": True,
        "file_uid": file_uid,
        "filename": file.filename,
        "size": uploaded_size,
        "download_url": file_download_url
    }
