"""
벡터 문서 업로드 API (Vector Document Upload)

기능:
- PDF, DOCX, TXT, HWP 등 문서 파일 업로드
- MinIO에 저장
- 카테고리 지정
- 메타데이터 저장 (EDB)
- 파일 타입 검증
- 파일 크기 제한 (최대 100MB)

Security:
- 파일 타입 검증
- 파일 크기 제한
- Path Traversal 방지
- 카테고리 존재 확인
"""
import os
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
import asyncpg
from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/vector-documents", tags=["admin-vector-document-upload"])

# 허용된 문서 파일 확장자
ALLOWED_EXTENSIONS = {
    '.pdf', '.txt', '.doc', '.docx', '.hwp',
    '.ppt', '.pptx', '.xls', '.xlsx',
    '.md', '.rtf', '.odt'
}

# 파일 크기 제한 (100MB)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# EDB 연결 설정
EDB_HOST = os.getenv("EDB_HOST", "host.docker.internal")
EDB_PORT = int(os.getenv("EDB_PORT", "5444"))
EDB_DATABASE = os.getenv("EDB_DATABASE", "AGENAI")
EDB_USER = os.getenv("EDB_USER", "wisenut_dev")
EDB_PASSWORD = os.getenv("EDB_PASSWORD", "express!12")

# MinIO 설정
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "host.docker.internal:10002")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "admin123")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "documents")


async def get_edb_connection():
    """EDB 데이터베이스 연결"""
    try:
        conn = await asyncpg.connect(
            host=EDB_HOST,
            port=EDB_PORT,
            database=EDB_DATABASE,
            user=EDB_USER,
            password=EDB_PASSWORD
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to EDB: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"데이터베이스 연결 실패: {str(e)}"
        )


def get_minio_client():
    """MinIO 클라이언트 생성"""
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        return client
    except Exception as e:
        logger.error(f"Failed to create MinIO client: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"MinIO 연결 실패: {str(e)}"
        )


def validate_filename(filename: str) -> bool:
    """파일명 검증"""
    # Path Traversal 방지
    if '..' in filename or '/' in filename or '\\' in filename:
        return False

    # 확장자 검증
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False

    return True


async def upload_to_minio(file: UploadFile, category_code: str, path_levels: Optional[List[str]] = None) -> str:
    """MinIO에 파일 업로드"""
    client = get_minio_client()

    # 버킷 존재 확인 및 생성
    if not client.bucket_exists(MINIO_BUCKET):
        client.make_bucket(MINIO_BUCKET)

    # 객체 경로 생성
    path_parts = [category_code]
    if path_levels:
        path_parts.extend(path_levels)
    path_parts.append(file.filename)
    object_name = "/".join(path_parts)

    # 파일 업로드
    file.file.seek(0)
    client.put_object(
        MINIO_BUCKET,
        object_name,
        file.file,
        length=-1,
        part_size=10*1024*1024,  # 10MB parts
        content_type=file.content_type
    )

    return f"{MINIO_BUCKET}/{object_name}"


async def save_document_metadata(
    conn: asyncpg.Connection,
    category_code: str,
    filename: str,
    file_size: int,
    minio_path: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    path_level1: Optional[str] = None,
    path_level2: Optional[str] = None,
    path_level3: Optional[str] = None
) -> int:
    """문서 메타데이터를 EDB에 저장"""
    # doc_id는 시퀀스로 자동 생성
    # doc_det_level_n1_cd는 NOT NULL이므로 기본값 설정
    doc_id = await conn.fetchval(
        """
        INSERT INTO wisenut.doc_bas_lst
        (doc_title_nm, doc_rep_title_nm, doc_cat_cd,
         doc_det_level_n1_cd, doc_det_level_n2_cd, doc_det_level_n3_cd,
         doc_txt, use_yn, reg_usr_id, reg_dt)
        VALUES ($1, $2, $3, $4, $5, $6, $7, 'Y', 'admin', CURRENT_TIMESTAMP)
        RETURNING doc_id
        """,
        title or filename,        # doc_title_nm
        title or filename,        # doc_rep_title_nm
        category_code,            # doc_cat_cd
        path_level1 or "기타",    # doc_det_level_n1_cd (기본값: "기타")
        path_level2 or "00",      # doc_det_level_n2_cd (기본값: "00")
        path_level3 or "00",      # doc_det_level_n3_cd (기본값: "00")
        description or ""         # doc_txt (임시로 description 저장)
    )

    return doc_id


@router.post("/upload", status_code=201)
async def upload_single_document(
    file: UploadFile = File(..., description="업로드할 문서 파일"),
    category_code: str = Form(..., description="카테고리 코드"),
    title: Optional[str] = Form(None, description="문서 제목"),
    description: Optional[str] = Form(None, description="문서 설명"),
    path_level1: Optional[str] = Form(None, description="경로 레벨 1"),
    path_level2: Optional[str] = Form(None, description="경로 레벨 2"),
    path_level3: Optional[str] = Form(None, description="경로 레벨 3")
):
    """
    단일 문서 파일 업로드

    Args:
        file: 업로드할 문서 파일
        category_code: 카테고리 코드
        title: 문서 제목 (선택)
        description: 문서 설명 (선택)
        path_level1: 경로 레벨 1 (선택)
        path_level2: 경로 레벨 2 (선택)
        path_level3: 경로 레벨 3 (선택)

    Returns:
        업로드된 문서 정보
    """
    conn = None
    try:
        # 파일명 검증
        if not validate_filename(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"파일 형식이 올바르지 않습니다: {file.filename}"
            )

        # 파일 크기 확인
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"파일 크기가 제한을 초과합니다: {file_size} bytes > 100MB"
            )

        # EDB 연결
        conn = await get_edb_connection()

        # 카테고리 존재 확인
        category_exists = await conn.fetchval(
            """
            SELECT COUNT(*) FROM wisenut.com_cd_lv2
            WHERE level_n1_cd = 'DOC_CAT_CD' AND level_n2_cd = $1
            """,
            category_code
        )

        if category_exists == 0:
            raise HTTPException(
                status_code=404,
                detail=f"카테고리를 찾을 수 없습니다: {category_code}"
            )

        # MinIO에 파일 업로드
        path_levels = [p for p in [path_level1, path_level2, path_level3] if p]
        minio_path = await upload_to_minio(file, category_code, path_levels)

        # EDB에 메타데이터 저장
        document_id = await save_document_metadata(
            conn,
            category_code,
            file.filename,
            file_size,
            minio_path,
            title,
            description,
            path_level1,
            path_level2,
            path_level3
        )

        logger.info(f"Uploaded document: {file.filename} (ID: {document_id})")

        return {
            "document_id": document_id,
            "filename": file.filename,
            "category_code": category_code,
            "title": title or file.filename,
            "size": file_size,
            "minio_path": minio_path,
            "path_level1": path_level1,
            "path_level2": path_level2,
            "path_level3": path_level3,
            "created_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"문서 업로드 실패: {str(e)}"
        )
    finally:
        if conn:
            await conn.close()


@router.post("/upload-batch", status_code=201)
async def upload_multiple_documents(
    files: List[UploadFile] = File(..., description="업로드할 문서 파일들"),
    category_code: str = Form(..., description="카테고리 코드")
):
    """
    다중 문서 파일 업로드

    Args:
        files: 업로드할 문서 파일들
        category_code: 카테고리 코드

    Returns:
        업로드 결과 (성공/실패 목록)
    """
    conn = None
    try:
        conn = await get_edb_connection()

        # 카테고리 존재 확인
        category_exists = await conn.fetchval(
            """
            SELECT COUNT(*) FROM wisenut.com_cd_lv2
            WHERE level_n1_cd = 'DOC_CAT_CD' AND level_n2_cd = $1
            """,
            category_code
        )

        if category_exists == 0:
            raise HTTPException(
                status_code=404,
                detail=f"카테고리를 찾을 수 없습니다: {category_code}"
            )

        uploaded_files = []
        failed_files = []

        for file in files:
            try:
                # 파일명 검증
                if not validate_filename(file.filename):
                    failed_files.append({
                        "filename": file.filename,
                        "reason": "Invalid filename or extension"
                    })
                    continue

                # 파일 크기 확인
                file.file.seek(0, 2)
                file_size = file.file.tell()
                file.file.seek(0)

                if file_size > MAX_FILE_SIZE:
                    failed_files.append({
                        "filename": file.filename,
                        "reason": f"File size exceeds limit: {file_size} bytes"
                    })
                    continue

                # MinIO에 업로드
                minio_path = await upload_to_minio(file, category_code)

                # EDB에 메타데이터 저장
                document_id = await save_document_metadata(
                    conn,
                    category_code,
                    file.filename,
                    file_size,
                    minio_path
                )

                uploaded_files.append({
                    "document_id": document_id,
                    "filename": file.filename,
                    "size": file_size,
                    "minio_path": minio_path
                })

            except Exception as e:
                failed_files.append({
                    "filename": file.filename,
                    "reason": str(e)
                })

        logger.info(f"Batch upload: {len(uploaded_files)} success, {len(failed_files)} failed")

        return {
            "uploaded_files": uploaded_files,
            "failed_files": failed_files,
            "total_count": len(uploaded_files),
            "failed_count": len(failed_files)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to batch upload documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"배치 업로드 실패: {str(e)}"
        )
    finally:
        if conn:
            await conn.close()
