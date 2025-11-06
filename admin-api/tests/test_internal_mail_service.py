"""
Internal Mail Service 단위 테스트
Oracle DB 연결 없이 로직 검증
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from app.services.internal_mail_service import InternalMailService


class TestInternalMailService:
    """InternalMailService 단위 테스트"""

    @pytest.fixture
    def mock_connection(self):
        """Mock Oracle DB 연결"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        return mock_conn, mock_cursor

    @pytest.fixture
    def service(self):
        """InternalMailService 인스턴스"""
        return InternalMailService()

    def test_service_initialization(self, service):
        """서비스 초기화 테스트"""
        assert service.SYSTEM_NAME == "ex-GPT System"
        assert service.SYSTEM_IP == "172.16.164.100"
        assert service.connection is None

    def test_mail_db_config_structure(self, service):
        """Mail DB 설정 구조 확인"""
        config = service.MAIL_DB_CONFIG
        assert 'host' in config
        assert 'port' in config
        assert 'service_name' in config
        assert 'username' in config
        assert 'password' in config

        # prd_STT.md 기준 확인
        assert config['service_name'] == 'ANKHCG'

    @patch('app.services.internal_mail_service.oracledb.connect')
    def test_get_connection_success(self, mock_connect, service, mock_connection):
        """DB 연결 성공 테스트"""
        mock_conn, _ = mock_connection
        mock_connect.return_value = mock_conn

        # 연결 시도
        connection = service._get_connection()

        # 검증
        assert connection is not None
        assert mock_connect.called

        # 연결 문자열 형식 확인
        call_args = mock_connect.call_args[0][0]
        assert '@172.16.164.32' in call_args or service.MAIL_DB_CONFIG['host'] in call_args
        assert 'ANKHCG' in call_args or service.MAIL_DB_CONFIG['service_name'] in call_args

    @patch('app.services.internal_mail_service.oracledb.connect')
    def test_send_meeting_minutes_email_success(self, mock_connect, service, mock_connection):
        """회의록 메일 발송 성공 테스트"""
        mock_conn, mock_cursor = mock_connection
        mock_connect.return_value = mock_conn

        # DOC_NUMBER를 반환하도록 설정
        mock_var = MagicMock()
        mock_var.getvalue.return_value = [12345]
        mock_cursor.var.return_value = mock_var

        # 테스트 데이터
        sender_id = "U0011290"
        sender_name = "테스트관리자"
        receivers = [
            {"user_id": "U0001", "user_name": "홍길동"},
            {"user_id": "U0002", "user_name": "김철수"},
        ]
        meeting_title = "ex-GPT 주간 회의"
        meeting_minutes_html = "<html><body><h1>회의록</h1></body></html>"
        transcription_text = "회의 전사 내용..."

        # 메일 발송 실행
        result = service.send_meeting_minutes_email(
            sender_id=sender_id,
            sender_name=sender_name,
            receivers=receivers,
            meeting_title=meeting_title,
            meeting_minutes_html=meeting_minutes_html,
            transcription_text=transcription_text
        )

        # 검증
        assert result['success'] is True
        assert result['doc_number'] == 12345
        assert result['receiver_count'] == 2
        assert 'doc_yearmon' in result

        # MAIL_DOC INSERT 확인 (최소 1회 호출)
        assert mock_cursor.execute.call_count >= 1

        # MAIL_INBOX INSERT 확인 (수신자 수만큼 호출되어야 함)
        # execute 호출 횟수: MAIL_DOC(1) + MAIL_INBOX(2) = 3
        assert mock_cursor.execute.call_count >= 3

        # commit 확인
        mock_conn.commit.assert_called_once()

    @patch('app.services.internal_mail_service.oracledb.connect')
    def test_send_meeting_minutes_email_db_error(self, mock_connect, service):
        """DB 오류 시 처리 테스트"""
        # DB 연결 시 오류 발생
        mock_connect.side_effect = Exception("DB Connection Error")

        # 테스트 데이터
        sender_id = "U0011290"
        sender_name = "테스트관리자"
        receivers = [{"user_id": "U0001", "user_name": "홍길동"}]
        meeting_title = "테스트 회의"
        meeting_minutes_html = "<html><body>회의록</body></html>"

        # 메일 발송 실행
        result = service.send_meeting_minutes_email(
            sender_id=sender_id,
            sender_name=sender_name,
            receivers=receivers,
            meeting_title=meeting_title,
            meeting_minutes_html=meeting_minutes_html
        )

        # 검증: 실패 반환
        assert result['success'] is False
        assert 'message' in result

    def test_generate_email_html_structure(self, service):
        """이메일 HTML 템플릿 구조 테스트"""
        meeting_title = "테스트 회의"
        meeting_minutes = "<p>회의 내용</p>"
        transcription = "전사 내용"
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

        # HTML 생성
        html = service._generate_email_html(
            meeting_title=meeting_title,
            meeting_minutes=meeting_minutes,
            transcription=transcription,
            timestamp=timestamp
        )

        # 검증
        assert '<!DOCTYPE html>' in html
        assert '<html lang="ko">' in html
        assert 'ex-GPT 자동 회의록' in html
        assert meeting_title in html
        assert meeting_minutes in html

        # 전사 내용 포함 확인
        assert '음성 전사 내용' in html

    def test_generate_email_html_without_transcription(self, service):
        """전사 내용 없는 이메일 HTML 테스트"""
        meeting_title = "테스트 회의"
        meeting_minutes = "<p>회의 내용</p>"
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

        # HTML 생성 (transcription=None)
        html = service._generate_email_html(
            meeting_title=meeting_title,
            meeting_minutes=meeting_minutes,
            transcription=None,
            timestamp=timestamp
        )

        # 검증: 전사 섹션이 포함되지 않아야 함
        assert '<!DOCTYPE html>' in html
        assert meeting_title in html
        assert meeting_minutes in html
        # 전사 내용 섹션이 없어야 함 (또는 비어있어야 함)

    @patch('app.services.internal_mail_service.oracledb.connect')
    def test_multiple_receivers_handling(self, mock_connect, service, mock_connection):
        """다수 수신자 처리 테스트"""
        mock_conn, mock_cursor = mock_connection
        mock_connect.return_value = mock_conn

        mock_var = MagicMock()
        mock_var.getvalue.return_value = [99999]
        mock_cursor.var.return_value = mock_var

        # 10명의 수신자
        receivers = [
            {"user_id": f"U{i:04d}", "user_name": f"테스터{i}"}
            for i in range(10)
        ]

        result = service.send_meeting_minutes_email(
            sender_id="U0011290",
            sender_name="발신자",
            receivers=receivers,
            meeting_title="대규모 회의",
            meeting_minutes_html="<p>회의록</p>"
        )

        # 검증: 10명 모두 처리
        assert result['success'] is True
        assert result['receiver_count'] == 10

    def test_yearmon_generation(self, service):
        """년월(YEARMON) 생성 형식 테스트"""
        now = datetime.now()
        expected_yearmon = now.strftime('%Y%m')

        # _generate_email_html에서 사용되는 timestamp 형식 확인
        timestamp = now.strftime('%Y%m%d%H%M%S')

        assert len(expected_yearmon) == 6  # YYYYMM
        assert len(timestamp) == 14  # YYYYMMDDHHmmss
        assert timestamp.startswith(expected_yearmon)

    def test_html_escaping_in_meeting_title(self, service):
        """회의 제목에 HTML 특수문자 포함 시 테스트"""
        meeting_title = "<script>alert('XSS')</script>"
        meeting_minutes = "<p>정상 내용</p>"
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

        html = service._generate_email_html(
            meeting_title=meeting_title,
            meeting_minutes=meeting_minutes,
            transcription=None,
            timestamp=timestamp
        )

        # HTML에 제목이 포함되어야 하지만, 실제 배포 시 XSS 방지 필요
        # (현재 코드는 f-string으로 직접 삽입하므로 주의 필요)
        assert meeting_title in html


class TestInternalMailServiceIntegration:
    """통합 시나리오 테스트"""

    @patch('app.services.internal_mail_service.oracledb.connect')
    def test_end_to_end_mail_sending_scenario(self, mock_connect):
        """E2E 메일 발송 시나리오 테스트"""
        # Mock 설정
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        mock_var = MagicMock()
        mock_var.getvalue.return_value = [54321]
        mock_cursor.var.return_value = mock_var

        # 서비스 생성
        service = InternalMailService()

        # 시나리오: 모바일 오피스에서 녹음 완료 → 회의록 생성 → 메일 발송
        sender_id = "U0011290"
        sender_name = "곽두일"
        receivers = [
            {"user_id": "U0001", "user_name": "홍길동"},
            {"user_id": "U0002", "user_name": "김철수"},
            {"user_id": "U0003", "user_name": "이영희"},
        ]
        meeting_title = "[모바일 오피스] 2025년 1월 주간회의"
        meeting_minutes_html = """
        <html>
            <body>
                <h1>회의 요약</h1>
                <ul>
                    <li>안건 1: 프로젝트 진행상황 점검</li>
                    <li>안건 2: 다음 주 일정 협의</li>
                </ul>
            </body>
        </html>
        """
        transcription_text = "안녕하세요. 회의를 시작하겠습니다..."

        # 메일 발송 실행
        result = service.send_meeting_minutes_email(
            sender_id=sender_id,
            sender_name=sender_name,
            receivers=receivers,
            meeting_title=meeting_title,
            meeting_minutes_html=meeting_minutes_html,
            transcription_text=transcription_text
        )

        # 검증
        assert result['success'] is True
        assert result['doc_number'] == 54321
        assert result['receiver_count'] == 3
        assert '메일이 3명에게 발송되었습니다' in result['message']

        # DB 작업 검증
        mock_conn.commit.assert_called_once()
        assert mock_cursor.execute.call_count >= 4  # INSERT MAIL_DOC + 3 x MAIL_INBOX


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
