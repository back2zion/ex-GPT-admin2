"""
Files API Router
채팅 파일 업로드 API
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.services.minio_service import minio_service
from app.utils.auth import get_current_user_from_session
from app.services.chat_service import validate_room_id
from pathlib import Path
import logging

router = APIRouter(prefix="/api/v1/files", tags=["chat-files"])
logger = logging.getLogger(__name__)

# 허용된 파일 확장자
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.xlsx', '.txt', '.png', '.jpg', '.jpeg'}

# 파일 크기 제한 (100MB)
MAX_FILE_SIZE = 100 * 1024 * 1024


@router.post("/upload")
async def upload_chat_file(
    file: UploadFile = File(...),
    room_id: str = Form(...),
    current_user: dict = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db)
):
    """
    채팅 파일 업로드 (MinIO + DB)

    Args:
        file: 업로드할 파일
        room_id: 대화방 ID
        current_user: 인증된 사용자
        db: 데이터베이스 세션

    Returns:
        dict: 업로드 결과

    Security:
        - 파일 타입 검증 (PDF, DOCX, XLSX, TXT, PNG, JPG)
        - 파일 크기 제한 (100MB)
        - Path Traversal 방지
        - Room ID 소유권 검증
    """
    user_id = current_user["user_id"]

    # 1. 권한 검증: room_id가 사용자 소유인지 확인
    is_valid = await validate_room_id(room_id, user_id, db)
    if not is_valid:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

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
            detail="파일 크기가 100MB를 초과합니다."
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

    # TODO: 벡터화 트리거 (백그라운드 작업)
    # from app.tasks.vectorization import trigger_vectorization
    # await trigger_vectorization(file_uid, room_id)

    return {
        "success": True,
        "file_uid": file_uid,
        "filename": file.filename,
        "size": uploaded_size,
        "download_url": file_download_url
    }
