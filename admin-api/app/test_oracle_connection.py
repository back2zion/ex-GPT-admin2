"""
Oracle DB 연결 테스트 스크립트
사내메일 시스템 Oracle DB 연결 확인
"""
import oracledb
import sys
from app.core.config import settings

def test_oracle_connection():
    """Oracle DB 연결 테스트"""

    print("=" * 60)
    print("Oracle DB 연결 테스트 시작")
    print("=" * 60)

    # 연결 정보 출력
    print(f"\n📋 연결 정보:")
    print(f"  - Host: {settings.MAIL_ORACLE_HOST}")
    print(f"  - Port: {settings.MAIL_ORACLE_PORT}")
    print(f"  - Service: {settings.MAIL_ORACLE_SERVICE}")
    print(f"  - User: {settings.MAIL_ORACLE_USER}")
    print(f"  - Password: {'*' * len(settings.MAIL_ORACLE_PASSWORD)}")

    try:
        # 연결 문자열 생성
        connection_string = (
            f"{settings.MAIL_ORACLE_USER}/"
            f"{settings.MAIL_ORACLE_PASSWORD}@"
            f"{settings.MAIL_ORACLE_HOST}:"
            f"{settings.MAIL_ORACLE_PORT}/"
            f"{settings.MAIL_ORACLE_SERVICE}"
        )

        print(f"\n🔄 연결 시도 중...")
        connection = oracledb.connect(connection_string)

        print(f"✅ 연결 성공!")

        # 버전 정보 조회
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM v$version WHERE banner LIKE 'Oracle%'")
        version = cursor.fetchone()

        if version:
            print(f"\n📊 Oracle 버전:")
            print(f"  {version[0]}")

        # 사용자 정보 조회
        cursor.execute("SELECT USER FROM DUAL")
        user = cursor.fetchone()
        print(f"\n👤 현재 접속 사용자: {user[0]}")

        # 테이블 접근 권한 확인
        print(f"\n🔑 테이블 접근 권한 확인:")

        tables_to_check = [
            ('EXGWMAIN.MAIL_DOC', 'INSERT'),
            ('EXGWMAIN.MAIL_INBOX', 'INSERT'),
            ('EXGWMAIN.PT_USER', 'SELECT'),
        ]

        for table_name, privilege in tables_to_check:
            try:
                # 권한 확인을 위한 쿼리
                if privilege == 'SELECT':
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE ROWNUM = 1")
                    cursor.fetchone()
                    print(f"  ✅ {table_name} - {privilege} 권한 있음")
                elif privilege == 'INSERT':
                    # INSERT 권한은 실제 INSERT 없이 확인하기 어려우므로 테이블 존재 여부만 확인
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE ROWNUM = 1")
                    cursor.fetchone()
                    print(f"  ✅ {table_name} - 테이블 접근 가능 (INSERT 권한은 실제 사용 시 확인)")
            except Exception as e:
                print(f"  ❌ {table_name} - 접근 불가: {str(e)}")

        # 시퀀스 접근 확인
        print(f"\n🔢 시퀀스 접근 확인:")
        try:
            cursor.execute("SELECT EXGWMAIN.XFMAIL_SEQ.NEXTVAL FROM DUAL")
            seq_val = cursor.fetchone()
            print(f"  ✅ EXGWMAIN.XFMAIL_SEQ - 접근 가능 (현재 값: {seq_val[0]})")
            print(f"  ⚠️  시퀀스 값이 증가되었습니다. 테스트 목적으로만 사용하세요.")
        except Exception as e:
            print(f"  ❌ EXGWMAIN.XFMAIL_SEQ - 접근 불가: {str(e)}")

        cursor.close()
        connection.close()

        print(f"\n" + "=" * 60)
        print("✅ Oracle DB 연결 테스트 완료!")
        print("=" * 60)

        return True

    except oracledb.DatabaseError as e:
        error, = e.args
        print(f"\n❌ Oracle 데이터베이스 오류:")
        print(f"  - 오류 코드: {error.code}")
        print(f"  - 오류 메시지: {error.message}")

        if error.code == 1017:
            print(f"\n💡 해결 방법:")
            print(f"  - 사용자명 또는 비밀번호가 잘못되었습니다.")
            print(f"  - .env 파일의 MAIL_ORACLE_USER, MAIL_ORACLE_PASSWORD를 확인하세요.")
        elif error.code == 12154:
            print(f"\n💡 해결 방법:")
            print(f"  - Service Name이 잘못되었습니다.")
            print(f"  - .env 파일의 MAIL_ORACLE_SERVICE를 확인하세요.")
        elif error.code in [12541, 12514]:
            print(f"\n💡 해결 방법:")
            print(f"  - 호스트 또는 포트 번호가 잘못되었거나 리스너가 실행되지 않습니다.")
            print(f"  - .env 파일의 MAIL_ORACLE_HOST, MAIL_ORACLE_PORT를 확인하세요.")
            print(f"  - 방화벽에서 {settings.MAIL_ORACLE_HOST}:{settings.MAIL_ORACLE_PORT} 포트가 열려있는지 확인하세요.")

        return False

    except Exception as e:
        print(f"\n❌ 예상치 못한 오류:")
        print(f"  {str(e)}")
        return False

if __name__ == "__main__":
    success = test_oracle_connection()
    sys.exit(0 if success else 1)
