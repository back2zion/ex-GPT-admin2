"""
이메일 서비스 레이어
시큐어 코딩: Email Injection 방지, SMTP Injection 방지
"""
import re
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailService:
    """이메일 송출 서비스 (보안 검증 포함)"""

    # 보안: 이메일 정규식 (RFC 5322 기반)
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    # 보안: 금지된 문자 (SMTP Injection 방지)
    FORBIDDEN_CHARS = ['\n', '\r', '\0', '%0a', '%0d']

    def validate_email(self, email: str) -> bool:
        """
        이메일 주소 검증 (Email Injection 방지)

        Args:
            email: 검증할 이메일 주소

        Returns:
            bool: 유효한 이메일이면 True

        Security:
            - Email Injection 방지 (newline, CRLF 등)
            - SMTP Injection 방지 (Bcc, To 헤더 주입 등)
            - SQL Injection 방지 (특수문자 차단)
        """
        if not email or not isinstance(email, str):
            return False

        # 보안: SMTP Injection 패턴 감지 (newline, CRLF)
        for forbidden_char in self.FORBIDDEN_CHARS:
            if forbidden_char in email.lower():
                return False

        # 보안: 정규식 검증
        if not self.EMAIL_REGEX.match(email):
            return False

        # 보안: 길이 제한 (DoS 방지)
        if len(email) > 254:  # RFC 5321 표준
            return False

        return True

    def sanitize_email_content(self, content: str) -> str:
        """
        이메일 본문 정제 (XSS 방지)

        Args:
            content: 정제할 이메일 본문

        Returns:
            str: 정제된 본문

        Security:
            - HTML 태그 제거 (XSS 방지)
            - Script 태그 제거
            - 위험한 프로토콜 제거 (javascript:, data:)
        """
        # 보안: HTML 태그 제거
        content = re.sub(r'<script.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<.*?>', '', content)

        # 보안: 위험한 프로토콜 제거
        content = re.sub(r'javascript:', '', content, flags=re.IGNORECASE)
        content = re.sub(r'data:', '', content, flags=re.IGNORECASE)

        return content

    def create_email_message(
        self,
        recipient_email: str,
        subject: str,
        body: str,
        cc_emails: Optional[List[str]] = None,
        from_email: str = "noreply@ex.co.kr"
    ) -> MIMEMultipart:
        """
        이메일 메시지 생성 (보안 검증 포함)

        Args:
            recipient_email: 수신자 이메일
            subject: 제목
            body: 본문
            cc_emails: 참조(CC) 이메일 목록
            from_email: 발신자 이메일

        Returns:
            MIMEMultipart: 이메일 메시지 객체

        Raises:
            ValueError: 유효하지 않은 이메일 주소

        Security:
            - 모든 이메일 주소 검증
            - 본문 정제 (XSS 방지)
        """
        # 보안: 발신자 이메일 검증
        if not self.validate_email(from_email):
            raise ValueError(f"Invalid sender email: '{from_email}'")

        # 보안: 수신자 이메일 검증
        if not self.validate_email(recipient_email):
            raise ValueError(f"Invalid recipient email: '{recipient_email}'")

        # 보안: CC 이메일 검증
        if cc_emails:
            for cc_email in cc_emails:
                if not self.validate_email(cc_email):
                    raise ValueError(f"Invalid CC email: '{cc_email}'")

        # 보안: 본문 정제
        sanitized_body = self.sanitize_email_content(body)

        # 이메일 메시지 생성
        message = MIMEMultipart()
        message['From'] = from_email
        message['To'] = recipient_email
        message['Subject'] = subject

        if cc_emails:
            message['Cc'] = ', '.join(cc_emails)

        # 본문 추가
        message.attach(MIMEText(sanitized_body, 'plain', 'utf-8'))

        return message

    async def send_email(
        self,
        recipient_email: str,
        subject: str,
        body: str,
        cc_emails: Optional[List[str]] = None
    ) -> bool:
        """
        이메일 전송 (보안 검증 포함)

        Args:
            recipient_email: 수신자 이메일
            subject: 제목
            body: 본문
            cc_emails: 참조(CC) 이메일 목록

        Returns:
            bool: 전송 성공 여부

        Raises:
            ValueError: 유효하지 않은 입력
        """
        # 이메일 메시지 생성 (검증 포함)
        message = self.create_email_message(
            recipient_email=recipient_email,
            subject=subject,
            body=body,
            cc_emails=cc_emails
        )

        # TODO: 실제 이메일 전송 로직 (SMTP, SendGrid, AWS SES 등)
        # 현재는 테스트용 더미 반환
        print(f"[EmailService] Sending email to {recipient_email}")
        print(f"[EmailService] Subject: {subject}")
        print(f"[EmailService] Body: {body[:100]}...")

        return True
