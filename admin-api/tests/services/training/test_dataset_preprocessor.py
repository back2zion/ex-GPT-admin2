"""
Dataset Preprocessor Service Tests (TDD)
데이터셋 전처리 서비스 테스트

책임:
- CSV/Parquet → JSONL 변환
- JSONL → Axolotl 형식 변환
- 데이터셋 통계 생성

TDD Red Phase: 테스트 먼저 작성
"""
import pytest
import pandas as pd
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any

# TDD: 구현 완료 - import 활성화
from app.services.training.dataset_preprocessor import (
    DatasetPreprocessor,
    PreprocessingError,
    UnsupportedFormatError
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def preprocessor():
    """DatasetPreprocessor 인스턴스"""
    return DatasetPreprocessor()


@pytest.fixture
def sample_csv_file(tmp_path):
    """CSV 샘플 파일 생성"""
    csv_path = tmp_path / "sample.csv"
    df = pd.DataFrame({
        "instruction": ["What is Python?", "Explain machine learning"],
        "input": ["", ""],
        "output": ["Python is a programming language", "ML is a subset of AI"]
    })
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def sample_parquet_file(tmp_path):
    """Parquet 샘플 파일 생성"""
    parquet_path = tmp_path / "sample.parquet"
    df = pd.DataFrame({
        "instruction": ["Define AI", "What is NLP?"],
        "input": ["", ""],
        "output": ["AI is artificial intelligence", "NLP is natural language processing"]
    })
    df.to_parquet(parquet_path, index=False)
    return parquet_path


@pytest.fixture
def sample_jsonl_file(tmp_path):
    """JSONL 샘플 파일 생성"""
    jsonl_path = tmp_path / "sample.jsonl"
    samples = [
        {"instruction": "What is Docker?", "input": "", "output": "Docker is a containerization platform"},
        {"instruction": "Explain Kubernetes", "input": "", "output": "K8s is an orchestration tool"}
    ]
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    return jsonl_path


# ============================================================================
# Test Class: CSV 변환
# ============================================================================

class TestCSVConversion:
    """CSV 파일을 JSONL로 변환"""

    # Test activated
    def test_convert_csv_to_jsonl_success(self, preprocessor, sample_csv_file, tmp_path):
        """정상: CSV를 JSONL로 변환"""
        output_path = tmp_path / "output.jsonl"

        result_path = preprocessor.convert_csv_to_jsonl(
            csv_path=str(sample_csv_file),
            output_path=str(output_path)
        )

        assert Path(result_path).exists()

        # JSONL 파일 검증
        with open(result_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 2

            sample1 = json.loads(lines[0])
            assert sample1["instruction"] == "What is Python?"
            assert sample1["output"] == "Python is a programming language"

    # Test activated
    def test_convert_csv_missing_columns(self, preprocessor, tmp_path):
        """실패: 필수 컬럼 누락"""
        csv_path = tmp_path / "invalid.csv"
        df = pd.DataFrame({"question": ["What?"], "answer": ["Nothing"]})
        df.to_csv(csv_path, index=False)

        with pytest.raises(PreprocessingError, match="Missing required columns"):
            preprocessor.convert_csv_to_jsonl(str(csv_path), str(tmp_path / "out.jsonl"))

    # Test activated
    def test_convert_csv_empty_file(self, preprocessor, tmp_path):
        """실패: 빈 CSV 파일"""
        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("")

        with pytest.raises(PreprocessingError, match="Empty dataset"):
            preprocessor.convert_csv_to_jsonl(str(csv_path), str(tmp_path / "out.jsonl"))

    # Test activated
    def test_convert_csv_with_custom_columns(self, preprocessor, tmp_path):
        """정상: 커스텀 컬럼 매핑"""
        csv_path = tmp_path / "custom.csv"
        df = pd.DataFrame({
            "question": ["Q1", "Q2"],
            "context": ["", ""],
            "answer": ["A1", "A2"]
        })
        df.to_csv(csv_path, index=False)

        output_path = tmp_path / "output.jsonl"
        result_path = preprocessor.convert_csv_to_jsonl(
            csv_path=str(csv_path),
            output_path=str(output_path),
            column_mapping={"instruction": "question", "input": "context", "output": "answer"}
        )

        with open(result_path, 'r', encoding='utf-8') as f:
            sample = json.loads(f.readline())
            assert sample["instruction"] == "Q1"
            assert sample["output"] == "A1"


# ============================================================================
# Test Class: Parquet 변환
# ============================================================================

class TestParquetConversion:
    """Parquet 파일을 JSONL로 변환"""

    # Test activated
    def test_convert_parquet_to_jsonl_success(self, preprocessor, sample_parquet_file, tmp_path):
        """정상: Parquet를 JSONL로 변환"""
        output_path = tmp_path / "output.jsonl"

        result_path = preprocessor.convert_parquet_to_jsonl(
            parquet_path=str(sample_parquet_file),
            output_path=str(output_path)
        )

        assert Path(result_path).exists()

        with open(result_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 2

            sample1 = json.loads(lines[0])
            assert sample1["instruction"] == "Define AI"

    # Test activated
    def test_convert_parquet_corrupted_file(self, preprocessor, tmp_path):
        """실패: 손상된 Parquet 파일"""
        parquet_path = tmp_path / "corrupted.parquet"
        parquet_path.write_bytes(b"not a parquet file")

        with pytest.raises(PreprocessingError, match="Failed to read Parquet"):
            preprocessor.convert_parquet_to_jsonl(str(parquet_path), str(tmp_path / "out.jsonl"))


# ============================================================================
# Test Class: Axolotl 형식 변환
# ============================================================================

class TestAxolotlFormatConversion:
    """JSONL을 Axolotl 형식으로 변환"""

    # Test activated
    def test_convert_to_axolotl_alpaca_format(self, preprocessor, sample_jsonl_file, tmp_path):
        """정상: Alpaca 형식으로 변환"""
        output_path = tmp_path / "axolotl_alpaca.jsonl"

        result_path = preprocessor.convert_to_axolotl_format(
            jsonl_path=str(sample_jsonl_file),
            output_path=str(output_path),
            format_type="alpaca"
        )

        with open(result_path, 'r', encoding='utf-8') as f:
            sample = json.loads(f.readline())
            # Alpaca 형식: instruction, input, output
            assert "instruction" in sample
            assert "input" in sample
            assert "output" in sample

    # Test activated
    def test_convert_to_axolotl_sharegpt_format(self, preprocessor, sample_jsonl_file, tmp_path):
        """정상: ShareGPT 형식으로 변환"""
        output_path = tmp_path / "axolotl_sharegpt.jsonl"

        result_path = preprocessor.convert_to_axolotl_format(
            jsonl_path=str(sample_jsonl_file),
            output_path=str(output_path),
            format_type="sharegpt"
        )

        with open(result_path, 'r', encoding='utf-8') as f:
            sample = json.loads(f.readline())
            # ShareGPT 형식: conversations
            assert "conversations" in sample
            assert isinstance(sample["conversations"], list)
            assert sample["conversations"][0]["from"] == "human"
            assert sample["conversations"][1]["from"] == "gpt"

    # Test activated
    def test_convert_to_axolotl_unsupported_format(self, preprocessor, sample_jsonl_file, tmp_path):
        """실패: 지원하지 않는 형식"""
        with pytest.raises(UnsupportedFormatError, match="Unsupported format"):
            preprocessor.convert_to_axolotl_format(
                str(sample_jsonl_file),
                str(tmp_path / "out.jsonl"),
                format_type="unknown"
            )


# ============================================================================
# Test Class: 데이터셋 통계
# ============================================================================

class TestDatasetStatistics:
    """데이터셋 통계 생성"""

    # Test activated
    def test_generate_statistics(self, preprocessor, sample_jsonl_file):
        """정상: 데이터셋 통계 생성"""
        stats = preprocessor.generate_statistics(str(sample_jsonl_file))

        assert stats["total_samples"] == 2
        assert stats["avg_instruction_length"] > 0
        assert stats["avg_output_length"] > 0
        assert "token_distribution" in stats
        assert "sample_examples" in stats
        assert len(stats["sample_examples"]) <= 5

    # Test activated
    def test_generate_statistics_with_token_count(self, preprocessor, sample_jsonl_file):
        """정상: 토큰 수 포함 통계"""
        stats = preprocessor.generate_statistics(
            str(sample_jsonl_file),
            count_tokens=True
        )

        assert "avg_tokens_per_sample" in stats
        assert "total_tokens" in stats
        assert stats["total_tokens"] > 0

    # Test activated
    def test_generate_statistics_empty_dataset(self, preprocessor, tmp_path):
        """실패: 빈 데이터셋"""
        empty_path = tmp_path / "empty.jsonl"
        empty_path.write_text("")

        with pytest.raises(PreprocessingError, match="Empty dataset"):
            preprocessor.generate_statistics(str(empty_path))


# ============================================================================
# Test Class: 통합 파이프라인
# ============================================================================

class TestPreprocessingPipeline:
    """전처리 파이프라인 통합 테스트"""

    # Test activated
    def test_full_preprocessing_pipeline_csv(self, preprocessor, sample_csv_file, tmp_path):
        """정상: CSV → JSONL → Axolotl 전체 파이프라인"""
        # Step 1: CSV → JSONL
        jsonl_path = tmp_path / "intermediate.jsonl"
        preprocessor.convert_csv_to_jsonl(str(sample_csv_file), str(jsonl_path))

        # Step 2: JSONL → Axolotl
        axolotl_path = tmp_path / "axolotl.jsonl"
        preprocessor.convert_to_axolotl_format(str(jsonl_path), str(axolotl_path), "alpaca")

        # Step 3: 통계 생성
        stats = preprocessor.generate_statistics(str(axolotl_path))

        assert stats["total_samples"] == 2
        assert Path(axolotl_path).exists()

    # Test activated
    def test_preprocess_with_validation(self, preprocessor, tmp_path):
        """정상: 검증 포함 전처리 (충분한 샘플)"""
        # 10개 이상의 샘플로 CSV 생성
        csv_path = tmp_path / "large_sample.csv"
        df = pd.DataFrame({
            "instruction": [f"Question {i}" for i in range(15)],
            "input": ["" for _ in range(15)],
            "output": [f"Answer {i} with sufficient length to pass validation" for i in range(15)]
        })
        df.to_csv(csv_path, index=False)

        output_path = tmp_path / "validated.jsonl"

        result = preprocessor.preprocess_dataset(
            input_path=str(csv_path),
            output_path=str(output_path),
            input_format="csv",
            output_format="alpaca",
            validate=True
        )

        assert result["success"] is True
        assert result["output_path"] == str(output_path)
        assert "statistics" in result
        assert "validation_errors" in result
        assert len(result["validation_errors"]) == 0


# ============================================================================
# Test Class: 시큐어 코딩
# ============================================================================

class TestSecurityValidation:
    """시큐어 코딩: 입력 검증 및 보안"""

    # Test activated
    def test_reject_large_file(self, preprocessor, tmp_path):
        """시큐어: 대용량 파일 거부 (DoS 방지)"""
        # 작은 파일을 만들고 max_file_size를 더 작게 설정
        csv_path = tmp_path / "small.csv"
        df = pd.DataFrame({
            "instruction": ["test"],
            "output": ["test output"]
        })
        df.to_csv(csv_path, index=False)

        # 파일 크기보다 작은 limit 설정 (1 byte)
        with pytest.raises(PreprocessingError, match="File size exceeds limit"):
            preprocessor.convert_csv_to_jsonl(
                str(csv_path),
                str(tmp_path / "out.jsonl"),
                max_file_size=1  # 1 byte로 제한
            )

    # Test activated
    def test_sanitize_output_paths(self, preprocessor, sample_csv_file):
        """시큐어: 경로 조작 공격 방지"""
        with pytest.raises(PreprocessingError, match="Invalid output path"):
            preprocessor.convert_csv_to_jsonl(
                str(sample_csv_file),
                "../../../etc/passwd"
            )

    # Test activated
    def test_handle_malformed_jsonl_gracefully(self, preprocessor, tmp_path):
        """정상: 손상된 JSONL 처리"""
        malformed_path = tmp_path / "malformed.jsonl"
        with open(malformed_path, 'w') as f:
            f.write('{"valid": "json"}\n')
            f.write('invalid json line\n')
            f.write('{"another": "valid"}\n')

        stats = preprocessor.generate_statistics(
            str(malformed_path),
            skip_invalid=True
        )

        # 유효한 2개만 카운트
        assert stats["total_samples"] == 2
        assert stats["invalid_samples"] == 1
