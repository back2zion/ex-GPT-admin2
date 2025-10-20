"""
Storage Service (MinIO Integration)
저장소 서비스 - MinIO 연동
"""
from minio import Minio
from minio.error import S3Error
from typing import List, Optional
import io
import logging

logger = logging.getLogger(__name__)


class StorageService:
    """MinIO 저장소 서비스"""

    def __init__(
        self,
        endpoint: str = "localhost:9000",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
        secure: bool = False
    ):
        """
        초기화

        Args:
            endpoint: MinIO 엔드포인트
            access_key: 액세스 키
            secret_key: 시크릿 키
            secure: HTTPS 사용 여부
        """
        try:
            self.client = Minio(
                endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure
            )
            logger.info(f"MinIO client initialized: {endpoint}")
        except Exception as e:
            logger.warning(f"Failed to initialize MinIO client: {e}")
            self.client = None

    def health_check(self) -> bool:
        """
        MinIO 서버 연결 확인

        Returns:
            bool: 연결 성공 시 True
        """
        if not self.client:
            return False

        try:
            # 버킷 목록 조회로 연결 확인
            list(self.client.list_buckets())
            return True
        except Exception as e:
            logger.error(f"MinIO health check failed: {e}")
            return False

    def list_buckets(self) -> List[str]:
        """
        버킷 목록 조회

        Returns:
            List[str]: 버킷 이름 리스트
        """
        if not self.client:
            return []

        try:
            buckets = self.client.list_buckets()
            return [bucket.name for bucket in buckets]
        except Exception as e:
            logger.error(f"Failed to list buckets: {e}")
            return []

    def get_object(
        self,
        bucket_name: str,
        object_name: str
    ) -> Optional[bytes]:
        """
        객체(파일) 다운로드

        Args:
            bucket_name: 버킷 이름
            object_name: 객체 이름

        Returns:
            Optional[bytes]: 파일 데이터
        """
        if not self.client:
            return None

        try:
            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"Failed to get object: {e}")
            return None

    def put_object(
        self,
        bucket_name: str,
        object_name: str,
        data: io.BytesIO,
        length: int,
        content_type: str = "application/octet-stream"
    ) -> Optional[str]:
        """
        객체(파일) 업로드

        Args:
            bucket_name: 버킷 이름
            object_name: 객체 이름
            data: 파일 데이터 스트림
            length: 데이터 길이
            content_type: 콘텐츠 타입

        Returns:
            Optional[str]: 업로드된 객체의 ETag
        """
        if not self.client:
            return None

        try:
            # 버킷이 없으면 생성
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)

            result = self.client.put_object(
                bucket_name,
                object_name,
                data,
                length,
                content_type=content_type
            )
            return result.etag
        except S3Error as e:
            logger.error(f"Failed to put object: {e}")
            return None
