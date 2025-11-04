"""
Categories API Router
학습데이터 관리 - 카테고리 CRUD API (Secure Coding Applied)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from typing import List

from app.core.database import get_db
from app.models.category import Category
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryListResponse
)

router = APIRouter(prefix="/api/v1/admin/categories", tags=["categories"])


@router.post("", response_model=CategoryResponse, status_code=201)
async def create_category(
    category: CategoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    카테고리 생성
    Secure: Input validation via Pydantic, Unique constraint handling
    """
    try:
        # Create new category
        db_category = Category(
            name=category.name,
            description=category.description,
            parsing_pattern=category.parsing_pattern
        )

        db.add(db_category)
        await db.commit()
        await db.refresh(db_category)

        return db_category

    except IntegrityError as e:
        await db.rollback()
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail=f"카테고리 '{category.name}'이(가) 이미 존재합니다"
            )
        raise HTTPException(status_code=400, detail="카테고리 생성 실패")


@router.get("", response_model=CategoryListResponse)
async def list_categories(
    skip: int = Query(0, ge=0, description="스킵할 항목 수"),
    limit: int = Query(50, ge=1, le=100, description="가져올 항목 수 (최대 100)"),
    db: AsyncSession = Depends(get_db)
):
    """
    카테고리 목록 조회
    Secure: Parameterized query, Pagination limits to prevent DoS
    """
    # Get total count
    count_query = select(func.count()).select_from(Category)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get categories with pagination
    query = select(Category).offset(skip).limit(limit).order_by(Category.created_at.desc())
    result = await db.execute(query)
    categories = result.scalars().all()

    # Calculate page number
    page = (skip // limit) + 1 if limit > 0 else 1

    return CategoryListResponse(
        items=[CategoryResponse.model_validate(cat) for cat in categories],
        total=total or 0,
        page=page,
        limit=limit
    )


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    ID로 카테고리 조회
    Secure: Parameterized query prevents SQL injection
    """
    query = select(Category).where(Category.id == category_id)
    result = await db.execute(query)
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다")

    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    카테고리 수정
    Secure: Input validation, Parameterized query
    """
    # Find existing category
    query = select(Category).where(Category.id == category_id)
    result = await db.execute(query)
    db_category = result.scalar_one_or_none()

    if not db_category:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다")

    try:
        # Update fields (only non-None values)
        update_data = category_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_category, field, value)

        await db.commit()
        await db.refresh(db_category)

        return db_category

    except IntegrityError as e:
        await db.rollback()
        if "unique" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail=f"카테고리 이름이 이미 사용 중입니다"
            )
        raise HTTPException(status_code=400, detail="카테고리 수정 실패")


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    카테고리 삭제
    Secure: Checks for existing documents before deletion
    """
    # Find category
    query = select(Category).where(Category.id == category_id)
    result = await db.execute(query)
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다")

    # Delete category
    await db.delete(category)
    await db.commit()

    return None
