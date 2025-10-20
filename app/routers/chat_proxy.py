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
    conversation_title: Optional[str] = None
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

    llm_payload = {
        "model": "default-model",
        "messages": messages,
        "stream": True,
        "max_tokens": 2000,
        "temperature": 0.7
    }

    # 응답 데이터 누적 (DB 저장용)
    accumulated_response = ""

    async def stream_and_save():
        nonlocal accumulated_response

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
                                            accumulated_response += token
                                            # layout.html이 기대하는 형식으로 변환 (type: "token" 필드 추가)
                                            yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"

                                except json.JSONDecodeError:
                                    pass

            # 스트리밍 완료 후 DB에 저장
            # thinking 내용만 있는 경우는 저장하지 않음
            if accumulated_response and not accumulated_response.strip().startswith('<think>'):
                await save_usage_to_db(
                    db=db,
                    user_id=request.user_id,
                    session_id=request.session_id,
                    question=request.message,
                    answer=accumulated_response
                )

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

    Returns:
        List of unique sessions with their titles and latest message time
    """
    from sqlalchemy import func, distinct

    # 각 세션의 첫 메시지(대화 제목)와 최신 시간 조회
    query = select(
        UsageHistory.session_id,
        UsageHistory.conversation_title,
        func.max(UsageHistory.created_at).label('latest_time'),
        func.count(UsageHistory.id).label('message_count')
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
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            }
            for msg in messages
        ]
    }
