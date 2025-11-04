"""
Dataset Preprocessor Service
데이터셋 전처리 서비스

책임:
- CSV/Parquet → JSONL 변환
- JSONL → Axolotl 형식 변환 (alpaca, sharegpt)
- 데이터셋 통계 생성

시큐어 코딩:
- 파일 크기 제한 (DoS 방지)
- 경로 검증 (Path Traversal 방지)
- 손상된 데이터 처리

유지보수성:
- 명확한 책임 분리
- 의존성 주입 가능
- 확장 가능한 포맷 시스템
"""
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from collections import Counter

logger = logging.getLogger(__name__)


# ============================================================================
# 예외 클래스
# ============================================================================

class PreprocessingError(Exception):
    """전처리 에러"""
    pass


class UnsupportedFormatError(PreprocessingError):
    """지원하지 않는 형식"""
    pass


# ============================================================================
# DatasetPreprocessor 서비스
# ============================================================================

class DatasetPreprocessor:
    """
    데이터셋 전처리 서비스

    유지보수성:
    - 각 변환 기능이 독립적인 메서드
    - 재사용 가능한 유틸리티 함수
    - 명확한 에러 메시지
    """

    # 시큐어 코딩: 파일 크기 제한 (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

    # 필수 컬럼
    REQUIRED_COLUMNS = {"instruction", "output"}

    # 지원 형식
    SUPPORTED_FORMATS = {"alpaca", "sharegpt"}

    def __init__(self, max_file_size: Optional[int] = None):
        """
        Args:
            max_file_size: 최대 파일 크기 (bytes). None이면 기본값 사용
        """
        self.max_file_size = max_file_size or self.MAX_FILE_SIZE

    # ========================================================================
    # 시큐어 코딩: 입력 검증
    # ========================================================================

    def _validate_file_size(self, file_path: str) -> None:
        """
        파일 크기 검증 (DoS 방지)

        Args:
            file_path: 파일 경로

        Raises:
            PreprocessingError: 파일 크기 초과
        """
        path = Path(file_path)
        if not path.exists():
            raise PreprocessingError(f"File not found: {file_path}")

        file_size = path.stat().st_size
        if file_size > self.max_file_size:
            raise PreprocessingError(
                f"File size exceeds limit: {file_size} bytes > {self.max_file_size} bytes"
            )

    def _validate_output_path(self, output_path: str) -> None:
        """
        출력 경로 검증 (Path Traversal 방지)

        Args:
            output_path: 출력 경로

        Raises:
            PreprocessingError: 유효하지 않은 경로
        """
        # 경로 조작 공격 감지
        if ".." in output_path or output_path.startswith("/etc"):
            raise PreprocessingError(f"Invalid output path: {output_path}")

    def _validate_columns(
        self,
        df: pd.DataFrame,
        required_columns: Optional[set] = None
    ) -> None:
        """
        DataFrame 컬럼 검증

        Args:
            df: DataFrame
            required_columns: 필수 컬럼 집합. None이면 기본값 사용

        Raises:
            PreprocessingError: 필수 컬럼 누락
        """
        required = required_columns or self.REQUIRED_COLUMNS
        missing_columns = required - set(df.columns)

        if missing_columns:
            raise PreprocessingError(
                f"Missing required columns: {missing_columns}"
            )

    # ========================================================================
    # CSV 변환
    # ========================================================================

    def convert_csv_to_jsonl(
        self,
        csv_path: str,
        output_path: str,
        column_mapping: Optional[Dict[str, str]] = None,
        max_file_size: Optional[int] = None
    ) -> str:
        """
        CSV 파일을 JSONL로 변환

        Args:
            csv_path: CSV 파일 경로
            output_path: 출력 JSONL 경로
            column_mapping: 컬럼 매핑 (예: {"instruction": "question"} = instruction은 question 컬럼에서 가져옴)
            max_file_size: 최대 파일 크기 (None이면 인스턴스 기본값)

        Returns:
            출력 파일 경로

        Raises:
            PreprocessingError: 변환 실패
        """
        try:
            # 시큐어 코딩: 입력 검증
            max_size = max_file_size or self.max_file_size
            original_max = self.max_file_size
            self.max_file_size = max_size

            self._validate_file_size(csv_path)
            self._validate_output_path(output_path)

            self.max_file_size = original_max

            # CSV 읽기
            df = pd.read_csv(csv_path)

            if df.empty:
                raise PreprocessingError("Empty dataset")

            # 컬럼 매핑 적용 (역방향으로)
            # {"instruction": "question"} → "question" 컬럼을 "instruction"으로 rename
            if column_mapping:
                reverse_mapping = {v: k for k, v in column_mapping.items()}
                df = df.rename(columns=reverse_mapping)

            # 필수 컬럼 검증
            self._validate_columns(df)

            # input 컬럼이 없으면 빈 문자열로 추가
            if "input" not in df.columns:
                df["input"] = ""

            # JSONL로 변환
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                for _, row in df.iterrows():
                    sample = {
                        "instruction": str(row["instruction"]),
                        "input": str(row.get("input", "")),
                        "output": str(row["output"])
                    }
                    f.write(json.dumps(sample, ensure_ascii=False) + '\n')

            logger.info(f"CSV → JSONL 변환 완료: {csv_path} → {output_path}")
            return output_path

        except pd.errors.EmptyDataError:
            raise PreprocessingError("Empty dataset")
        except Exception as e:
            logger.error(f"CSV 변환 실패: {e}")
            raise PreprocessingError(f"Failed to convert CSV: {str(e)}")

    # ========================================================================
    # Parquet 변환
    # ========================================================================

    def convert_parquet_to_jsonl(
        self,
        parquet_path: str,
        output_path: str,
        column_mapping: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Parquet 파일을 JSONL로 변환

        Args:
            parquet_path: Parquet 파일 경로
            output_path: 출력 JSONL 경로
            column_mapping: 컬럼 매핑

        Returns:
            출력 파일 경로

        Raises:
            PreprocessingError: 변환 실패
        """
        try:
            # 시큐어 코딩: 입력 검증
            self._validate_file_size(parquet_path)
            self._validate_output_path(output_path)

            # Parquet 읽기
            df = pd.read_parquet(parquet_path)

            if df.empty:
                raise PreprocessingError("Empty dataset")

            # 컬럼 매핑 적용
            if column_mapping:
                df = df.rename(columns=column_mapping)

            # 필수 컬럼 검증
            self._validate_columns(df)

            # input 컬럼이 없으면 빈 문자열로 추가
            if "input" not in df.columns:
                df["input"] = ""

            # JSONL로 변환
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                for _, row in df.iterrows():
                    sample = {
                        "instruction": str(row["instruction"]),
                        "input": str(row.get("input", "")),
                        "output": str(row["output"])
                    }
                    f.write(json.dumps(sample, ensure_ascii=False) + '\n')

            logger.info(f"Parquet → JSONL 변환 완료: {parquet_path} → {output_path}")
            return output_path

        except Exception as e:
            if "parquet" in str(e).lower():
                raise PreprocessingError(f"Failed to read Parquet: {str(e)}")
            logger.error(f"Parquet 변환 실패: {e}")
            raise PreprocessingError(f"Failed to convert Parquet: {str(e)}")

    # ========================================================================
    # Axolotl 형식 변환
    # ========================================================================

    def convert_to_axolotl_format(
        self,
        jsonl_path: str,
        output_path: str,
        format_type: str = "alpaca"
    ) -> str:
        """
        JSONL을 Axolotl 형식으로 변환

        Args:
            jsonl_path: 입력 JSONL 경로
            output_path: 출력 경로
            format_type: 형식 타입 ("alpaca" | "sharegpt")

        Returns:
            출력 파일 경로

        Raises:
            UnsupportedFormatError: 지원하지 않는 형식
            PreprocessingError: 변환 실패
        """
        if format_type not in self.SUPPORTED_FORMATS:
            raise UnsupportedFormatError(
                f"Unsupported format: {format_type}. "
                f"Supported formats: {self.SUPPORTED_FORMATS}"
            )

        try:
            # 시큐어 코딩: 입력 검증
            self._validate_file_size(jsonl_path)
            self._validate_output_path(output_path)

            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            with open(jsonl_path, 'r', encoding='utf-8') as f_in, \
                 open(output_path, 'w', encoding='utf-8') as f_out:

                for line in f_in:
                    sample = json.loads(line.strip())

                    if format_type == "alpaca":
                        # Alpaca 형식: instruction, input, output
                        converted = {
                            "instruction": sample["instruction"],
                            "input": sample.get("input", ""),
                            "output": sample["output"]
                        }

                    elif format_type == "sharegpt":
                        # ShareGPT 형식: conversations
                        conversations = [
                            {"from": "human", "value": sample["instruction"]},
                            {"from": "gpt", "value": sample["output"]}
                        ]

                        # input이 있으면 context로 추가
                        if sample.get("input"):
                            conversations.insert(0, {
                                "from": "system",
                                "value": sample["input"]
                            })

                        converted = {"conversations": conversations}

                    f_out.write(json.dumps(converted, ensure_ascii=False) + '\n')

            logger.info(f"Axolotl {format_type} 형식 변환 완료: {jsonl_path} → {output_path}")
            return output_path

        except json.JSONDecodeError as e:
            raise PreprocessingError(f"Invalid JSON in JSONL: {str(e)}")
        except Exception as e:
            logger.error(f"Axolotl 변환 실패: {e}")
            raise PreprocessingError(f"Failed to convert to Axolotl format: {str(e)}")

    # ========================================================================
    # 데이터셋 통계
    # ========================================================================

    def generate_statistics(
        self,
        jsonl_path: str,
        count_tokens: bool = False,
        skip_invalid: bool = False
    ) -> Dict[str, Any]:
        """
        데이터셋 통계 생성

        Args:
            jsonl_path: JSONL 파일 경로
            count_tokens: 토큰 수 계산 여부
            skip_invalid: 잘못된 라인 건너뛰기

        Returns:
            통계 딕셔너리

        Raises:
            PreprocessingError: 통계 생성 실패
        """
        try:
            self._validate_file_size(jsonl_path)

            samples = []
            invalid_count = 0

            with open(jsonl_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        sample = json.loads(line.strip())
                        samples.append(sample)
                    except json.JSONDecodeError:
                        invalid_count += 1
                        if not skip_invalid:
                            raise PreprocessingError(
                                f"Invalid JSON at line {line_num}"
                            )

            if not samples:
                raise PreprocessingError("Empty dataset")

            # 기본 통계
            instruction_lengths = [len(s.get("instruction", "")) for s in samples]
            output_lengths = [len(s.get("output", "")) for s in samples]

            stats = {
                "total_samples": len(samples),
                "invalid_samples": invalid_count,
                "avg_instruction_length": sum(instruction_lengths) / len(samples),
                "avg_output_length": sum(output_lengths) / len(samples),
                "min_output_length": min(output_lengths),
                "max_output_length": max(output_lengths),
                "sample_examples": samples[:5]  # 첫 5개 샘플
            }

            # 길이 분포
            length_ranges = [(0, 50), (50, 100), (100, 200), (200, 500), (500, float('inf'))]
            token_distribution = {}

            for start, end in length_ranges:
                range_key = f"{start}-{end if end != float('inf') else '∞'}"
                count = sum(1 for length in output_lengths if start <= length < end)
                token_distribution[range_key] = count

            stats["token_distribution"] = token_distribution

            # 토큰 수 계산 (간단한 추정: 공백 기준)
            if count_tokens:
                total_tokens = sum(
                    len(s.get("instruction", "").split()) +
                    len(s.get("output", "").split())
                    for s in samples
                )
                stats["total_tokens"] = total_tokens
                stats["avg_tokens_per_sample"] = total_tokens / len(samples)

            logger.info(f"통계 생성 완료: {len(samples)} 샘플")
            return stats

        except Exception as e:
            if isinstance(e, PreprocessingError):
                raise
            logger.error(f"통계 생성 실패: {e}")
            raise PreprocessingError(f"Failed to generate statistics: {str(e)}")

    # ========================================================================
    # 통합 파이프라인
    # ========================================================================

    def preprocess_dataset(
        self,
        input_path: str,
        output_path: str,
        input_format: str,
        output_format: str = "alpaca",
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        데이터셋 전처리 파이프라인

        Args:
            input_path: 입력 파일 경로
            output_path: 출력 파일 경로
            input_format: 입력 형식 ("csv" | "parquet" | "jsonl")
            output_format: 출력 형식 ("alpaca" | "sharegpt")
            validate: 검증 수행 여부

        Returns:
            결과 딕셔너리 (success, output_path, statistics, validation_errors)

        Raises:
            PreprocessingError: 전처리 실패
        """
        try:
            # Step 1: 입력 형식 → JSONL
            intermediate_path = str(Path(output_path).parent / "intermediate.jsonl")

            if input_format == "csv":
                self.convert_csv_to_jsonl(input_path, intermediate_path)
            elif input_format == "parquet":
                self.convert_parquet_to_jsonl(input_path, intermediate_path)
            elif input_format == "jsonl":
                # 이미 JSONL이면 복사
                import shutil
                shutil.copy(input_path, intermediate_path)
            else:
                raise UnsupportedFormatError(f"Unsupported input format: {input_format}")

            # Step 2: JSONL → Axolotl 형식
            self.convert_to_axolotl_format(
                intermediate_path,
                output_path,
                output_format
            )

            # Step 3: 통계 생성
            stats = self.generate_statistics(output_path, count_tokens=True)

            # Step 4: 검증 (선택)
            validation_errors = []
            if validate:
                # 간단한 검증: 샘플 수, 평균 길이
                if stats["total_samples"] < 10:
                    validation_errors.append("Dataset has less than 10 samples")

                if stats["avg_output_length"] < 10:
                    validation_errors.append("Average output length is too short")

            # 중간 파일 삭제
            Path(intermediate_path).unlink(missing_ok=True)

            return {
                "success": True,
                "output_path": output_path,
                "statistics": stats,
                "validation_errors": validation_errors
            }

        except Exception as e:
            logger.error(f"전처리 파이프라인 실패: {e}")
            raise PreprocessingError(f"Preprocessing pipeline failed: {str(e)}")
