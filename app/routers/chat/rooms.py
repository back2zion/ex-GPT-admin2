"""
Rooms API Router
대화방 관리 API (대화명 변경, 삭제)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.utils.auth import get_current_user_from_session
from app.services.chat_service import validate_room_id
from app.schemas.chat_schemas import RoomNameUpdateRequest
from datetime import datetime
import logging

router = APIRouter(prefix="/api/v1/rooms", tags=["chat-rooms"])
logger = logging.getLogger(__name__)


@router.patch("/{room_id}/name")
async def update_room_name(
    room_id: str,
    request: RoomNameUpdateRequest,
    current_user: dict = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db)
):
    """
    대화명 변경

    Args:
        room_id: 대화방 ID (CNVS_IDT_ID)
        request: 대화명 변경 요청
        current_user: 인증된 사용자
        db: 데이터베이스 세션

    Returns:
        dict: 업데이트된 대화방 정보

    Security:
        - Room ID 소유권 검증
    """
    user_id = current_user["user_id"]

    # 권한 검증
    is_valid = await validate_room_id(room_id, user_id, db)
    if not is_valid:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    # 대화명 업데이트
    await db.execute(
        text("""
        UPDATE "USR_CNVS_SMRY"
        SET "REP_CNVS_NM" = :name,
            "MOD_DT" = CURRENT_TIMESTAMP
        WHERE "CNVS_IDT_ID" = :room_id
        """),
        {"name": request.name, "room_id": room_id}
    )
    await db.commit()

    logger.info(f"Room name updated - room_id: {room_id}, user: {user_id}")

    return {
        "success": True,
        "cnvs_idt_id": room_id,
        "name": request.name,
        "updated_at": datetime.now().isoformat()
    }


@router.delete("/{room_id}")
async def delete_room(
    room_id: str,
    current_user: dict = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db)
):
    """
    대화 삭제 (소프트 삭제)

    Args:
        room_id: 대화방 ID
        current_user: 인증된 사용자
        db: 데이터베이스 세션

    Returns:
        dict: 삭제 결과

    Security:
        - Room ID 소유권 검증
        - 소프트 삭제 (USE_YN = 'N')
    """
    user_id = current_user["user_id"]

    # 권한 검증
    is_valid = await validate_room_id(room_id, user_id, db)
    if not is_valid:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    # 소프트 삭제: USR_CNVS_SMRY
    await db.execute(
        text("""
        UPDATE "USR_CNVS_SMRY"
        SET "USE_YN" = 'N',
            "MOD_DT" = CURRENT_TIMESTAMP
        WHERE "CNVS_IDT_ID" = :room_id
        """),
        {"room_id": room_id}
    )

    # 소프트 삭제: USR_CNVS (하위 메시지)
    await db.execute(
        text("""
        UPDATE "USR_CNVS"
        SET "USE_YN" = 'N',
            "MOD_DT" = CURRENT_TIMESTAMP
        WHERE "CNVS_IDT_ID" = :room_id
        """),
        {"room_id": room_id}
    )

    await db.commit()

    logger.info(f"Room deleted - room_id: {room_id}, user: {user_id}")

    return {
        "success": True,
        "cnvs_idt_id": room_id,
        "deleted": True,
        "deleted_at": datetime.now().isoformat()
    }
