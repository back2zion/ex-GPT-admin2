#!/usr/bin/env python3
"""
한국도로공사용 카테고리 생성 스크립트
RFP 기반 17개 카테고리 자동 생성
"""
import asyncio
import sys
import os

# PYTHONPATH 설정
sys.path.insert(0, '/app')

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.category import Category, ParsingPattern


# 한국도로공사용 카테고리 정의 (RFP 기반)
CATEGORIES = [
    {
        "name": "법령",
        "description": "국가계약법, 야생동물보호법 등 관련 법령 (부서별 참조 범위 제한 가능)",
        "parsing_pattern": ParsingPattern.PARAGRAPH
    },
    {
        "name": "사규",
        "description": "한국도로공사 내부 규정 및 규칙",
        "parsing_pattern": ParsingPattern.PARAGRAPH
    },
    {
        "name": "업무기준",
        "description": "부서별 업무 수행 기준 및 가이드라인",
        "parsing_pattern": ParsingPattern.PARAGRAPH
    },
    {
        "name": "매뉴얼",
        "description": "업무 프로세스 매뉴얼, 시스템 사용 설명서 등",
        "parsing_pattern": ParsingPattern.PAGE
    },
    {
        "name": "지침",
        "description": "업무별 실무 지침서",
        "parsing_pattern": ParsingPattern.PARAGRAPH
    },
    {
        "name": "보고서",
        "description": "경영보고서, 분기보고서, 연간보고서 등 각종 보고서",
        "parsing_pattern": ParsingPattern.PAGE
    },
    {
        "name": "R&D 보고서",
        "description": "연구개발 관련 보고서 및 기술 연구 자료",
        "parsing_pattern": ParsingPattern.PAGE
    },
    {
        "name": "내부방침",
        "description": "경영방침, 부서별 운영방침 등",
        "parsing_pattern": ParsingPattern.PARAGRAPH
    },
    {
        "name": "보도자료",
        "description": "대외 발표 보도자료 및 언론 배포자료",
        "parsing_pattern": ParsingPattern.PARAGRAPH
    },
    {
        "name": "공시자료",
        "description": "알리오(공공기관 경영정보 공개시스템) 공시 자료",
        "parsing_pattern": ParsingPattern.PAGE
    },
    {
        "name": "감사",
        "description": "감사사례, 징계양정요구기준, 유사사례별 감사의견 등 (특정업무 맞춤형)",
        "parsing_pattern": ParsingPattern.PARAGRAPH
    },
    {
        "name": "안전",
        "description": "위험성평가, 안전관리 기준, 공종별 안전 매뉴얼 (특정업무 맞춤형)",
        "parsing_pattern": ParsingPattern.PARAGRAPH
    },
    {
        "name": "재난",
        "description": "재난상황별 대응 매뉴얼, 비상대응 절차 (특정업무 맞춤형)",
        "parsing_pattern": ParsingPattern.PARAGRAPH
    },
    {
        "name": "기술심사",
        "description": "기술 규격, 평가기준, 기술심사 가이드라인 (특정업무 맞춤형)",
        "parsing_pattern": ParsingPattern.PARAGRAPH
    },
    {
        "name": "계약",
        "description": "국가계약법 관련 문서, 계약서 양식, 계약 관련 법규 → 전부서 참조",
        "parsing_pattern": ParsingPattern.PARAGRAPH
    },
    {
        "name": "환경",
        "description": "야생동물보호법 등 환경 관련 법규 → 품질환경처만 참조",
        "parsing_pattern": ParsingPattern.PARAGRAPH
    },
    {
        "name": "민원",
        "description": "고객민원 응대 사례, STT 변환된 민원 데이터",
        "parsing_pattern": ParsingPattern.SENTENCE
    }
]


async def create_categories():
    """카테고리 생성 (중복 체크 포함)"""
    async with AsyncSessionLocal() as db:
        created_count = 0
        skipped_count = 0

        print("=" * 60)
        print("한국도로공사용 카테고리 생성 시작")
        print("=" * 60)

        for cat_data in CATEGORIES:
            # 중복 체크
            from sqlalchemy import select
            query = select(Category).where(Category.name == cat_data["name"])
            result = await db.execute(query)
            existing = result.scalar_one_or_none()

            if existing:
                print(f"⏭️  '{cat_data['name']}' - 이미 존재 (스킵)")
                skipped_count += 1
                continue

            # 카테고리 생성
            category = Category(
                name=cat_data["name"],
                description=cat_data["description"],
                parsing_pattern=cat_data["parsing_pattern"]
            )

            db.add(category)
            await db.commit()
            await db.refresh(category)

            print(f"✅ '{category.name}' 생성 완료 (ID: {category.id}, 파싱: {category.parsing_pattern.value})")
            created_count += 1

        print("=" * 60)
        print(f"카테고리 생성 완료: 신규 {created_count}개, 스킵 {skipped_count}개")
        print(f"총 카테고리: {created_count + skipped_count}개")
        print("=" * 60)


async def list_categories():
    """생성된 카테고리 목록 조회"""
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
        print(f"카테고리 목록 (총 {total}개)")
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
        # 카테고리 생성
        await create_categories()

        # 생성된 목록 확인
        await list_categories()

        print("\n✅ 모든 작업이 완료되었습니다!")
        print("📝 관리자 페이지에서 확인: https://ui.datastreams.co.kr/admin/#/vector-data")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
