"""
Tests for chat_service.py
채팅 비즈니스 로직 테스트
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.services.chat_service import (
    validate_room_id,
    create_room,
    save_question,
    save_answer,
    save_reference_documents,
    count_tokens
)


@pytest_asyncio.fixture
async def test_user_room(db_session: AsyncSession):
    """테스트용 대화방 생성"""
    from app.utils.room_id_generator import generate_room_id

    user_id = "test_user_service"
    room_id = generate_room_id(user_id)
    first_question = "테스트 질문입니다"

    # 대화방 생성
    created_room_id = await create_room(db_session, room_id, user_id, first_question)
    await db_session.commit()

    yield {
        "room_id": created_room_id,
        "user_id": user_id
    }

    # Cleanup은 db_session fixture가 rollback으로 처리


class TestValidateRoomId:
    """Room ID 검증 테스트"""

    @pytest.mark.asyncio
    async def test_validate_valid_room_id(self, db_session: AsyncSession, test_user_room):
        """올바른 Room ID 검증 테스트"""
        room_id = test_user_room["room_id"]
        user_id = test_user_room["user_id"]

        is_valid = await validate_room_id(room_id, user_id, db_session)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_invalid_room_id(self, db_session: AsyncSession):
        """존재하지 않는 Room ID 검증 테스트"""
        is_valid = await validate_room_id("nonexistent_room", "test_user", db_session)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_wrong_user(self, db_session: AsyncSession, test_user_room):
        """다른 사용자가 Room ID 접근 시도 테스트"""
        room_id = test_user_room["room_id"]
        wrong_user = "wrong_user"

        is_valid = await validate_room_id(room_id, wrong_user, db_session)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_empty_room_id(self, db_session: AsyncSession):
        """빈 Room ID 검증 테스트"""
        is_valid = await validate_room_id("", "test_user", db_session)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_deleted_room(self, db_session: AsyncSession, test_user_room):
        """삭제된(USE_YN='N') Room ID 검증 테스트"""
        room_id = test_user_room["room_id"]
        user_id = test_user_room["user_id"]

        # Room을 삭제 (USE_YN = 'N')
        await db_session.execute(
            text("""
            UPDATE "USR_CNVS_SMRY"
            SET "USE_YN" = 'N'
            WHERE "CNVS_IDT_ID" = :room_id
            """),
            {"room_id": room_id}
        )
        await db_session.commit()

        # 검증
        is_valid = await validate_room_id(room_id, user_id, db_session)
        assert is_valid is False


class TestCreateRoom:
    """대화방 생성 테스트"""

    @pytest.mark.asyncio
    async def test_create_room_success(self, db_session: AsyncSession):
        """대화방 생성 성공 테스트"""
        from app.utils.room_id_generator import generate_room_id

        user_id = "create_test_user"
        room_id = generate_room_id(user_id)
        first_question = "처음 질문입니다"

        created_room_id = await create_room(db_session, room_id, user_id, first_question)

        assert created_room_id == room_id

        # DB에서 확인
        result = await db_session.execute(
            text("""
            SELECT "CNVS_SMRY_TXT", "USR_ID", "USE_YN"
            FROM "USR_CNVS_SMRY"
            WHERE "CNVS_IDT_ID" = :room_id
            """),
            {"room_id": room_id}
        )
        row = result.fetchone()

        assert row is not None
        assert row[1] == user_id  # USR_ID
        assert row[2] == "Y"  # USE_YN

    @pytest.mark.asyncio
    async def test_create_room_long_question_truncation(self, db_session: AsyncSession):
        """긴 질문이 50자로 잘리는지 테스트"""
        from app.utils.room_id_generator import generate_room_id

        user_id = "truncate_test_user"
        room_id = generate_room_id(user_id)
        long_question = "x" * 100  # 100자 질문

        await create_room(db_session, room_id, user_id, long_question)

        # DB에서 CNVS_SMRY_TXT 확인
        result = await db_session.execute(
            text("""
            SELECT "CNVS_SMRY_TXT"
            FROM "USR_CNVS_SMRY"
            WHERE "CNVS_IDT_ID" = :room_id
            """),
            {"room_id": room_id}
        )
        row = result.fetchone()

        summary = row[0]
        # 50자 + "..." = 53자
        assert len(summary) == 53
        assert summary.endswith("...")


class TestSaveQuestion:
    """질문 저장 테스트"""

    @pytest.mark.asyncio
    async def test_save_question_success(self, db_session: AsyncSession, test_user_room):
        """질문 저장 성공 테스트"""
        room_id = test_user_room["room_id"]
        question = "새로운 질문입니다"

        cnvs_id = await save_question(db_session, room_id, question)

        assert cnvs_id is not None
        assert isinstance(cnvs_id, int)

        # DB에서 확인
        result = await db_session.execute(
            text("""
            SELECT "QUES_TXT", "USE_YN"
            FROM "USR_CNVS"
            WHERE "CNVS_ID" = :cnvs_id
            """),
            {"cnvs_id": cnvs_id}
        )
        row = result.fetchone()

        assert row is not None
        assert row[0] == question  # QUES_TXT
        assert row[1] == "Y"  # USE_YN

    @pytest.mark.asyncio
    async def test_save_question_with_session_id(self, db_session: AsyncSession, test_user_room):
        """세션 ID를 포함한 질문 저장 테스트"""
        room_id = test_user_room["room_id"]
        question = "세션 포함 질문"
        session_id = "SESSION_12345"

        cnvs_id = await save_question(db_session, room_id, question, session_id)

        # DB에서 SESN_ID 확인
        result = await db_session.execute(
            text("""
            SELECT "SESN_ID"
            FROM "USR_CNVS"
            WHERE "CNVS_ID" = :cnvs_id
            """),
            {"cnvs_id": cnvs_id}
        )
        row = result.fetchone()

        assert row[0] == session_id


class TestSaveAnswer:
    """답변 저장 테스트"""

    @pytest.mark.asyncio
    async def test_save_answer_success(self, db_session: AsyncSession, test_user_room):
        """답변 저장 성공 테스트"""
        room_id = test_user_room["room_id"]

        # 먼저 질문 저장
        cnvs_id = await save_question(db_session, room_id, "질문")

        # 답변 저장
        answer = "답변입니다"
        token_count = 500
        response_time_ms = 2000

        await save_answer(db_session, cnvs_id, answer, token_count, response_time_ms)

        # DB에서 확인
        result = await db_session.execute(
            text("""
            SELECT "ANS_TXT", "TKN_USE_CNT", "RSP_TIM_MS"
            FROM "USR_CNVS"
            WHERE "CNVS_ID" = :cnvs_id
            """),
            {"cnvs_id": cnvs_id}
        )
        row = result.fetchone()

        assert row[0] == answer
        assert row[1] == token_count
        assert row[2] == response_time_ms


class TestSaveReferenceDocuments:
    """참조 문서 저장 테스트"""

    @pytest.mark.asyncio
    async def test_save_reference_documents_success(
        self, db_session: AsyncSession, test_user_room
    ):
        """참조 문서 저장 성공 테스트"""
        room_id = test_user_room["room_id"]

        # 질문 저장
        cnvs_id = await save_question(db_session, room_id, "RAG 질문")

        # 참조 문서 데이터
        search_results = [
            {
                "metadata": {"title": "문서1.pdf"},
                "chunk_text": "참조 내용 1",
                "score": 0.95
            },
            {
                "metadata": {"title": "문서2.pdf"},
                "chunk_text": "참조 내용 2",
                "score": 0.88
            }
        ]

        await save_reference_documents(db_session, cnvs_id, search_results)

        # DB에서 확인
        result = await db_session.execute(
            text("""
            SELECT "REF_SEQ", "ATT_DOC_NM", "DOC_CHNK_TXT", "SMLT_RTE"
            FROM "USR_CNVS_REF_DOC_LST"
            WHERE "CNVS_ID" = :cnvs_id
            ORDER BY "REF_SEQ"
            """),
            {"cnvs_id": cnvs_id}
        )
        rows = result.fetchall()

        assert len(rows) == 2
        assert rows[0][0] == 0  # REF_SEQ
        assert rows[0][1] == "문서1.pdf"
        assert rows[0][3] == 0.95  # SMLT_RTE
        assert rows[1][0] == 1
        assert rows[1][1] == "문서2.pdf"

    @pytest.mark.asyncio
    async def test_save_empty_reference_documents(
        self, db_session: AsyncSession, test_user_room
    ):
        """빈 참조 문서 리스트 저장 테스트"""
        room_id = test_user_room["room_id"]
        cnvs_id = await save_question(db_session, room_id, "질문")

        await save_reference_documents(db_session, cnvs_id, [])

        # DB에서 확인
        result = await db_session.execute(
            text("""
            SELECT COUNT(*)
            FROM "USR_CNVS_REF_DOC_LST"
            WHERE "CNVS_ID" = :cnvs_id
            """),
            {"cnvs_id": cnvs_id}
        )
        count = result.scalar()

        assert count == 0


class TestCountTokens:
    """토큰 수 계산 테스트"""

    def test_count_tokens_simple(self):
        """간단한 텍스트 토큰 수 계산 테스트"""
        text = "안녕하세요 반갑습니다"
        tokens = count_tokens(text)

        # 공백 기준으로 2개 단어
        assert tokens == 2

    def test_count_tokens_empty(self):
        """빈 텍스트 토큰 수 계산 테스트"""
        assert count_tokens("") == 0

    def test_count_tokens_multiple_spaces(self):
        """여러 공백이 있는 텍스트 토큰 수 계산 테스트"""
        text = "단어1   단어2    단어3"
        tokens = count_tokens(text)

        # split()은 연속된 공백을 하나로 처리
        assert tokens == 3

    def test_count_tokens_english(self):
        """영어 텍스트 토큰 수 계산 테스트"""
        text = "Hello world this is a test"
        tokens = count_tokens(text)

        assert tokens == 6
