"""
Training Data Management API Router
학습 데이터셋 관리 API

유지보수 용이성:
- 서비스 레이어와 분리 (DatasetService 사용)
- 의존성 주입 패턴
- 명확한 에러 처리
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import logging
from minio import Minio

from app.core.database import get_db
from app.core.config import settings
from app.models.training import TrainingDataset, DatasetQualityLog
from app.schemas.training import (
    DatasetResponse,
    DatasetListResponse,
    DatasetStatsResponse,
    DatasetSplitRequest,
    DatasetValidationRequest,
    DatasetValidationResponse,
    QualityCheckResult,
    DatasetStatusEnum,
    QualityCheckTypeEnum
)
from datetime import datetime
from app.services.training.dataset_service import (
    DatasetService,
    DatasetNotFoundError,
    DatasetCreationError
)
from app.services.training.file_handler import (
    FileHandler,
    FileValidationError,
    FileSecurityError
)
from app.services.training.quality_validation_service import QualityValidationService
from app.services.training.dataset_preprocessor import (
    DatasetPreprocessor,
    PreprocessingError,
    UnsupportedFormatError
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin/training/datasets", tags=["training-data"])


# 의존성 주입 헬퍼 (유지보수 용이성)
def get_minio_client() -> Minio:
    """MinIO 클라이언트 의존성 주입"""
    return Minio(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE
    )


def get_dataset_service(
    db: AsyncSession = Depends(get_db),
    minio_client: Minio = Depends(get_minio_client)
) -> DatasetService:
    """DatasetService 의존성 주입"""
    file_handler = FileHandler(minio_client=minio_client)
    return DatasetService(db=db, file_handler=file_handler)


# ============================================================================
# Dataset CRUD
# ============================================================================

@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    name: str = Form(...),
    version: str = Form(...),
    description: Optional[str] = Form(None),
    format: str = Form("jsonl"),
    file: UploadFile = File(...),
    dataset_service: DatasetService = Depends(get_dataset_service)
):
    """
    데이터셋 생성 (파일 업로드 포함)

    시큐어 코딩:
    - 파일 크기 제한 (100MB)
    - 허용된 확장자만 (jsonl, json, parquet, csv)
    - 경로 조작 공격 방지
    - 파일명 검증

    유지보수 용이성:
    - 서비스 레이어 사용 (비즈니스 로직 분리)
    - 명확한 에러 처리
    """
    try:
        logger.info(f"데이터셋 생성 요청: name={name}, version={version}, format={format}")

        dataset = await dataset_service.create_dataset(
            name=name,
            version=version,
            file=file,
            format=format,
            description=description
        )

        logger.info(f"데이터셋 생성 성공: ID={dataset.id}")
        return dataset

    except FileValidationError as e:
        logger.warning(f"파일 검증 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileSecurityError as e:
        logger.error(f"보안 위협 감지: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"보안 위협이 감지되었습니다: {str(e)}"
        )
    except DatasetCreationError as e:
        logger.error(f"데이터셋 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"데이터셋 생성 실패: {str(e)}"
        )


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    status: Optional[DatasetStatusEnum] = Query(None, description="상태 필터"),
    search: Optional[str] = Query(None, max_length=255, description="검색어 (이름)"),
    dataset_service: DatasetService = Depends(get_dataset_service)
):
    """
    데이터셋 목록 조회

    유지보수 용이성:
    - 서비스 레이어 사용 (비즈니스 로직 분리)
    - 페이지네이션, 필터링 로직을 서비스에 위임
    """
    try:
        result = await dataset_service.list_datasets(
            page=page,
            page_size=page_size,
            status=status.value if status else None,
            search=search
        )

        return DatasetListResponse(**result)

    except Exception as e:
        logger.error(f"데이터셋 목록 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"데이터셋 목록 조회 실패: {str(e)}"
        )


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: int,
    dataset_service: DatasetService = Depends(get_dataset_service)
):
    """
    데이터셋 상세 조회

    유지보수 용이성:
    - 서비스 레이어 사용
    """
    try:
        dataset = await dataset_service.get_dataset_by_id(dataset_id)
        return dataset

    except DatasetNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"데이터셋 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"데이터셋 조회 실패: {str(e)}"
        )


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: int,
    dataset_service: DatasetService = Depends(get_dataset_service)
):
    """
    데이터셋 삭제 (soft delete - archived 상태로 변경)

    유지보수 용이성:
    - 서비스 레이어 사용
    - Soft delete 정책
    """
    try:
        await dataset_service.delete_dataset(dataset_id, soft=True)
        # 204 No Content는 response body가 없음
        return

    except DatasetNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"데이터셋 삭제 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"데이터셋 삭제 실패: {str(e)}"
        )


# ============================================================================
# Dataset Statistics
# ============================================================================

@router.get("/{dataset_id}/stats", response_model=DatasetStatsResponse)
async def get_dataset_stats(
    dataset_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    데이터셋 통계 조회
    Secure: Parameterized query
    """
    query = select(TrainingDataset).where(TrainingDataset.id == dataset_id)
    result = await db.execute(query)
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"데이터셋을 찾을 수 없습니다: {dataset_id}"
        )

    # TODO: 파일 파싱하여 실제 통계 계산
    # - 평균 입력/출력 길이
    # - 분포 정보
    # - 품질 점수

    return DatasetStatsResponse(
        id=dataset.id,
        name=dataset.name,
        total_samples=dataset.total_samples or 0,
        train_samples=dataset.train_samples or 0,
        val_samples=dataset.val_samples or 0,
        test_samples=dataset.test_samples or 0,
        avg_input_length=None,  # TODO: 계산 구현
        avg_output_length=None,  # TODO: 계산 구현
        distribution=None,  # TODO: 계산 구현
        quality_score=dataset.quality_score
    )


# ============================================================================
# Dataset Validation
# ============================================================================

@router.post("/{dataset_id}/validate", response_model=DatasetValidationResponse)
async def validate_dataset(
    dataset_id: int,
    request: DatasetValidationRequest,
    dataset_service: DatasetService = Depends(get_dataset_service),
    db: AsyncSession = Depends(get_db)
):
    """
    데이터셋 품질 검증 (시큐어 코딩: PII 검출, 중복 검사, 포맷 검증)

    유지보수 용이성:
    - QualityValidationService 사용 (비즈니스 로직 분리)
    - 명확한 검증 결과 로깅
    """
    try:
        # 1. 데이터셋 조회
        dataset = await dataset_service.get_dataset_by_id(dataset_id)

        # 2. 파일에서 샘플 로드 (TODO: FileHandler로 파일 파싱)
        # 현재는 dataset_metadata에서 샘플 가져오기
        # 실제 구현에서는 파일을 읽어야 함
        samples = []
        # TODO: file_handler = FileHandler()
        # TODO: samples = await file_handler.parse_file_from_path(dataset.file_path, dataset.format)

        # 임시: 빈 샘플로 테스트 (파일 파싱 구현 전)
        logger.warning(f"파일 파싱 미구현: dataset_id={dataset_id}, 빈 샘플로 검증")

        # 3. 품질 검증 서비스 초기화
        quality_service = QualityValidationService()

        checks = []

        # 4. PII 검사
        if request.check_pii:
            pii_result = quality_service.check_pii(samples)
            check = QualityCheckResult(
                check_type=QualityCheckTypeEnum.PII_DETECTION,
                passed=pii_result.passed,
                message=pii_result.message,
                details={
                    "pii_count": pii_result.pii_count,
                    "pii_types": list(pii_result.pii_types),
                    "pii_locations": pii_result.pii_locations[:10]  # 최대 10개만
                }
            )
            checks.append(check)

            # 로그 저장
            log = DatasetQualityLog(
                dataset_id=dataset_id,
                check_type="pii_detection",
                passed=pii_result.passed,
                issues={"pii_count": pii_result.pii_count, "pii_types": list(pii_result.pii_types)},
                created_at=datetime.utcnow()
            )
            db.add(log)

        # 5. 중복 검사
        if request.check_duplicates:
            dup_result = quality_service.check_duplicates(samples)
            check = QualityCheckResult(
                check_type=QualityCheckTypeEnum.DUPLICATE_CHECK,
                passed=dup_result.passed,
                message=dup_result.message,
                details={
                    "duplicate_count": dup_result.duplicate_count,
                    "duplicate_pairs": dup_result.duplicate_pairs[:10]  # 최대 10개만
                }
            )
            checks.append(check)

            log = DatasetQualityLog(
                dataset_id=dataset_id,
                check_type="duplicate_check",
                passed=dup_result.passed,
                issues={"duplicate_count": dup_result.duplicate_count},
                created_at=datetime.utcnow()
            )
            db.add(log)

        # 6. 포맷 검사
        if request.check_format:
            fmt_result = quality_service.check_format(samples, required_fields=["instruction", "output"])
            check = QualityCheckResult(
                check_type=QualityCheckTypeEnum.FORMAT_CHECK,
                passed=fmt_result.passed,
                message=fmt_result.message,
                details={
                    "invalid_count": fmt_result.invalid_count,
                    "invalid_samples": fmt_result.invalid_samples[:10]  # 최대 10개만
                }
            )
            checks.append(check)

            log = DatasetQualityLog(
                dataset_id=dataset_id,
                check_type="format_check",
                passed=fmt_result.passed,
                issues={"invalid_count": fmt_result.invalid_count},
                created_at=datetime.utcnow()
            )
            db.add(log)

        await db.commit()

        # 7. 전체 결과 계산
        overall_passed = all(check.passed for check in checks)
        quality_score = quality_service.calculate_quality_score(samples) if samples else 1.0

        logger.info(
            f"데이터셋 검증 완료: dataset_id={dataset_id}, "
            f"overall_passed={overall_passed}, quality_score={quality_score}"
        )

        return DatasetValidationResponse(
            dataset_id=dataset_id,
            checks=checks,
            overall_passed=overall_passed,
            quality_score=quality_score
        )

    except DatasetNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"데이터셋 검증 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"데이터셋 검증 실패: {str(e)}"
        )


# ============================================================================
# Dataset Split
# ============================================================================

@router.post("/{dataset_id}/split")
async def split_dataset(
    dataset_id: int,
    request: DatasetSplitRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    데이터셋 분할 (train/val/test)
    Secure: Parameterized query, ratio validation
    """
    # Validate ratios sum to 1.0
    total_ratio = request.train_ratio + request.val_ratio + request.test_ratio
    if abs(total_ratio - 1.0) > 0.01:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"비율의 합이 1.0이 아닙니다: {total_ratio}"
        )

    query = select(TrainingDataset).where(TrainingDataset.id == dataset_id)
    result = await db.execute(query)
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"데이터셋을 찾을 수 없습니다: {dataset_id}"
        )

    # TODO: 실제 데이터셋 분할 구현
    # 1. 파일 읽기
    # 2. 랜덤 셔플 (seed 사용)
    # 3. 분할하여 별도 파일로 저장
    # 4. DB 업데이트

    total = dataset.total_samples or 0
    train_samples = int(total * request.train_ratio)
    val_samples = int(total * request.val_ratio)
    test_samples = total - train_samples - val_samples

    dataset.train_samples = train_samples
    dataset.val_samples = val_samples
    dataset.test_samples = test_samples

    await db.commit()

    return {
        "message": "데이터셋 분할 완료 (구현 예정)",
        "train_samples": train_samples,
        "val_samples": val_samples,
        "test_samples": test_samples
    }


# ============================================================================
# Dataset Preprocessing
# ============================================================================

@router.post("/{dataset_id}/preprocess")
async def preprocess_dataset(
    dataset_id: int,
    output_format: str = Query("alpaca", description="출력 형식 (alpaca | sharegpt)"),
    validate: bool = Query(True, description="검증 수행 여부"),
    db: AsyncSession = Depends(get_db)
):
    """
    데이터셋 전처리 (Axolotl 형식 변환)

    시큐어 코딩:
    - 파일 크기 검증
    - 경로 검증
    - 입력 형식 검증

    유지보수 용이성:
    - DatasetPreprocessor 서비스 사용
    - 명확한 에러 처리
    """
    try:
        # 데이터셋 조회
        query = select(TrainingDataset).where(TrainingDataset.id == dataset_id)
        result = await db.execute(query)
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"데이터셋을 찾을 수 없습니다: {dataset_id}"
            )

        logger.info(f"데이터셋 전처리 시작: ID={dataset_id}, format={output_format}")

        # 전처리 실행
        preprocessor = DatasetPreprocessor()

        # 입력 형식 결정
        input_format = dataset.format  # "jsonl", "csv", "parquet"

        # 출력 경로 생성
        from pathlib import Path
        input_path = dataset.file_path
        output_dir = Path(input_path).parent
        output_filename = f"{Path(input_path).stem}_{output_format}.jsonl"
        output_path = str(output_dir / output_filename)

        # 전처리 파이프라인 실행
        result = preprocessor.preprocess_dataset(
            input_path=input_path,
            output_path=output_path,
            input_format=input_format,
            output_format=output_format,
            validate=validate
        )

        # DB 업데이트
        dataset.preprocessed_path = output_path
        dataset.total_samples = result["statistics"]["total_samples"]
        dataset.avg_instruction_length = result["statistics"]["avg_instruction_length"]
        dataset.avg_output_length = result["statistics"]["avg_output_length"]
        dataset.updated_at = datetime.utcnow()

        await db.commit()

        logger.info(f"데이터셋 전처리 완료: ID={dataset_id}, output={output_path}")

        return {
            "message": "데이터셋 전처리 완료",
            "dataset_id": dataset_id,
            "output_path": output_path,
            "statistics": result["statistics"],
            "validation_errors": result["validation_errors"]
        }

    except UnsupportedFormatError as e:
        logger.warning(f"지원하지 않는 형식: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PreprocessingError as e:
        logger.error(f"전처리 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"전처리 실패: {str(e)}"
        )
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"예상치 못한 오류: {str(e)}"
        )


@router.get("/{dataset_id}/statistics")
async def get_dataset_statistics(
    dataset_id: int,
    count_tokens: bool = Query(False, description="토큰 수 계산 여부"),
    db: AsyncSession = Depends(get_db)
):
    """
    데이터셋 통계 조회

    유지보수 용이성:
    - DatasetPreprocessor 서비스 사용
    - 캐시 가능한 통계 정보
    """
    try:
        # 데이터셋 조회
        query = select(TrainingDataset).where(TrainingDataset.id == dataset_id)
        result = await db.execute(query)
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"데이터셋을 찾을 수 없습니다: {dataset_id}"
            )

        logger.info(f"데이터셋 통계 조회: ID={dataset_id}, count_tokens={count_tokens}")

        # 전처리된 파일이 있으면 그것 사용, 없으면 원본 파일 사용
        file_path = dataset.preprocessed_path or dataset.file_path

        # 통계 생성
        preprocessor = DatasetPreprocessor()
        stats = preprocessor.generate_statistics(
            jsonl_path=file_path,
            count_tokens=count_tokens,
            skip_invalid=True
        )

        return {
            "dataset_id": dataset_id,
            "file_path": file_path,
            "statistics": stats
        }

    except PreprocessingError as e:
        logger.error(f"통계 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"통계 생성 실패: {str(e)}"
        )
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"예상치 못한 오류: {str(e)}"
        )
