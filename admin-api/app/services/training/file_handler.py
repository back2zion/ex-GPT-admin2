"""
File Handler Service for Training Datasets
파일 업로드, 검증, 파싱을 담당하는 서비스

시큐어 코딩 적용:
- 파일 크기 제한
- 허용된 확장자만 허용
- 경로 조작 공격 방지
- 파일명 검증
- MIME 타입 검증

유지보수 용이성:
- 단일 책임 원칙 (SRP)
- 의존성 주입 (DI)
- 명확한 에러 메시지
"""
import os
import json
import re
import zipfile
from typing import Dict, Any, List, Optional
from io import BytesIO
from fastapi import UploadFile
from minio import Minio
import logging

logger = logging.getLogger(__name__)

# 시큐어 코딩: 상수 정의
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB (대용량 학습 데이터 지원)
MAX_FILENAME_LENGTH = 255
ALLOWED_EXTENSIONS = {".jsonl", ".json", ".parquet", ".csv", ".zip"}
# 한글, 일본어, 중국어 등 유니코드 문자 허용 (경로 조작 문자만 차단)
ALLOWED_FILENAME_PATTERN = re.compile(r'^[^\\/:\*\?"<>\|]+$')


class FileValidationError(Exception):
    """파일 검증 실패 예외"""
    pass


class FileSecurityError(Exception):
    """파일 보안 위협 감지 예외"""
    pass


class FileHandler:
    """
    파일 핸들러 서비스

    책임:
    - 파일 검증 (크기, 확장자, 이름)
    - 파일 파싱 (JSONL, JSON, Parquet, CSV)
    - 파일 업로드 (MinIO)
    - 통계 계산
    """

    def __init__(self, minio_client: Optional[Minio] = None):
        """
        생성자 (의존성 주입 for 유지보수 용이성)

        Args:
            minio_client: MinIO 클라이언트 (테스트 시 Mock 주입 가능)
        """
        self.minio_client = minio_client

    def validate_file_size(self, file: UploadFile) -> None:
        """
        파일 크기 검증 (시큐어 코딩: DoS 공격 방지)

        Args:
            file: 업로드 파일

        Raises:
            FileValidationError: 파일 크기가 제한을 초과한 경우
        """
        # Seek to end to get file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        if file_size > MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            limit_mb = MAX_FILE_SIZE / (1024 * 1024)
            raise FileValidationError(
                f"파일 크기가 너무 큽니다. "
                f"현재: {size_mb:.2f}MB, 제한: {limit_mb}MB"
            )

        logger.info(f"파일 크기 검증 통과: {file_size} bytes")

    def validate_file_extension(self, filename: str) -> None:
        """
        파일 확장자 검증 (시큐어 코딩)

        Args:
            filename: 파일명

        Raises:
            FileValidationError: 허용되지 않은 확장자
        """
        _, ext = os.path.splitext(filename.lower())

        if ext not in ALLOWED_EXTENSIONS:
            raise FileValidationError(
                f"허용되지 않은 파일 형식: {ext}. "
                f"허용되는 형식: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        logger.info(f"파일 확장자 검증 통과: {ext}")

    def validate_file_name(self, filename: str) -> None:
        """
        파일명 검증 (시큐어 코딩: 경로 조작 공격 방지)

        검증 항목:
        - 경로 조작 시도 (../, ..\\ 등)
        - 특수 문자 포함 여부
        - null byte 포함 여부
        - 빈 파일명
        - 너무 긴 파일명

        Args:
            filename: 파일명

        Raises:
            FileSecurityError: 보안 위협 감지
            FileValidationError: 유효하지 않은 파일명
        """
        # 빈 파일명 검사
        if not filename or not filename.strip():
            raise FileValidationError("파일명이 비어있습니다")

        # 길이 제한 (DoS 방지)
        if len(filename) > MAX_FILENAME_LENGTH:
            raise FileValidationError(
                f"파일명이 너무 깁니다. 최대 {MAX_FILENAME_LENGTH}자"
            )

        # 경로 조작 공격 탐지
        if ".." in filename or "/" in filename or "\\" in filename:
            logger.warning(f"경로 조작 시도 감지: {filename}")
            raise FileSecurityError(
                f"파일명에 경로 조작 시도가 감지되었습니다: {filename}"
            )

        # null byte 검사 (보안)
        if "\x00" in filename:
            logger.warning(f"Null byte 포함된 파일명 감지: {filename}")
            raise FileSecurityError(
                "파일명에 null byte가 포함되어 있습니다"
            )

        # 위험한 문자 검사 (경로 구분자, 와일드카드 등만 차단)
        if not ALLOWED_FILENAME_PATTERN.match(filename):
            logger.warning(f"위험한 문자가 포함된 파일명: {filename}")
            raise FileSecurityError(
                f"파일명에 위험한 문자가 포함되어 있습니다: {filename}. "
                f"경로 구분자(/, \\), 와일드카드(*, ?), 파이프(|), 콜론(:) 등은 사용할 수 없습니다."
            )

        logger.info(f"파일명 검증 통과: {filename}")

    async def parse_file(
        self,
        file: UploadFile,
        format: str
    ) -> Dict[str, Any]:
        """
        파일 파싱 (형식에 따라 다르게 처리)

        Args:
            file: 업로드 파일
            format: 파일 형식 (jsonl, json, parquet, csv)

        Returns:
            파싱 결과 (total_samples, format, samples 포함)

        Raises:
            FileValidationError: 파싱 실패
        """
        try:
            content = await file.read()
            await file.seek(0)  # Reset for later use

            if format == "jsonl":
                samples = self._parse_jsonl(content)
            elif format == "json":
                samples = self._parse_json(content)
            elif format == "zip":
                samples = self._parse_zip(content)
            elif format == "parquet":
                samples = self._parse_parquet(content)
            elif format == "csv":
                samples = self._parse_csv(content)
            else:
                raise FileValidationError(f"지원하지 않는 형식: {format}")

            return {
                "total_samples": len(samples),
                "format": format,
                "samples": samples
            }

        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e}")
            raise FileValidationError(f"파일 파싱 실패: {str(e)}")
        except Exception as e:
            logger.error(f"파일 파싱 실패: {e}")
            raise FileValidationError(f"파일 파싱 실패: {str(e)}")

    def _parse_jsonl(self, content: bytes) -> List[Dict[str, Any]]:
        """JSONL 파일 파싱"""
        samples = []
        lines = content.decode('utf-8').strip().split('\n')

        for i, line in enumerate(lines):
            if not line.strip():
                continue

            try:
                sample = json.loads(line)
                samples.append(sample)
            except json.JSONDecodeError as e:
                raise FileValidationError(
                    f"JSONL 파싱 실패 (라인 {i+1}): {str(e)}"
                )

        return samples

    def _parse_json(self, content: bytes) -> List[Dict[str, Any]]:
        """JSON 파일 파싱"""
        data = json.loads(content.decode('utf-8'))

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            raise FileValidationError(
                "JSON 형식이 올바르지 않습니다. 리스트 또는 딕셔너리여야 합니다."
            )

    def _parse_parquet(self, content: bytes) -> List[Dict[str, Any]]:
        """Parquet 파일 파싱 (TODO: 구현 필요)"""
        # TODO: pyarrow 사용하여 구현
        raise NotImplementedError("Parquet 파싱은 아직 구현되지 않았습니다")

    def _parse_csv(self, content: bytes) -> List[Dict[str, Any]]:
        """CSV 파일 파싱 (TODO: 구현 필요)"""
        # TODO: pandas 사용하여 구현
        raise NotImplementedError("CSV 파싱은 아직 구현되지 않았습니다")

    def _parse_zip(self, content: bytes) -> List[Dict[str, Any]]:
        """
        ZIP 파일 파싱 (여러 폴더 구조의 JSON 파일들 처리)

        ZIP 내부의 모든 .json 파일을 재귀적으로 수집하여 하나의 데이터셋으로 병합
        """
        samples = []

        try:
            with zipfile.ZipFile(BytesIO(content), 'r') as zip_ref:
                # ZIP 내부의 모든 파일 목록
                file_list = zip_ref.namelist()

                # .json 파일만 필터링 (숨김 파일, __MACOSX 등 제외)
                json_files = [
                    f for f in file_list
                    if f.endswith('.json')
                    and not f.startswith('__MACOSX')
                    and not os.path.basename(f).startswith('.')
                ]

                if not json_files:
                    raise FileValidationError(
                        "ZIP 파일 내에 .json 파일이 없습니다"
                    )

                logger.info(f"ZIP 파일에서 {len(json_files)}개의 JSON 파일 발견")

                # 각 JSON 파일 파싱
                for json_file in json_files:
                    try:
                        with zip_ref.open(json_file) as f:
                            file_content = f.read()
                            data = json.loads(file_content.decode('utf-8'))

                            # 리스트면 각 항목을, 딕셔너리면 그 자체를 추가
                            if isinstance(data, list):
                                samples.extend(data)
                            elif isinstance(data, dict):
                                samples.append(data)
                            else:
                                logger.warning(
                                    f"'{json_file}': 지원하지 않는 JSON 구조 (리스트 또는 딕셔너리여야 함)"
                                )

                    except json.JSONDecodeError as e:
                        logger.warning(f"'{json_file}' JSON 파싱 실패: {str(e)}")
                        # 개별 파일 실패는 경고만 하고 계속 진행
                        continue
                    except Exception as e:
                        logger.warning(f"'{json_file}' 처리 실패: {str(e)}")
                        continue

                if not samples:
                    raise FileValidationError(
                        "ZIP 파일 내 JSON 파일들에서 유효한 데이터를 찾을 수 없습니다"
                    )

                logger.info(f"ZIP 파일에서 총 {len(samples)}개의 샘플 수집 완료")
                return samples

        except zipfile.BadZipFile:
            raise FileValidationError("유효하지 않은 ZIP 파일입니다")
        except Exception as e:
            logger.error(f"ZIP 파일 파싱 실패: {e}")
            raise FileValidationError(f"ZIP 파일 처리 중 오류 발생: {str(e)}")

    def calculate_statistics(self, samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        데이터셋 통계 계산

        Args:
            samples: 데이터셋 샘플 리스트

        Returns:
            통계 정보 (count, avg_input_length, avg_output_length 등)
        """
        if not samples:
            return {
                "count": 0,
                "avg_input_length": 0,
                "avg_output_length": 0
            }

        total_input_len = 0
        total_output_len = 0
        count = 0

        for sample in samples:
            # 입력/출력 필드명은 다양할 수 있음
            input_fields = ["instruction", "input", "prompt", "question"]
            output_fields = ["output", "response", "answer", "completion"]

            input_text = ""
            output_text = ""

            for field in input_fields:
                if field in sample:
                    input_text = str(sample[field])
                    break

            for field in output_fields:
                if field in sample:
                    output_text = str(sample[field])
                    break

            total_input_len += len(input_text)
            total_output_len += len(output_text)
            count += 1

        return {
            "count": count,
            "avg_input_length": total_input_len / count if count > 0 else 0,
            "avg_output_length": total_output_len / count if count > 0 else 0
        }

    async def upload_file(
        self,
        file: UploadFile,
        object_name: str
    ) -> Dict[str, Any]:
        """
        MinIO에 파일 업로드 (의존성 주입된 클라이언트 사용)

        Args:
            file: 업로드할 파일
            object_name: MinIO 오브젝트 이름 (경로 포함)

        Returns:
            업로드 결과 (success, file_path 등)

        Raises:
            Exception: 업로드 실패
        """
        if not self.minio_client:
            raise ValueError("MinIO 클라이언트가 설정되지 않았습니다")

        try:
            # 파일 크기 계산
            content = await file.read()
            file_size = len(content)
            await file.seek(0)

            # 버킷 존재 확인 및 생성
            bucket_name = "datasets"
            if not self.minio_client.bucket_exists(bucket_name):
                logger.info(f"버킷이 없어 생성합니다: {bucket_name}")
                self.minio_client.make_bucket(bucket_name)

            # MinIO 업로드
            self.minio_client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=BytesIO(content),
                length=file_size,
                content_type=file.content_type
            )

            logger.info(f"파일 업로드 성공: {object_name}")

            return {
                "success": True,
                "file_path": f"datasets/{object_name}",
                "file_size": file_size
            }

        except Exception as e:
            logger.error(f"파일 업로드 실패: {e}")
            raise
