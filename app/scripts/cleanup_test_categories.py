#!/usr/bin/env python3
"""
테스트 카테고리 정리 스크립트
Category 0~14 및 기타 테스트 데이터 삭제
"""
import asyncio
import sys

# PYTHONPATH 설정
sys.path.insert(0, '/app')

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.core.database import AsyncSessionLocal
from app.models.category import Category


async def cleanup_test_categories():
    """테스트 카테고리 삭제"""
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("테스트 카테고리 삭제 시작")
        print("=" * 60)

        # 삭제할 카테고리 목록
        test_category_names = [
            "법령 문서",
            "Category 0",
            "Category 1",
            "Category 2",
            "Category 3",
            "Category 4",
            "Category 5",
            "Category 6",
            "Category 7",
            "Category 8",
            "Category 9",
            "Category 10",
            "Category 11",
            "Category 12",
            "Category 13",
            "Category 14",
            "Integration Test"
        ]

        deleted_count = 0

        for name in test_category_names:
            # 카테고리 조회
            query = select(Category).where(Category.name == name)
            result = await db.execute(query)
            category = result.scalar_one_or_none()

            if category:
                print(f"🗑️  '{category.name}' 삭제 중... (ID: {category.id})")
                await db.delete(category)
                deleted_count += 1
            else:
                print(f"⏭️  '{name}' - 존재하지 않음 (스킵)")

        # 커밋
        if deleted_count > 0:
            await db.commit()
            print("=" * 60)
            print(f"✅ 테스트 카테고리 {deleted_count}개 삭제 완료")
        else:
            print("=" * 60)
            print("ℹ️  삭제할 테스트 카테고리가 없습니다")

        print("=" * 60)


async def list_remaining_categories():
    """남은 카테고리 목록 조회"""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select, func

        # 총 개수
        count_query = select(func.count()).select_from(Category)
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # 목록 조회
        query = select(Category).order_by(Category.id)
        result = await db.execute(query)
        categories = result.scalars().all()

        print("\n" + "=" * 80)
        print(f"남은 카테고리 목록 (총 {total}개)")
        print("=" * 80)
        print(f"{'ID':<5} {'이름':<15} {'파싱패턴':<12} {'설명':<50}")
        print("-" * 80)

        for cat in categories:
            desc = cat.description[:47] + "..." if len(cat.description) > 50 else cat.description
            print(f"{cat.id:<5} {cat.name:<15} {cat.parsing_pattern.value:<12} {desc:<50}")

        print("=" * 80)


async def main():
    """메인 실행"""
    try:
        # 테스트 카테고리 삭제
        await cleanup_test_categories()

        # 남은 목록 확인
        await list_remaining_categories()

        print("\n✅ 정리 작업이 완료되었습니다!")
        print("📝 관리자 페이지에서 확인: https://ui.datastreams.co.kr/admin/#/vector-data")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
