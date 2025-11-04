"""
간단한 STT 업로드 및 처리 API
폴더 드래그 앤 드롭 방식에 최적화
"""
from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
import uuid
from datetime import datetime
from cerbos.sdk.model import Principal

from app.dependencies import get_principal

router = APIRouter(prefix="/api/v1/admin/stt", tags=["admin-stt-simple"])


@router.post("/upload-and-process")
async def upload_and_process_audio(
    file: UploadFile = File(..., description="음성 파일 (mp3, m4a)"),
    filename: str = Form(None, description="원본 파일명"),
    principal: Principal = Depends(get_principal)
):
    """
    음성 파일 업로드 및 즉시 STT 처리

    Architecture:
    1. 파일을 /tmp/stt-uploads/ 에 저장
    2. ex-GPT-STT의 transcribe_audio_api() 호출
    3. 전사 결과 반환

    Args:
        file: 업로드된 음성 파일
        filename: 원본 파일명 (선택)

    Returns:
        {
            "success": true,
            "filename": str,
            "transcription_text": str,
            "duration": float,
            "language": str,
            "segment_count": int
        }

    Security:
        - 파일 크기 제한: 100MB
        - 허용 확장자: mp3, m4a
        - Path Traversal 방지
    """
    # 1. 파일 검증
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일명이 없습니다")

    # 확장자 검증
    ext = file.filename.lower().split('.')[-1]
    if ext not in ['mp3', 'm4a', 'wav', 'flac']:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식: {ext}. 허용: mp3, m4a, wav, flac"
        )

    # 파일 크기 제한 (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"파일 크기 초과: {len(file_content) / (1024 * 1024):.1f}MB. 최대: 100MB"
        )

    # 2. 파일 저장
    upload_dir = Path("/tmp/stt-uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 고유한 파일명 생성 (UUID)
    unique_id = uuid.uuid4().hex[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_filename = f"{timestamp}_{unique_id}_{file.filename}"
    saved_path = upload_dir / saved_filename

    # Path Traversal 방지
    if not saved_path.resolve().is_relative_to(upload_dir.resolve()):
        raise HTTPException(status_code=400, detail="잘못된 파일 경로")

    # 파일 저장
    with open(saved_path, 'wb') as f:
        f.write(file_content)

    try:
        # 3. STT 처리 (ex-GPT-STT의 stt_api.py 사용)
        import sys
        sys.path.insert(0, '/home/aigen/ex-GPT-STT/src')

        from stt.stt_api import transcribe_audio_api

        # 진행 상황 로그
        def progress_callback(message):
            print(f"[STT Progress] {message}")

        # STT 실행
        result = transcribe_audio_api(str(saved_path), progress_callback=progress_callback)

        if not result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=f"STT 처리 실패: {result.get('error', 'Unknown error')}"
            )

        # 4. 결과 반환
        return {
            "success": True,
            "filename": filename or file.filename,
            "saved_path": str(saved_path),
            "transcription_text": result.get('transcription_text', ''),
            "duration": result.get('duration', 0),
            "language": result.get('language', 'unknown'),
            "segment_count": result.get('segment_count', 0),
            "diarization_success": result.get('diarization_success', False),
            "ai_analysis_success": result.get('ai_analysis_success', False),
            "minutes_text": result.get('minutes_text', ''),
        }

    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"STT 모듈을 로드할 수 없습니다: {str(e)}"
        )
    except Exception as e:
        # 오류 발생 시 업로드된 파일 삭제
        if saved_path.exists():
            saved_path.unlink()
        raise HTTPException(
            status_code=500,
            detail=f"STT 처리 중 오류 발생: {str(e)}"
        )


@router.post("/batch-upload-and-process")
async def batch_upload_and_process(
    files: list[UploadFile] = File(..., description="음성 파일들 (mp3, m4a)"),
    principal: Principal = Depends(get_principal)
):
    """
    여러 음성 파일을 한번에 업로드 및 STT 처리

    Args:
        files: 업로드된 음성 파일 리스트

    Returns:
        {
            "total": int,
            "success": int,
            "failed": int,
            "results": [...]
        }
    """
    results = []
    success_count = 0
    failed_count = 0

    for file in files:
        try:
            # 단일 파일 처리
            result = await upload_and_process_audio(file, file.filename, principal)
            results.append({
                "filename": file.filename,
                "success": True,
                "result": result
            })
            success_count += 1

        except HTTPException as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": e.detail
            })
            failed_count += 1

        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
            failed_count += 1

    return {
        "total": len(files),
        "success": success_count,
        "failed": failed_count,
        "results": results
    }
