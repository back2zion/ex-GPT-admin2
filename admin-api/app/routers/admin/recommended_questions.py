"""
추천 질문 관리 API 엔드포인트

DATABASE_SCHEMA.md의 RCM_QUES 테이블 기반
L-013: 메뉴 추천 질의 조회 기능과 연계
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from typing import Optional

from app.models import RecommendedQuestion
from app.schemas.recommended_question import (
    RecommendedQuestionCreate,
    RecommendedQuestionUpdate,
    RecommendedQuestionResponse,
    RecommendedQuestionListResponse
)
from app.core.database import get_db
from app.dependencies import get_principal
from cerbos.sdk.model import Principal

router = APIRouter(prefix="/api/v1/admin/recommended_questions", tags=["admin-recommended-questions"])


def orm_to_dict(orm_obj: RecommendedQuestion) -> dict:
    """ORM 객체를 React Admin 형식의 dict로 변환 (필드명 매핑)"""
    return {
        "id": orm_obj.rcm_ques_id,
        "question": orm_obj.ques_txt,
        "category": orm_obj.cat_nm,
        "description": orm_obj.desc_txt,
        "display_order": orm_obj.disp_ord,
        "is_active": orm_obj.use_yn == 'Y',
        "created_at": orm_obj.created_at,
        "updated_at": orm_obj.updated_at,
    }


@router.get("/active", response_model=RecommendedQuestionListResponse)
async def get_active_recommended_questions(
    db: AsyncSession = Depends(get_db)
):
    """
    활성화된 추천 질문 조회 (사용자 UI용)

    - 인증 불필요 (public)
    - use_yn='Y'인 추천 질문만 반환
    - disp_ord 순으로 정렬
    - 최대 4개까지만 반환 (UI 레이아웃 제약)
    """
    # Filter active questions
    query = select(RecommendedQuestion).filter(
        RecommendedQuestion.use_yn == 'Y'
    ).order_by(
        RecommendedQuestion.disp_ord.asc()
    ).limit(4)

    result = await db.execute(query)
    items = result.scalars().all()

    # 필드명 변환
    items_dict = [orm_to_dict(item) for item in items]

    return RecommendedQuestionListResponse(items=items_dict, total=len(items_dict))


@router.get("", response_model=RecommendedQuestionListResponse)
async def list_recommended_questions(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(100, le=1000, description="조회할 최대 레코드 수"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    is_active: Optional[bool] = Query(None, description="활성화 상태 필터"),
    sort_by: Optional[str] = Query("display_order", description="정렬 필드"),
    order: Optional[str] = Query("asc", description="정렬 방향 (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    추천 질문 목록 조회 (관리자용)

    - 모든 사용자 접근 가능 (인증만 필요)
    - 검색, 필터링, 페이지네이션, 정렬 지원
    """
    # Base query
    query = select(RecommendedQuestion)
    count_query = select(func.count()).select_from(RecommendedQuestion)

    # 필터링
    if category:
        query = query.filter(RecommendedQuestion.cat_nm == category)
        count_query = count_query.filter(RecommendedQuestion.cat_nm == category)

    if is_active is not None:
        use_yn_value = 'Y' if is_active else 'N'
        query = query.filter(RecommendedQuestion.use_yn == use_yn_value)
        count_query = count_query.filter(RecommendedQuestion.use_yn == use_yn_value)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 정렬
    sort_column = {
        "id": RecommendedQuestion.rcm_ques_id,
        "display_order": RecommendedQuestion.disp_ord,
        "question": RecommendedQuestion.ques_txt,
        "created_at": RecommendedQuestion.created_at,
    }.get(sort_by, RecommendedQuestion.disp_ord)

    if order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # 페이지네이션
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()

    # 필드명 변환
    items_dict = [orm_to_dict(item) for item in items]

    return RecommendedQuestionListResponse(items=items_dict, total=total)


@router.get("/{question_id}", response_model=RecommendedQuestionResponse)
async def get_recommended_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """추천 질문 상세 조회"""
    query = select(RecommendedQuestion).filter(RecommendedQuestion.rcm_ques_id == question_id)
    result = await db.execute(query)
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="추천 질문을 찾을 수 없습니다")

    return RecommendedQuestionResponse(**orm_to_dict(item))


@router.post("", response_model=RecommendedQuestionResponse)
async def create_recommended_question(
    data: RecommendedQuestionCreate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """추천 질문 생성"""
    # Create new question
    new_question = RecommendedQuestion(
        ques_txt=data.question,
        cat_nm=data.category,
        desc_txt=data.description,
        disp_ord=data.display_order,
        use_yn='Y' if data.is_active else 'N',
        created_by=principal.id
    )

    db.add(new_question)
    await db.commit()
    await db.refresh(new_question)

    return RecommendedQuestionResponse(**orm_to_dict(new_question))


@router.put("/{question_id}", response_model=RecommendedQuestionResponse)
async def update_recommended_question(
    question_id: int,
    data: RecommendedQuestionUpdate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """추천 질문 수정"""
    # Check if exists
    query = select(RecommendedQuestion).filter(RecommendedQuestion.rcm_ques_id == question_id)
    result = await db.execute(query)
    question = result.scalar_one_or_none()

    if not question:
        raise HTTPException(status_code=404, detail="추천 질문을 찾을 수 없습니다")

    # Update fields
    update_data = {}
    if data.question is not None:
        update_data["ques_txt"] = data.question
    if data.category is not None:
        update_data["cat_nm"] = data.category
    if data.description is not None:
        update_data["desc_txt"] = data.description
    if data.display_order is not None:
        update_data["disp_ord"] = data.display_order
    if data.is_active is not None:
        update_data["use_yn"] = 'Y' if data.is_active else 'N'

    update_data["updated_by"] = principal.id

    if update_data:
        stmt = update(RecommendedQuestion).filter(
            RecommendedQuestion.rcm_ques_id == question_id
        ).values(**update_data)
        await db.execute(stmt)
        await db.commit()
        await db.refresh(question)

    return RecommendedQuestionResponse(**orm_to_dict(question))


@router.delete("/{question_id}")
async def delete_recommended_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """추천 질문 삭제 (Soft Delete: use_yn='N'으로 변경)"""
    # Check if exists
    query = select(RecommendedQuestion).filter(RecommendedQuestion.rcm_ques_id == question_id)
    result = await db.execute(query)
    question = result.scalar_one_or_none()

    if not question:
        raise HTTPException(status_code=404, detail="추천 질문을 찾을 수 없습니다")

    # Soft delete: set use_yn='N'
    stmt = update(RecommendedQuestion).filter(
        RecommendedQuestion.rcm_ques_id == question_id
    ).values(use_yn='N', updated_by=principal.id)
    await db.execute(stmt)
    await db.commit()

    return {"message": "추천 질문이 사용중지되었습니다", "id": question_id}
