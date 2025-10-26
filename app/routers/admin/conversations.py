"""
대화내역 조회 API 엔드포인트
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import joinedload
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel

from app.models.usage import UsageHistory
from app.models.user import User
from app.core.database import get_db
from app.dependencies import get_principal
from cerbos.sdk.model import Principal
from app.services.excel_service import ExcelService

router = APIRouter(prefix="/api/v1/admin/conversations", tags=["admin-conversations"])


class ConversationListItem(BaseModel):
    """대화내역 목록 아이템 (사용자 정보 포함)"""
    id: int
    user_id: str

    # 사용자 조직 정보
    position: Optional[str] = None  # 직급
    rank: Optional[str] = None      # 직위
    team: Optional[str] = None      # 팀명
    join_year: Optional[int] = None # 입사년도

    # 대화 내용
    question: str
    answer: Optional[str] = None
    thinking_content: Optional[str] = None
    response_time: Optional[float] = None

    # 분류 정보
    main_category: Optional[str] = None  # 대분류
    sub_category: Optional[str] = None   # 소분류

    # 추가 정보
    referenced_documents: Optional[List[str]] = None  # 참조 문서

    # 일시
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ConversationDetail(BaseModel):
    """대화내역 상세"""
    id: int
    user_id: str

    # 사용자 조직 정보
    position: Optional[str] = None
    rank: Optional[str] = None
    team: Optional[str] = None
    join_year: Optional[int] = None
    department: Optional[str] = None  # 부서명

    # 대화 정보
    session_id: Optional[str] = None
    question: str
    answer: Optional[str] = None
    thinking_content: Optional[str] = None
    response_time: Optional[float] = None

    # 분류 정보
    main_category: Optional[str] = None
    sub_category: Optional[str] = None

    # 추가 정보
    model_name: Optional[str] = None
    referenced_documents: Optional[List[str]] = None
    usage_metadata: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ConversationListResponse(BaseModel):
    """대화내역 목록 응답"""
    items: List[ConversationListItem]
    total: int
    page: int
    limit: int
    total_pages: int


# 인증 없이 사용 가능한 간단한 조회 엔드포인트
@router.get("/simple", response_model=ConversationListResponse)
async def get_conversations_simple(
    start: Optional[date] = Query(None, description="시작일 (YYYY-MM-DD)"),
    end: Optional[date] = Query(None, description="종료일 (YYYY-MM-DD)"),
    main_category: Optional[str] = Query(None, description="대분류 (경영분야, 기술분야, 경영/기술 외, 미분류)"),
    sub_category: Optional[str] = Query(None, description="소분류"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(50, ge=1, le=10000, description="페이지당 항목 수"),
    sort_by: str = Query(default="created_at", description="정렬 필드"),
    order: str = Query(default="desc", description="정렬 방향 (asc/desc)"),
    db: AsyncSession = Depends(get_db)
):
    """
    대화내역 목록 조회 (인증 불필요)

    대분류/소분류 필터링 지원:
    - 경영분야: 기획/감사, 관리/홍보, 영업/디지털, 복리후생, 기타
    - 기술분야: 도로/안전, 교통, 건설, 신사업, 기타
    - 경영/기술 외: 기타
    - 미분류
    """
    from sqlalchemy.orm import selectinload

    conditions = []

    # 날짜 필터
    if start:
        conditions.append(func.date(UsageHistory.created_at) >= start)
    if end:
        conditions.append(func.date(UsageHistory.created_at) <= end)

    # 대분류 필터
    if main_category and main_category != "전체":
        if main_category == "미분류":
            conditions.append(
                (UsageHistory.main_category.is_(None)) |
                (UsageHistory.main_category == "") |
                (UsageHistory.main_category == "미분류")
            )
        else:
            conditions.append(UsageHistory.main_category == main_category)

    # 소분류 필터
    if sub_category and sub_category != "전체":
        conditions.append(UsageHistory.sub_category == sub_category)

    # 전체 개수 조회
    count_query = select(func.count(UsageHistory.id))
    if conditions:
        count_query = count_query.filter(and_(*conditions))

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # 페이지네이션 계산
    offset = (page - 1) * limit
    total_pages = (total + limit - 1) // limit if limit > 0 else 0

    # 목록 조회 (User와 LEFT JOIN)
    query = select(
        UsageHistory,
        User.position,
        User.rank,
        User.team,
        User.join_year
    ).outerjoin(
        User, UsageHistory.user_id == User.username
    )

    if conditions:
        query = query.filter(and_(*conditions))

    # 정렬 처리
    sort_column = getattr(UsageHistory, sort_by, UsageHistory.created_at)
    if order.lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    # ConversationListItem으로 변환
    items = []
    for row in rows:
        usage_history, position, rank, team, join_year = row
        item_dict = {
            "id": usage_history.id,
            "user_id": usage_history.user_id,
            "position": position,
            "rank": rank,
            "team": team,
            "join_year": join_year,
            "question": usage_history.question,
            "answer": usage_history.answer,
            "thinking_content": usage_history.thinking_content,
            "response_time": usage_history.response_time,
            "main_category": usage_history.main_category,
            "sub_category": usage_history.sub_category,
            "referenced_documents": usage_history.referenced_documents,
            "created_at": usage_history.created_at,
        }
        items.append(ConversationListItem(**item_dict))

    return ConversationListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )


@router.get("/simple/{conversation_id}", response_model=ConversationDetail)
async def get_conversation_detail_simple(
    conversation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """대화내역 상세 조회 (인증 불필요)"""
    # User와 LEFT JOIN하여 조회
    query = select(
        UsageHistory,
        User.position,
        User.rank,
        User.team,
        User.join_year,
        User.full_name
    ).outerjoin(
        User, UsageHistory.user_id == User.username
    ).filter(UsageHistory.id == conversation_id)

    result = await db.execute(query)
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="대화내역을 찾을 수 없습니다.")

    usage_history, position, rank, team, join_year, full_name = row

    detail_dict = {
        "id": usage_history.id,
        "user_id": usage_history.user_id,
        "position": position,
        "rank": rank,
        "team": team,
        "join_year": join_year,
        "department": full_name,  # department 필드에 full_name 임시 매핑
        "session_id": usage_history.session_id,
        "question": usage_history.question,
        "answer": usage_history.answer,
        "thinking_content": usage_history.thinking_content,
        "response_time": usage_history.response_time,
        "main_category": usage_history.main_category,
        "sub_category": usage_history.sub_category,
        "model_name": usage_history.model_name,
        "referenced_documents": usage_history.referenced_documents,
        "usage_metadata": usage_history.usage_metadata,
        "ip_address": usage_history.ip_address,
        "created_at": usage_history.created_at,
        "updated_at": usage_history.updated_at if hasattr(usage_history, 'updated_at') else None,
    }

    return ConversationDetail(**detail_dict)


@router.get("/session/{session_id}", response_model=List[ConversationDetail])
async def get_session_conversations(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    세션 내 모든 대화 조회 (시간순)

    - 한 세션 내의 모든 질문/답변을 시간순으로 반환
    - 대화 흐름 파악에 유용
    - 인증 불필요 (관리자 페이지에서 사용)
    """
    # User와 LEFT JOIN하여 세션 내 모든 대화 조회
    query = select(
        UsageHistory,
        User.position,
        User.rank,
        User.team,
        User.join_year,
        User.full_name
    ).outerjoin(
        User, UsageHistory.user_id == User.username
    ).filter(
        UsageHistory.session_id == session_id
    ).order_by(UsageHistory.created_at.asc())  # 시간순 정렬

    result = await db.execute(query)
    rows = result.all()

    if not rows:
        raise HTTPException(status_code=404, detail="해당 세션의 대화를 찾을 수 없습니다.")

    conversations = []
    for row in rows:
        usage_history, position, rank, team, join_year, full_name = row

        detail_dict = {
            "id": usage_history.id,
            "user_id": usage_history.user_id,
            "position": position,
            "rank": rank,
            "team": team,
            "join_year": join_year,
            "department": None,  # User 모델에 department 필드가 있다면 추가
            "session_id": usage_history.session_id,
            "question": usage_history.question,
            "answer": usage_history.answer,
            "thinking_content": usage_history.thinking_content,
            "response_time": usage_history.response_time,
            "main_category": usage_history.main_category,
            "sub_category": usage_history.sub_category,
            "model_name": usage_history.model_name,
            "referenced_documents": usage_history.referenced_documents,
            "usage_metadata": usage_history.usage_metadata,
            "ip_address": usage_history.ip_address,
            "created_at": usage_history.created_at,
            "updated_at": usage_history.updated_at if hasattr(usage_history, 'updated_at') else None,
        }

        conversations.append(ConversationDetail(**detail_dict))

    return conversations


@router.get("/", response_model=ConversationListResponse)
async def get_conversations(
    start: Optional[date] = Query(None, description="시작일 (YYYY-MM-DD)"),
    end: Optional[date] = Query(None, description="종료일 (YYYY-MM-DD)"),
    main_category: Optional[str] = Query(None, description="대분류"),
    sub_category: Optional[str] = Query(None, description="소분류"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(50, ge=1, le=10000, description="페이지당 항목 수 (최대 10000)"),
    sort_by: str = Query(default="created_at", description="정렬 필드"),
    order: str = Query(default="desc", description="정렬 방향 (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    대화내역 목록 조회 (인증 필요)

    - 날짜 필터링 가능
    - 대분류/소분류 필터링 가능
    - 페이지네이션 지원 (최대 10000개/페이지 - 엑셀 다운로드용)
    - 최신순 정렬
    """
    # simple 엔드포인트와 동일한 로직 사용
    return await get_conversations_simple(
        start=start,
        end=end,
        main_category=main_category,
        sub_category=sub_category,
        page=page,
        limit=limit,
        sort_by=sort_by,
        order=order,
        db=db
    )


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation_detail(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    대화내역 상세 조회 (인증 필요)

    - 전체 질문/답변 내용
    - 사용자 정보
    - 세션 정보
    - 참조 문서 목록
    - 메타데이터
    """
    return await get_conversation_detail_simple(conversation_id, db)


@router.get("/export/excel")
async def export_conversations_excel(
    start: Optional[date] = Query(None, description="시작일 (YYYY-MM-DD)"),
    end: Optional[date] = Query(None, description="종료일 (YYYY-MM-DD)"),
    main_category: Optional[str] = Query(None, description="대분류"),
    sub_category: Optional[str] = Query(None, description="소분류"),
    limit: int = Query(10000, ge=1, le=100000, description="최대 다운로드 개수"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    대화내역 엑셀 다운로드 (xlsx)

    - 필터링 조건 적용 가능
    - 최대 100,000개까지 다운로드 가능
    - 한국도로공사 브랜드 스타일 적용
    """
    conditions = []

    # 날짜 필터
    if start:
        conditions.append(func.date(UsageHistory.created_at) >= start)
    if end:
        conditions.append(func.date(UsageHistory.created_at) <= end)

    # 대분류 필터
    if main_category and main_category != "전체":
        if main_category == "미분류":
            conditions.append(
                (UsageHistory.main_category.is_(None)) |
                (UsageHistory.main_category == "") |
                (UsageHistory.main_category == "미분류")
            )
        else:
            conditions.append(UsageHistory.main_category == main_category)

    # 소분류 필터
    if sub_category and sub_category != "전체":
        conditions.append(UsageHistory.sub_category == sub_category)

    # 데이터 조회 (User와 LEFT JOIN)
    query = select(
        UsageHistory,
        User.position,
        User.rank,
        User.team,
        User.join_year
    ).outerjoin(
        User, UsageHistory.user_id == User.username
    )

    if conditions:
        query = query.filter(and_(*conditions))

    query = query.order_by(UsageHistory.created_at.desc()).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    # 엑셀용 데이터 변환
    excel_data = []
    for row in rows:
        usage_history, position, rank, team, join_year = row
        excel_data.append({
            'id': usage_history.id,
            'user_id': usage_history.user_id,
            'position': position or '',
            'rank': rank or '',
            'team': team or '',
            'join_year': join_year or '',
            'question': usage_history.question or '',
            'answer': usage_history.answer or '',
            'response_time': usage_history.response_time or 0,
            'main_category': usage_history.main_category or '미분류',
            'sub_category': usage_history.sub_category or '미분류',
            'model_name': usage_history.model_name or '',
            'created_at': usage_history.created_at
        })

    # 엑셀 파일 생성
    headers = {
        'id': 'ID',
        'user_id': '사용자 ID',
        'position': '직급',
        'rank': '직위',
        'team': '팀명',
        'join_year': '입사년도',
        'question': '질문',
        'answer': '답변',
        'response_time': '응답시간(ms)',
        'main_category': '대분류',
        'sub_category': '소분류',
        'model_name': '모델',
        'created_at': '생성일시'
    }

    excel_file = ExcelService.create_workbook_from_data(
        data=excel_data,
        headers=headers,
        sheet_name="대화내역",
        title="ex-GPT 대화 내역"
    )

    # 파일명 생성
    filename = f"conversations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
