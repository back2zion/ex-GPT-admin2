"""
MinIO Service for Document Upload
학습데이터 관리 - MinIO 파일 업로드 서비스
"""
from minio import Minio
from minio.error import S3Error
from app.core.config import settings
import uuid
import os
from typing import BinaryIO, Tuple
import hashlib


class MinIOService:
    """MinIO 파일 업로드 서비스"""

    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket()

    def _ensure_bucket(self):
        """버킷이 없으면 생성"""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error as e:
            print(f"MinIO bucket check error: {e}")

    def upload_file(
        self,
        file_obj: BinaryIO,
        filename: str,
        content_type: str = "application/octet-stream"
    ) -> Tuple[str, int]:
        """
        파일 업로드
        Returns: (file_path, file_size)
        Secure: 파일명 sanitization, 크기 제한
        """
        # Sanitize filename (Secure: Path Traversal Prevention)
        safe_filename = self._sanitize_filename(filename)

        # Generate unique path with UUID
        file_extension = os.path.splitext(safe_filename)[1]
        unique_id = str(uuid.uuid4())
        object_name = f"documents/{unique_id}{file_extension}"

        # Read file content to get size
        file_content = file_obj.read()
        file_size = len(file_content)

        # Security: File size limit (100MB)
        max_size = 100 * 1024 * 1024  # 100MB
        if file_size > max_size:
            raise ValueError(f"파일 크기가 제한을 초과했습니다 (최대 100MB)")

        # Upload to MinIO
        from io import BytesIO
        self.client.put_object(
            self.bucket,
            object_name,
            BytesIO(file_content),
            length=file_size,
            content_type=content_type
        )

        return object_name, file_size

    def _sanitize_filename(self, filename: str) -> str:
        """
        파일명 정제 (Secure: Path Traversal Prevention)
        """
        # Remove path components
        filename = os.path.basename(filename)

        # Remove dangerous characters
        dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')

        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext

        return filename

    def get_file_url(self, object_name: str, expires_in: int = 3600) -> str:
        """
        파일 다운로드용 presigned URL 생성
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket,
                object_name,
                expires=expires_in
            )
            return url
        except S3Error as e:
            raise ValueError(f"파일 URL 생성 실패: {e}")

    def delete_file(self, object_name: str):
        """파일 삭제"""
        try:
            self.client.remove_object(self.bucket, object_name)
        except S3Error as e:
            print(f"MinIO delete error: {e}")


# Singleton instance
minio_service = MinIOService()
