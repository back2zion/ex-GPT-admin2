"""
Chat Proxy Router - layout.html의 /api/chat_stream 요청을 ds-api로 프록시
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import json
import asyncio
from datetime import datetime

from app.models import UsageHistory
from app.core.database import get_db
from app.core.config import settings

router = APIRouter(prefix="/api", tags=["chat-proxy"])

# vLLM API URL (Docker 컨테이너에서 host 접근)
import os
LLM_API_URL = os.getenv("LLM_API_URL", "http://host.docker.internal:8000")


class ChatStreamRequest(BaseModel):
    """layout.html에서 보내는 채팅 요청"""
    message: str
    session_id: Optional[str] = None  # Optional로 변경
    user_id: str = "anonymous"
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
    thinking_content: Optional[str] = None
):
    """usage_history에 대화 저장"""
    try:
        # 해당 세션의 첫 대화인지 확인
        if not conversation_title:
            query = select(UsageHistory).filter(
                UsageHistory.session_id == session_id
            ).limit(1)
            result = await db.execute(query)
            existing = result.scalar_one_or_none()

            # 첫 대화라면 질문으로 제목 생성
            if not existing:
                conversation_title = question[:50] + "..." if len(question) > 50 else question

        # 새 레코드 생성
        usage_record = UsageHistory(
            user_id=user_id,
            session_id=session_id,
            conversation_title=conversation_title,
            question=question,
            answer=answer,
            thinking_content=thinking_content,  # thinking 내용 저장
            model_name="ex-GPT",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(usage_record)
        await db.commit()

        print(f"✅ Usage saved to DB: user_id={user_id}, session_id={session_id}")

    except Exception as e:
        print(f"❌ Failed to save usage to DB: {e}")
        await db.rollback()


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

    # vLLM OpenAI 호환 형식으로 변환
    messages = []

    # history가 있으면 추가
    if request.history:
        for msg in request.history:
            if isinstance(msg, dict):
                messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

    # 현재 메시지 추가
    messages.append({"role": "user", "content": request.message})

    # vLLM OpenAI 호환 형식으로 변환 (thinking 모드 지원)
    llm_payload = {
        "model": "default-model",
        "messages": messages,
        "stream": True,
        "max_tokens": 2000,
        "temperature": 0.7
    }

    # Think mode 활성화 (DeepSeek-R1 등 thinking 지원 모델용)
    if request.think_mode:
        # vLLM extra_body로 전달
        llm_payload["extra_body"] = {
            "enable_thinking": True,
            "thinking_budget": 2000  # thinking 토큰 예산
        }
        print(f"🧠 Think mode 활성화: {request.think_mode}")

    # 응답 데이터 누적 (DB 저장용)
    accumulated_response = ""
    accumulated_thinking = ""  # thinking 내용 별도 저장
    is_thinking = False  # 현재 thinking 처리 중인지 여부

    async def stream_and_save():
        nonlocal accumulated_response, accumulated_thinking, is_thinking

        try:
            # LLM API로 스트리밍 요청 (follow_redirects=True 추가)
            async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
                async with client.stream(
                    "POST",
                    f"{LLM_API_URL}/v1/chat/completions",
                    json=llm_payload,
                    headers={"Content-Type": "application/json"}
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

                    # 스트리밍 응답 전달 및 파싱 (vLLM OpenAI 호환 형식)
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

                                    # vLLM 형식: choices[0].delta.content 추출
                                    if "choices" in data and len(data["choices"]) > 0:
                                        delta = data["choices"][0].get("delta", {})
                                        token = delta.get("content", "")

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

                                            # layout.html이 기대하는 형식으로 변환 (type: "token" 필드 추가)
                                            yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"

                                except json.JSONDecodeError:
                                    pass

            # 스트리밍 완료 후 DB에 저장
            # 제목 생성용 세션은 DB에 저장하지 않음
            if request.session_id and request.session_id.startswith('title_gen_'):
                print(f"⏭️ 제목 생성 세션 ({request.session_id}) - DB 저장 생략")
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
                    thinking_content=clean_thinking if clean_thinking else None
                )
                print(f"💾 DB 저장 완료: answer={len(accumulated_response)} chars, thinking={len(clean_thinking)} chars")

        except Exception as e:
            error_msg = f"프록시 오류: {str(e)}"
            print(f"❌ Chat stream proxy error: {e}")
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

    Returns:
        List of unique sessions with their titles and latest message time
    """
    from sqlalchemy import func, distinct

    # 각 세션의 첫 메시지(대화 제목)와 최신 시간 조회
    # 제목 생성용 세션 제외
    query = select(
        UsageHistory.session_id,
        UsageHistory.conversation_title,
        func.max(UsageHistory.created_at).label('latest_time'),
        func.count(UsageHistory.id).label('message_count')
    ).filter(
        ~UsageHistory.session_id.like('title_gen_%')  # title_gen_ 세션 제외
    ).group_by(
        UsageHistory.session_id,
        UsageHistory.conversation_title
    ).order_by(
        func.max(UsageHistory.created_at).desc()
    )

    if user_id:
        query = query.filter(UsageHistory.user_id == user_id)

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
    특정 세션의 모든 메시지 삭제
    """
    from sqlalchemy import delete as sql_delete

    # 해당 세션의 모든 메시지 삭제
    delete_query = sql_delete(UsageHistory).filter(
        UsageHistory.session_id == session_id
    )

    result = await db.execute(delete_query)
    await db.commit()

    deleted_count = result.rowcount

    print(f"🗑️ 세션 삭제: {session_id}, {deleted_count}개 메시지 삭제됨")

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

    print(f"📝 세션 제목 업데이트: {session_id}, 제목='{request.title}', {updated_count}개 레코드 업데이트됨")

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

        print(f"✅ STT conversation saved to DB: id={usage_record.id}, session_id={request.session_id}")

        return {
            "success": True,
            "id": usage_record.id,
            "message": "STT 대화가 저장되었습니다."
        }

    except Exception as e:
        print(f"❌ Failed to save STT conversation to DB: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"STT 대화 저장 실패: {str(e)}")
