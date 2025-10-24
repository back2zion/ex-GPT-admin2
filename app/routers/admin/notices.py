"""
공지사항 CRUD API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from app.models import Notice
from app.schemas.notice import NoticeCreate, NoticeUpdate, NoticeResponse, NoticeListResponse
from app.core.database import get_db
from app.dependencies import require_permission, get_principal
from cerbos.sdk.model import Principal

router = APIRouter(prefix="/api/v1/admin/notices", tags=["admin-notices"])


@router.get("/active", response_model=NoticeListResponse)
async def get_active_notices(
    db: AsyncSession = Depends(get_db)
):
    """
    활성화된 공지사항 조회 (사용자 UI용)

    - 인증 불필요 (public)
    - is_active=true인 공지사항만 반환
    - 만료되지 않은 공지사항만 반환 (end_date >= today 또는 end_date가 null)
    - 우선순위 높은 순, 최근 생성 순으로 정렬
    - 최대 5개까지만 반환
    """
    from datetime import date
    today = str(date.today())

    # Filter active and non-expired notices
    query = select(Notice).filter(
        Notice.is_active == True
    ).filter(
        (Notice.end_date == None) | (Notice.end_date >= today)
    ).order_by(
        Notice.priority.desc(),  # urgent > high > normal > low
        Notice.created_at.desc()
    ).limit(5)

    # Get total count of active and non-expired notices
    count_query = select(func.count()).select_from(Notice).filter(
        Notice.is_active == True
    ).filter(
        (Notice.end_date == None) | (Notice.end_date >= today)
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    result = await db.execute(query)
    items = result.scalars().all()

    return NoticeListResponse(items=items, total=total)


@router.get("", response_model=NoticeListResponse)
async def list_notices(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(100, le=1000, description="조회할 최대 레코드 수"),
    search: Optional[str] = Query(None, description="검색어 (제목/내용)"),
    priority: Optional[str] = Query(None, pattern="^(low|normal|high|urgent)$", description="우선순위 필터"),
    is_active: bool | None = Query(None, description="활성화 상태 필터"),
    is_important: bool | None = Query(None, description="중요 공지 필터"),
    sort_by: Optional[str] = Query("created_at", description="정렬 필드"),
    order: Optional[str] = Query("desc", description="정렬 방향 (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    공지사항 목록 조회

    - 모든 사용자 접근 가능 (인증만 필요)
    - 검색, 필터링, 페이지네이션, 정렬 지원
    """
    # Base query
    query = select(Notice)
    count_query = select(func.count()).select_from(Notice)

    # 검색
    if search:
        search_filter = (Notice.title.contains(search)) | (Notice.content.contains(search))
        query = query.filter(search_filter)
        count_query = count_query.filter(search_filter)

    # 필터
    if priority:
        query = query.filter(Notice.priority == priority)
        count_query = count_query.filter(Notice.priority == priority)
    if is_active is not None:
        query = query.filter(Notice.is_active == is_active)
        count_query = count_query.filter(Notice.is_active == is_active)
    if is_important is not None:
        query = query.filter(Notice.is_important == is_important)
        count_query = count_query.filter(Notice.is_important == is_important)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 정렬 처리
    sort_column = getattr(Notice, sort_by, Notice.created_at)
    if order.lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # 페이징
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()

    return NoticeListResponse(items=items, total=total)


@router.post("", response_model=NoticeResponse, status_code=201)
async def create_notice(
    notice: NoticeCreate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("notice", "create"))
):
    """
    공지사항 생성

    - admin, manager 역할만 가능
    - Cerbos 정책으로 권한 제어
    """
    db_notice = Notice(**notice.model_dump())
    db.add(db_notice)
    await db.commit()
    await db.refresh(db_notice)
    return db_notice


@router.get("/{notice_id}", response_model=NoticeResponse)
async def get_notice(
    notice_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    공지사항 상세 조회

    - 조회수 자동 증가
    """
    result = await db.execute(select(Notice).filter(Notice.id == notice_id))
    notice = result.scalar_one_or_none()

    if not notice:
        raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다")

    # 조회수 증가
    notice.view_count += 1
    await db.commit()
    await db.refresh(notice)

    return notice


@router.put("/{notice_id}", response_model=NoticeResponse)
async def update_notice(
    notice_id: int,
    notice_update: NoticeUpdate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("notice", "update"))
):
    """
    공지사항 수정

    - admin, manager 역할만 가능
    """
    result = await db.execute(select(Notice).filter(Notice.id == notice_id))
    db_notice = result.scalar_one_or_none()

    if not db_notice:
        raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다")

    # 제공된 필드만 업데이트
    for field, value in notice_update.model_dump(exclude_unset=True).items():
        setattr(db_notice, field, value)

    await db.commit()
    await db.refresh(db_notice)
    return db_notice


@router.delete("/{notice_id}", status_code=200)
async def delete_notice(
    notice_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("notice", "delete"))
):
    """
    공지사항 삭제

    - admin 역할만 가능
    """
    result = await db.execute(select(Notice).filter(Notice.id == notice_id))
    db_notice = result.scalar_one_or_none()

    if not db_notice:
        raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다")

    await db.delete(db_notice)
    await db.commit()

    return {"message": "공지사항이 삭제되었습니다", "id": notice_id}
