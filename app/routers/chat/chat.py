"""
Chat API Router
POST /api/v1/chat/send - 채팅 메시지 전송 (SSE 스트리밍)
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.chat_schemas import ChatRequest
from app.services.chat_service import generate_chat_stream
from app.utils.auth import get_current_user_from_session
import logging

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("/send")
async def send_chat_message(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db)
):
    """
    채팅 메시지 전송 (SSE 스트리밍)

    Args:
        request: 채팅 요청 (cnvs_idt_id, message, stream, ...)
        current_user: 인증된 사용자 정보
        db: 데이터베이스 세션

    Returns:
        StreamingResponse: SSE 스트리밍 응답
            - data: {"type": "room_created", "room_id": "..."}
            - data: {"content": {"response": "..."}}
            - data: {"metadata": {...}}
            - data: [DONE]

    Security:
        - HTTP 세션 기반 인증
        - Room ID 소유권 검증
        - SQL Injection 방지 (파라미터 바인딩)
        - XSS 방지 (HTML 이스케이프)
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Chat request - user: {user_id}, message length: {len(request.message)}")

        return StreamingResponse(
            generate_chat_stream(request, user_id, db),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as e:
        logger.error(f"Chat send error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="서버 오류가 발생했습니다"
        )
