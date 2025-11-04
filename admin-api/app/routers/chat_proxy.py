"""
Chat Proxy Router - layout.html의 /api/chat_stream 요청을 ds-api로 프록시
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import aliased
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import json
import asyncio
import logging
from datetime import datetime

from app.models import UsageHistory
from app.core.database import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat-proxy"])


class ChatStreamRequest(BaseModel):
    """layout.html에서 보내는 채팅 요청"""
    message: str
    session_id: Optional[str] = None
    user_id: str = settings.DEFAULT_USER
    think_mode: bool = False
    file_ids: List[str] = []
    history: List[Dict[str, Any]] = []


async def save_usage_to_db(
    db: AsyncSession,
    user_id: str,
    session_id: str,
    question: str,
    answer: str,
    conversation_title: Optional[str] = None,
    thinking_content: Optional[str] = None,
    main_category: Optional[str] = None,
    sub_category: Optional[str] = None,
    referenced_documents: Optional[List[str]] = None
) -> None:
    """
    대화 내용을 usage_history 테이블에 저장

    Args:
        db: 비동기 데이터베이스 세션
        user_id: 사용자 식별자 (예: "user_123456")
        session_id: 대화 세션 ID (예: "user_123_session_789")
        question: 사용자 질문 텍스트
        answer: AI 응답 텍스트
        conversation_title: 대화 제목 (None일 경우 자동 생성)
        thinking_content: AI 사고 과정 (<think> 태그 내용)
        main_category: 대분류 (None일 경우 자동 분류)
        sub_category: 소분류 (None일 경우 자동 분류)
        referenced_documents: 참조 문서 목록 (파일명 리스트)

    Returns:
        None

    Raises:
        SQLAlchemyError: 데이터베이스 저장 실패 시

    Note:
        - 제목이 없으면 질문의 첫 50자로 자동 생성
        - 카테고리가 없으면 LLM을 사용하여 자동 분류
        - 에러 발생 시 자동으로 롤백 처리
    """
    try:
        # 중복 저장 방지: 같은 session_id + question이 이미 있으면 skip (시간 제한 없음)
        from datetime import datetime, timedelta
        duplicate_check = select(UsageHistory).filter(
            UsageHistory.session_id == session_id,
            UsageHistory.question == question
        ).limit(1)
        duplicate_result = await db.execute(duplicate_check)
        existing_duplicate = duplicate_result.scalar_one_or_none()

        if existing_duplicate:
            logger.warning(f"Duplicate save prevented: session_id={session_id}, question={question[:50]}...")
            # 기존 레코드에 카테고리가 없고 새 요청에 카테고리가 있으면 업데이트
            if not existing_duplicate.main_category and main_category:
                existing_duplicate.main_category = main_category
                existing_duplicate.sub_category = sub_category
                await db.commit()
                logger.info(f"Updated category for existing record: {main_category} > {sub_category}")
            return

        # 해당 세션의 첫 대화인지 확인
        if not conversation_title:
            query = select(UsageHistory).filter(
                UsageHistory.session_id == session_id
            ).limit(1)
            result = await db.execute(query)
            existing = result.scalar_one_or_none()

            # 첫 대화라면 질문으로 제목 생성 (규칙 기반 즉시 생성)
            if not existing:
                from app.utils.title_generator import generate_conversation_title, sanitize_title
                title, was_truncated = generate_conversation_title(question)
                conversation_title = sanitize_title(title)
                logger.info(f"Auto-generated title (chat_proxy): '{conversation_title}' (truncated={was_truncated})")

        # 자동 카테고리 분류 (P0 요구사항)
        if not main_category or not sub_category:
            from app.services.categorization import categorize_conversation_safe
            try:
                auto_main, auto_sub = await categorize_conversation_safe(question, answer)
                main_category = main_category or auto_main
                sub_category = sub_category or auto_sub
                logger.info(f"Auto-categorized: {main_category} > {sub_category}")
            except Exception as e:
                logger.error(f"Categorization failed: {e}", exc_info=True)
                main_category = main_category or "미분류"
                sub_category = sub_category or "없음"

        # 새 레코드 생성
        usage_record = UsageHistory(
            user_id=user_id,
            session_id=session_id,
            conversation_title=conversation_title,
            question=question,
            answer=answer,
            thinking_content=thinking_content,
            referenced_documents=referenced_documents,
            main_category=main_category,
            sub_category=sub_category,
            model_name=settings.CHAT_MODEL_NAME,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(usage_record)
        await db.commit()

        logger.info(f"Usage saved to DB: user_id={user_id}, session_id={session_id}")

    except IntegrityError as e:
        # Unique constraint violation (중복 저장 시도) - 무시하고 계속 진행
        await db.rollback()
        if "idx_unique_session_question" in str(e):
            logger.warning(f"Duplicate prevented by DB constraint: session_id={session_id}, question={question[:50]}...")
        else:
            logger.error(f"IntegrityError while saving usage: {e}", exc_info=True)
        # 중복은 에러가 아니므로 raise하지 않음
    except SQLAlchemyError as e:
        logger.error(f"Database error while saving usage: {e}", exc_info=True)
        await db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error while saving usage: {e}", exc_info=True)
        await db.rollback()
        raise


@router.post("/chat_stream")
async def chat_stream_proxy(
    request: ChatStreamRequest,
    db: AsyncSession = Depends(get_db),
    raw_request: Request = None
):
    """
    layout.html의 채팅 요청을 ds-api로 프록시하고 응답을 스트리밍
    동시에 usage_history에 저장
    """

    # session_id가 없으면 자동 생성 (user_id + timestamp)
    if not request.session_id:
        import time
        request.session_id = f"{request.user_id}_session_{int(time.time())}"

    # 업로드된 파일 자동 조회 (file_ids 자동 채우기)
    if len(request.file_ids) == 0 and request.session_id:
        from sqlalchemy import text
        try:
            file_query = await db.execute(
                text("""
                SELECT "FILE_UID" FROM "USR_UPLD_DOC_MNG"
                WHERE "CNVS_IDT_ID" = :session_id
                ORDER BY "REG_DT" DESC
                """),
                {"session_id": request.session_id}
            )
            uploaded_files = [row[0] for row in file_query.fetchall()]
            if uploaded_files:
                request.file_ids = uploaded_files
                logger.info(f"Auto-loaded {len(uploaded_files)} files for session {request.session_id}: {uploaded_files}")
        except Exception as e:
            logger.warning(f"Failed to load uploaded files for session {request.session_id}: {e}")

    # ds-api ExGPTRequest 형식으로 변환
    history_messages = []

    # history가 있으면 추가
    if request.history:
        for msg in request.history:
            if isinstance(msg, dict):
                history_messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

    # 현재 메시지 추가
    history_messages.append({"role": "user", "content": request.message})

    # ds-api WebChatRequest 형식 (RAG 검색 포함)
    llm_payload = {
        "message": request.message,
        "session_id": request.session_id,
        "user_id": request.user_id,
        "think_mode": request.think_mode,
        "file_ids": request.file_ids,
        "history": history_messages,
        "temperature": settings.CHAT_DEFAULT_TEMPERATURE,
        "search_documents": True,  # RAG 검색 활성화
        "suggest_questions": False,
        "generate_search_query": True
    }

    logger.info(f"Chat request to ds-api: session_id={request.session_id}, message={request.message[:50]}...")

    # 응답 데이터 누적 (DB 저장용)
    accumulated_response = ""
    accumulated_thinking = ""  # thinking 내용 별도 저장
    referenced_documents = []  # 참조 문서 목록
    is_thinking = False  # 현재 thinking 처리 중인지 여부

    async def stream_and_save():
        nonlocal accumulated_response, accumulated_thinking, referenced_documents, is_thinking

        try:
            # ds-api 스트리밍 요청 (RAG 검색 포함)
            async with httpx.AsyncClient(timeout=settings.CHAT_TIMEOUT, follow_redirects=True) as client:
                async with client.stream(
                    "POST",
                    f"{settings.DS_API_URL}/v1/chat/",
                    json=llm_payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-API-Key": settings.DS_API_KEY
                    }
                ) as response:

                    if response.status_code != 200:
                        error_msg = f"LLM API 오류: {response.status_code}"
                        yield f"data: {json.dumps({'content': error_msg}, ensure_ascii=False)}\n\n"
                        yield "data: [DONE]\n\n"

                        # 오류도 DB에 저장
                        await save_usage_to_db(
                            db=db,
                            user_id=request.user_id,
                            session_id=request.session_id,
                            question=request.message,
                            answer=error_msg
                        )
                        return

                    # ds-api SSE 응답 전달 (type: token, final, sources 등)
                    async for line in response.aiter_lines():
                        if line:
                            # 응답 데이터 파싱 및 누적
                            if line.startswith("data: "):
                                data_str = line[6:].strip()
                                if data_str == "[DONE]":
                                    yield "data: [DONE]\n\n"
                                    break

                                try:
                                    data = json.loads(data_str)

                                    # ds-api 형식: type 기반 처리
                                    if data.get("type") == "token":
                                        token = data.get("content", "")
                                        if token:
                                            # Thinking 태그 감지 및 분리
                                            if '<think>' in token:
                                                is_thinking = True

                                            if is_thinking:
                                                accumulated_thinking += token
                                                if '</think>' in token:
                                                    is_thinking = False
                                            else:
                                                accumulated_response += token

                                    # 참조 문서(sources) 수집
                                    elif data.get("type") == "sources":
                                        sources = data.get("sources", [])
                                        if sources:
                                            for source in sources:
                                                # 각 source에서 파일명 추출
                                                if isinstance(source, dict):
                                                    filename = source.get("filename") or source.get("title") or source.get("metadata", {}).get("filename")
                                                    if filename and filename not in referenced_documents:
                                                        referenced_documents.append(filename)
                                                elif isinstance(source, str):
                                                    if source not in referenced_documents:
                                                        referenced_documents.append(source)

                                    # 응답 그대로 전달 (sources, metadata 포함)
                                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                                except json.JSONDecodeError:
                                    pass

            # 스트리밍 완료 후 DB에 저장
            # 제목 생성용 세션은 DB에 저장하지 않음
            if request.session_id and request.session_id.startswith(settings.TITLE_GEN_PREFIX):
                logger.info(f"Title generation session ({request.session_id}) - skipping DB save")
            elif accumulated_response or accumulated_thinking:
                # 응답이 있거나 thinking이 있으면 저장
                # thinking 태그 제거 (내용만 저장)
                clean_thinking = accumulated_thinking.replace('<think>', '').replace('</think>', '').strip()

                await save_usage_to_db(
                    db=db,
                    user_id=request.user_id,
                    session_id=request.session_id,
                    question=request.message,
                    answer=accumulated_response.strip(),
                    thinking_content=clean_thinking if clean_thinking else None,
                    referenced_documents=referenced_documents if referenced_documents else None
                )
                logger.info(f"DB save completed: answer={len(accumulated_response)} chars, thinking={len(clean_thinking)} chars, docs={len(referenced_documents)}")

        except httpx.HTTPError as e:
            error_msg = f"HTTP 오류: {str(e)}"
            logger.error(f"HTTP error during chat stream: {e}", exc_info=True)
            yield f"data: {json.dumps({'content': error_msg}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

            # 오류도 DB에 저장
            try:
                await save_usage_to_db(
                    db=db,
                    user_id=request.user_id,
                    session_id=request.session_id,
                    question=request.message,
                    answer=error_msg
                )
            except Exception as db_error:
                logger.error(f"Failed to save error to DB: {db_error}", exc_info=True)

        except Exception as e:
            error_msg = f"프록시 오류: {str(e)}"
            logger.error(f"Unexpected error during chat stream: {e}", exc_info=True)
            yield f"data: {json.dumps({'content': error_msg}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

            # 오류도 DB에 저장
            try:
                await save_usage_to_db(
                    db=db,
                    user_id=request.user_id,
                    session_id=request.session_id,
                    question=request.message,
                    answer=error_msg
                )
            except Exception as db_error:
                logger.error(f"Failed to save error to DB: {db_error}", exc_info=True)

    return StreamingResponse(
        stream_and_save(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/chat/sessions")
async def get_chat_sessions(
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    사용자의 대화 세션 목록 조회 (사이드바용)
    제목 생성용 세션(title_gen_)은 제외
    삭제된 세션(is_deleted=true)은 제외

    Returns:
        List of unique sessions with their titles and latest message time
    """
    from sqlalchemy import func, distinct

    # 각 세션의 첫 메시지(대화 제목)와 최신 시간 조회
    # 제목 생성용 세션 제외, 삭제된 세션 제외
    # 가장 최근 conversation_title 사용 (중복 방지)
    from sqlalchemy.sql import func as sqlfunc

    # 서브쿼리: 각 세션의 최신 레코드 ID와 통계 정보
    subquery = select(
        UsageHistory.session_id,
        func.max(UsageHistory.id).label('latest_id'),
        func.max(UsageHistory.created_at).label('latest_time'),
        func.count(UsageHistory.id).label('message_count')
    ).filter(
        ~UsageHistory.session_id.like('title_gen_%'),
        UsageHistory.is_deleted == False
    ).group_by(
        UsageHistory.session_id
    ).subquery()

    # 메인 쿼리: latest_id에 해당하는 레코드의 conversation_title 가져오기
    UsageHistoryLatest = aliased(UsageHistory)
    query = select(
        subquery.c.session_id,
        UsageHistoryLatest.conversation_title,
        subquery.c.latest_time,
        subquery.c.message_count
    ).join(
        UsageHistoryLatest,
        UsageHistoryLatest.id == subquery.c.latest_id
    ).order_by(
        subquery.c.latest_time.desc()
    )

    if user_id:
        query = query.filter(UsageHistoryLatest.user_id == user_id)

    result = await db.execute(query)
    sessions = result.all()

    return {
        "sessions": [
            {
                "session_id": session.session_id,
                "title": session.conversation_title or "대화 제목 없음",
                "latest_time": session.latest_time.isoformat() if session.latest_time else None,
                "message_count": session.message_count
            }
            for session in sessions
        ]
    }


@router.get("/chat/sessions/{session_id}")
async def get_session_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    특정 세션의 모든 메시지 조회
    """
    from sqlalchemy import asc

    query = select(UsageHistory).filter(
        UsageHistory.session_id == session_id
    ).order_by(asc(UsageHistory.created_at))

    result = await db.execute(query)
    messages = result.scalars().all()

    return {
        "session_id": session_id,
        "messages": [
            {
                "id": msg.id,
                "question": msg.question,
                "answer": msg.answer,
                "thinking_content": msg.thinking_content,  # thinking 포함
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            }
            for msg in messages
        ]
    }


@router.delete("/chat/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    특정 세션의 모든 메시지 소프트 딜리트 (is_deleted = true)
    """
    from sqlalchemy import update as sql_update
    from datetime import datetime, timezone

    # 해당 세션의 모든 메시지를 소프트 딜리트
    update_query = sql_update(UsageHistory).where(
        UsageHistory.session_id == session_id
    ).values(
        is_deleted=True,
        deleted_at=datetime.now(timezone.utc)
    )

    result = await db.execute(update_query)
    await db.commit()

    deleted_count = result.rowcount

    logger.info(f"Session soft deleted: {session_id}, {deleted_count} messages marked as deleted")

    return {
        "session_id": session_id,
        "deleted_count": deleted_count,
        "message": "Session deleted successfully"
    }


class UpdateSessionTitleRequest(BaseModel):
    """세션 제목 업데이트 요청"""
    session_id: str
    title: str


@router.patch("/chat/sessions/{session_id}/title")
async def update_session_title(
    session_id: str,
    request: UpdateSessionTitleRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    특정 세션의 대화 제목 업데이트
    """
    from sqlalchemy import update

    # 해당 세션의 모든 레코드의 conversation_title 업데이트
    update_query = update(UsageHistory).where(
        UsageHistory.session_id == session_id
    ).values(
        conversation_title=request.title,
        updated_at=datetime.utcnow()
    )

    result = await db.execute(update_query)
    await db.commit()

    updated_count = result.rowcount

    logger.info(f"Session title updated: {session_id}, title='{request.title}', {updated_count} records updated")

    return {
        "session_id": session_id,
        "title": request.title,
        "updated_count": updated_count,
        "message": "Session title updated successfully"
    }


class STTConversationRequest(BaseModel):
    """STT 대화 저장 요청"""
    user_id: str
    session_id: str
    question: str  # "STT 전사해줘: filename.mp3"
    answer: str  # AI 분석 회의록
    thinking_content: Optional[str] = None  # 음성 전사 내용
    response_time: Optional[float] = None
    usage_metadata: Optional[Dict[str, Any]] = None


@router.post("/stt/save_conversation")
async def save_stt_conversation(
    request: STTConversationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    STT 대화 내역을 데이터베이스에 저장
    layout.html의 processVoiceToChat()에서 호출
    """
    try:
        # 대화 제목 생성 (첫 대화인 경우)
        query = select(UsageHistory).filter(
            UsageHistory.session_id == request.session_id
        ).limit(1)
        result = await db.execute(query)
        existing = result.scalar_one_or_none()

        conversation_title = None
        if not existing:
            # STT 요청임을 명시한 제목
            conversation_title = f"🎤 {request.question[:50]}"

        # 새 레코드 생성
        usage_record = UsageHistory(
            user_id=request.user_id,
            session_id=request.session_id,
            conversation_title=conversation_title,
            question=request.question,
            answer=request.answer,
            thinking_content=request.thinking_content,
            response_time=request.response_time,
            model_name="ex-GPT-STT",  # STT임을 명시
            usage_metadata=request.usage_metadata,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(usage_record)
        await db.commit()
        await db.refresh(usage_record)

        logger.info(f"STT conversation saved to DB: id={usage_record.id}, session_id={request.session_id}")

        return {
            "success": True,
            "id": usage_record.id,
            "message": "STT 대화가 저장되었습니다."
        }

    except SQLAlchemyError as e:
        logger.error(f"Database error while saving STT conversation: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"STT 대화 저장 실패: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while saving STT conversation: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"STT 대화 저장 실패: {str(e)}")
