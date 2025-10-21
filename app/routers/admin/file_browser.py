"""
파일 브라우저 API
서버 파일 시스템 탐색 기능 (보안 강화)

Security:
- Path Traversal 방지
- 허용된 루트 디렉토리만 탐색 가능
- 심볼릭 링크 차단
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel


router = APIRouter(prefix="/file-browser", tags=["File Browser"])


class DirectoryEntry(BaseModel):
    """디렉토리 항목"""
    name: str
    path: str
    is_directory: bool
    size: Optional[int] = None
    modified_time: Optional[float] = None


class DirectoryListResponse(BaseModel):
    """디렉토리 목록 응답"""
    current_path: str
    parent_path: Optional[str]
    entries: List[DirectoryEntry]


# 보안: 허용된 루트 디렉토리 (화이트리스트)
# Windows와 Linux 경로 모두 지원
ALLOWED_ROOT_DIRECTORIES = [
    "/data/audio",           # Linux 예시
    "/mnt/audio",            # Linux 마운트 포인트
    "C:\\AudioFiles",        # Windows 예시
    "D:\\Data\\Audio",       # Windows 예시
    "\\\\server\\audio",     # UNC 네트워크 공유
]


def validate_path(path: str) -> Path:
    """
    경로 검증 (Path Traversal 방지)

    Args:
        path: 검증할 경로

    Returns:
        Path: 검증된 경로 객체

    Raises:
        HTTPException: 유효하지 않은 경로

    Security:
        - Path Traversal 공격 차단 (../, ..\\ 등)
        - 허용된 루트 디렉토리만 접근 가능
        - 심볼릭 링크 차단
        - 절대 경로로 정규화
    """
    # 보안: Path Traversal 패턴 감지
    dangerous_patterns = ['../', '..\\', '%2e%2e', '....']
    for pattern in dangerous_patterns:
        if pattern in path.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Invalid path: Path traversal detected in '{path}'"
            )

    # 경로 객체 생성
    try:
        path_obj = Path(path).resolve()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid path format: {str(e)}"
        )

    # 보안: 심볼릭 링크 차단
    if path_obj.is_symlink():
        raise HTTPException(
            status_code=403,
            detail="Symbolic links are not allowed"
        )

    # 보안: 허용된 루트 디렉토리 중 하나의 하위 경로인지 확인
    is_allowed = False
    for allowed_root in ALLOWED_ROOT_DIRECTORIES:
        try:
            allowed_root_path = Path(allowed_root).resolve()
            # 경로가 허용된 루트 아래에 있는지 확인
            if path_obj == allowed_root_path or allowed_root_path in path_obj.parents:
                is_allowed = True
                break
        except Exception:
            continue

    if not is_allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: Path must be under one of the allowed directories: {ALLOWED_ROOT_DIRECTORIES}"
        )

    return path_obj


@router.get("/roots", response_model=List[Dict[str, str]])
async def get_root_directories():
    """
    허용된 루트 디렉토리 목록 조회

    Returns:
        List[Dict]: 루트 디렉토리 목록
    """
    roots = []
    for root in ALLOWED_ROOT_DIRECTORIES:
        try:
            root_path = Path(root)
            if root_path.exists():
                roots.append({
                    "path": str(root_path),
                    "name": root_path.name or str(root_path),
                    "exists": True
                })
            else:
                # 존재하지 않는 경로도 표시 (생성 가능)
                roots.append({
                    "path": str(root_path),
                    "name": root_path.name or str(root_path),
                    "exists": False
                })
        except Exception:
            continue

    return roots


@router.get("/list", response_model=DirectoryListResponse)
async def list_directory(
    path: str = Query(..., description="탐색할 디렉토리 경로")
):
    """
    디렉토리 내용 조회 (보안 검증 포함)

    Args:
        path: 탐색할 디렉토리 경로

    Returns:
        DirectoryListResponse: 디렉토리 내용

    Raises:
        HTTPException: 유효하지 않은 경로 또는 접근 거부

    Security:
        - Path Traversal 방지
        - 허용된 디렉토리만 접근
        - 심볼릭 링크 차단
    """
    # 보안: 경로 검증
    path_obj = validate_path(path)

    # 디렉토리 존재 확인
    if not path_obj.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Directory not found: {path}"
        )

    if not path_obj.is_dir():
        raise HTTPException(
            status_code=400,
            detail=f"Path is not a directory: {path}"
        )

    # 디렉토리 내용 읽기
    entries = []
    try:
        for entry in sorted(path_obj.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            try:
                # 심볼릭 링크 건너뛰기
                if entry.is_symlink():
                    continue

                # 숨김 파일 건너뛰기 (선택적)
                if entry.name.startswith('.'):
                    continue

                # 디렉토리와 음성 파일만 표시
                is_dir = entry.is_dir()
                is_audio = entry.suffix.lower() in ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.opus']

                if not (is_dir or is_audio):
                    continue

                # 파일 정보 수집
                stat = entry.stat()
                entries.append(DirectoryEntry(
                    name=entry.name,
                    path=str(entry),
                    is_directory=is_dir,
                    size=stat.st_size if not is_dir else None,
                    modified_time=stat.st_mtime
                ))
            except (PermissionError, OSError):
                # 접근 권한이 없는 항목은 건너뛰기
                continue
    except PermissionError:
        raise HTTPException(
            status_code=403,
            detail=f"Permission denied: Cannot read directory '{path}'"
        )

    # 부모 디렉토리 경로 계산
    parent_path = None
    if path_obj.parent != path_obj:
        # 부모가 허용된 루트 중 하나인지 확인
        try:
            validate_path(str(path_obj.parent))
            parent_path = str(path_obj.parent)
        except HTTPException:
            # 부모가 허용 범위를 벗어나면 None
            parent_path = None

    return DirectoryListResponse(
        current_path=str(path_obj),
        parent_path=parent_path,
        entries=entries
    )


@router.get("/validate")
async def validate_directory_path(
    path: str = Query(..., description="검증할 경로")
):
    """
    경로 유효성 검증 (실제 접근 없이 검증만)

    Args:
        path: 검증할 경로

    Returns:
        dict: 검증 결과
    """
    try:
        path_obj = validate_path(path)
        return {
            "valid": True,
            "path": str(path_obj),
            "exists": path_obj.exists(),
            "is_directory": path_obj.is_dir() if path_obj.exists() else None
        }
    except HTTPException as e:
        return {
            "valid": False,
            "error": e.detail
        }
