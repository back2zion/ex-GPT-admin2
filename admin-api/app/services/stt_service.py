"""
STT 배치 처리 서비스
TDD 방식으로 구현: 테스트가 정의한 인터페이스 준수
"""
import re
from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.stt import STTBatch, STTTranscription
from app.services.email_service import EmailService


class STTService:
    """STT 배치 처리 서비스"""

    # 허용된 파일 경로 패턴 (Path Traversal 방지)
    ALLOWED_PATH_PATTERNS = [
        r"^s3://[\w\-_/\.]+$",  # S3 경로
        r"^minio://[\w\-_/\.]+$",  # MinIO 경로
        r"^/data/audio[\w\-_/\. ㄀-ㅣ가-힣()]*$",  # 로컬 허용 경로 (한글 포함)
        r"^/data/images[\w\-_/\. ㄀-ㅣ가-힣()]*$",  # 이미지 경로
        r"^/tmp/test-audio[\w\-_/\. ㄀-ㅣ가-힣()]*$",  # 테스트용 경로
    ]

    def validate_file_path(self, path: str) -> bool:
        """
        파일 경로 검증 (Path Traversal 공격 방지)

        Args:
            path: 검증할 파일 경로

        Returns:
            bool: 경로가 안전하면 True

        Raises:
            ValueError: 허용되지 않은 경로 패턴
        """
        # Path Traversal 시도 감지
        if ".." in path or path.startswith("../") or "/../" in path:
            raise ValueError(f"Invalid file path: '{path}' contains path traversal patterns")

        # 허용된 패턴 확인
        for pattern in self.ALLOWED_PATH_PATTERNS:
            if re.match(pattern, path):
                return True

        # 허용되지 않은 경로
        raise ValueError(
            f"Invalid file path: '{path}' does not match allowed patterns. "
            f"Allowed patterns: {', '.join(self.ALLOWED_PATH_PATTERNS)}"
        )

    async def create_batch(
        self,
        name: str,
        source_path: str,
        file_pattern: str,
        created_by: str,
        description: Optional[str] = None,
        priority: str = "normal",
        notify_emails: Optional[List[str]] = None,
        db: Optional[AsyncSession] = None
    ) -> STTBatch:
        """
        STT 배치 작업 생성

        Args:
            name: 배치 작업 이름
            source_path: 음성파일 경로
            file_pattern: 파일 패턴 (예: *.mp3)
            created_by: 생성자 user_id
            description: 배치 설명
            priority: 우선순위
            notify_emails: 알림 받을 이메일 목록
            db: 데이터베이스 세션

        Returns:
            STTBatch: 생성된 배치 객체

        Raises:
            ValueError: 잘못된 경로 또는 파라미터
        """
        # 경로 검증
        self.validate_file_path(source_path)

        # 이메일 검증
        if notify_emails:
            email_service = EmailService()
            for email in notify_emails:
                if not email_service.validate_email(email):
                    raise ValueError(f"Invalid email address: '{email}'")

        # 배치 생성
        batch = STTBatch(
            name=name,
            description=description,
            source_path=source_path,
            file_pattern=file_pattern,
            priority=priority,
            status="pending",
            created_by=created_by
        )

        # 데이터베이스 저장
        if db:
            db.add(batch)
            await db.commit()
            await db.refresh(batch)

        return batch

    async def get_batch_progress(
        self,
        batch_id: int,
        db: AsyncSession
    ) -> Dict:
        """
        배치 진행 상황 조회

        Args:
            batch_id: 배치 ID
            db: 데이터베이스 세션

        Returns:
            dict: 진행 상황 정보
        """
        # 배치 조회
        batch_result = await db.execute(
            select(STTBatch).where(STTBatch.id == batch_id)
        )
        batch = batch_result.scalar_one_or_none()

        if not batch:
            raise ValueError(f"Batch {batch_id} not found")

        # 완료된 전사 개수 계산
        completed_result = await db.execute(
            select(func.count())
            .select_from(STTTranscription)
            .where(
                STTTranscription.batch_id == batch_id,
                STTTranscription.status == "success"
            )
        )
        completed = completed_result.scalar() or 0

        # 실패한 전사 개수 계산
        failed_result = await db.execute(
            select(func.count())
            .select_from(STTTranscription)
            .where(
                STTTranscription.batch_id == batch_id,
                STTTranscription.status == "failed"
            )
        )
        failed = failed_result.scalar() or 0

        # 대기 중인 전사 개수
        pending = batch.total_files - completed - failed

        # 진행률 계산
        progress_percentage = 0.0
        if batch.total_files > 0:
            progress_percentage = (completed / batch.total_files) * 100.0

        return {
            "batch_id": batch_id,
            "status": batch.status,
            "total_files": batch.total_files,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "progress_percentage": progress_percentage,
            "avg_processing_time": None,  # TODO: Calculate from transcriptions
            "estimated_completion": None  # TODO: Calculate based on avg_processing_time
        }

    async def search_batches(
        self,
        name: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> list:
        """
        배치 검색 (SQL Injection 방지)

        Args:
            name: 배치 이름 검색어
            db: 데이터베이스 세션

        Returns:
            list: 검색된 배치 목록
        """
        if db is None:
            return []

        # Parameterized query로 SQL Injection 방지
        query = select(STTBatch)

        if name:
            # LIKE 검색 (Parameterized)
            query = query.where(STTBatch.name.ilike(f"%{name}%"))

        result = await db.execute(query)
        return list(result.scalars().all())

    async def process_audio_file(
        self,
        file_path: str,
        file_size: int,
        batch_id: int
    ) -> Dict:
        """
        오디오 파일 처리 (파일 크기 제한)

        Args:
            file_path: 오디오 파일 경로
            file_size: 파일 크기 (bytes)
            batch_id: 배치 ID

        Returns:
            dict: 처리 결과

        Raises:
            ValueError: 파일 크기 제한 초과 (DoS 방지)
        """
        # 파일 크기 제한: 1GB
        MAX_FILE_SIZE = 1 * 1024 * 1024 * 1024  # 1GB

        if file_size > MAX_FILE_SIZE:
            raise ValueError(
                f"File size exceeds limit: {file_size} bytes "
                f"(max: {MAX_FILE_SIZE} bytes)"
            )

        # 경로 검증
        self.validate_file_path(file_path)

        # TODO: 실제 STT 처리는 ex-GPT-STT 통합 후 구현
        return {
            "success": True,
            "file_path": file_path,
            "file_size": file_size,
            "batch_id": batch_id
        }
