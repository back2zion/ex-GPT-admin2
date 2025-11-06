"""
STT 결과를 채팅 히스토리에 통합하는 서비스
모바일 오피스에서 녹음한 내용을 layout.html 채팅 인터페이스에서 볼 수 있도록 저장
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chat_models import ConversationSummary, Conversation
from app.services.internal_mail_service import InternalMailService

logger = logging.getLogger(__name__)


class STTChatIntegrationService:
    """
    STT 결과를 채팅 히스토리로 통합하는 서비스
    """

    def __init__(self):
        """서비스 초기화"""
        self.mail_service = InternalMailService()

    async def save_stt_result_to_chat_history(
        self,
        user_id: str,
        meeting_title: str,
        transcription_text: str,
        meeting_minutes: str,
        sender_name: str,
        sender_email: Optional[str],
        recipient_emails: Optional[list],
        db: AsyncSession
    ) -> Dict:
        """
        STT 처리 결과를 채팅 히스토리에 저장

        Args:
            user_id: 사용자 ID
            meeting_title: 회의 제목
            transcription_text: 전사된 텍스트
            meeting_minutes: 생성된 회의록 (HTML)
            sender_name: 발신자 이름
            sender_email: 발신자 이메일
            recipient_emails: 수신자 이메일 목록
            db: 데이터베이스 세션

        Returns:
            Dict: 처리 결과
        """
        try:
            # 1. 대화방 생성 (ConversationSummary)
            cnvs_idt_id = f"stt_{uuid.uuid4().hex}"

            conversation_summary = ConversationSummary(
                cnvs_idt_id=cnvs_idt_id,
                cnvs_smry_txt=f"[STT 회의록] {meeting_title}",
                rep_cnvs_nm=meeting_title,
                usr_id=user_id,
                use_yn="Y"
            )

            db.add(conversation_summary)
            await db.flush()  # ID 생성을 위해 flush

            logger.info(f"✅ ConversationSummary 생성: {cnvs_idt_id}")

            # 2. 질문-답변 쌍 저장 (Conversation)
            # 질문: "음성 파일을 전사하고 회의록을 생성해주세요"
            # 답변: 전사 텍스트 + 회의록

            question_text = f"""[모바일 오피스 STT 요청]
회의 제목: {meeting_title}
요청자: {sender_name}
처리 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

음성 파일을 전사하고 회의록을 생성해주세요."""

            # 답변 구성: 전사 결과 + 회의록
            answer_text = f"""# 음성 전사 결과

{transcription_text}

---

# 자동 생성된 회의록

{meeting_minutes}

---

*이 내용은 ex-GPT STT 시스템이 자동으로 생성한 결과입니다.*
"""

            conversation = Conversation(
                cnvs_idt_id=cnvs_idt_id,
                ques_txt=question_text,
                ans_txt=answer_text,
                tkn_use_cnt=None,  # STT는 토큰 카운트 없음
                rsp_tim_ms=None,   # 응답시간 추후 추가 가능
                sesn_id=None,
                use_yn="Y"
            )

            db.add(conversation)
            await db.commit()

            logger.info(f"✅ Conversation 저장 완료: CNVS_ID={conversation.cnvs_id}")

            # 3. 사내메일 발송 (수신자가 있는 경우)
            mail_result = None
            if recipient_emails and len(recipient_emails) > 0:
                # 수신자 이메일 → user_id 매핑 필요
                # TODO: PT_USER 테이블에서 조회
                # 임시로 더미 데이터 사용
                receivers = [
                    {"user_id": f"U{i:07d}", "user_name": email.split('@')[0]}
                    for i, email in enumerate(recipient_emails, 1)
                ]

                mail_result = self.mail_service.send_meeting_minutes_email(
                    sender_id=user_id,
                    sender_name=sender_name,
                    receivers=receivers,
                    meeting_title=meeting_title,
                    meeting_minutes_html=meeting_minutes,
                    transcription_text=transcription_text
                )

                if mail_result['success']:
                    logger.info(f"✅ 사내메일 발송 완료: {mail_result['receiver_count']}명")
                else:
                    logger.error(f"❌ 사내메일 발송 실패: {mail_result['message']}")

            return {
                "success": True,
                "cnvs_idt_id": cnvs_idt_id,
                "cnvs_id": conversation.cnvs_id,
                "cnvs_smry_id": conversation_summary.cnvs_smry_id,
                "mail_sent": mail_result['success'] if mail_result else False,
                "mail_result": mail_result,
                "message": "STT 결과가 채팅 히스토리에 저장되었습니다."
            }

        except Exception as e:
            logger.error(f"❌ STT 채팅 히스토리 저장 실패: {str(e)}", exc_info=True)
            await db.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": "STT 결과 저장 중 오류가 발생했습니다."
            }

    def __del__(self):
        """소멸자 - 메일 서비스 연결 종료"""
        if hasattr(self, 'mail_service'):
            self.mail_service.close()
