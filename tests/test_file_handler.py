"""
File Handler Unit Tests (TDD)
파일 핸들러 단위 테스트

테스트 항목:
1. 한글 파일명 검증
2. 파일 크기 검증 (1GB 제한)
3. ZIP 파일 파싱 (여러 JSON 파일 병합)
4. 보안 검증 (경로 조작 공격 방지)
"""
import pytest
import io
import json
import zipfile
from unittest.mock import Mock, AsyncMock, patch
from fastapi import UploadFile

from app.services.training.file_handler import (
    FileHandler,
    FileValidationError,
    FileSecurityError,
    MAX_FILE_SIZE
)


class TestFileNameValidation:
    """파일명 검증 테스트"""

    def test_korean_filename_should_pass(self):
        """한글 파일명은 허용되어야 함"""
        handler = FileHandler()

        # 한글 파일명 검증
        handler.validate_file_name("2015가합13718.json")
        handler.validate_file_name("학습데이터_v1.jsonl")
        handler.validate_file_name("법률문서_2024.json")
        # 통과하면 예외 발생 안 함

    def test_path_traversal_attack_should_fail(self):
        """경로 조작 공격은 차단되어야 함"""
        handler = FileHandler()

        with pytest.raises(FileSecurityError):
            handler.validate_file_name("../../../etc/passwd")

        with pytest.raises(FileSecurityError):
            handler.validate_file_name("..\\..\\windows\\system32")

    def test_special_chars_in_filename_should_fail(self):
        """위험한 특수문자는 차단되어야 함"""
        handler = FileHandler()

        # 경로 구분자, 와일드카드 등
        with pytest.raises(FileSecurityError):
            handler.validate_file_name("file/name.json")

        with pytest.raises(FileSecurityError):
            handler.validate_file_name("file*name.json")

        with pytest.raises(FileSecurityError):
            handler.validate_file_name("file?name.json")

    def test_null_byte_in_filename_should_fail(self):
        """Null byte 포함 파일명은 차단되어야 함"""
        handler = FileHandler()

        with pytest.raises(FileSecurityError):
            handler.validate_file_name("file\x00name.json")


class TestFileSizeValidation:
    """파일 크기 검증 테스트"""

    def test_file_under_1gb_should_pass(self):
        """1GB 이하 파일은 통과해야 함"""
        handler = FileHandler()

        # 100MB 파일 시뮬레이션
        content = b"x" * (100 * 1024 * 1024)
        file = UploadFile(filename="test.json", file=io.BytesIO(content))

        handler.validate_file_size(file)
        # 통과하면 예외 발생 안 함

    def test_file_over_1gb_should_fail(self):
        """1GB 초과 파일은 차단되어야 함"""
        handler = FileHandler()

        # 1GB + 1MB 파일 시뮬레이션
        large_size = MAX_FILE_SIZE + (1024 * 1024)

        # Mock 파일 객체 생성
        large_file_buffer = io.BytesIO()
        # 실제 데이터를 쓰지 않고 포인터만 이동시켜 큰 파일 시뮬레이션
        large_file_buffer.write(b'\x00')  # Write 1 byte
        large_file_buffer.seek(large_size - 1)  # Seek to large position
        large_file_buffer.write(b'\x00')  # Write 1 byte at end
        large_file_buffer.seek(0)  # Reset to beginning

        upload_file = UploadFile(
            filename="large_file.json",
            file=large_file_buffer
        )

        with pytest.raises(FileValidationError, match="파일 크기가 너무 큽니다"):
            handler.validate_file_size(upload_file)


class TestFileExtensionValidation:
    """파일 확장자 검증 테스트"""

    def test_allowed_extensions_should_pass(self):
        """허용된 확장자는 통과해야 함"""
        handler = FileHandler()

        handler.validate_file_extension("data.jsonl")
        handler.validate_file_extension("data.json")
        handler.validate_file_extension("data.zip")
        handler.validate_file_extension("data.csv")
        handler.validate_file_extension("data.parquet")

    def test_disallowed_extensions_should_fail(self):
        """허용되지 않은 확장자는 차단되어야 함"""
        handler = FileHandler()

        with pytest.raises(FileValidationError):
            handler.validate_file_extension("malware.exe")

        with pytest.raises(FileValidationError):
            handler.validate_file_extension("script.sh")


class TestZIPFileParsing:
    """ZIP 파일 파싱 테스트"""

    @pytest.mark.asyncio
    async def test_zip_with_multiple_json_files_should_merge(self):
        """여러 JSON 파일이 포함된 ZIP은 하나로 병합되어야 함"""
        handler = FileHandler()

        # ZIP 파일 생성
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            # 3개의 JSON 파일 추가
            zf.writestr("folder1/file1.json", json.dumps({"id": 1, "text": "첫번째"}))
            zf.writestr("folder2/file2.json", json.dumps([{"id": 2, "text": "두번째"}, {"id": 3, "text": "세번째"}]))
            zf.writestr("file3.json", json.dumps({"id": 4, "text": "네번째"}))

        zip_content = zip_buffer.getvalue()

        # ZIP 파일 업로드 시뮬레이션
        upload_file = UploadFile(
            filename="test.zip",
            file=io.BytesIO(zip_content)
        )

        # 파싱 실행
        result = await handler.parse_file(upload_file, format="zip")

        # 검증
        assert result["total_samples"] == 4, "4개의 샘플이 병합되어야 함"
        assert result["format"] == "zip"
        assert len(result["samples"]) == 4

    @pytest.mark.asyncio
    async def test_zip_with_korean_filenames_should_work(self):
        """한글 파일명이 포함된 ZIP도 처리되어야 함"""
        handler = FileHandler()

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr("학습데이터/2015가합13718.json", json.dumps({"id": 1, "text": "법률문서"}))
            zf.writestr("판례/대법원판결.json", json.dumps({"id": 2, "text": "판례"}))

        zip_content = zip_buffer.getvalue()
        upload_file = UploadFile(filename="법률데이터.zip", file=io.BytesIO(zip_content))

        result = await handler.parse_file(upload_file, format="zip")

        assert result["total_samples"] == 2
        assert result["samples"][0]["text"] == "법률문서"

    @pytest.mark.asyncio
    async def test_zip_without_json_files_should_fail(self):
        """JSON 파일이 없는 ZIP은 실패해야 함"""
        handler = FileHandler()

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr("readme.txt", "This is a text file")
            zf.writestr("image.png", b"fake image data")

        zip_content = zip_buffer.getvalue()
        upload_file = UploadFile(filename="test.zip", file=io.BytesIO(zip_content))

        with pytest.raises(FileValidationError, match="ZIP 파일 내에 .json 파일이 없습니다"):
            await handler.parse_file(upload_file, format="zip")

    @pytest.mark.asyncio
    async def test_zip_with_macosx_folder_should_ignore(self):
        """__MACOSX 폴더는 무시되어야 함"""
        handler = FileHandler()

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr("data.json", json.dumps({"id": 1, "text": "valid"}))
            zf.writestr("__MACOSX/._data.json", "garbage")
            zf.writestr("__MACOSX/.DS_Store", "garbage")

        zip_content = zip_buffer.getvalue()
        upload_file = UploadFile(filename="test.zip", file=io.BytesIO(zip_content))

        result = await handler.parse_file(upload_file, format="zip")

        # __MACOSX 파일은 무시되고 1개만 파싱
        assert result["total_samples"] == 1

    @pytest.mark.asyncio
    async def test_zip_with_invalid_json_should_skip_and_continue(self):
        """잘못된 JSON 파일이 있어도 다른 파일은 계속 처리해야 함"""
        handler = FileHandler()

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr("valid1.json", json.dumps({"id": 1, "text": "valid"}))
            zf.writestr("invalid.json", "{invalid json")
            zf.writestr("valid2.json", json.dumps({"id": 2, "text": "also valid"}))

        zip_content = zip_buffer.getvalue()
        upload_file = UploadFile(filename="test.zip", file=io.BytesIO(zip_content))

        result = await handler.parse_file(upload_file, format="zip")

        # 유효한 2개만 파싱됨
        assert result["total_samples"] == 2


class TestJSONLParsing:
    """JSONL 파일 파싱 테스트"""

    @pytest.mark.asyncio
    async def test_valid_jsonl_should_parse(self):
        """유효한 JSONL 파일은 파싱되어야 함"""
        handler = FileHandler()

        jsonl_content = '\n'.join([
            json.dumps({"id": 1, "text": "first"}),
            json.dumps({"id": 2, "text": "second"}),
            json.dumps({"id": 3, "text": "third"})
        ])

        upload_file = UploadFile(
            filename="test.jsonl",
            file=io.BytesIO(jsonl_content.encode('utf-8'))
        )

        result = await handler.parse_file(upload_file, format="jsonl")

        assert result["total_samples"] == 3
        assert result["format"] == "jsonl"


class TestStatisticsCalculation:
    """통계 계산 테스트"""

    def test_statistics_with_valid_samples(self):
        """유효한 샘플의 통계는 정확해야 함"""
        handler = FileHandler()

        samples = [
            {"instruction": "질문1", "output": "답변1"},
            {"instruction": "질문22", "output": "답변22"},
            {"instruction": "질문333", "output": "답변333"},
        ]

        stats = handler.calculate_statistics(samples)

        assert stats["count"] == 3
        # 평균 길이 계산
        avg_input = (len("질문1") + len("질문22") + len("질문333")) / 3
        avg_output = (len("답변1") + len("답변22") + len("답변333")) / 3
        assert stats["avg_input_length"] == avg_input
        assert stats["avg_output_length"] == avg_output

    def test_statistics_with_empty_samples(self):
        """빈 샘플의 통계는 0이어야 함"""
        handler = FileHandler()

        stats = handler.calculate_statistics([])

        assert stats["count"] == 0
        assert stats["avg_input_length"] == 0
        assert stats["avg_output_length"] == 0


@pytest.mark.integration
class TestMinIOIntegration:
    """MinIO 통합 테스트"""

    @pytest.mark.asyncio
    async def test_upload_file_without_minio_client_should_fail(self):
        """MinIO 클라이언트 없이 업로드 시도하면 실패해야 함"""
        handler = FileHandler(minio_client=None)

        upload_file = UploadFile(
            filename="test.json",
            file=io.BytesIO(b"test content")
        )

        with pytest.raises(ValueError, match="MinIO 클라이언트가 설정되지 않았습니다"):
            await handler.upload_file(upload_file, "test/path.json")

    @pytest.mark.asyncio
    async def test_upload_file_with_minio_client_should_create_bucket_if_not_exists(self):
        """MinIO 버킷이 없으면 자동으로 생성해야 함"""
        # Mock MinIO client
        mock_minio = Mock()
        mock_minio.bucket_exists.return_value = False
        mock_minio.make_bucket.return_value = None
        mock_minio.put_object.return_value = None

        handler = FileHandler(minio_client=mock_minio)

        upload_file = UploadFile(
            filename="test.json",
            file=io.BytesIO(b"test content")
        )

        result = await handler.upload_file(upload_file, "test/path.json")

        # 버킷 존재 확인 호출됨
        mock_minio.bucket_exists.assert_called_once_with("datasets")
        # 버킷 생성 호출됨
        mock_minio.make_bucket.assert_called_once_with("datasets")
        # 파일 업로드 호출됨
        assert mock_minio.put_object.called
        assert result["success"] is True
