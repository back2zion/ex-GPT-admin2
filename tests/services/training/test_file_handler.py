"""
Test cases for file handler service
TDD: Red-Green-Refactor 방식으로 작성

시큐어 코딩 테스트:
- 파일 크기 제한
- 허용된 확장자 검증
- 경로 조작 공격 방지
- MIME 타입 검증
"""
import pytest
from io import BytesIO
from fastapi import UploadFile
from app.services.training.file_handler import (
    FileHandler,
    FileValidationError,
    FileSecurityError,
    MAX_FILE_SIZE,
    ALLOWED_EXTENSIONS
)


class TestFileValidation:
    """파일 검증 테스트 (시큐어 코딩)"""

    @pytest.fixture
    def file_handler(self):
        """FileHandler 인스턴스 생성"""
        return FileHandler()

    def test_validate_file_size_within_limit(self, file_handler):
        """정상: 허용된 크기 이내의 파일"""
        # 10MB 파일 (허용)
        file_content = b"x" * (10 * 1024 * 1024)
        file = UploadFile(
            filename="test.jsonl",
            file=BytesIO(file_content)
        )

        # Should not raise exception
        file_handler.validate_file_size(file)

    def test_validate_file_size_exceeds_limit(self, file_handler):
        """실패: 허용 크기 초과 파일 (시큐어 코딩)"""
        # 200MB 파일 (거부)
        file_content = b"x" * (200 * 1024 * 1024)
        file = UploadFile(
            filename="test.jsonl",
            file=BytesIO(file_content)
        )

        with pytest.raises(FileValidationError) as exc_info:
            file_handler.validate_file_size(file)

        assert "파일 크기가 너무 큽니다" in str(exc_info.value)

    def test_validate_allowed_extension_jsonl(self, file_handler):
        """정상: 허용된 확장자 (.jsonl)"""
        file_handler.validate_file_extension("test_dataset.jsonl")

    def test_validate_allowed_extension_json(self, file_handler):
        """정상: 허용된 확장자 (.json)"""
        file_handler.validate_file_extension("data.json")

    def test_validate_allowed_extension_parquet(self, file_handler):
        """정상: 허용된 확장자 (.parquet)"""
        file_handler.validate_file_extension("dataset.parquet")

    def test_validate_disallowed_extension(self, file_handler):
        """실패: 허용되지 않은 확장자 (시큐어 코딩)"""
        with pytest.raises(FileValidationError) as exc_info:
            file_handler.validate_file_extension("malicious.exe")

        assert "허용되지 않은 파일 형식" in str(exc_info.value)

    def test_prevent_path_traversal_attack(self, file_handler):
        """실패: 경로 조작 공격 방지 (시큐어 코딩)"""
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config",
            "../../sensitive_data.txt",
            "test/../../../etc/shadow"
        ]

        for filename in malicious_filenames:
            with pytest.raises(FileSecurityError) as exc_info:
                file_handler.validate_file_name(filename)

            assert "경로 조작" in str(exc_info.value)

    def test_prevent_special_characters_in_filename(self, file_handler):
        """실패: 특수문자 포함 파일명 거부 (시큐어 코딩)"""
        invalid_filenames = [
            "test<script>.jsonl",
            "data|pipe.json",
            "file;semicolon.parquet",
            "test&command.csv"
        ]

        for filename in invalid_filenames:
            with pytest.raises(FileValidationError) as exc_info:
                file_handler.validate_file_name(filename)

            assert "허용되지 않은 문자" in str(exc_info.value)

    def test_validate_safe_filename(self, file_handler):
        """정상: 안전한 파일명"""
        safe_filenames = [
            "test_dataset_v1.jsonl",
            "data-2024-10-30.json",
            "legal_qa_korean.parquet",
            "training_data_001.csv"
        ]

        for filename in safe_filenames:
            # Should not raise exception
            file_handler.validate_file_name(filename)


class TestFileProcessing:
    """파일 처리 테스트"""

    @pytest.fixture
    def file_handler(self):
        return FileHandler()

    @pytest.mark.asyncio
    async def test_parse_jsonl_file(self, file_handler):
        """정상: JSONL 파일 파싱"""
        content = b'{"instruction": "test", "output": "result"}\n{"instruction": "test2", "output": "result2"}\n'
        file = UploadFile(
            filename="test.jsonl",
            file=BytesIO(content)
        )

        result = await file_handler.parse_file(file, "jsonl")

        assert result["total_samples"] == 2
        assert result["format"] == "jsonl"
        assert "samples" in result

    @pytest.mark.asyncio
    async def test_parse_json_file(self, file_handler):
        """정상: JSON 파일 파싱"""
        content = b'[{"input": "q1", "output": "a1"}, {"input": "q2", "output": "a2"}]'
        file = UploadFile(
            filename="test.json",
            file=BytesIO(content)
        )

        result = await file_handler.parse_file(file, "json")

        assert result["total_samples"] == 2
        assert result["format"] == "json"

    @pytest.mark.asyncio
    async def test_parse_invalid_jsonl(self, file_handler):
        """실패: 잘못된 JSONL 형식"""
        content = b'invalid json content\n'
        file = UploadFile(
            filename="test.jsonl",
            file=BytesIO(content)
        )

        with pytest.raises(FileValidationError) as exc_info:
            await file_handler.parse_file(file, "jsonl")

        assert "파싱 실패" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_calculate_statistics(self, file_handler):
        """정상: 파일 통계 계산"""
        samples = [
            {"instruction": "a" * 100, "output": "b" * 50},
            {"instruction": "c" * 200, "output": "d" * 100},
            {"instruction": "e" * 150, "output": "f" * 75}
        ]

        stats = file_handler.calculate_statistics(samples)

        assert stats["count"] == 3
        assert "avg_input_length" in stats
        assert "avg_output_length" in stats
        assert stats["avg_input_length"] > 0


class TestMinIOIntegration:
    """MinIO 통합 테스트 (유지보수 용이성: 의존성 주입)"""

    @pytest.fixture
    def file_handler(self, mocker):
        """Mock MinIO client를 주입한 FileHandler"""
        mock_minio = mocker.Mock()
        return FileHandler(minio_client=mock_minio)

    @pytest.mark.asyncio
    async def test_upload_to_minio(self, file_handler, mocker):
        """정상: MinIO에 파일 업로드"""
        file_content = b"test content"
        file = UploadFile(
            filename="test.jsonl",
            file=BytesIO(file_content)
        )

        result = await file_handler.upload_file(file, "datasets/test.jsonl")

        assert result["success"] is True
        assert "file_path" in result
        file_handler.minio_client.put_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_fails_gracefully(self, file_handler, mocker):
        """실패: MinIO 업로드 실패 시 예외 처리"""
        file_handler.minio_client.put_object.side_effect = Exception("Connection error")

        file = UploadFile(
            filename="test.jsonl",
            file=BytesIO(b"content")
        )

        with pytest.raises(Exception) as exc_info:
            await file_handler.upload_file(file, "datasets/test.jsonl")

        assert "Connection error" in str(exc_info.value)


class TestSecurityChecks:
    """추가 보안 검사 테스트"""

    @pytest.fixture
    def file_handler(self):
        return FileHandler()

    def test_detect_null_bytes_in_filename(self, file_handler):
        """실패: 파일명에 null byte 포함 (보안)"""
        with pytest.raises(FileSecurityError):
            file_handler.validate_file_name("test\x00.jsonl")

    def test_reject_empty_filename(self, file_handler):
        """실패: 빈 파일명"""
        with pytest.raises(FileValidationError):
            file_handler.validate_file_name("")

    def test_reject_too_long_filename(self, file_handler):
        """실패: 너무 긴 파일명 (DoS 방지)"""
        long_name = "a" * 300 + ".jsonl"

        with pytest.raises(FileValidationError):
            file_handler.validate_file_name(long_name)
