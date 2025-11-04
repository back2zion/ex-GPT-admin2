"""
더미 데이터 고도화: 입사년도와 직급의 상관관계 반영

사번 형식: YYYYXXXX (YYYY = 입사년도, XXXX = 순번)
- 1980년대 입사 → 2급갑, 2급을, 3급
- 직급이 낮을수록 입사년도가 늦음
"""
import psycopg2
import random
from datetime import datetime, timedelta

# DB 연결 정보
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'admin_db',
    'user': 'postgres',
    'password': 'password'
}

# 직급별 입사년도 범위 및 비율
RANK_CONFIG = {
    '2급갑': {'years': (1980, 1985), 'ratio': 0.005},  # 46명 (0.5%)
    '2급을': {'years': (1980, 1985), 'ratio': 0.005},  # 46명 (0.5%)
    '3급': {'years': (1985, 1995), 'ratio': 0.03},     # 276명 (3%)
    '4급': {'years': (1995, 2005), 'ratio': 0.08},     # 737명 (8%)
    '5급': {'years': (2005, 2015), 'ratio': 0.15},     # 1382명 (15%)
    '6급': {'years': (2015, 2020), 'ratio': 0.20},     # 1842명 (20%)
    '7급': {'years': (2020, 2023), 'ratio': 0.22},     # 2027명 (22%)
    '8급': {'years': (2023, 2025), 'ratio': 0.12},     # 1105명 (12%)
    '9급': {'years': (2023, 2025), 'ratio': 0.12},     # 1105명 (12%)
    '계약직': {'years': (2020, 2025), 'ratio': 0.03},   # 276명
    '인턴사원': {'years': (2023, 2025), 'ratio': 0.02}, # 184명
    '촉탁직': {'years': (2018, 2025), 'ratio': 0.02},   # 184명
    '순찰직': {'years': (2015, 2025), 'ratio': 0.01},   # 92명
    '현장지원직': {'years': (2015, 2025), 'ratio': 0.01}, # 92명
    '실무직(9급)': {'years': (2020, 2025), 'ratio': 0.01}  # 92명
}

# 한국 성씨 (빈도 반영)
SURNAMES = ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '한', '오', '서', '신', '권', '황', '안', '송', '류', '홍']
# 한국 이름 (2글자)
GIVEN_NAMES_2 = [
    '민준', '서준', '도윤', '예준', '시우', '주원', '하준', '지호', '지우', '준서',
    '서연', '서현', '지우', '서윤', '지유', '하은', '민서', '하윤', '윤서', '지원',
    '준영', '현우', '태양', '민재', '성민', '지훈', '현준', '승우', '승현', '유진',
    '수빈', '예은', '채원', '수아', '지아', '다은', '은서', '채은', '소율', '예린'
]
# 한국 이름 (3글자)
GIVEN_NAMES_3 = [
    '승현', '민지', '지현', '현준', '서영', '태형', '준혁', '재원', '수연', '은지',
    '정우', '혜진', '민수', '영호', '성훈', '주희', '동현', '예나', '상현', '보라'
]

# 부서별 팀 목록
DEPARTMENT_TEAMS = {
    1: ['경영기획팀', '전략기획팀', '성과관리팀', '경영지원팀'],
    2: ['건설기획팀', '공사관리팀', '품질관리팀', '토목설계팀', '구조설계팀'],
    3: ['기술개발팀', '연구기획팀', 'R&D센터', '기술평가팀'],
    4: ['스마트도로팀', 'ICT융합팀', '자율주행팀', '빅데이터팀'],
    5: ['교통운영팀', '도로관리팀', '유지보수팀', '안전점검팀'],
    6: ['미래전략팀', '신사업개발팀', '투자관리팀'],
    7: ['혁신기획팀', '프로세스혁신팀', '디지털전환팀'],
    8: ['안전관리팀', '재난대응팀', '위험관리팀'],
    9: ['감사기획팀', '조사팀', '심사팀'],
    10: ['홍보기획팀', '대외협력팀', '미디어팀'],
    11: ['법무지원팀', '송무팀', '계약법무팀'],
    12: ['인사기획팀', '채용팀', '교육팀', '복지팀'],
}

# 직책 (position) - 직급별
POSITIONS_BY_RANK = {
    '2급갑': ['본부장', '실장', '처장', '단장'],
    '2급을': ['본부장', '실장', '처장', '단장'],
    '3급': ['부장', '팀장', '센터장'],
    '4급': ['차장', '팀장', '파트장'],
    '5급': ['과장', '파트장', '주임'],
    '6급': ['대리', '주임', ''],
    '7급': ['사원', '주임', ''],
    '8급': ['사원', ''],
    '9급': ['사원', ''],
    '계약직': ['계약사원', ''],
    '인턴사원': ['인턴', ''],
    '촉탁직': ['촉탁', ''],
    '순찰직': ['순찰원', ''],
    '현장지원직': ['현장지원', ''],
    '실무직(9급)': ['실무사원', '']
}

def generate_employee_number(year: int, sequence: int) -> str:
    """사번 생성: YYYYXXXX"""
    return f"{year}{sequence:04d}"

def generate_korean_name() -> str:
    """한국 이름 생성"""
    surname = random.choice(SURNAMES)
    if random.random() < 0.7:  # 70%는 2글자 이름
        given_name = random.choice(GIVEN_NAMES_2)
    else:  # 30%는 3글자 이름
        given_name = random.choice(GIVEN_NAMES_3)
    return surname + given_name

def get_hire_date(year: int) -> datetime:
    """입사일 생성 (주로 1월, 3월, 7월, 9월)"""
    months = [1, 3, 7, 9]
    month = random.choice(months)
    day = random.randint(1, 28)
    return datetime(year, month, day)

def update_user_data():
    """9212명의 사용자 데이터를 현실적으로 업데이트"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        # 0. 기존 데이터 초기화 (중복 방지)
        print("기존 데이터 초기화 중...")
        cur.execute("""
            UPDATE users
            SET
                employee_number = NULL,
                username = CONCAT('temp_user_', id::text),
                email = CONCAT('temp_', id::text, '@temp.com')
        """)
        conn.commit()
        print("✓ 데이터 초기화 완료\n")

        # 1. 기존 사용자 조회
        cur.execute("SELECT id FROM users ORDER BY id")
        user_ids = [row[0] for row in cur.fetchall()]
        total_users = len(user_ids)
        print(f"총 {total_users}명의 사용자 데이터를 업데이트합니다...")

        # 2. 직급별 사용자 할당
        rank_users = {}
        user_idx = 0

        for rank, config in RANK_CONFIG.items():
            count = int(total_users * config['ratio'])
            rank_users[rank] = user_ids[user_idx:user_idx + count]
            user_idx += count
            print(f"{rank}: {count}명")

        # 3. 각 직급별 데이터 업데이트
        updated_count = 0
        used_employee_numbers = set()  # 이미 사용된 사번 추적

        for rank, ids in rank_users.items():
            year_range = RANK_CONFIG[rank]['years']
            positions = POSITIONS_BY_RANK.get(rank, [''])

            for user_id in ids:
                # 입사년도 랜덤 선택
                hire_year = random.randint(year_range[0], year_range[1])

                # 중복되지 않는 사번 생성
                max_attempts = 100
                for attempt in range(max_attempts):
                    sequence = random.randint(1, 9999)
                    employee_number = generate_employee_number(hire_year, sequence)

                    if employee_number not in used_employee_numbers:
                        used_employee_numbers.add(employee_number)
                        break
                else:
                    # 100번 시도해도 실패하면 순차적으로 할당
                    for seq in range(1, 10000):
                        employee_number = generate_employee_number(hire_year, seq)
                        if employee_number not in used_employee_numbers:
                            used_employee_numbers.add(employee_number)
                            break

                # 데이터 생성
                full_name = generate_korean_name()
                username = f"user{employee_number}"
                email = f"{username}@koreaexpressway.kr"
                position = random.choice(positions)

                # 부서 랜덤 선택 (조직 규모별 가중치)
                # - 본부/처/실 (1~73): 60%
                # - 지사/사업단 (74~162): 30%
                # - 관리소/센터 (163~622): 10%
                rand = random.random()
                if rand < 0.60:  # 60%: 본부/처/실
                    department_id = random.randint(1, 73)
                elif rand < 0.90:  # 30%: 지사/사업단
                    department_id = random.randint(74, 162)
                else:  # 10%: 관리소/센터
                    department_id = random.randint(163, 622)

                # 팀 선택
                if department_id <= 73:
                    dept_teams = DEPARTMENT_TEAMS.get(department_id, ['일반팀', '관리팀', '운영팀'])
                elif department_id <= 162:
                    dept_teams = ['관리팀', '운영팀', '지원팀', '현장팀']
                else:
                    dept_teams = ['1반', '2반', '3반', '현장팀']
                team = random.choice(dept_teams)

                # 직무 카테고리 (부서별로 다르게)
                if department_id <= 73:  # 본부/처/실
                    job_categories = ['행정직', '사무직', '연구직', '기술직']
                    weights = [0.4, 0.3, 0.2, 0.1]
                elif department_id <= 162:  # 지사/사업단
                    job_categories = ['기술직', '행정직', '사무직', '현장직']
                    weights = [0.4, 0.3, 0.2, 0.1]
                else:  # 관리소/센터
                    job_categories = ['현장직', '기술직', '사무직']
                    weights = [0.7, 0.2, 0.1]

                job_category = random.choices(job_categories, weights=weights)[0]

                # 업데이트 쿼리
                cur.execute("""
                    UPDATE users
                    SET
                        employee_number = %s,
                        full_name = %s,
                        username = %s,
                        email = %s,
                        rank = %s,
                        position = %s,
                        department_id = %s,
                        team = %s,
                        job_category = %s
                    WHERE id = %s
                """, (
                    employee_number,
                    full_name,
                    username,
                    email,
                    rank,
                    position,
                    department_id,
                    team,
                    job_category,
                    user_id
                ))

                updated_count += 1
                if updated_count % 1000 == 0:
                    print(f"진행: {updated_count}/{total_users} ({updated_count*100//total_users}%)")
                    conn.commit()

        # 4. 최종 커밋
        conn.commit()
        print(f"\n✅ 총 {updated_count}명의 데이터 업데이트 완료!")

        # 5. 검증: 직급별 분포 확인
        print("\n📊 직급별 분포:")
        cur.execute("""
            SELECT
                rank,
                COUNT(*) as count,
                MIN(SUBSTRING(employee_number, 1, 4)) as min_year,
                MAX(SUBSTRING(employee_number, 1, 4)) as max_year
            FROM users
            WHERE rank IS NOT NULL
            GROUP BY rank
            ORDER BY
                CASE
                    WHEN rank = '2급갑' THEN 1
                    WHEN rank = '2급을' THEN 2
                    WHEN rank = '3급' THEN 3
                    WHEN rank = '4급' THEN 4
                    WHEN rank = '5급' THEN 5
                    WHEN rank = '6급' THEN 6
                    WHEN rank = '7급' THEN 7
                    WHEN rank = '8급' THEN 8
                    WHEN rank = '9급' THEN 9
                    ELSE 99
                END;
        """)

        for row in cur.fetchall():
            print(f"  {row[0]:12s}: {row[1]:4d}명 (입사년도: {row[2]} ~ {row[3]})")

        # 6. 연도별 분포 확인
        print("\n📅 입사년도별 분포:")
        cur.execute("""
            SELECT
                SUBSTRING(employee_number, 1, 4) as year,
                COUNT(*) as count
            FROM users
            WHERE employee_number IS NOT NULL
            GROUP BY SUBSTRING(employee_number, 1, 4)
            ORDER BY year;
        """)

        year_dist = cur.fetchall()
        for year, count in year_dist[:10]:  # 처음 10년만 출력
            print(f"  {year}년: {count}명")
        print(f"  ... ({len(year_dist)}개 연도)")

        # 7. 부서 유형별 분포 확인
        print("\n🏢 부서 유형별 분포:")
        cur.execute("""
            SELECT
                CASE
                    WHEN department_id <= 73 THEN '본부/처/실 (1~73)'
                    WHEN department_id BETWEEN 74 AND 162 THEN '지사/사업단 (74~162)'
                    ELSE '관리소/센터 (163~622)'
                END as dept_type,
                COUNT(*) as user_count
            FROM users
            WHERE department_id IS NOT NULL
            GROUP BY
                CASE
                    WHEN department_id <= 73 THEN '본부/처/실 (1~73)'
                    WHEN department_id BETWEEN 74 AND 162 THEN '지사/사업단 (74~162)'
                    ELSE '관리소/센터 (163~622)'
                END
            ORDER BY MIN(department_id);
        """)

        for dept_type, count in cur.fetchall():
            print(f"  {dept_type}: {count}명 ({count*100//total_users}%)")

        # 8. 직무 카테고리별 분포
        print("\n💼 직무 카테고리별 분포:")
        cur.execute("""
            SELECT
                job_category,
                COUNT(*) as count
            FROM users
            WHERE job_category IS NOT NULL
            GROUP BY job_category
            ORDER BY count DESC;
        """)

        for job_cat, count in cur.fetchall():
            print(f"  {job_cat}: {count}명 ({count*100//total_users}%)")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("한국도로공사 더미 데이터 고도화")
    print("=" * 60)
    update_user_data()
    print("\n완료!")
