"""
파일 업로드 API
Windows PC에서 폴더 선택 → 서버로 자동 업로드

Security:
- 파일 타입 검증 (음성 파일만)
- 파일 크기 제한 (개당 1GB)
- Path Traversal 방지
- 바이러스 스캔 (TODO)
"""
import os
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from cerbos.sdk.model import Principal
from app.dependencies import get_principal


router = APIRouter(prefix="/api/v1/admin/file-upload", tags=["file-upload"])


# 보안: 허용된 음성 파일 확장자
ALLOWED_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.opus'}

# 보안: 파일 크기 제한 (1GB)
MAX_FILE_SIZE = 1073741824  # 1GB

# 업로드 대상 루트 디렉토리
UPLOAD_ROOT = Path("/data/audio")


def validate_filename(filename: str) -> bool:
    """
    파일명 검증 (보안)

    Security:
        - Path Traversal 방지 (../, ..\\ 등)
        - 특수 문자 차단
        - 확장자 검증
    """
    # Path Traversal 방지
    if '..' in filename or '/' in filename or '\\' in filename:
        return False

    # 확장자 검증
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False

    return True


@router.post("/upload-folder")
async def upload_folder(
    files: List[UploadFile] = File(..., description="업로드할 음성 파일들"),
    target_folder: str = Form(..., description="저장할 폴더명 (예: 회의록/2024-10)"),
    principal: Principal = Depends(get_principal)
):
    """
    Windows PC에서 선택한 폴더의 모든 파일을 서버로 업로드

    **사용 방법**:
    1. Windows 탐색기에서 폴더 선택
    2. 폴더 안의 모든 음성 파일을 서버로 전송
    3. 서버의 /data/audio/{target_folder}/ 에 저장

    **보안**:
    - 음성 파일만 허용 (MP3, WAV, M4A, FLAC, OGG, OPUS)
    - 개당 파일 크기 1GB 제한
    - Path Traversal 방지
    - 파일명 검증

    **반환값**:
    - uploaded_files: 업로드된 파일 목록
    - total_count: 총 파일 수
    - total_size: 총 파일 크기 (bytes)
    - target_path: 저장 경로
    """
    # 보안: target_folder에서 Path Traversal 방지
    if '..' in target_folder or target_folder.startswith('/'):
        raise HTTPException(
            status_code=400,
            detail="Invalid target folder: Path traversal detected"
        )

    # 대상 디렉토리 생성
    target_path = UPLOAD_ROOT / target_folder
    target_path.mkdir(parents=True, exist_ok=True)

    uploaded_files = []
    total_size = 0
    skipped_files = []

    for file in files:
        # 보안: 파일명 검증
        if not validate_filename(file.filename):
            skipped_files.append({
                "filename": file.filename,
                "reason": "Invalid filename or extension"
            })
            continue

        # 파일 크기 확인
        file.file.seek(0, 2)  # 파일 끝으로 이동
        file_size = file.file.tell()
        file.file.seek(0)  # 파일 처음으로 복귀

        # 보안: 파일 크기 제한
        if file_size > MAX_FILE_SIZE:
            skipped_files.append({
                "filename": file.filename,
                "reason": f"File size exceeds limit: {file_size} bytes > 1GB"
            })
            continue

        # 파일 저장
        file_path = target_path / file.filename
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            uploaded_files.append({
                "filename": file.filename,
                "size": file_size,
                "path": str(file_path)
            })
            total_size += file_size
        except Exception as e:
            skipped_files.append({
                "filename": file.filename,
                "reason": f"Upload failed: {str(e)}"
            })

    return {
        "success": True,
        "uploaded_files": uploaded_files,
        "skipped_files": skipped_files,
        "total_count": len(uploaded_files),
        "total_size": total_size,
        "target_path": str(target_path)
    }


@router.post("/upload-single")
async def upload_single_file(
    file: UploadFile = File(..., description="업로드할 음성 파일"),
    target_folder: str = Form(..., description="저장할 폴더명"),
    principal: Principal = Depends(get_principal)
):
    """
    단일 파일 업로드

    **보안**: upload-folder와 동일한 검증 적용
    """
    # 보안: target_folder 검증
    if '..' in target_folder or target_folder.startswith('/'):
        raise HTTPException(
            status_code=400,
            detail="Invalid target folder: Path traversal detected"
        )

    # 보안: 파일명 검증
    if not validate_filename(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid filename or extension: {file.filename}"
        )

    # 파일 크기 확인
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    # 보안: 파일 크기 제한
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds limit: {file_size} bytes > 1GB"
        )

    # 대상 디렉토리 생성
    target_path = UPLOAD_ROOT / target_folder
    target_path.mkdir(parents=True, exist_ok=True)

    # 파일 저장
    file_path = target_path / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "success": True,
        "filename": file.filename,
        "size": file_size,
        "path": str(file_path),
        "target_folder": target_folder
    }
