"""
STT 배치 처리 시스템 테스트
TDD 방식: 테스트 먼저 작성, 코드 나중에 구현
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.stt import STTBatch, STTTranscription, STTSummary, STTEmailLog


class TestSTTBatchModel:
    """STT 배치 모델 테스트"""

    @pytest.mark.asyncio
    async def test_create_batch_with_valid_data(self, db_session: AsyncSession):
        """정상 데이터로 배치 생성 테스트"""
        batch = STTBatch(
            name="2024년 12월 총무처 회의록",
            description="총무처 정기 회의 음성파일 500만건",
            source_path="s3://audio-files/2024-12/",
            file_pattern="*.mp3",
            total_files=5000000,
            status="pending",
            priority="high",
            created_by="admin"
        )
        db_session.add(batch)
        await db_session.commit()
        await db_session.refresh(batch)

        assert batch.id is not None
        assert batch.name == "2024년 12월 총무처 회의록"
        assert batch.status == "pending"
        assert batch.total_files == 5000000

    @pytest.mark.asyncio
    async def test_create_batch_with_invalid_path(self, db_session: AsyncSession):
        """잘못된 파일 경로로 배치 생성 시 실패 (Path Traversal 방지)"""
        from app.services.stt_service import STTService

        stt_service = STTService()

        # Path Traversal 시도
        with pytest.raises(ValueError, match="Invalid file path"):
            await stt_service.create_batch(
                name="악의적 배치",
                source_path="../../etc/passwd",  # 🔴 Path Traversal 시도
                file_pattern="*",
                created_by="attacker"
            )

    @pytest.mark.asyncio
    async def test_batch_progress_calculation(self, db_session: AsyncSession):
        """진행률 계산 정확도 테스트"""
        batch = STTBatch(
            name="테스트 배치",
            source_path="s3://test/",
            total_files=1000,
            status="processing",
            created_by="admin"
        )
        db_session.add(batch)
        await db_session.commit()
        await db_session.refresh(batch)

        # 500개 전사 완료
        for i in range(500):
            transcription = STTTranscription(
                batch_id=batch.id,
                audio_file_path=f"s3://test/file_{i}.mp3",
                transcription_text=f"테스트 전사 {i}",
                status="success"
            )
            db.add(transcription)
        await db.commit()

        # 진행률 계산
        from app.services.stt_service import STTService
        progress = await STTService().get_batch_progress(batch.id, db)

        assert progress["total_files"] == 1000
        assert progress["completed"] == 500
        assert progress["progress_percentage"] == 50.0


class TestSTTTranscription:
    """STT 전사 모델 테스트"""

    @pytest.mark.asyncio
    async def test_create_transcription_with_valid_data(self, db_session: AsyncSession):
        """정상 데이터로 전사 생성 테스트"""
        # 배치 먼저 생성
        batch = STTBatch(
            name="테스트 배치",
            source_path="s3://test/",
            total_files=100,
            status="processing",
            created_by="admin"
        )
        db_session.add(batch)
        await db_session.commit()
        await db_session.refresh(batch)

        # 전사 생성
        transcription = STTTranscription(
            batch_id=batch.id,
            audio_file_path="s3://test/meeting_001.mp3",
            audio_file_size=10485760,  # 10MB
            audio_duration=600.0,  # 10분
            transcription_text="안녕하세요. 오늘 회의를 시작하겠습니다.",
            transcription_confidence=0.95,
            language_code="ko-KR",
            stt_engine="whisper-large-v3",
            status="success"
        )
        db.add(transcription)
        await db.commit()
        await db.refresh(transcription)

        assert transcription.id is not None
        assert transcription.batch_id == batch.id
        assert transcription.transcription_confidence == 0.95
        assert transcription.status == "success"

    @pytest.mark.asyncio
    async def test_transcription_with_speaker_diarization(self, db_session: AsyncSession):
        """화자 분리 데이터가 포함된 전사 테스트"""
        batch = STTBatch(
            name="테스트 배치",
            source_path="s3://test/",
            total_files=100,
            status="processing",
            created_by="admin"
        )
        db_session.add(batch)
        await db_session.commit()
        await db_session.refresh(batch)

        # 화자 분리 정보 포함
        speaker_labels = {
            "speaker_1": "홍길동",
            "speaker_2": "김철수"
        }
        segments = [
            {"start": 0.0, "end": 5.2, "speaker": "speaker_1", "text": "안녕하세요"},
            {"start": 5.3, "end": 10.1, "speaker": "speaker_2", "text": "반갑습니다"}
        ]

        transcription = STTTranscription(
            batch_id=batch.id,
            audio_file_path="s3://test/meeting_002.mp3",
            transcription_text="안녕하세요 반갑습니다",
            speaker_labels=speaker_labels,
            segments=segments,
            status="success"
        )
        db.add(transcription)
        await db.commit()
        await db.refresh(transcription)

        assert transcription.speaker_labels is not None
        assert len(transcription.segments) == 2
        assert transcription.segments[0]["speaker"] == "speaker_1"


class TestSTTSummary:
    """STT 요약 모델 테스트"""

    @pytest.mark.asyncio
    async def test_create_summary_with_llm(self, db_session: AsyncSession):
        """LLM으로 요약 생성 테스트"""
        # 배치 및 전사 먼저 생성
        batch = STTBatch(
            name="테스트 배치",
            source_path="s3://test/",
            total_files=10,
            status="processing",
            created_by="admin"
        )
        db.add(batch)
        await db.commit()

        transcription = STTTranscription(
            batch_id=batch.id,
            audio_file_path="s3://test/meeting_003.mp3",
            transcription_text="회의 내용이 길게 전사된 텍스트입니다...",
            status="success"
        )
        db.add(transcription)
        await db.commit()
        await db.refresh(transcription)

        # 요약 생성
        summary = STTSummary(
            transcription_id=transcription.id,
            summary_text="1. 회의 개요\n2. 주요 논의 사항\n3. 결정 사항",
            summary_level="normal",
            keywords=["예산", "인사", "프로젝트"],
            action_items=[
                {"task": "보고서 제출", "assignee": "홍길동", "due_date": "2025-11-01"}
            ],
            llm_model="gpt-4-turbo",
            tokens_used=2500
        )
        db.add(summary)
        await db.commit()
        await db.refresh(summary)

        assert summary.id is not None
        assert summary.transcription_id == transcription.id
        assert len(summary.keywords) == 3
        assert summary.action_items[0]["assignee"] == "홍길동"


class TestSTTEmailLog:
    """STT 이메일 로그 모델 테스트"""

    @pytest.mark.asyncio
    async def test_email_validation(self, db_session: AsyncSession):
        """이메일 주소 검증 테스트 (Email Injection 방지)"""
        from app.services.email_service import EmailService

        email_service = EmailService()

        # 정상 이메일
        valid_email = "admin@ex.co.kr"
        assert email_service.validate_email(valid_email) is True

        # 악의적 이메일 (SMTP Injection 시도)
        malicious_emails = [
            "attacker@ex.co.kr\nBcc: spam@evil.com",  # 🔴 Newline injection
            "admin@ex.co.kr\r\nTo: spam@evil.com",    # 🔴 CRLF injection
            "'; DROP TABLE users; --@ex.co.kr"        # 🔴 SQL Injection 시도
        ]

        for bad_email in malicious_emails:
            assert email_service.validate_email(bad_email) is False

    @pytest.mark.asyncio
    async def test_email_send_tracking(self, db_session: AsyncSession):
        """이메일 송출 추적 테스트"""
        # 요약 생성
        batch = STTBatch(
            name="테스트 배치",
            source_path="s3://test/",
            total_files=10,
            status="processing",
            created_by="admin"
        )
        db.add(batch)
        await db.commit()

        transcription = STTTranscription(
            batch_id=batch.id,
            audio_file_path="s3://test/meeting.mp3",
            transcription_text="회의 내용",
            status="success"
        )
        db.add(transcription)
        await db.commit()

        summary = STTSummary(
            transcription_id=transcription.id,
            summary_text="요약 내용",
            llm_model="gpt-4-turbo"
        )
        db.add(summary)
        await db.commit()
        await db.refresh(summary)

        # 이메일 로그 생성
        email_log = STTEmailLog(
            summary_id=summary.id,
            recipient_email="hong@ex.co.kr",
            recipient_name="홍길동",
            cc_emails=["kim@ex.co.kr", "park@ex.co.kr"],
            subject="[회의록] 테스트 회의 - 2025-10-21",
            status="sent",
            sent_at=datetime.utcnow(),
            delivery_status="delivered",
            email_provider="aws-ses",
            message_id="msg_12345"
        )
        db.add(email_log)
        await db.commit()
        await db.refresh(email_log)

        assert email_log.id is not None
        assert email_log.status == "sent"
        assert len(email_log.cc_emails) == 2
        assert email_log.message_id == "msg_12345"


class TestSecurityValidation:
    """시큐어 코딩 검증 테스트"""

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, db_session: AsyncSession):
        """SQL Injection 방어 테스트"""
        from app.services.stt_service import STTService

        stt_service = STTService()

        # SQL Injection 시도
        malicious_input = "'; DROP TABLE stt_batches; --"

        # 정상적으로 파라미터화된 쿼리 사용 시 안전
        batches = await stt_service.search_batches(
            name=malicious_input,
            db=db_session
        )

        # 테이블이 삭제되지 않고 빈 결과 반환
        assert batches == []

    @pytest.mark.asyncio
    async def test_path_traversal_prevention(self, db_session: AsyncSession):
        """Path Traversal 방어 테스트"""
        from app.services.stt_service import STTService

        stt_service = STTService()

        # Path Traversal 시도 목록
        malicious_paths = [
            "../../etc/passwd",
            "../../../../../etc/shadow",
            "s3://bucket/../../../etc/passwd",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\sam"
        ]

        for bad_path in malicious_paths:
            with pytest.raises(ValueError, match="Invalid file path"):
                await stt_service.create_batch(
                    name="test",
                    source_path=bad_path,
                    file_pattern="*",
                    created_by="attacker"
                )

    @pytest.mark.asyncio
    async def test_file_size_limit(self, db_session: AsyncSession):
        """파일 크기 제한 테스트 (DoS 방지)"""
        from app.services.stt_service import STTService

        stt_service = STTService()

        # 1GB 초과 파일 거부
        with pytest.raises(ValueError, match="File size exceeds limit"):
            await stt_service.process_audio_file(
                file_path="s3://test/huge_file.mp3",
                file_size=1073741825,  # 1GB + 1 byte (🔴 제한 초과)
                batch_id=1
            )
