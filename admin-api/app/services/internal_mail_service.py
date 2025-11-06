"""
한국도로공사 사내메일 연동 서비스
Oracle Database의 MAIL_DOC, MAIL_INBOX 테이블을 통한 메일 발송

참조: prd_STT.md - 전자문서시스템 사내메일 연동 인터페이스 설계서
"""
import logging
from datetime import datetime
from typing import List, Dict, Optional
import oracledb
from app.core.config import settings

logger = logging.getLogger(__name__)


class InternalMailService:
    """
    한국도로공사 사내메일 연동 서비스
    MAIL_DOC, MAIL_INBOX 테이블을 통한 메일 발송
    """

    # 사내메일 서버 정보 (prd_STT.md 기준)
    MAIL_DB_CONFIG = {
        'host': settings.MAIL_ORACLE_HOST,
        'port': settings.MAIL_ORACLE_PORT,
        'service_name': settings.MAIL_ORACLE_SERVICE,
        'username': settings.MAIL_ORACLE_USER,
        'password': settings.MAIL_ORACLE_PASSWORD
    }

    SYSTEM_NAME = "ex-GPT System"
    SYSTEM_IP = "172.16.164.100"  # ex-GPT 시스템 IP

    def __init__(self):
        """사내메일 서비스 초기화"""
        self.connection = None

    def _get_connection(self):
        """Oracle DB 연결"""
        if self.connection is None or not self._is_connection_alive():
            # python-oracledb thin mode (Instant Client 불필요)
            connection_string = (
                f"{self.MAIL_DB_CONFIG['username']}/"
                f"{self.MAIL_DB_CONFIG['password']}@"
                f"{self.MAIL_DB_CONFIG['host']}:"
                f"{self.MAIL_DB_CONFIG['port']}/"
                f"{self.MAIL_DB_CONFIG['service_name']}"
            )
            self.connection = oracledb.connect(connection_string)
            logger.info(f"✅ Oracle DB 연결 성공: {self.MAIL_DB_CONFIG['host']}")

        return self.connection

    def _is_connection_alive(self) -> bool:
        """연결 상태 확인"""
        try:
            if self.connection:
                self.connection.ping()
                return True
        except Exception:
            return False
        return False

    def close(self):
        """연결 종료"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Oracle DB 연결 종료")

    def send_meeting_minutes_email(
        self,
        sender_id: str,
        sender_name: str,
        receivers: List[Dict[str, str]],
        meeting_title: str,
        meeting_minutes_html: str,
        transcription_text: Optional[str] = None
    ) -> Dict:
        """
        회의록을 사내메일로 발송

        Args:
            sender_id: 발신자 사용자 ID (예: U0011290)
            sender_name: 발신자 이름
            receivers: 수신자 목록 [{"user_id": "U0001", "user_name": "홍길동"}, ...]
            meeting_title: 회의 제목
            meeting_minutes_html: HTML 형식의 회의록
            transcription_text: 전사 텍스트 (선택)

        Returns:
            Dict: {
                "success": bool,
                "doc_number": int,
                "doc_yearmon": str,
                "receiver_count": int,
                "message": str
            }
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 1. 현재 년월 및 타임스탬프 생성
            now = datetime.now()
            yearmon = now.strftime('%Y%m')
            timestamp = now.strftime('%Y%m%d%H%M%S')

            # 2. HTML 본문 생성
            email_html = self._generate_email_html(
                meeting_title=meeting_title,
                meeting_minutes=meeting_minutes_html,
                transcription=transcription_text,
                timestamp=timestamp
            )

            # 3. MAIL_DOC 테이블에 메일 본문 저장
            doc_number_var = cursor.var(int)

            insert_doc_sql = """
                INSERT INTO EXGWMAIN.MAIL_DOC (
                    DOC_YEARMON,
                    DOC_NUMBER,
                    DOC_TYPE,
                    DOC_SUBJECT,
                    DOC_MESSAGE,
                    DOC_WRITER,
                    DOC_WRITERNAME,
                    DOC_SPEC,
                    DOC_REQ_SYSTEM,
                    DOC_REQ_SYS_IP
                ) VALUES (
                    :yearmon,
                    EXGWMAIN.XFMAIL_SEQ.NEXTVAL,
                    'I',
                    :subject,
                    :content,
                    :writer_id,
                    :writer_name,
                    'ODNR',
                    :system_name,
                    :system_ip
                ) RETURNING DOC_NUMBER INTO :doc_number
            """

            cursor.execute(
                insert_doc_sql,
                yearmon=yearmon,
                subject=f"[회의록] {meeting_title}",
                content=email_html,
                writer_id=sender_id,
                writer_name=sender_name,
                system_name=self.SYSTEM_NAME,
                system_ip=self.SYSTEM_IP,
                doc_number=doc_number_var
            )

            doc_number = int(doc_number_var.getvalue()[0])
            logger.info(f"📧 MAIL_DOC 저장 완료: DOC_NUMBER={doc_number}")

            # 4. MAIL_INBOX 테이블에 수신자별 레코드 생성
            insert_inbox_sql = """
                INSERT INTO EXGWMAIN.MAIL_INBOX (
                    DOC_YEARMON,
                    DOC_NUMBER,
                    SENDER,
                    RECEIVER,
                    SEND_NAME,
                    RECV_NAME,
                    SEND_DATE,
                    RECV_DATE,
                    RESV_DATE,
                    CC_FLAG,
                    SEND_DONE
                ) VALUES (
                    :yearmon,
                    :doc_number,
                    :sender,
                    :receiver,
                    :send_name,
                    :recv_name,
                    :send_date,
                    '99999999999999',
                    :send_date,
                    'N',
                    'S'
                )
            """

            # 수신자별 INSERT
            receiver_count = 0
            for receiver in receivers:
                cursor.execute(
                    insert_inbox_sql,
                    yearmon=yearmon,
                    doc_number=doc_number,
                    sender=sender_id,
                    receiver=receiver['user_id'],
                    send_name=sender_name,
                    recv_name=receiver['user_name'],
                    send_date=timestamp
                )
                receiver_count += 1

            # 5. 커밋
            conn.commit()
            cursor.close()

            logger.info(
                f"✅ 사내메일 발송 완료 - DOC_NUMBER: {doc_number}, "
                f"수신자: {receiver_count}명"
            )

            return {
                "success": True,
                "doc_number": doc_number,
                "doc_yearmon": yearmon,
                "receiver_count": receiver_count,
                "message": f"사내메일이 {receiver_count}명에게 발송되었습니다."
            }

        except oracledb.Error as e:
            error = e.args[0] if e.args else e
            logger.error(
                f"❌ Oracle 오류: {error}",
                exc_info=True
            )
            if conn:
                conn.rollback()
            return {
                "success": False,
                "message": f"사내메일 발송 실패: {str(error)}"
            }

        except Exception as e:
            logger.error(f"❌ 사내메일 발송 실패: {str(e)}", exc_info=True)
            if conn:
                conn.rollback()
            return {
                "success": False,
                "message": f"사내메일 발송 중 오류 발생: {str(e)}"
            }

    def _generate_email_html(
        self,
        meeting_title: str,
        meeting_minutes: str,
        transcription: Optional[str],
        timestamp: str
    ) -> str:
        """회의록 이메일 HTML 템플릿 생성"""

        # 전사 텍스트 섹션 (있는 경우에만)
        transcription_section = ""
        if transcription:
            transcription_preview = transcription[:1000] + "..." if len(transcription) > 1000 else transcription
            transcription_section = f"""
                <div class="section">
                    <div class="section-title">📝 음성 전사 내용</div>
                    <div style="background-color: #f9f9f9; padding: 15px; white-space: pre-wrap; font-family: monospace; font-size: 13px;">
{transcription_preview}
                    </div>
                    <p style="color: #666; font-size: 12px;">
                        <em>※ 전체 전사 내용은 ex-GPT 시스템에서 확인하실 수 있습니다.</em>
                    </p>
                </div>
            """

        html_template = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: "Malgun Gothic", "맑은 고딕", sans-serif; line-height: 1.6; margin: 0; padding: 0; }}
        .header {{ background-color: #003d82; color: white; padding: 20px; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .header p {{ margin: 5px 0 0 0; font-size: 14px; opacity: 0.9; }}
        .content {{ padding: 20px; }}
        .section {{ margin-bottom: 30px; }}
        .section-title {{
            font-size: 18px;
            font-weight: bold;
            color: #003d82;
            border-bottom: 2px solid #003d82;
            padding-bottom: 5px;
            margin-bottom: 15px;
        }}
        .info-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        .info-table th, .info-table td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }}
        .info-table th {{
            background-color: #f5f5f5;
            font-weight: bold;
            width: 150px;
        }}
        .minutes-content {{
            background-color: #ffffff;
            border: 1px solid #ddd;
            padding: 20px;
            border-radius: 4px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 12px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎙️ ex-GPT 자동 회의록</h1>
        <p>한국도로공사 AI 시스템이 자동으로 생성한 회의록입니다.</p>
    </div>

    <div class="content">
        <!-- 회의 기본 정보 -->
        <div class="section">
            <div class="section-title">📋 회의 정보</div>
            <table class="info-table">
                <tr>
                    <th>회의명</th>
                    <td>{meeting_title}</td>
                </tr>
                <tr>
                    <th>처리 일시</th>
                    <td>{datetime.strptime(timestamp, '%Y%m%d%H%M%S').strftime('%Y년 %m월 %d일 %H시 %M분')}</td>
                </tr>
            </table>
        </div>

        <!-- 회의록 내용 -->
        <div class="section">
            <div class="section-title">📄 회의록</div>
            <div class="minutes-content">
{meeting_minutes}
            </div>
        </div>

        <!-- 전사 내용 (선택) -->
{transcription_section}
    </div>

    <div class="footer">
        <p>이 메일은 ex-GPT 시스템에서 자동으로 생성되었습니다.</p>
        <p>문의사항: ex-GPT 담당자</p>
        <p>생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>
        """

        return html_template

    def __del__(self):
        """소멸자 - 연결 자동 종료"""
        self.close()
