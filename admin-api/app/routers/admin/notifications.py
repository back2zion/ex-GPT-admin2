"""
알림 API
PRD FUN-002: 제·개정 문서 알림
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.models.notification import Notification
from app.schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse,
    NotificationListResponse,
)
from app.dependencies import get_principal
from cerbos.sdk.model import Principal

router = APIRouter(prefix="/api/v1/admin/notifications", tags=["admin-notifications"])


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_read: Optional[bool] = Query(None, description="읽음 여부 필터"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db)
):
    """
    알림 목록 조회

    - 전체 알림(user_id=NULL) + 본인 알림(user_id=현재 사용자)
    - 최신순 정렬
    """
    # 사용자 ID 추출 (X-Test-Auth의 경우 모든 알림 표시)
    user_id = principal.attr.get("user_id") if principal.attr else None

    # 필터 조건
    filters = []
    if user_id:
        # JWT 인증: user_id가 있는 경우만 필터링
        filters.append(
            or_(
                Notification.user_id == None,
                Notification.user_id == user_id
            )
        )
    # X-Test-Auth의 경우 필터 없음 (모든 알림 표시)

    if is_read is not None:
        filters.append(Notification.is_read == is_read)

    if category:
        filters.append(Notification.category == category)

    # 전체 개수
    if filters:
        count_query = select(func.count(Notification.id)).where(and_(*filters))
    else:
        count_query = select(func.count(Notification.id))
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # 미읽음 개수
    unread_filters = [Notification.is_read == False]
    if user_id:
        unread_filters.append(
            or_(
                Notification.user_id == None,
                Notification.user_id == user_id
            )
        )
    unread_query = select(func.count(Notification.id)).where(and_(*unread_filters))
    unread_result = await db.execute(unread_query)
    unread_count = unread_result.scalar_one()

    # 알림 목록 조회
    if filters:
        query = (
            select(Notification)
            .where(and_(*filters))
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
    else:
        query = (
            select(Notification)
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

    result = await db.execute(query)
    notifications = result.scalars().all()

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        unread_count=unread_count
    )


@router.get("/unread-count")
async def get_unread_count(
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db)
):
    """미읽음 알림 개수 조회"""
    user_id = principal.attr.get("user_id") if principal.attr else None

    filters = [Notification.is_read == False]
    if user_id:
        filters.append(
            or_(
                Notification.user_id == None,
                Notification.user_id == user_id
            )
        )

    query = select(func.count(Notification.id)).where(and_(*filters))
    result = await db.execute(query)
    count = result.scalar_one()

    return {"unread_count": count}


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db)
):
    """알림 상세 조회"""
    query = select(Notification).where(
        and_(
            Notification.id == notification_id,
            or_(
                Notification.user_id == None,
                Notification.user_id == current_user.id
            )
        )
    )

    result = await db.execute(query)
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다")

    return NotificationResponse.model_validate(notification)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: int,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db)
):
    """알림을 읽음으로 표시"""
    query = select(Notification).where(
        and_(
            Notification.id == notification_id,
            or_(
                Notification.user_id == None,
                Notification.user_id == current_user.id
            )
        )
    )

    result = await db.execute(query)
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다")

    notification.is_read = True
    notification.read_at = datetime.utcnow()

    await db.commit()
    await db.refresh(notification)

    return NotificationResponse.model_validate(notification)


@router.post("/mark-all-read")
async def mark_all_as_read(
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db)
):
    """모든 알림을 읽음으로 표시"""
    from sqlalchemy import update

    # 전체 알림 + 본인 알림만
    stmt = (
        update(Notification)
        .where(
            and_(
                Notification.is_read == False,
                or_(
                    Notification.user_id == None,
                    Notification.user_id == current_user.id
                )
            )
        )
        .values(is_read=True, read_at=datetime.utcnow())
    )

    result = await db.execute(stmt)
    await db.commit()

    return {"message": f"{result.rowcount}개 알림을 읽음 처리했습니다"}


@router.post("", response_model=NotificationResponse)
async def create_notification(
    notification: NotificationCreate,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db)
):
    """
    알림 생성 (관리자만)

    시스템 알림, 제·개정 문서 알림 등을 생성
    """
    # 슈퍼유저만 알림 생성 가능
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="권한이 없습니다")

    db_notification = Notification(
        type=notification.type,
        category=notification.category,
        title=notification.title,
        message=notification.message,
        link=notification.link,
        related_entity_type=notification.related_entity_type,
        related_entity_id=notification.related_entity_id,
        user_id=notification.user_id,
    )

    db.add(db_notification)
    await db.commit()
    await db.refresh(db_notification)

    return NotificationResponse.model_validate(db_notification)


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db)
):
    """알림 삭제 (슈퍼유저만)"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="권한이 없습니다")

    query = select(Notification).where(Notification.id == notification_id)
    result = await db.execute(query)
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다")

    await db.delete(notification)
    await db.commit()

    return {"message": "알림이 삭제되었습니다"}
