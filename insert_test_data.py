"""
테스트 사용 이력 데이터 추가
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import random
from app.models.usage import UsageHistory
from app.core.config import settings

async def insert_test_data():
    # DB 연결
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 최근 30일간의 데이터 생성
        now = datetime.utcnow()

        test_data = []

        # 한국도로공사 실제 부처 목록
        departments = [
            "인사처", "감사처", "홍보처", "기획처", "첨단융복합팀",
            "미래전략처", "구조물처", "도로기술마켓처", "안전혁신처", "지하고속도로추진단",
            "설계처", "성과혁신처", "법무처", "총무처",
            "사업개발처", "통행료시스템처", "인력처",
            "통행료정책처", "해외사업처", "시설처", "재무처", "통행료정산센터",
            "기술심사처", "ITS지원센터",
            "도로처", "교통처", "품질환경처",
            "건설처", "휴게사업처", "토지처", "재난관리처"
        ]

        # 실제 모델 목록 (ex-gpt에서 사용)
        models = [
            "Qwen3-32B",  # 실제 Chat 모델
            "Qwen/Qwen2.5-32B-Instruct",  # Qwen2.5 32B
            "meta-llama/Llama-3.1-8B-Instruct",  # Llama 3.1 8B
        ]

        # 샘플 질문
        questions = [
            "한국도로공사의 안전관리 규정은?",
            "차량 통행료 할인 정책에 대해 알려주세요",
            "하이패스 단말기 설치 방법은?",
            "도로 보수 작업 절차를 설명해주세요",
            "직원 복지 제도가 어떻게 되나요?",
            "출장비 청구는 어떻게 하나요?",
            "연차 신청 절차를 알려주세요",
            "업무 보고서 작성 양식은?",
            "고객 불만 처리 프로세스는?",
            "신입사원 교육 프로그램은?"
        ]

        print("📊 테스트 데이터 생성 중...")

        # 30일치 데이터 생성
        for day in range(30):
            date = now - timedelta(days=day)

            # 하루에 20~100개의 질문 생성
            daily_count = random.randint(20, 100)

            for _ in range(daily_count):
                # 시간대별 분포 (업무시간에 더 많이)
                hour = random.choices(
                    range(24),
                    weights=[1, 1, 1, 1, 1, 1, 2, 3, 5, 8, 10, 10, 8, 10, 12, 10, 8, 5, 3, 2, 1, 1, 1, 1]
                )[0]

                created_at = date.replace(
                    hour=hour,
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59)
                )

                department = random.choice(departments)
                user_num = random.randint(1, 100)

                usage = UsageHistory(
                    user_id=f"{department}_user{user_num}",
                    session_id=f"session_{random.randint(1000, 9999)}",
                    question=random.choice(questions),
                    answer=f"답변 내용입니다. (샘플 데이터)",
                    model_name=random.choice(models),
                    response_time=random.randint(500, 3000),  # 0.5~3초
                    thinking_content=f"사고 과정 (샘플)",
                    ip_address=f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
                    usage_metadata={
                        "department": department,
                        "user_role": random.choice(["일반직원", "관리자", "팀장"])
                    },
                    created_at=created_at
                )

                test_data.append(usage)

        print(f"✅ {len(test_data)}개의 테스트 데이터 생성 완료")
        print("💾 데이터베이스에 저장 중...")

        # 데이터 저장
        session.add_all(test_data)
        await session.commit()

        print(f"✅ 데이터 저장 완료!")
        print(f"   - 총 레코드: {len(test_data)}개")
        print(f"   - 기간: {(now - timedelta(days=29)).date()} ~ {now.date()}")
        print(f"   - 부서: {len(departments)}개 (한국도로공사 실제 부처)")
        print(f"   - 모델: {len(models)}개 (Qwen3-32B, Qwen2.5-32B, Llama-3.1-8B)")
        print(f"\n📋 부서 목록:")
        for i, dept in enumerate(departments, 1):
            print(f"   {i}. {dept}")

if __name__ == "__main__":
    asyncio.run(insert_test_data())
