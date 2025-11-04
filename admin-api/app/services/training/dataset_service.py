"""
Dataset Service for Training Data Management
데이터셋 생성, 조회, 업데이트, 삭제를 담당하는 서비스

유지보수 용이성:
- 단일 책임 원칙 (SRP): 데이터셋 관리만 담당
- 의존성 주입 (DI): DB와 FileHandler를 주입받음
- 명확한 에러 처리: 커스텀 예외 사용

시큐어 코딩:
- Input validation은 FileHandler에 위임
- DB 트랜잭션 관리
- Rollback 처리
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.exc import SQLAlchemyError
from fastapi import UploadFile
import logging

from app.models.training import TrainingDataset
from app.services.training.file_handler import FileHandler

logger = logging.getLogger(__name__)


class DatasetNotFoundError(Exception):
    """데이터셋을 찾을 수 없음"""
    pass


class DatasetCreationError(Exception):
    """데이터셋 생성 실패"""
    pass


class DatasetService:
    """
    데이터셋 서비스

    책임:
    - 데이터셋 생성 (파일 업로드 포함)
    - 데이터셋 조회 (ID, 목록)
    - 데이터셋 업데이트 (상태 변경 등)
    - 데이터셋 삭제 (Soft delete)
    - 데이터셋 통계 조회
    """

    def __init__(
        self,
        db: AsyncSession,
        file_handler: Optional[FileHandler] = None
    ):
        """
        생성자 (의존성 주입 for 유지보수 용이성)

        Args:
            db: AsyncSession (DB 세션)
            file_handler: FileHandler (파일 처리, 테스트 시 Mock 주입 가능)
        """
        self.db = db
        self.file_handler = file_handler or FileHandler()

    async def create_dataset(
        self,
        name: str,
        version: str,
        file: UploadFile,
        format: str,
        description: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> TrainingDataset:
        """
        데이터셋 생성 (파일 업로드 포함)

        Args:
            name: 데이터셋 이름
            version: 버전
            file: 업로드 파일
            format: 파일 형식 (jsonl, json, parquet, csv)
            description: 설명
            created_by: 생성자 ID

        Returns:
            생성된 TrainingDataset

        Raises:
            DatasetCreationError: 생성 실패
        """
        try:
            # 1. 파일 검증 (시큐어 코딩: FileHandler에 위임)
            self.file_handler.validate_file_name(file.filename)
            self.file_handler.validate_file_extension(file.filename)
            self.file_handler.validate_file_size(file)

            logger.info(f"데이터셋 생성 시작: {name} v{version}")

            # 2. 파일 파싱
            parse_result = await self.file_handler.parse_file(file, format)
            total_samples = parse_result["total_samples"]
            samples = parse_result["samples"]

            # 3. 통계 계산
            statistics = self.file_handler.calculate_statistics(samples)

            # 4. MinIO에 파일 업로드
            file_path = f"{name}_{version}.{format}"
            upload_result = await self.file_handler.upload_file(file, file_path)

            # 5. DB에 저장
            dataset = TrainingDataset(
                name=name,
                version=version,
                description=description,
                format=format,
                file_path=upload_result["file_path"],
                total_samples=total_samples,
                dataset_metadata=statistics,
                status="active",
                created_by=created_by
            )

            self.db.add(dataset)
            await self.db.commit()
            await self.db.refresh(dataset)

            logger.info(f"데이터셋 생성 완료: ID={dataset.id}")
            return dataset

        except SQLAlchemyError as e:
            logger.error(f"DB 오류: {e}")
            await self.db.rollback()
            raise DatasetCreationError(f"데이터셋 생성 실패 (DB 오류): {str(e)}")
        except Exception as e:
            logger.error(f"데이터셋 생성 실패: {e}")
            await self.db.rollback()
            raise DatasetCreationError(f"데이터셋 생성 실패: {str(e)}")

    async def get_dataset_by_id(self, dataset_id: int) -> TrainingDataset:
        """
        ID로 데이터셋 조회

        Args:
            dataset_id: 데이터셋 ID

        Returns:
            TrainingDataset

        Raises:
            DatasetNotFoundError: 데이터셋이 없는 경우
        """
        query = select(TrainingDataset).where(TrainingDataset.id == dataset_id)
        result = await self.db.execute(query)
        dataset = result.scalar_one_or_none()

        if not dataset:
            logger.warning(f"데이터셋을 찾을 수 없음: ID={dataset_id}")
            raise DatasetNotFoundError(f"데이터셋을 찾을 수 없습니다: {dataset_id}")

        return dataset

    async def list_datasets(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        데이터셋 목록 조회 (페이지네이션)

        Args:
            page: 페이지 번호
            page_size: 페이지 크기
            status: 상태 필터
            search: 검색어 (이름)

        Returns:
            {
                "items": List[TrainingDataset],
                "total": int,
                "page": int,
                "page_size": int
            }
        """
        # Build query
        query = select(TrainingDataset)

        # Apply filters
        conditions = []
        if status:
            conditions.append(TrainingDataset.status == status)
        if search:
            conditions.append(TrainingDataset.name.ilike(f"%{search}%"))

        if conditions:
            query = query.where(and_(*conditions))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.order_by(desc(TrainingDataset.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        datasets = result.scalars().all()

        return {
            "items": list(datasets),
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def update_dataset_status(
        self,
        dataset_id: int,
        status: str
    ) -> TrainingDataset:
        """
        데이터셋 상태 업데이트

        Args:
            dataset_id: 데이터셋 ID
            status: 새로운 상태 (active, deprecated, archived)

        Returns:
            업데이트된 TrainingDataset

        Raises:
            DatasetNotFoundError: 데이터셋이 없는 경우
        """
        dataset = await self.get_dataset_by_id(dataset_id)
        dataset.status = status
        await self.db.commit()
        await self.db.refresh(dataset)

        logger.info(f"데이터셋 상태 업데이트: ID={dataset_id}, status={status}")
        return dataset

    async def delete_dataset(
        self,
        dataset_id: int,
        soft: bool = True
    ) -> None:
        """
        데이터셋 삭제

        Args:
            dataset_id: 데이터셋 ID
            soft: True이면 soft delete (상태만 변경), False면 hard delete

        Raises:
            DatasetNotFoundError: 데이터셋이 없는 경우
        """
        dataset = await self.get_dataset_by_id(dataset_id)

        if soft:
            # Soft delete: 상태를 archived로 변경
            dataset.status = "archived"
            await self.db.commit()
            logger.info(f"데이터셋 soft delete: ID={dataset_id}")
        else:
            # Hard delete: DB에서 삭제
            await self.db.delete(dataset)
            await self.db.commit()
            logger.info(f"데이터셋 hard delete: ID={dataset_id}")

    async def get_dataset_statistics(
        self,
        dataset_id: int
    ) -> Dict[str, Any]:
        """
        데이터셋 통계 조회

        Args:
            dataset_id: 데이터셋 ID

        Returns:
            통계 정보 딕셔너리

        Raises:
            DatasetNotFoundError: 데이터셋이 없는 경우
        """
        dataset = await self.get_dataset_by_id(dataset_id)

        return {
            "id": dataset.id,
            "name": dataset.name,
            "version": dataset.version,
            "total_samples": dataset.total_samples,
            "train_samples": dataset.train_samples,
            "val_samples": dataset.val_samples,
            "test_samples": dataset.test_samples,
            "format": dataset.format,
            "quality_score": dataset.quality_score,
            "metadata": dataset.dataset_metadata,
            "status": dataset.status,
            "created_at": dataset.created_at
        }

    async def split_dataset(
        self,
        dataset_id: int,
        train_ratio: float,
        val_ratio: float,
        test_ratio: float,
        random_seed: int = 42
    ) -> TrainingDataset:
        """
        데이터셋 분할 (train/val/test)

        Args:
            dataset_id: 데이터셋 ID
            train_ratio: 학습 데이터 비율
            val_ratio: 검증 데이터 비율
            test_ratio: 테스트 데이터 비율
            random_seed: 랜덤 시드

        Returns:
            업데이트된 TrainingDataset

        Raises:
            DatasetNotFoundError: 데이터셋이 없는 경우
            ValueError: 비율의 합이 1.0이 아닌 경우
        """
        # 비율 검증
        total_ratio = train_ratio + val_ratio + test_ratio
        if abs(total_ratio - 1.0) > 0.01:
            raise ValueError(f"비율의 합이 1.0이 아닙니다: {total_ratio}")

        dataset = await self.get_dataset_by_id(dataset_id)

        # TODO: 실제 파일 분할 로직 구현
        # 현재는 비율만 계산하여 DB에 저장
        total = dataset.total_samples or 0
        train_samples = int(total * train_ratio)
        val_samples = int(total * val_ratio)
        test_samples = total - train_samples - val_samples

        dataset.train_samples = train_samples
        dataset.val_samples = val_samples
        dataset.test_samples = test_samples

        await self.db.commit()
        await self.db.refresh(dataset)

        logger.info(
            f"데이터셋 분할: ID={dataset_id}, "
            f"train={train_samples}, val={val_samples}, test={test_samples}"
        )

        return dataset
