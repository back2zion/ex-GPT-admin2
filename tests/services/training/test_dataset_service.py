"""
Test cases for Dataset Service
TDD: Red-Green-Refactor 방식으로 작성

유지보수 용이성 테스트:
- 의존성 주입 (DB, FileHandler)
- 단일 책임 원칙
- 명확한 에러 처리
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
from io import BytesIO

from app.services.training.dataset_service import (
    DatasetService,
    DatasetNotFoundError,
    DatasetCreationError
)
from app.services.training.file_handler import FileHandler
from app.models.training import TrainingDataset


class TestDatasetCreation:
    """데이터셋 생성 테스트"""

    @pytest.fixture
    def mock_db(self, mocker):
        """Mock AsyncSession"""
        mock = mocker.AsyncMock(spec=AsyncSession)
        return mock

    @pytest.fixture
    def mock_file_handler(self, mocker):
        """Mock FileHandler"""
        mock = mocker.Mock(spec=FileHandler)
        return mock

    @pytest.fixture
    def dataset_service(self, mock_db, mock_file_handler):
        """DatasetService 인스턴스 (의존성 주입)"""
        return DatasetService(
            db=mock_db,
            file_handler=mock_file_handler
        )

    @pytest.mark.asyncio
    async def test_create_dataset_success(
        self,
        dataset_service,
        mock_db,
        mock_file_handler
    ):
        """정상: 데이터셋 생성 성공"""
        # Arrange
        file_content = b'{"instruction": "test", "output": "result"}\n'
        file = UploadFile(
            filename="test.jsonl",
            file=BytesIO(file_content)
        )

        # Mock file handler responses
        mock_file_handler.parse_file = AsyncMock(return_value={
            "total_samples": 1,
            "format": "jsonl",
            "samples": [{"instruction": "test", "output": "result"}]
        })
        mock_file_handler.calculate_statistics = Mock(return_value={
            "count": 1,
            "avg_input_length": 4,
            "avg_output_length": 6
        })
        mock_file_handler.upload_file = AsyncMock(return_value={
            "success": True,
            "file_path": "datasets/test.jsonl"
        })

        # Mock DB operations
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Act
        result = await dataset_service.create_dataset(
            name="test_dataset",
            version="1.0",
            file=file,
            format="jsonl"
        )

        # Assert
        assert result is not None
        assert result.name == "test_dataset"
        assert result.version == "1.0"
        assert result.total_samples == 1
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_dataset_with_validation(
        self,
        dataset_service,
        mock_file_handler
    ):
        """정상: 데이터셋 생성 시 파일 검증"""
        file = UploadFile(
            filename="test.jsonl",
            file=BytesIO(b'content')
        )

        # Mock validations
        mock_file_handler.validate_file_name = Mock()
        mock_file_handler.validate_file_extension = Mock()
        mock_file_handler.validate_file_size = Mock()

        # Other mocks
        mock_file_handler.parse_file = AsyncMock(return_value={
            "total_samples": 1,
            "format": "jsonl",
            "samples": [{}]
        })
        mock_file_handler.calculate_statistics = Mock(return_value={})
        mock_file_handler.upload_file = AsyncMock(return_value={
            "success": True,
            "file_path": "path"
        })

        await dataset_service.create_dataset(
            name="test",
            version="1.0",
            file=file,
            format="jsonl"
        )

        # Verify validations were called
        mock_file_handler.validate_file_name.assert_called_once()
        mock_file_handler.validate_file_extension.assert_called_once()
        mock_file_handler.validate_file_size.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_dataset_handles_db_error(
        self,
        dataset_service,
        mock_db,
        mock_file_handler
    ):
        """실패: DB 오류 시 예외 처리"""
        file = UploadFile(
            filename="test.jsonl",
            file=BytesIO(b'content')
        )

        # Mock file operations to succeed
        mock_file_handler.parse_file = AsyncMock(return_value={
            "total_samples": 1,
            "format": "jsonl",
            "samples": [{}]
        })
        mock_file_handler.calculate_statistics = Mock(return_value={})
        mock_file_handler.upload_file = AsyncMock(return_value={
            "success": True,
            "file_path": "path"
        })

        # Mock DB to fail
        mock_db.commit = AsyncMock(side_effect=Exception("DB Error"))
        mock_db.rollback = AsyncMock()

        with pytest.raises(DatasetCreationError) as exc_info:
            await dataset_service.create_dataset(
                name="test",
                version="1.0",
                file=file,
                format="jsonl"
            )

        assert "DB Error" in str(exc_info.value)
        mock_db.rollback.assert_called_once()


class TestDatasetRetrieval:
    """데이터셋 조회 테스트"""

    @pytest.fixture
    def mock_db(self, mocker):
        return mocker.AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def dataset_service(self, mock_db):
        return DatasetService(db=mock_db, file_handler=None)

    @pytest.mark.asyncio
    async def test_get_dataset_by_id_success(
        self,
        dataset_service,
        mock_db
    ):
        """정상: ID로 데이터셋 조회"""
        # Mock dataset
        mock_dataset = TrainingDataset(
            id=1,
            name="test",
            version="1.0",
            format="jsonl",
            file_path="/path/to/file",
            total_samples=100
        )

        # Mock DB query
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_dataset)
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await dataset_service.get_dataset_by_id(1)

        # Assert
        assert result is not None
        assert result.id == 1
        assert result.name == "test"

    @pytest.mark.asyncio
    async def test_get_dataset_not_found(
        self,
        dataset_service,
        mock_db
    ):
        """실패: 존재하지 않는 데이터셋 조회"""
        # Mock DB to return None
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(DatasetNotFoundError) as exc_info:
            await dataset_service.get_dataset_by_id(999)

        assert "999" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_datasets_with_pagination(
        self,
        dataset_service,
        mock_db
    ):
        """정상: 페이지네이션을 포함한 데이터셋 목록 조회"""
        # Mock datasets
        mock_datasets = [
            TrainingDataset(id=1, name="ds1", version="1.0", format="jsonl", file_path="/path1"),
            TrainingDataset(id=2, name="ds2", version="1.0", format="json", file_path="/path2")
        ]

        # Mock count query
        mock_count_result = Mock()
        mock_count_result.scalar = Mock(return_value=2)

        # Mock list query
        mock_list_result = Mock()
        mock_list_result.scalars = Mock(return_value=Mock(all=Mock(return_value=mock_datasets)))

        mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_list_result])

        # Act
        result = await dataset_service.list_datasets(page=1, page_size=10)

        # Assert
        assert result["total"] == 2
        assert len(result["items"]) == 2
        assert result["page"] == 1


class TestDatasetUpdate:
    """데이터셋 업데이트 테스트"""

    @pytest.fixture
    def mock_db(self, mocker):
        return mocker.AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def dataset_service(self, mock_db):
        return DatasetService(db=mock_db, file_handler=None)

    @pytest.mark.asyncio
    async def test_update_dataset_status(
        self,
        dataset_service,
        mock_db
    ):
        """정상: 데이터셋 상태 업데이트"""
        # Mock existing dataset
        mock_dataset = TrainingDataset(
            id=1,
            name="test",
            version="1.0",
            format="jsonl",
            file_path="/path",
            status="active"
        )

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_dataset)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        # Act
        result = await dataset_service.update_dataset_status(1, "archived")

        # Assert
        assert result.status == "archived"
        mock_db.commit.assert_called_once()


class TestDatasetDeletion:
    """데이터셋 삭제 테스트 (Soft Delete)"""

    @pytest.fixture
    def mock_db(self, mocker):
        return mocker.AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def dataset_service(self, mock_db):
        return DatasetService(db=mock_db, file_handler=None)

    @pytest.mark.asyncio
    async def test_soft_delete_dataset(
        self,
        dataset_service,
        mock_db
    ):
        """정상: Soft Delete (상태를 archived로 변경)"""
        mock_dataset = TrainingDataset(
            id=1,
            name="test",
            version="1.0",
            format="jsonl",
            file_path="/path",
            status="active"
        )

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_dataset)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        # Act
        await dataset_service.delete_dataset(1, soft=True)

        # Assert
        assert mock_dataset.status == "archived"
        mock_db.commit.assert_called_once()


class TestDatasetStatistics:
    """데이터셋 통계 테스트"""

    @pytest.fixture
    def mock_db(self, mocker):
        return mocker.AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_file_handler(self, mocker):
        return mocker.Mock(spec=FileHandler)

    @pytest.fixture
    def dataset_service(self, mock_db, mock_file_handler):
        return DatasetService(db=mock_db, file_handler=mock_file_handler)

    @pytest.mark.asyncio
    async def test_get_dataset_statistics(
        self,
        dataset_service,
        mock_db,
        mock_file_handler
    ):
        """정상: 데이터셋 통계 조회"""
        mock_dataset = TrainingDataset(
            id=1,
            name="test",
            version="1.0",
            format="jsonl",
            file_path="/path",
            total_samples=100,
            train_samples=80,
            val_samples=10,
            test_samples=10,
            dataset_metadata={"source": "internal"}
        )

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_dataset)
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await dataset_service.get_dataset_statistics(1)

        # Assert
        assert result["id"] == 1
        assert result["total_samples"] == 100
        assert result["train_samples"] == 80
        assert result["metadata"] == {"source": "internal"}
