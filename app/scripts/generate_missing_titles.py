#!/usr/bin/env python3
"""
대화 제목 없는 세션에 제목 자동 생성
첫 번째 질문을 기반으로 간결한 제목 생성
"""
import asyncio
import sys

# PYTHONPATH 설정
sys.path.insert(0, '/app')

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app.core.database import AsyncSessionLocal
from app.models import UsageHistory
from datetime import datetime


async def generate_missing_titles():
    """대화 제목이 없는 세션에 제목 생성"""
    async with AsyncSessionLocal() as db:
        print("=" * 80)
        print("대화 제목 자동 생성 시작")
        print("=" * 80)

        # 대화 제목이 없거나 "대화 제목 없음"인 세션의 첫 번째 메시지 조회
        # 각 세션별로 첫 번째 메시지를 가져옴
        query = select(
            UsageHistory.session_id,
            UsageHistory.question,
            func.min(UsageHistory.created_at).label('first_time')
        ).filter(
            (UsageHistory.conversation_title == None) |
            (UsageHistory.conversation_title == "대화 제목 없음") |
            (UsageHistory.conversation_title == "")
        ).filter(
            ~UsageHistory.session_id.like('title_gen_%')  # title_gen_ 세션 제외
        ).group_by(
            UsageHistory.session_id,
            UsageHistory.question
        ).order_by(
            func.min(UsageHistory.created_at).asc()
        )

        result = await db.execute(query)
        sessions_to_update = result.all()

        print(f"📝 제목 생성 대상 세션: {len(sessions_to_update)}개\n")

        updated_count = 0

        # 세션별로 그룹화 (첫 번째 메시지만 사용)
        session_dict = {}
        for session_id, question, first_time in sessions_to_update:
            if session_id not in session_dict:
                session_dict[session_id] = {
                    'question': question,
                    'first_time': first_time
                }

        for session_id, data in session_dict.items():
            question = data['question']

            # 제목 생성: 질문의 처음 50자를 제목으로 사용
            title = question[:50].strip()
            if len(question) > 50:
                title += "..."

            # 해당 세션의 모든 레코드 업데이트
            update_query = update(UsageHistory).where(
                UsageHistory.session_id == session_id
            ).values(
                conversation_title=title,
                updated_at=datetime.utcnow()
            )

            result = await db.execute(update_query)
            record_count = result.rowcount

            if record_count > 0:
                print(f"✅ {session_id}")
                print(f"   제목: {title}")
                print(f"   업데이트된 레코드: {record_count}개\n")
                updated_count += 1

        # 커밋
        if updated_count > 0:
            await db.commit()
            print("=" * 80)
            print(f"✅ 제목 생성 완료: {updated_count}개 세션 업데이트")
        else:
            print("=" * 80)
            print("ℹ️  업데이트할 세션이 없습니다")

        print("=" * 80)


async def verify_titles():
    """생성된 제목 확인"""
    async with AsyncSessionLocal() as db:
        # 제목이 있는 세션 수
        query = select(
            func.count(func.distinct(UsageHistory.session_id))
        ).filter(
            UsageHistory.conversation_title != None,
            UsageHistory.conversation_title != "대화 제목 없음",
            UsageHistory.conversation_title != "",
            ~UsageHistory.session_id.like('title_gen_%')
        )
        result = await db.execute(query)
        with_title = result.scalar()

        # 제목이 없는 세션 수
        query = select(
            func.count(func.distinct(UsageHistory.session_id))
        ).filter(
            (UsageHistory.conversation_title == None) |
            (UsageHistory.conversation_title == "대화 제목 없음") |
            (UsageHistory.conversation_title == "")
        ).filter(
            ~UsageHistory.session_id.like('title_gen_%')
        )
        result = await db.execute(query)
        without_title = result.scalar()

        print("\n" + "=" * 80)
        print("📊 세션 제목 통계")
        print("=" * 80)
        print(f"✅ 제목 있음: {with_title}개 세션")
        print(f"❌ 제목 없음: {without_title}개 세션")
        print("=" * 80)

        # 최근 제목이 있는 세션 5개 조회
        query = select(
            UsageHistory.session_id,
            UsageHistory.conversation_title,
            func.max(UsageHistory.created_at).label('latest_time')
        ).filter(
            UsageHistory.conversation_title != None,
            UsageHistory.conversation_title != "대화 제목 없음",
            UsageHistory.conversation_title != "",
            ~UsageHistory.session_id.like('title_gen_%')
        ).group_by(
            UsageHistory.session_id,
            UsageHistory.conversation_title
        ).order_by(
            func.max(UsageHistory.created_at).desc()
        ).limit(10)

        result = await db.execute(query)
        recent_sessions = result.all()

        print("\n최근 세션 10개 (제목 있음):")
        print("-" * 80)
        for session_id, title, latest_time in recent_sessions:
            print(f"📝 {title}")
            print(f"   세션 ID: {session_id}")
            print(f"   최근 시간: {latest_time}")
            print()


async def main():
    """메인 실행"""
    try:
        # 제목 생성
        await generate_missing_titles()

        # 결과 확인
        await verify_titles()

        print("\n✅ 모든 작업이 완료되었습니다!")
        print("📝 사이드바를 새로고침하여 확인하세요: https://ui.datastreams.co.kr:20443/layout.html")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
