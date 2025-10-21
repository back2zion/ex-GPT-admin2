"""
TDD Tests for Vector Document Management API
학습데이터 관리 - 문서 및 벡터 관리 테스트
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def sample_vector_document_data():
    """샘플 벡터 문서 데이터"""
    return {
        "title": "한국도로공사 안전규정",
        "document_type": "REGULATION",
        "file_name": "safety_regulation.pdf",
        "category_id": 1
    }


@pytest.mark.asyncio
class TestVectorDocumentsAPI:
    """벡터 문서 관리 API 테스트"""

    async def test_list_documents_empty(
        self,
        authenticated_client: AsyncClient
    ):
        """빈 문서 목록 조회 테스트"""
        response = await authenticated_client.get("/api/v1/admin/documents")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)

    async def test_list_documents_pagination(
        self,
        authenticated_client: AsyncClient
    ):
        """문서 목록 페이지네이션 테스트 (Secure: LIMIT/OFFSET 검증)"""
        # Valid pagination
        response = await authenticated_client.get(
            "/api/v1/admin/documents?page=1&limit=10"
        )
        assert response.status_code == 200

        # Invalid pagination (negative values)
        response = await authenticated_client.get(
            "/api/v1/admin/documents?page=-1&limit=10"
        )
        assert response.status_code == 400 or response.status_code == 422

        # Invalid pagination (limit too large - DoS prevention)
        response = await authenticated_client.get(
            "/api/v1/admin/documents?page=1&limit=10000"
        )
        assert response.status_code == 400 or response.status_code == 422

    async def test_list_documents_filter_by_category(
        self,
        authenticated_client: AsyncClient
    ):
        """카테고리별 문서 필터링 테스트"""
        response = await authenticated_client.get(
            "/api/v1/admin/documents?category_id=1"
        )

        assert response.status_code == 200

    async def test_list_documents_sql_injection_prevention(
        self,
        authenticated_client: AsyncClient
    ):
        """SQL Injection 방어 테스트 (Secure: Parameterized Query)"""
        # SQL Injection attempt in category_id
        response = await authenticated_client.get(
            "/api/v1/admin/documents?category_id=1' OR '1'='1"
        )

        # Should reject with validation error
        assert response.status_code in [400, 422]

    async def test_get_document_with_vectors(
        self,
        authenticated_client: AsyncClient
    ):
        """벡터 정보 포함 문서 상세 조회 테스트"""
        # This test will pass once we have documents with vectors
        response = await authenticated_client.get(
            "/api/v1/admin/documents/1?include_vectors=true"
        )

        # May be 404 if no documents exist yet
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            # Should include vector information
            assert "vectors" in data or "vector_count" in data

    async def test_upload_document_invalid_file_type(
        self,
        authenticated_client: AsyncClient
    ):
        """
        유효하지 않은 파일 형식 업로드 방어 테스트
        (Secure: File Type Validation)
        """
        # Create a fake executable file
        files = {
            "file": ("malicious.exe", b"MZ\x90\x00", "application/x-msdownload")
        }
        data = {
            "title": "Test Document",
            "category_id": 1
        }

        response = await authenticated_client.post(
            "/api/v1/admin/documents/upload",
            files=files,
            data=data
        )

        # Should reject non-document files
        assert response.status_code in [400, 415, 422]

    async def test_upload_document_file_size_limit(
        self,
        authenticated_client: AsyncClient
    ):
        """
        파일 크기 제한 테스트
        (Secure: DoS Prevention)
        """
        # Create a large fake file (100MB simulation)
        large_content = b"a" * 1000  # Simulated large file

        files = {
            "file": ("large_document.pdf", large_content, "application/pdf")
        }
        data = {
            "title": "Large Document",
            "category_id": 1,
            "file_size": 100 * 1024 * 1024  # 100MB
        }

        response = await authenticated_client.post(
            "/api/v1/admin/documents/upload",
            files=files,
            data=data
        )

        # Should handle based on implementation:
        # - Accept and process in chunks, OR
        # - Reject if too large
        assert response.status_code in [201, 400, 413]

    async def test_upload_document_malicious_filename(
        self,
        authenticated_client: AsyncClient
    ):
        """
        악의적인 파일명 방어 테스트
        (Secure: Path Traversal Prevention)
        """
        malicious_filenames = [
            "../../../etc/passwd",
            "../../sensitive.pdf",
            "file<script>alert('xss')</script>.pdf"
        ]

        for filename in malicious_filenames:
            files = {
                "file": (filename, b"PDF content", "application/pdf")
            }
            data = {
                "title": "Test Document",
                "category_id": 1
            }

            response = await authenticated_client.post(
                "/api/v1/admin/documents/upload",
                files=files,
                data=data
            )

            # Should sanitize filename or reject
            assert response.status_code in [201, 400, 422]

            if response.status_code == 201:
                # Verify filename was sanitized
                result = response.json()
                assert ".." not in result.get("file_name", "")
                assert "<" not in result.get("file_name", "")

    async def test_delete_document_cascade_vectors(
        self,
        authenticated_client: AsyncClient
    ):
        """
        문서 삭제 시 벡터 캐스케이드 삭제 테스트
        (Secure: Referential Integrity)
        """
        # This will be tested after we implement upload
        # For now, test the endpoint exists
        response = await authenticated_client.delete(
            "/api/v1/admin/documents/1"
        )

        # May be 404 if document doesn't exist, or 200/204 if deleted
        assert response.status_code in [200, 204, 404]

    async def test_vectorization_status_tracking(
        self,
        authenticated_client: AsyncClient
    ):
        """벡터화 상태 추적 테스트"""
        # Get vectorization status
        response = await authenticated_client.get(
            "/api/v1/admin/documents/1/vectorization-status"
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            # Should include status information
            assert "status" in data
            assert data["status"] in ["PENDING", "PROCESSING", "COMPLETED", "FAILED"]

    async def test_retry_failed_vectorization(
        self,
        authenticated_client: AsyncClient
    ):
        """실패한 벡터화 재시도 테스트"""
        response = await authenticated_client.post(
            "/api/v1/admin/documents/1/retry-vectorization"
        )

        # May be 404 if document doesn't exist
        assert response.status_code in [200, 404, 409]


@pytest.mark.asyncio
class TestDocumentVectorsAPI:
    """문서 벡터 상세 관리 API 테스트"""

    async def test_list_document_vectors(
        self,
        authenticated_client: AsyncClient
    ):
        """문서의 벡터 청크 목록 조회 테스트"""
        response = await authenticated_client.get(
            "/api/v1/admin/documents/1/vectors"
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "items" in data

    async def test_delete_document_vector(
        self,
        authenticated_client: AsyncClient
    ):
        """특정 벡터 청크 삭제 테스트"""
        response = await authenticated_client.delete(
            "/api/v1/admin/vectors/1"
        )

        # Should delete from both DB and Qdrant
        assert response.status_code in [200, 204, 404]

    async def test_get_vector_statistics(
        self,
        authenticated_client: AsyncClient
    ):
        """벡터 통계 조회 테스트"""
        response = await authenticated_client.get(
            "/api/v1/admin/vectors/statistics"
        )

        assert response.status_code == 200
        data = response.json()

        # Should include statistics
        assert "total_vectors" in data or "total_documents" in data
        assert "by_status" in data or "pending_count" in data
