"""
STT 서비스 레이어
시큐어 코딩: Path Traversal 방지, SQL Injection 방지, 입력 검증
"""
import os
import re
import glob
from typing import Optional, List, Dict, Any
from pathlib import Path
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.stt import STTBatch, STTTranscription, STTSummary, STTEmailLog


class STTService:
    """STT 배치 처리 서비스"""

    # 보안: 허용된 파일 경로 패턴 (화이트리스트)
    # Windows와 Linux 경로 모두 지원, 한글 파일명도 지원
    ALLOWED_PATH_PATTERNS = [
        r'^s3://[\w\-_/\.]+$',                                    # S3 경로
        r'^minio://[\w\-_/\.]+$',                                 # MinIO 경로
        r'^/[\w\-_/\. ㄀-ㅣ가-힣]+$',                              # Linux 절대 경로 (한글 지원)
        r'^[A-Za-z]:[/\\][\w\-_/\\. ㄀-ㅣ가-힣()]+$',            # Windows 로컬 경로 (C:\, D:\ 등, 한글 지원)
        r'^\\\\[\w\-_.]+\\[\w\-_/\\. ㄀-ㅣ가-힣()]+$',           # UNC 네트워크 경로 (\\server\share\, 한글 지원)
    ]

    # 보안: 허용된 파일 확장자 (화이트리스트)
    ALLOWED_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.opus']

    # 보안: 파일 크기 제한 (1GB)
    MAX_FILE_SIZE = 1073741824  # 1GB in bytes

    def __init__(self):
        pass

    def validate_file_path(self, file_path: str) -> bool:
        """
        파일 경로 검증 (Path Traversal 방지)

        Args:
            file_path: 검증할 파일 경로

        Returns:
            bool: 유효한 경로면 True

        Raises:
            ValueError: 유효하지 않은 경로

        Security:
            - Path Traversal 공격 방지 (../, ..\\ 등)
            - 허용된 경로 패턴만 허용 (화이트리스트)
            - 절대 경로 변환 후 검증
        """
        # 보안: Path Traversal 패턴 감지
        dangerous_patterns = ['../', '..\\', '%2e%2e', '....', '\\..\\']
        for pattern in dangerous_patterns:
            if pattern in file_path.lower():
                raise ValueError(f"Invalid file path: Path traversal detected in '{file_path}'")

        # 보안: 허용된 패턴 중 하나와 매칭되는지 확인
        is_valid = False
        for pattern in self.ALLOWED_PATH_PATTERNS:
            if re.match(pattern, file_path):
                is_valid = True
                break

        if not is_valid:
            raise ValueError(
                f"Invalid file path: '{file_path}' does not match allowed patterns. "
                f"Allowed patterns: {', '.join(self.ALLOWED_PATH_PATTERNS)}"
            )

        return True

    def validate_file_extension(self, file_path: str) -> bool:
        """
        파일 확장자 검증 (화이트리스트)

        Args:
            file_path: 검증할 파일 경로

        Returns:
            bool: 유효한 확장자면 True

        Raises:
            ValueError: 유효하지 않은 확장자
        """
        ext = Path(file_path).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Invalid file extension: '{ext}'. "
                f"Allowed extensions: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )
        return True

    def validate_file_size(self, file_size: int) -> bool:
        """
        파일 크기 검증 (DoS 방지)

        Args:
            file_size: 파일 크기 (bytes)

        Returns:
            bool: 유효한 크기면 True

        Raises:
            ValueError: 파일 크기가 제한을 초과
        """
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(
                f"File size exceeds limit: {file_size} bytes > {self.MAX_FILE_SIZE} bytes (1GB)"
            )
        return True

    def count_audio_files(self, source_path: str, file_pattern: str = "*.mp3") -> int:
        """
        경로에서 음성 파일 개수 세기

        Args:
            source_path: 스캔할 경로
            file_pattern: 파일 패턴 (예: *.mp3, *.wav)

        Returns:
            int: 매칭되는 파일 개수

        Security:
            - 경로 검증 완료된 후 호출해야 함
            - 디렉토리만 스캔 (심볼릭 링크 제외)
        """
        # S3, MinIO 경로는 실제 스캔 불가 (0 반환)
        if source_path.startswith(('s3://', 'minio://')):
            # TODO: S3/MinIO SDK를 사용한 파일 리스팅 구현
            return 0

        # 로컬 파일 시스템 경로
        path_obj = Path(source_path)

        # 경로 존재 확인
        if not path_obj.exists():
            return 0

        if not path_obj.is_dir():
            return 0

        # glob 패턴으로 파일 검색 (재귀적)
        try:
            # **를 사용하여 모든 하위 디렉토리 재귀 검색
            pattern = str(path_obj / "**" / file_pattern)
            files = glob.glob(pattern, recursive=True)

            # 실제 파일만 카운트 (디렉토리, 심볼릭 링크 제외)
            count = 0
            for file_path in files:
                file_obj = Path(file_path)
                if file_obj.is_file() and not file_obj.is_symlink():
                    # 허용된 확장자인지 확인
                    if file_obj.suffix.lower() in self.ALLOWED_EXTENSIONS:
                        count += 1

            return count
        except (PermissionError, OSError) as e:
            # 권한 없거나 I/O 에러 시 0 반환
            return 0

    async def create_batch(
        self,
        name: str,
        source_path: str,
        file_pattern: str = "*.mp3",
        description: Optional[str] = None,
        priority: str = "normal",
        created_by: str = "admin",
        notify_emails: Optional[List[str]] = None,
        db: AsyncSession = None
    ) -> STTBatch:
        """
        배치 작업 생성 (보안 검증 포함)

        Args:
            name: 배치 작업 이름
            source_path: 음성파일 경로
            file_pattern: 파일 패턴
            description: 설명
            priority: 우선순위
            created_by: 생성자
            notify_emails: 알림 이메일 목록
            db: 데이터베이스 세션

        Returns:
            STTBatch: 생성된 배치 객체

        Raises:
            ValueError: 유효하지 않은 입력

        Security:
            - 파일 경로 검증 (Path Traversal 방지)
            - 이메일 검증 (Email Injection 방지)
            - SQL Injection 방지 (SQLAlchemy Parameterized Query)
        """
        # 보안: 파일 경로 검증
        self.validate_file_path(source_path)

        # 보안: 이메일 주소 검증 (있는 경우)
        if notify_emails:
            from app.services.email_service import EmailService
            email_service = EmailService()
            for email in notify_emails:
                if not email_service.validate_email(email):
                    raise ValueError(f"Invalid email address: '{email}'")

        # 파일 개수 스캔 (보안 검증 완료 후)
        total_files = self.count_audio_files(source_path, file_pattern)

        # 배치 객체 생성
        batch = STTBatch(
            name=name,
            description=description,
            source_path=source_path,
            file_pattern=file_pattern,
            total_files=total_files,
            priority=priority,
            status="pending",
            created_by=created_by,
            notify_emails=notify_emails
        )

        # 데이터베이스에 저장 (SQL Injection 방지: SQLAlchemy 사용)
        if db:
            db.add(batch)
            await db.commit()
            await db.refresh(batch)

        return batch

    async def get_batch_progress(
        self,
        batch_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        배치 진행 상황 조회

        Args:
            batch_id: 배치 ID
            db: 데이터베이스 세션

        Returns:
            dict: 진행 상황 정보

        Security:
            - SQL Injection 방지 (Parameterized Query)
        """
        # 배치 정보 조회 (Parameterized Query)
        result = await db.execute(
            select(STTBatch).where(STTBatch.id == batch_id)
        )
        batch = result.scalar_one_or_none()

        if not batch:
            raise ValueError(f"Batch not found: {batch_id}")

        # 전사 상태별 개수 조회 (Parameterized Query)
        completed_result = await db.execute(
            select(func.count(STTTranscription.id)).where(
                STTTranscription.batch_id == batch_id,
                STTTranscription.status == "success"
            )
        )
        completed_count = completed_result.scalar() or 0

        failed_result = await db.execute(
            select(func.count(STTTranscription.id)).where(
                STTTranscription.batch_id == batch_id,
                STTTranscription.status == "failed"
            )
        )
        failed_count = failed_result.scalar() or 0

        # 진행 상황 반환
        return {
            "batch_id": batch.id,
            "status": batch.status,
            "total_files": batch.total_files,
            "completed": completed_count,
            "failed": failed_count,
            "pending": batch.total_files - completed_count - failed_count,
            "progress_percentage": batch.progress_percentage,
            "avg_processing_time": batch.avg_processing_time,
            "estimated_completion": None  # TODO: 예상 완료 시간 계산
        }

    async def search_batches(
        self,
        name: Optional[str] = None,
        status: Optional[str] = None,
        db: AsyncSession = None
    ) -> List[STTBatch]:
        """
        배치 검색 (SQL Injection 방지)

        Args:
            name: 검색할 이름 (부분 일치)
            status: 필터링할 상태
            db: 데이터베이스 세션

        Returns:
            List[STTBatch]: 검색 결과

        Security:
            - SQL Injection 방지 (Parameterized Query)
            - 입력 값 검증 (화이트리스트)
        """
        query = select(STTBatch)

        # 보안: Parameterized Query 사용 (SQL Injection 방지)
        if name:
            query = query.where(STTBatch.name.contains(name))

        # 보안: status 값 검증 (화이트리스트)
        valid_statuses = ["pending", "processing", "completed", "failed", "paused"]
        if status:
            if status not in valid_statuses:
                raise ValueError(f"Invalid status: '{status}'. Allowed: {valid_statuses}")
            query = query.where(STTBatch.status == status)

        if db:
            result = await db.execute(query)
            return result.scalars().all()

        return []

    async def process_audio_file(
        self,
        file_path: str,
        file_size: int,
        batch_id: int,
        db: AsyncSession = None
    ) -> STTTranscription:
        """
        음성파일 처리 (검증 포함)

        Args:
            file_path: 음성파일 경로
            file_size: 파일 크기 (bytes)
            batch_id: 배치 ID
            db: 데이터베이스 세션

        Returns:
            STTTranscription: 전사 결과

        Raises:
            ValueError: 유효하지 않은 입력

        Security:
            - 파일 경로 검증
            - 파일 확장자 검증
            - 파일 크기 제한
        """
        # 보안: 파일 경로 검증
        self.validate_file_path(file_path)

        # 보안: 파일 확장자 검증
        self.validate_file_extension(file_path)

        # 보안: 파일 크기 검증 (DoS 방지)
        self.validate_file_size(file_size)

        # TODO: 실제 STT 처리 로직 구현 (Whisper, Google STT 등)
        # 현재는 테스트용 더미 객체 반환
        transcription = STTTranscription(
            batch_id=batch_id,
            audio_file_path=file_path,
            audio_file_size=file_size,
            transcription_text="[Placeholder] 전사 결과",
            status="pending"
        )

        if db:
            db.add(transcription)
            await db.commit()
            await db.refresh(transcription)

        return transcription
