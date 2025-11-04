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
from datetime import timedelta
import hashlib


class MinIOService:
    """MinIO 파일 업로드 서비스"""

    def __init__(self):
        try:
            self.client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            self.bucket = settings.MINIO_BUCKET
            self._ensure_bucket()
        except Exception as e:
            print(f"MinIO initialization error: {e}")
            # Allow application to start even if MinIO is unavailable
            self.client = None
            self.bucket = settings.MINIO_BUCKET

    def _ensure_bucket(self):
        """버킷이 없으면 생성"""
        try:
            if self.client and not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except Exception as e:
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
        if not self.client:
            raise RuntimeError("MinIO service is not available")

        # Sanitize filename (Secure: Path Traversal Prevention)
        safe_filename = self._sanitize_filename(filename)

        # Generate unique path with UUID
        file_extension = os.path.splitext(safe_filename)[1]
        unique_id = str(uuid.uuid4())
        object_name = f"documents/{unique_id}{file_extension}"

        # Read file content to get size
        file_content = file_obj.read()
        file_size = len(file_content)

        # Security: File size limit (200MB)
        max_size = 200 * 1024 * 1024  # 200MB
        if file_size > max_size:
            raise ValueError(f"파일 크기가 제한을 초과했습니다 (최대 200MB)")

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
        if not self.client:
            raise RuntimeError("MinIO service is not available")

        try:
            url = self.client.presigned_get_object(
                self.bucket,
                object_name,
                expires=timedelta(seconds=expires_in)
            )
            return url
        except S3Error as e:
            raise ValueError(f"파일 URL 생성 실패: {e}")

    def get_file(self, object_name: str) -> bytes:
        """
        파일 다운로드 (bytes 반환)
        벡터화를 위한 파일 읽기에 사용
        """
        if not self.client:
            raise RuntimeError("MinIO service is not available")

        try:
            response = self.client.get_object(self.bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            print(f"MinIO get file error: {e}")
            return None
        except Exception as e:
            print(f"MinIO get file error: {e}")
            return None

    def delete_file(self, object_name: str):
        """파일 삭제"""
        if not self.client:
            print("MinIO service is not available, skip delete")
            return

        try:
            self.client.remove_object(self.bucket, object_name)
        except S3Error as e:
            print(f"MinIO delete error: {e}")


# Singleton instance
minio_service = MinIOService()
