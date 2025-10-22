"""
Chat Service
채팅 비즈니스 로직 (Room ID 생성/검증, 메시지 저장 등)
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.chat_schemas import ChatRequest
from app.utils.room_id_generator import generate_room_id
from app.services.ai_service import ai_service
from typing import AsyncGenerator, List, Dict, Any
import json
import logging
import time

logger = logging.getLogger(__name__)


async def validate_room_id(
    room_id: str,
    user_id: str,
    db: AsyncSession
) -> bool:
    """
    Room ID 검증 (DB에서 소유권 확인 - Stateless)

    Args:
        room_id: 대화방 ID (CNVS_IDT_ID)
        user_id: 사용자 ID
        db: 데이터베이스 세션

    Returns:
        bool: 유효 여부 (소유권 + USE_YN = 'Y')

    Security:
        - SQL Injection 방지 (파라미터 바인딩)
        - 소유권 검증
    """
    if not room_id or not room_id.strip():
        return False

    result = await db.execute(
        """
        SELECT COUNT(*)
        FROM USR_CNVS_SMRY
        WHERE CNVS_IDT_ID = :room_id
          AND USR_ID = :user_id
          AND USE_YN = 'Y'
        """,
        {"room_id": room_id, "user_id": user_id}
    )

    count = result.scalar()
    return count > 0


async def create_room(
    db: AsyncSession,
    room_id: str,
    user_id: str,
    first_question: str
) -> str:
    """
    새 대화방 생성 (USR_CNVS_SMRY INSERT)

    Args:
        db: 데이터베이스 세션
        room_id: 생성할 대화방 ID
        user_id: 사용자 ID
        first_question: 첫 질문 (요약으로 사용)

    Returns:
        str: 생성된 room_id

    Note:
        - CNVS_SMRY_TXT: 첫 질문으로 자동 생성
        - REP_CNVS_NM: 사용자가 나중에 수정 가능
    """
    # 요약 텍스트 생성 (첫 질문의 앞 50자)
    summary = first_question[:50] + "..." if len(first_question) > 50 else first_question

    await db.execute(
        """
        INSERT INTO USR_CNVS_SMRY (
            CNVS_IDT_ID, CNVS_SMRY_TXT, USR_ID, USE_YN, REG_DT
        ) VALUES (
            :room_id, :summary, :user_id, 'Y', CURRENT_TIMESTAMP
        )
        """,
        {
            "room_id": room_id,
            "summary": summary,
            "user_id": user_id
        }
    )
    await db.commit()

    logger.info(f"Room created - room_id: {room_id}, user: {user_id}")
    return room_id


async def save_question(
    db: AsyncSession,
    room_id: str,
    question: str,
    session_id: str = None
) -> int:
    """
    질문 저장 (USR_CNVS INSERT)

    Args:
        db: 데이터베이스 세션
        room_id: 대화방 ID
        question: 질문 텍스트
        session_id: HTTP 세션 ID

    Returns:
        int: CNVS_ID (생성된 메시지 ID)
    """
    result = await db.execute(
        """
        INSERT INTO USR_CNVS (
            CNVS_IDT_ID, QUES_TXT, SESN_ID, USE_YN, REG_DT
        ) VALUES (
            :room_id, :question, :session_id, 'Y', CURRENT_TIMESTAMP
        )
        RETURNING CNVS_ID
        """,
        {
            "room_id": room_id,
            "question": question,
            "session_id": session_id
        }
    )
    cnvs_id = result.scalar()
    await db.commit()

    logger.info(f"Question saved - room_id: {room_id}, cnvs_id: {cnvs_id}")
    return cnvs_id


async def save_answer(
    db: AsyncSession,
    cnvs_id: int,
    answer: str,
    token_count: int,
    response_time_ms: int
):
    """
    답변 저장 (USR_CNVS UPDATE)

    Args:
        db: 데이터베이스 세션
        cnvs_id: 메시지 ID
        answer: 답변 텍스트
        token_count: 토큰 사용 수
        response_time_ms: 응답 시간 (밀리초)
    """
    await db.execute(
        """
        UPDATE USR_CNVS
        SET ANS_TXT = :answer,
            TKN_USE_CNT = :tokens,
            RSP_TIM_MS = :response_time,
            MOD_DT = CURRENT_TIMESTAMP
        WHERE CNVS_ID = :cnvs_id
        """,
        {
            "answer": answer,
            "tokens": token_count,
            "response_time": response_time_ms,
            "cnvs_id": cnvs_id
        }
    )
    await db.commit()

    logger.info(f"Answer saved - cnvs_id: {cnvs_id}, tokens: {token_count}")


async def save_reference_documents(
    db: AsyncSession,
    cnvs_id: int,
    search_results: List[Dict[str, Any]]
):
    """
    참조 문서 저장 (USR_CNVS_REF_DOC_LST INSERT)

    Args:
        db: 데이터베이스 세션
        cnvs_id: 메시지 ID
        search_results: 검색 결과 리스트
    """
    for idx, doc in enumerate(search_results):
        await db.execute(
            """
            INSERT INTO USR_CNVS_REF_DOC_LST (
                CNVS_ID, REF_SEQ, ATT_DOC_NM,
                DOC_CHNK_TXT, SMLT_RTE, REG_DT
            ) VALUES (
                :cnvs_id, :ref_seq, :doc_name,
                :chunk_text, :score, CURRENT_TIMESTAMP
            )
            """,
            {
                "cnvs_id": cnvs_id,
                "ref_seq": idx,
                "doc_name": doc["metadata"]["title"],
                "chunk_text": doc["chunk_text"],
                "score": doc["score"]
            }
        )
    await db.commit()

    logger.info(f"Reference documents saved - cnvs_id: {cnvs_id}, count: {len(search_results)}")


def count_tokens(text: str) -> int:
    """
    토큰 수 계산 (간단한 구현)

    Args:
        text: 텍스트

    Returns:
        int: 토큰 수 (공백 기준 단어 수)

    TODO: tiktoken 등 정확한 토큰화 라이브러리 사용
    """
    return len(text.split())


async def generate_chat_stream(
    request: ChatRequest,
    user_id: str,
    db: AsyncSession
) -> AsyncGenerator[str, None]:
    """
    채팅 스트리밍 생성 (SSE)

    Args:
        request: 채팅 요청
        user_id: 사용자 ID
        db: 데이터베이스 세션

    Yields:
        str: SSE 데이터
            - data: {"type": "room_created", "room_id": "..."}
            - data: {"content": {"response": "..."}}
            - data: {"metadata": {...}}
            - data: [DONE]

    Flow:
        1. Room ID 생성/검증
        2. 질문 저장
        3. AI 응답 스트리밍
        4. 답변 저장
        5. 메타데이터 전송
    """
    try:
        # 1. Room ID 생성 또는 검증
        if not request.cnvs_idt_id or request.cnvs_idt_id.strip() == "":
            # 새 대화 - Room ID 생성
            room_id = generate_room_id(user_id)
            await create_room(db, room_id, user_id, request.message)
            is_new_room = True
            logger.info(f"New conversation started - room_id: {room_id}")
        else:
            # 기존 대화 - Room ID 검증
            room_id = request.cnvs_idt_id
            is_valid = await validate_room_id(room_id, user_id, db)
            if not is_valid:
                error_msg = json.dumps({"error": "유효하지 않은 대화방 ID이거나 접근 권한이 없습니다."})
                yield f"data: {error_msg}\n\n"
                yield "data: [DONE]\n\n"
                return
            is_new_room = False
            logger.info(f"Continue conversation - room_id: {room_id}")

        # 2. 새 룸 생성 시 room_id 전송
        if is_new_room:
            yield f"data: {json.dumps({'type': 'room_created', 'room_id': room_id})}\n\n"

        # 3. 질문 저장
        cnvs_id = await save_question(
            db,
            room_id,
            request.message,
            session_id=None  # TODO: 세션 ID 전달
        )

        # 4. AI 응답 스트리밍
        accumulated_response = ""
        search_results = []
        start_time = time.time()

        async for chunk in ai_service.stream_chat(
            message=request.message,
            history=request.history,
            search_documents=request.search_documents,
            department=request.department,
            search_scope=request.search_scope,
            max_context_tokens=request.max_context_tokens,
            temperature=request.temperature,
            think_mode=request.think_mode
        ):
            accumulated_response += chunk
            yield f"data: {json.dumps({'content': {'response': chunk}})}\n\n"

        # 5. 답변 저장
        response_time_ms = int((time.time() - start_time) * 1000)
        token_count = count_tokens(accumulated_response)

        await save_answer(
            db,
            cnvs_id,
            accumulated_response,
            token_count,
            response_time_ms
        )

        # 6. 참조 문서 저장 (RAG 사용 시)
        if request.search_documents and search_results:
            await save_reference_documents(db, cnvs_id, search_results)

        # 7. 메타데이터 전송
        metadata = {
            "tokens": token_count,
            "time_ms": response_time_ms
        }
        yield f"data: {json.dumps({'metadata': metadata})}\n\n"

        # 8. 추천 질문 (TODO)
        if request.suggest_questions:
            # suggested = await ai_service.generate_suggested_questions(accumulated_response)
            # yield f"data: {json.dumps({'suggested_questions': suggested})}\n\n"
            pass

        # 9. 종료 신호
        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"Chat stream error: {e}", exc_info=True)
        yield f"data: {json.dumps({'error': '서버 오류가 발생했습니다'})}\n\n"
        yield "data: [DONE]\n\n"
