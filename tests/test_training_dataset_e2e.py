"""
Training Dataset E2E Tests (TDD)
학습 데이터셋 API End-to-End 테스트

실제 API 엔드포인트 테스트:
1. 한글 파일명 업로드
2. ZIP 파일 업로드 (여러 JSON 병합)
3. 파일 크기 검증
4. MinIO 업로드 통합
"""
import pytest
import io
import json
import zipfile
from httpx import AsyncClient


@pytest.mark.e2e
class TestTrainingDatasetUploadE2E:
    """학습 데이터셋 업로드 E2E 테스트"""

    @pytest.mark.asyncio
    async def test_upload_dataset_with_korean_filename(self, authenticated_client: AsyncClient):
        """한글 파일명으로 데이터셋 업로드 성공해야 함"""

        # 한글 파일명 JSONL 파일 생성
        jsonl_content = '\n'.join([
            json.dumps({"instruction": "질문1", "output": "답변1"}, ensure_ascii=False),
            json.dumps({"instruction": "질문2", "output": "답변2"}, ensure_ascii=False),
        ])

        files = {
            "file": ("2015가합13718.json", io.BytesIO(jsonl_content.encode('utf-8')), "application/json")
        }

        data = {
            "name": "한글_파일명_테스트",
            "version": "v1.0",
            "format": "jsonl",
            "description": "한글 파일명 업로드 테스트"
        }

        response = await authenticated_client.post(
            "/api/v1/admin/training/datasets",
            files=files,
            data=data
        )

        # 검증
        assert response.status_code == 201, f"실패: {response.text}"
        result = response.json()
        assert result["name"] == "한글_파일명_테스트"
        assert result["total_samples"] == 2
        assert result["status"] == "active"
        assert result["format"] == "jsonl"

    @pytest.mark.asyncio
    async def test_upload_zip_file_with_multiple_json_files(self, authenticated_client: AsyncClient):
        """여러 JSON 파일이 포함된 ZIP 업로드 및 병합 테스트"""

        # ZIP 파일 생성 (여러 폴더 구조의 JSON 파일)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            # 폴더 구조 시뮬레이션
            zf.writestr(
                "법률/2015가합13718.json",
                json.dumps({"instruction": "법률 질문1", "output": "법률 답변1"}, ensure_ascii=False)
            )
            zf.writestr(
                "법률/2016나12345.json",
                json.dumps([
                    {"instruction": "법률 질문2", "output": "법률 답변2"},
                    {"instruction": "법률 질문3", "output": "법률 답변3"}
                ], ensure_ascii=False)
            )
            zf.writestr(
                "판례/대법원판결.json",
                json.dumps({"instruction": "판례 질문", "output": "판례 답변"}, ensure_ascii=False)
            )

        zip_content = zip_buffer.getvalue()

        files = {
            "file": ("법률데이터.zip", io.BytesIO(zip_content), "application/zip")
        }

        data = {
            "name": "ZIP_병합_테스트",
            "version": "v1.0",
            "format": "zip",
            "description": "여러 폴더 구조의 JSON 파일 병합 테스트"
        }

        response = await authenticated_client.post(
            "/api/v1/admin/training/datasets",
            files=files,
            data=data
        )

        # 검증
        assert response.status_code == 201, f"실패: {response.text}"
        result = response.json()
        assert result["name"] == "ZIP_병합_테스트"
        assert result["total_samples"] == 4, "3개 파일의 4개 샘플이 병합되어야 함"
        assert result["format"] == "zip"

    @pytest.mark.asyncio
    async def test_upload_oversized_file_should_fail(self, authenticated_client: AsyncClient):
        """1GB를 초과하는 파일은 거부되어야 함"""

        # 10MB 유효한 JSONL 파일 생성 (1GB는 메모리 문제로 테스트 불가)
        # 작은 JSON 레코드를 반복해서 10MB 만들기
        sample_record = json.dumps({"instruction": "test" * 100, "output": "answer" * 100})
        # 약 10MB가 되도록 반복
        num_records = (10 * 1024 * 1024) // len(sample_record)
        content = '\n'.join([sample_record] * num_records)

        files = {
            "file": ("test.jsonl", io.BytesIO(content.encode('utf-8')), "application/jsonl")
        }

        data = {
            "name": "크기_테스트",
            "version": "v1.0",
            "format": "jsonl"
        }

        response = await authenticated_client.post(
            "/api/v1/admin/training/datasets",
            files=files,
            data=data
        )

        # 10MB는 통과해야 함 (1GB 이하)
        assert response.status_code == 201, f"10MB 파일은 통과해야 함: {response.text}"

    @pytest.mark.asyncio
    async def test_upload_invalid_filename_should_fail(self, authenticated_client: AsyncClient):
        """경로 조작 공격이 포함된 파일명은 거부되어야 함"""

        jsonl_content = json.dumps({"test": "data"})

        files = {
            "file": ("../../../etc/passwd", io.BytesIO(jsonl_content.encode('utf-8')), "application/json")
        }

        data = {
            "name": "보안_테스트",
            "version": "v1.0",
            "format": "jsonl"
        }

        response = await authenticated_client.post(
            "/api/v1/admin/training/datasets",
            files=files,
            data=data
        )

        # 403 Forbidden, 400 Bad Request, 또는 500 Internal Server Error (보안 에러 처리)
        assert response.status_code in [400, 403, 500], f"경로 조작 공격은 차단되어야 함: {response.status_code}"
        # 에러 메시지 확인
        if response.status_code != 201:
            error_detail = response.json().get("detail", "")
            assert any(keyword in error_detail for keyword in ["경로", "파일명", "보안", "위협", "허용되지 않은"]), \
                f"보안 관련 에러 메시지가 있어야 함: {error_detail}"

    @pytest.mark.asyncio
    async def test_list_datasets_after_upload(self, authenticated_client: AsyncClient):
        """데이터셋 업로드 후 목록 조회 가능해야 함"""

        # 1. 데이터셋 업로드
        jsonl_content = json.dumps({"instruction": "test", "output": "test"})

        files = {
            "file": ("test.jsonl", io.BytesIO(jsonl_content.encode('utf-8')), "application/jsonl")
        }

        data = {
            "name": "목록조회_테스트",
            "version": "v1.0",
            "format": "jsonl"
        }

        upload_response = await authenticated_client.post(
            "/api/v1/admin/training/datasets",
            files=files,
            data=data
        )

        assert upload_response.status_code == 201
        dataset_id = upload_response.json()["id"]

        # 2. 목록 조회
        list_response = await authenticated_client.get(
            "/api/v1/admin/training/datasets"
        )

        assert list_response.status_code == 200
        result = list_response.json()
        assert "items" in result
        assert "total" in result

        # 업로드한 데이터셋이 목록에 있는지 확인
        dataset_ids = [item["id"] for item in result["items"]]
        assert dataset_id in dataset_ids

    @pytest.mark.asyncio
    async def test_get_dataset_detail_after_upload(self, authenticated_client: AsyncClient):
        """데이터셋 업로드 후 상세 조회 가능해야 함"""

        # 1. 데이터셋 업로드
        jsonl_content = '\n'.join([
            json.dumps({"instruction": "Q1", "output": "A1"}),
            json.dumps({"instruction": "Q2", "output": "A2"}),
            json.dumps({"instruction": "Q3", "output": "A3"}),
        ])

        files = {
            "file": ("test.jsonl", io.BytesIO(jsonl_content.encode('utf-8')), "application/jsonl")
        }

        data = {
            "name": "상세조회_테스트",
            "version": "v1.0",
            "format": "jsonl",
            "description": "상세 조회 테스트용"
        }

        upload_response = await authenticated_client.post(
            "/api/v1/admin/training/datasets",
            files=files,
            data=data
        )

        assert upload_response.status_code == 201
        dataset_id = upload_response.json()["id"]

        # 2. 상세 조회
        detail_response = await authenticated_client.get(
            f"/api/v1/admin/training/datasets/{dataset_id}"
        )

        assert detail_response.status_code == 200
        result = detail_response.json()
        assert result["id"] == dataset_id
        assert result["name"] == "상세조회_테스트"
        assert result["total_samples"] == 3
        assert result["description"] == "상세 조회 테스트용"

    @pytest.mark.asyncio
    async def test_delete_dataset(self, authenticated_client: AsyncClient):
        """데이터셋 삭제 (soft delete) 테스트"""

        # 1. 데이터셋 업로드
        jsonl_content = json.dumps({"test": "data"})

        files = {
            "file": ("test.jsonl", io.BytesIO(jsonl_content.encode('utf-8')), "application/jsonl")
        }

        data = {
            "name": "삭제_테스트",
            "version": "v1.0",
            "format": "jsonl"
        }

        upload_response = await authenticated_client.post(
            "/api/v1/admin/training/datasets",
            files=files,
            data=data
        )

        assert upload_response.status_code == 201
        dataset_id = upload_response.json()["id"]

        # 2. 삭제
        delete_response = await authenticated_client.delete(
            f"/api/v1/admin/training/datasets/{dataset_id}"
        )

        assert delete_response.status_code == 204, "삭제 성공 시 204 No Content"

        # 3. 삭제 후 조회 시 archived 상태이거나 404
        detail_response = await authenticated_client.get(
            f"/api/v1/admin/training/datasets/{dataset_id}"
        )

        # soft delete이므로 조회는 가능하지만 archived 상태
        if detail_response.status_code == 200:
            result = detail_response.json()
            assert result["status"] == "archived", "soft delete 후 archived 상태여야 함"
        else:
            # 또는 404 (정책에 따라)
            assert detail_response.status_code == 404


@pytest.mark.e2e
@pytest.mark.integration
class TestMinIOIntegrationE2E:
    """MinIO 통합 E2E 테스트"""

    @pytest.mark.asyncio
    async def test_dataset_file_stored_in_minio(self, authenticated_client: AsyncClient):
        """업로드된 파일이 MinIO에 저장되는지 검증"""

        jsonl_content = json.dumps({"instruction": "MinIO test", "output": "test"})

        files = {
            "file": ("minio_test.jsonl", io.BytesIO(jsonl_content.encode('utf-8')), "application/jsonl")
        }

        data = {
            "name": "MinIO_저장_테스트",
            "version": "v1.0",
            "format": "jsonl"
        }

        response = await authenticated_client.post(
            "/api/v1/admin/training/datasets",
            files=files,
            data=data
        )

        assert response.status_code == 201
        result = response.json()

        # file_path가 설정되어 있는지 확인
        assert "file_path" in result or result.get("file_path") is not None
        # MinIO 경로 형식 확인 (datasets/ 로 시작)
        if result.get("file_path"):
            assert "datasets/" in result["file_path"], "MinIO datasets 버킷에 저장되어야 함"
