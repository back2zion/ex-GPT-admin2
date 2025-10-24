"""
사전 관리 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime
from cerbos.sdk.model import Principal

from app.core.database import get_db
from app.dependencies import get_principal, require_permission
from app.models.dictionary import Dictionary, DictionaryTerm, DictType
from app.schemas.dictionary import (
    DictionaryCreate,
    DictionaryUpdate,
    DictionaryResponse,
    DictionaryWithTermsResponse,
    DictionaryListResponse,
    DictionaryTermCreate,
    DictionaryTermUpdate,
    DictionaryTermResponse,
    DictionaryTermListResponse,
)
from app.services.excel_service import ExcelService

router = APIRouter(prefix="/api/v1/admin/dictionaries", tags=["admin-dictionaries"])


# ========== Dictionary CRUD ==========

@router.get("", response_model=DictionaryListResponse)
async def list_dictionaries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    dict_type: Optional[DictType] = None,
    use_yn: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """사전 목록 조회 (인증 필요)"""
    query = select(Dictionary)

    # 필터링
    if dict_type:
        query = query.where(Dictionary.dict_type == dict_type)
    if use_yn is not None:
        query = query.where(Dictionary.use_yn == use_yn)
    if search:
        query = query.where(
            (Dictionary.dict_name.ilike(f"%{search}%")) |
            (Dictionary.dict_desc.ilike(f"%{search}%"))
        )

    # 총 개수
    total_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(total_query)
    total = total_result.scalar_one()

    # 페이징
    query = query.order_by(Dictionary.created_at.desc())
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()

    return DictionaryListResponse(items=items, total=total)


@router.get("/{dict_id}", response_model=DictionaryWithTermsResponse)
async def get_dictionary(
    dict_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """사전 상세 조회 (용어 포함, 인증 필요)"""
    query = select(Dictionary).options(selectinload(Dictionary.terms)).where(Dictionary.dict_id == dict_id)
    result = await db.execute(query)
    dictionary = result.scalar_one_or_none()

    if not dictionary:
        raise HTTPException(status_code=404, detail="사전을 찾을 수 없습니다")

    return dictionary


@router.post("", response_model=DictionaryResponse)
async def create_dictionary(
    data: DictionaryCreate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("dictionary", "create"))
):
    """사전 생성 (관리자 권한 필요)"""
    dictionary = Dictionary(**data.model_dump())
    db.add(dictionary)
    await db.commit()
    await db.refresh(dictionary)
    return dictionary


@router.put("/{dict_id}", response_model=DictionaryResponse)
async def update_dictionary(
    dict_id: int,
    data: DictionaryUpdate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("dictionary", "update"))
):
    """사전 수정 (관리자 권한 필요)"""
    query = select(Dictionary).where(Dictionary.dict_id == dict_id)
    result = await db.execute(query)
    dictionary = result.scalar_one_or_none()

    if not dictionary:
        raise HTTPException(status_code=404, detail="사전을 찾을 수 없습니다")

    # 업데이트
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(dictionary, key, value)

    await db.commit()
    await db.refresh(dictionary)
    return dictionary


@router.delete("/{dict_id}")
async def delete_dictionary(
    dict_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("dictionary", "delete"))
):
    """사전 삭제 (관리자 권한 필요, CASCADE로 관련 용어도 함께 삭제)"""
    query = select(Dictionary).where(Dictionary.dict_id == dict_id)
    result = await db.execute(query)
    dictionary = result.scalar_one_or_none()

    if not dictionary:
        raise HTTPException(status_code=404, detail="사전을 찾을 수 없습니다")

    await db.delete(dictionary)
    await db.commit()

    return {"message": "사전이 삭제되었습니다", "dict_id": dict_id}


# ========== Dictionary Term CRUD ==========

@router.get("/terms/list", response_model=DictionaryTermListResponse)
async def list_dictionary_terms(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    dict_id: Optional[int] = None,
    category: Optional[str] = None,
    use_yn: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """사전 용어 목록 조회 (인증 필요)"""
    query = select(DictionaryTerm)

    # 필터링
    if dict_id:
        query = query.where(DictionaryTerm.dict_id == dict_id)
    if category:
        query = query.where(DictionaryTerm.category == category)
    if use_yn is not None:
        query = query.where(DictionaryTerm.use_yn == use_yn)
    if search:
        query = query.where(
            (DictionaryTerm.main_term.ilike(f"%{search}%")) |
            (DictionaryTerm.main_alias.ilike(f"%{search}%")) |
            (DictionaryTerm.definition.ilike(f"%{search}%"))
        )

    # 총 개수
    total_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(total_query)
    total = total_result.scalar_one()

    # 페이징
    query = query.order_by(DictionaryTerm.created_at.desc())
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()

    return DictionaryTermListResponse(items=items, total=total)


@router.get("/terms/{term_id}", response_model=DictionaryTermResponse)
async def get_dictionary_term(
    term_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """사전 용어 상세 조회 (인증 필요)"""
    query = select(DictionaryTerm).where(DictionaryTerm.term_id == term_id)
    result = await db.execute(query)
    term = result.scalar_one_or_none()

    if not term:
        raise HTTPException(status_code=404, detail="용어를 찾을 수 없습니다")

    return term


@router.post("/terms", response_model=DictionaryTermResponse)
async def create_dictionary_term(
    data: DictionaryTermCreate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("dictionary", "create"))
):
    """사전 용어 생성 (관리자 권한 필요)"""
    # 사전 존재 확인
    dict_query = select(Dictionary).where(Dictionary.dict_id == data.dict_id)
    dict_result = await db.execute(dict_query)
    if not dict_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="사전을 찾을 수 없습니다")

    # 중복 확인
    duplicate_query = select(DictionaryTerm).where(
        DictionaryTerm.dict_id == data.dict_id,
        DictionaryTerm.main_term == data.main_term
    )
    duplicate_result = await db.execute(duplicate_query)
    if duplicate_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"이미 존재하는 용어입니다: {data.main_term}")

    term = DictionaryTerm(**data.model_dump())
    db.add(term)
    await db.commit()
    await db.refresh(term)
    return term


@router.put("/terms/{term_id}", response_model=DictionaryTermResponse)
async def update_dictionary_term(
    term_id: int,
    data: DictionaryTermUpdate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("dictionary", "update"))
):
    """사전 용어 수정 (관리자 권한 필요)"""
    query = select(DictionaryTerm).where(DictionaryTerm.term_id == term_id)
    result = await db.execute(query)
    term = result.scalar_one_or_none()

    if not term:
        raise HTTPException(status_code=404, detail="용어를 찾을 수 없습니다")

    # 업데이트
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(term, key, value)

    await db.commit()
    await db.refresh(term)
    return term


@router.delete("/terms/{term_id}")
async def delete_dictionary_term(
    term_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("dictionary", "delete"))
):
    """사전 용어 삭제 (관리자 권한 필요)"""
    query = select(DictionaryTerm).where(DictionaryTerm.term_id == term_id)
    result = await db.execute(query)
    term = result.scalar_one_or_none()

    if not term:
        raise HTTPException(status_code=404, detail="용어를 찾을 수 없습니다")

    await db.delete(term)
    await db.commit()

    return {"message": "용어가 삭제되었습니다", "term_id": term_id}


@router.delete("/terms/batch")
async def delete_dictionary_terms_batch(
    term_ids: list[int],
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("dictionary", "delete"))
):
    """사전 용어 일괄 삭제 (관리자 권한 필요)"""
    query = delete(DictionaryTerm).where(DictionaryTerm.term_id.in_(term_ids))
    result = await db.execute(query)
    await db.commit()

    return {
        "message": f"{result.rowcount}개 용어가 삭제되었습니다",
        "deleted_count": result.rowcount
    }


# ========== Excel Export ==========

@router.get("/export/excel")
async def export_dictionaries_excel(
    dict_type: Optional[DictType] = None,
    use_yn: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    사전 목록 엑셀 다운로드 (xlsx)

    - 사전 종류별 필터링 가능
    - 사용 여부 필터링 가능
    """
    query = select(Dictionary)

    # 필터링
    if dict_type:
        query = query.where(Dictionary.dict_type == dict_type)
    if use_yn is not None:
        query = query.where(Dictionary.use_yn == use_yn)

    query = query.order_by(Dictionary.created_at.desc())

    result = await db.execute(query)
    dictionaries = result.scalars().all()

    # 엑셀용 데이터 변환
    excel_data = []
    for dictionary in dictionaries:
        excel_data.append({
            'dict_id': dictionary.dict_id,
            'dict_name': dictionary.dict_name,
            'dict_type': dictionary.dict_type.value if dictionary.dict_type else '',
            'dict_desc': dictionary.dict_desc or '',
            'word_count': dictionary.word_count or 0,
            'case_sensitive': dictionary.case_sensitive,
            'word_boundary': dictionary.word_boundary,
            'use_yn': dictionary.use_yn,
            'created_at': dictionary.created_at
        })

    # 엑셀 파일 생성
    excel_file = ExcelService.create_dictionaries_excel(excel_data)

    # 파일명 생성
    filename = f"dictionaries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{dict_id}/terms/export/excel")
async def export_dictionary_terms_excel(
    dict_id: int,
    category: Optional[str] = None,
    use_yn: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)
):
    """
    특정 사전의 용어 목록 엑셀 다운로드 (xlsx)

    - 카테고리별 필터링 가능
    - 사용 여부 필터링 가능
    """
    # 사전 존재 확인
    dict_query = select(Dictionary).where(Dictionary.dict_id == dict_id)
    dict_result = await db.execute(dict_query)
    dictionary = dict_result.scalar_one_or_none()

    if not dictionary:
        raise HTTPException(status_code=404, detail="사전을 찾을 수 없습니다")

    # 용어 조회
    query = select(DictionaryTerm).where(DictionaryTerm.dict_id == dict_id)

    if category:
        query = query.where(DictionaryTerm.category == category)
    if use_yn is not None:
        query = query.where(DictionaryTerm.use_yn == use_yn)

    query = query.order_by(DictionaryTerm.created_at.desc())

    result = await db.execute(query)
    terms = result.scalars().all()

    # 엑셀용 데이터 변환
    excel_data = []
    for term in terms:
        excel_data.append({
            'term_id': term.term_id,
            'main_term': term.main_term,
            'main_alias': term.main_alias or '',
            'synonym1': term.synonym1 or '',
            'synonym2': term.synonym2 or '',
            'synonym3': term.synonym3 or '',
            'category': term.category or '',
            'definition': term.definition or '',
            'use_yn': term.use_yn,
            'created_at': term.created_at
        })

    # 엑셀 파일 생성
    excel_file = ExcelService.create_dictionary_terms_excel(excel_data, dict_name=dictionary.dict_name)

    # 파일명 생성
    filename = f"dictionary_terms_{dict_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
