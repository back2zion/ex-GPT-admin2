"""
STT API 엔드포인트 테스트 (TDD Red Phase)
테스트 먼저 작성 → 실패 확인 → 구현 → 통과
"""
import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.stt import STTBatch, STTTranscription


class TestSTTBatchAPI:
    """STT 배치 API 테스트"""

    @pytest.mark.asyncio
    async def test_create_batch(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        배치 생성 API 테스트

        Given: 유효한 배치 데이터
        When: POST /api/v1/admin/stt-batches 호출
        Then: 201 Created, 배치 생성됨
        """
        # Given
        batch_data = {
            "name": "2024년 12월 총무처 회의록",
            "description": "총무처 정기 회의 음성파일 500만건",
            "source_path": "s3://audio-files/2024-12/",
            "file_pattern": "*.mp3",
            "priority": "high"
        }

        # When
        response = await authenticated_client.post(
            "/api/v1/admin/stt-batches",
            json=batch_data
        )

        # Then
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == batch_data["name"]
        assert data["source_path"] == batch_data["source_path"]
        assert data["status"] == "pending"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_batch_with_invalid_path(
        self,
        authenticated_client: AsyncClient
    ):
        """
        잘못된 경로로 배치 생성 시 실패

        Given: Path Traversal 시도 경로
        When: POST /api/v1/admin/stt-batches 호출
        Then: 400 Bad Request
        """
        # Given
        batch_data = {
            "name": "악의적 배치",
            "source_path": "../../etc/passwd",  # Path Traversal
            "file_pattern": "*"
        }

        # When
        response = await authenticated_client.post(
            "/api/v1/admin/stt-batches",
            json=batch_data
        )

        # Then
        assert response.status_code == 400
        data = response.json()
        assert "Invalid file path" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_batch(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        배치 상세 조회 API 테스트

        Given: 생성된 배치
        When: GET /api/v1/admin/stt-batches/{id} 호출
        Then: 200 OK, 배치 정보 반환
        """
        # Given: 배치 생성
        batch = STTBatch(
            name="테스트 배치",
            source_path="s3://test/",
            total_files=100,
            status="pending",
            created_by="admin"
        )
        db_session.add(batch)
        await db_session.commit()
        await db_session.refresh(batch)

        # When
        response = await authenticated_client.get(
            f"/api/v1/admin/stt-batches/{batch.id}"
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == batch.id
        assert data["name"] == "테스트 배치"

    @pytest.mark.asyncio
    async def test_get_batch_not_found(
        self,
        authenticated_client: AsyncClient
    ):
        """
        존재하지 않는 배치 조회

        Given: 존재하지 않는 배치 ID
        When: GET /api/v1/admin/stt-batches/{id} 호출
        Then: 404 Not Found
        """
        # When
        response = await authenticated_client.get(
            "/api/v1/admin/stt-batches/99999"
        )

        # Then
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_batches(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        배치 목록 조회 API 테스트

        Given: 여러 배치 생성
        When: GET /api/v1/admin/stt-batches 호출
        Then: 200 OK, 배치 목록 반환
        """
        # Given: 배치 3개 생성
        for i in range(3):
            batch = STTBatch(
                name=f"테스트 배치 {i}",
                source_path="s3://test/",
                total_files=100,
                status="pending",
                created_by="admin"
            )
            db_session.add(batch)
        await db_session.commit()

        # When
        response = await authenticated_client.get(
            "/api/v1/admin/stt-batches"
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 3

    @pytest.mark.asyncio
    async def test_get_batch_progress(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        배치 진행 상황 조회 API 테스트

        Given: 진행 중인 배치 (일부 전사 완료)
        When: GET /api/v1/admin/stt-batches/{id}/progress 호출
        Then: 200 OK, 진행 상황 정보 반환
        """
        # Given: 배치 생성
        batch = STTBatch(
            name="진행 중 배치",
            source_path="s3://test/",
            total_files=100,
            status="processing",
            created_by="admin"
        )
        db_session.add(batch)
        await db_session.commit()
        await db_session.refresh(batch)

        # 50개 완료
        for i in range(50):
            unique_id = uuid.uuid4().hex[:8]
            transcription = STTTranscription(
                batch_id=batch.id,
                audio_file_path=f"s3://test/progress_{unique_id}_{i}.mp3",
                transcription_text=f"전사 {i}",
                status="success"
            )
            db_session.add(transcription)
        await db_session.commit()

        # When
        response = await authenticated_client.get(
            f"/api/v1/admin/stt-batches/{batch.id}/progress"
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["batch_id"] == batch.id
        assert data["total_files"] == 100
        assert data["completed"] == 50
        assert data["progress_percentage"] == 50.0


class TestSTTBatchSecurity:
    """STT 배치 보안 테스트"""

    @pytest.mark.asyncio
    async def test_batch_requires_authentication(
        self,
        client: AsyncClient
    ):
        """
        인증 없이 배치 조회 불가

        Given: 인증되지 않은 요청
        When: GET /api/v1/admin/stt-batches 호출
        Then: 401 Unauthorized
        """
        # When
        response = await client.get("/api/v1/admin/stt-batches")

        # Then
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_sql_injection_in_list_batches(
        self,
        authenticated_client: AsyncClient
    ):
        """
        SQL Injection 방어 테스트 (목록 조회)

        Given: SQL Injection 시도 검색어
        When: GET /api/v1/admin/stt-batches?name=... 호출
        Then: 안전하게 처리됨 (빈 결과 또는 정상 응답)
        """
        # Given
        malicious_name = "'; DROP TABLE stt_batches; --"

        # When
        response = await authenticated_client.get(
            "/api/v1/admin/stt-batches",
            params={"name": malicious_name}
        )

        # Then
        assert response.status_code == 200
        # 테이블이 삭제되지 않고 정상 응답
        data = response.json()
        assert "items" in data


class TestSTTBatchPagination:
    """STT 배치 페이지네이션 테스트"""

    @pytest.mark.asyncio
    async def test_list_batches_with_pagination(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        페이지네이션 테스트

        Given: 20개 배치 생성
        When: GET /api/v1/admin/stt-batches?limit=10 호출
        Then: 최대 10개만 반환
        """
        # Given: 20개 배치 생성
        for i in range(20):
            batch = STTBatch(
                name=f"페이지네이션 배치 {i}",
                source_path="s3://test/",
                total_files=10,
                status="pending",
                created_by="admin"
            )
            db_session.add(batch)
        await db_session.commit()

        # When
        response = await authenticated_client.get(
            "/api/v1/admin/stt-batches",
            params={"limit": 10}
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 10
