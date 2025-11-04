"""
History API Router
대화 히스토리 조회 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from app.core.database import get_db
from app.schemas.chat_schemas import ConversationListResponse, HistoryDetailResponse
from app.utils.auth import get_current_user_from_session
from app.services.chat_service import validate_room_id
import logging

router = APIRouter(prefix="/api/v1/history", tags=["chat-history"])
logger = logging.getLogger(__name__)


class PaginationRequest(BaseModel):
    page: int = 1
    page_size: int = 10


@router.post("/list")
async def get_conversation_list(
    pagination: PaginationRequest,
    current_user: dict = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db)
):
    """
    대화 목록 조회

    Args:
        pagination: 페이지네이션 파라미터
        current_user: 인증된 사용자
        db: 데이터베이스 세션

    Returns:
        ConversationListResponse: 대화 목록

    Security:
        - 본인 데이터만 조회 가능
    """
    # 사용자 ID는 세션에서 가져옴
    user_id = current_user["user_id"]

    # 페이지네이션 계산
    offset = (pagination.page - 1) * pagination.page_size
    limit = pagination.page_size

    # USR_CNVS_SMRY 조회
    result = await db.execute(
        text("""
        SELECT
            "CNVS_IDT_ID" as cnvs_idt_id,
            COALESCE("CNVS_SMRY_TXT", '대화 요약 없음') as cnvs_smry_txt,
            "REG_DT" as reg_dt
        FROM "USR_CNVS_SMRY"
        WHERE "USR_ID" = :user_id
          AND "USE_YN" = 'Y'
        ORDER BY "REG_DT" DESC
        LIMIT :limit OFFSET :offset
        """),
        {"user_id": user_id, "limit": limit, "offset": offset}
    )

    conversations = result.fetchall()

    logger.info(f"Conversation list retrieved - user: {user_id}, count: {len(conversations)}")

    return {
        "conversations": [
            {
                "cnvs_idt_id": row.cnvs_idt_id,
                "cnvs_smry_txt": row.cnvs_smry_txt,
                "reg_dt": row.reg_dt.isoformat() if row.reg_dt else None
            }
            for row in conversations
        ],
        "total": len(conversations)
    }


@router.get("/{room_id}")
async def get_conversation_detail(
    room_id: str,
    current_user: dict = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db)
):
    """
    특정 대화의 메시지 상세 조회

    Args:
        room_id: 대화방 ID
        current_user: 인증된 사용자
        db: 데이터베이스 세션

    Returns:
        HistoryDetailResponse: 메시지 리스트

    Security:
        - Room ID 소유권 검증
    """
    user_id = current_user["user_id"]

    # 권한 검증
    is_valid = await validate_room_id(room_id, user_id, db)
    if not is_valid:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    # USR_CNVS 조회 (질문 + 답변)
    result = await db.execute(
        text("""
        SELECT
            "CNVS_ID",
            "QUES_TXT",
            "ANS_TXT",
            "TKN_USE_CNT",
            "RSP_TIM_MS",
            "REG_DT"
        FROM "USR_CNVS"
        WHERE "CNVS_IDT_ID" = :room_id
          AND "USE_YN" = 'Y'
        ORDER BY "REG_DT", "CNVS_ID"
        """),
        {"room_id": room_id}
    )

    conversations = result.fetchall()
    messages = []

    for row in conversations:
        # 질문 메시지
        messages.append({
            "cnvs_id": row.CNVS_ID,
            "role": "user",
            "content": row.QUES_TXT,
            "timestamp": row.REG_DT.isoformat() if row.REG_DT else None,
            "metadata": {
                "tokens": 0,
                "search_time_ms": 0
            }
        })

        # 답변 메시지
        if row.ANS_TXT:
            # 참조 문서 조회
            refs_result = await db.execute(
                text("""
                SELECT "REF_SEQ", "ATT_DOC_NM", "DOC_CHNK_TXT", "SMLT_RTE"
                FROM "USR_CNVS_REF_DOC_LST"
                WHERE "CNVS_ID" = :cnvs_id
                ORDER BY "REF_SEQ"
                """),
                {"cnvs_id": row.CNVS_ID}
            )
            references = [
                {
                    "ref_seq": r.REF_SEQ,
                    "doc_name": r.ATT_DOC_NM,
                    "chunk_text": r.DOC_CHNK_TXT,
                    "similarity": float(r.SMLT_RTE) if r.SMLT_RTE else 0.0
                }
                for r in refs_result.fetchall()
            ]

            # 추천 질문 조회
            sugg_result = await db.execute(
                text("""
                SELECT "ADD_QUES_TXT"
                FROM "USR_CNVS_ADD_QUES_LST"
                WHERE "CNVS_ID" = :cnvs_id
                ORDER BY "ADD_QUES_SEQ"
                """),
                {"cnvs_id": row.CNVS_ID}
            )
            suggested = [r.ADD_QUES_TXT for r in sugg_result.fetchall()]

            messages.append({
                "cnvs_id": row.CNVS_ID,
                "role": "assistant",
                "content": row.ANS_TXT,
                "timestamp": row.REG_DT.isoformat() if row.REG_DT else None,
                "metadata": {
                    "tokens": row.TKN_USE_CNT or 0,
                    "response_time_ms": row.RSP_TIM_MS or 0
                },
                "references": references if references else None,
                "suggested_questions": suggested if suggested else None
            })

    logger.info(f"Conversation detail retrieved - room_id: {room_id}, messages: {len(messages)}")

    return {
        "cnvs_idt_id": room_id,
        "messages": messages,
        "total_messages": len(messages)
    }
