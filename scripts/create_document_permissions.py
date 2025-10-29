"""
문서 권한 초기 데이터 생성
부서별 학습데이터 참조 범위 지정 구현
"""
import psycopg2
from datetime import datetime

# DB 연결 정보
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'admin_db',
    'user': 'postgres',
    'password': 'password'
}

# 부서별 키워드 매핑 (문서 제목에서 부서 추론)
DEPARTMENT_KEYWORDS = {
    '경영기획처': ['경영', '기획', '전략', '성과'],
    '건설처': ['건설', '공사', '토목', '구조', '설계'],
    '기술연구원': ['기술', '연구', 'R&D', '개발', '평가'],
    '스마트도로처': ['스마트', 'ICT', '자율주행', '빅데이터', '디지털'],
    '도로교통연구원': ['교통', '도로', '운영', '관리'],
    '미래사업처': ['미래', '신사업', '투자'],
    '혁신기획처': ['혁신', '프로세스', '디지털전환'],
    '안전환경처': ['안전', '재난', '환경', '위험'],
    '감사실': ['감사', '조사', '심사'],
    '홍보실': ['홍보', '대외협력', '미디어'],
    '법무통상처': ['법무', '송무', '계약'],
    '인사처': ['인사', '채용', '교육', '복지'],
}

# 전체 공개 문서 키워드
PUBLIC_KEYWORDS = ['공고', '안내', '가이드', 'guide', '매뉴얼', '절차', '규정']

# 보안 문서 키워드 (제한적 접근)
RESTRICTED_KEYWORDS = ['보안', '기밀', '내부', '취약점', '분석', '평가']


def get_department_id_by_name(cur, name: str) -> int:
    """부서명으로 부서 ID 조회"""
    cur.execute("SELECT id FROM departments WHERE name = %s LIMIT 1", (name,))
    result = cur.fetchone()
    return result[0] if result else None


def get_all_root_departments(cur):
    """최상위 부서 조회"""
    cur.execute("""
        SELECT id, name
        FROM departments
        WHERE parent_id IS NULL
        ORDER BY id
    """)
    return cur.fetchall()


def infer_department_from_title(title: str, departments: dict) -> list:
    """문서 제목에서 관련 부서 추론"""
    title_lower = title.lower()
    matched_depts = []

    # 전체 공개 키워드 체크
    for keyword in PUBLIC_KEYWORDS:
        if keyword in title_lower:
            return None  # None means all departments

    # 보안 키워드 체크 - 특정 부서만
    is_restricted = any(keyword in title_lower for keyword in RESTRICTED_KEYWORDS)

    # 부서별 키워드 매칭
    for dept_name, keywords in DEPARTMENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in title_lower:
                matched_depts.append(dept_name)
                break

    # 보안 문서는 매칭된 부서만
    if is_restricted and matched_depts:
        return matched_depts

    # 키워드 매칭 없으면 전체 공개
    if not matched_depts:
        return None  # All departments

    return matched_depts


def create_permissions():
    """문서 권한 생성"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        print("=" * 70)
        print("문서 권한 초기 데이터 생성")
        print("=" * 70)

        # 1. 기존 권한 삭제 (재실행 대비)
        cur.execute("DELETE FROM document_permissions")
        conn.commit()
        print("✓ 기존 권한 데이터 삭제\n")

        # 2. 최상위 부서 조회
        root_depts = get_all_root_departments(cur)
        dept_dict = {name: dept_id for dept_id, name in root_depts}
        print(f"📋 최상위 부서 {len(root_depts)}개 로드")
        for dept_id, name in root_depts[:10]:
            print(f"  - {name} (ID: {dept_id})")
        if len(root_depts) > 10:
            print(f"  ... 외 {len(root_depts)-10}개\n")

        # 3. 모든 문서 조회
        cur.execute("""
            SELECT id, document_id, title, category_id
            FROM documents
            ORDER BY id
        """)
        documents = cur.fetchall()
        print(f"\n📚 총 {len(documents)}개 문서 처리 중...\n")

        # 4. 각 문서에 대해 권한 생성
        all_permissions = 0
        dept_restricted = 0
        public_docs = 0

        for doc_id, document_id, title, category_id in documents:
            # 제목에서 부서 추론
            related_depts = infer_department_from_title(title, dept_dict)

            if related_depts is None:
                # 전체 공개 - 모든 최상위 부서에 권한 부여
                for dept_name, dept_id in dept_dict.items():
                    now = datetime.now()
                    cur.execute("""
                        INSERT INTO document_permissions
                        (document_id, department_id, can_read, can_write, can_delete, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        doc_id,
                        dept_id,
                        True,  # can_read
                        False,  # can_write
                        False,  # can_delete
                        now,
                        now
                    ))
                    all_permissions += 1
                public_docs += 1
                print(f"  ✓ [{doc_id:4d}] {title[:50]:50s} → 전체 공개 ({len(dept_dict)}개 부서)")

            elif related_depts:
                # 특정 부서만 접근 가능
                granted_count = 0
                for dept_name in related_depts:
                    dept_id = dept_dict.get(dept_name)
                    if dept_id:
                        now = datetime.now()
                        cur.execute("""
                            INSERT INTO document_permissions
                            (document_id, department_id, can_read, can_write, can_delete, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            doc_id,
                            dept_id,
                            True,  # can_read
                            False,  # can_write
                            False,  # can_delete
                            now,
                            now
                        ))
                        all_permissions += 1
                        granted_count += 1

                if granted_count > 0:
                    dept_names = ', '.join(related_depts[:3])
                    if len(related_depts) > 3:
                        dept_names += f' 외 {len(related_depts)-3}'
                    print(f"  ✓ [{doc_id:4d}] {title[:50]:50s} → {dept_names}")
                    dept_restricted += 1
                else:
                    # 매칭 실패 - 전체 공개로 폴백
                    for dept_name, dept_id in dept_dict.items():
                        now = datetime.now()
                        cur.execute("""
                            INSERT INTO document_permissions
                            (document_id, department_id, can_read, can_write, can_delete, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            doc_id,
                            dept_id,
                            True,
                            False,
                            False,
                            now,
                            now
                        ))
                        all_permissions += 1
                    public_docs += 1
                    print(f"  ✓ [{doc_id:4d}] {title[:50]:50s} → 전체 공개 (폴백)")

        # 5. 커밋
        conn.commit()

        # 6. 통계 출력
        print("\n" + "=" * 70)
        print("📊 문서 권한 생성 완료")
        print("=" * 70)
        print(f"총 문서 수: {len(documents)}개")
        print(f"  - 전체 공개: {public_docs}개")
        print(f"  - 부서 제한: {dept_restricted}개")
        print(f"\n생성된 권한 레코드: {all_permissions}개")
        print(f"평균 권한/문서: {all_permissions/len(documents):.1f}개")

        # 7. 검증
        cur.execute("""
            SELECT
                COUNT(DISTINCT document_id) as docs_with_perms,
                COUNT(*) as total_perms
            FROM document_permissions
        """)
        docs_with_perms, total_perms = cur.fetchone()

        print(f"\n검증:")
        print(f"  권한이 있는 문서: {docs_with_perms}/{len(documents)}")
        print(f"  총 권한 레코드: {total_perms}")

        # 8. 부서별 접근 가능 문서 수
        print(f"\n부서별 접근 가능 문서 수 (상위 10개):")
        cur.execute("""
            SELECT
                d.name,
                COUNT(DISTINCT dp.document_id) as accessible_docs
            FROM document_permissions dp
            JOIN departments d ON d.id = dp.department_id
            GROUP BY d.name
            ORDER BY accessible_docs DESC
            LIMIT 10
        """)
        for dept_name, doc_count in cur.fetchall():
            print(f"  {dept_name:30s}: {doc_count:3d}개 문서")

        print("\n✅ 완료!")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    create_permissions()
