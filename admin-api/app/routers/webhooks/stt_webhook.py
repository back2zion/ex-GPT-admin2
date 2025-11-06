"""
STT Webhook Router
ex-GPT-STT에서 처리 완료 시 호출하는 webhook
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.stt_chat_integration_service import STTChatIntegrationService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


class STTCompletedWebhook(BaseModel):
    """STT 처리 완료 Webhook 데이터"""
    task_id: str
    status: str  # "completed" or "failed"
    success: bool

    # STT 결과
    transcription: Optional[str] = None
    meeting_minutes: Optional[str] = None
    duration: Optional[float] = None
    language: Optional[str] = None

    # 메타데이터
    meeting_title: str
    sender_name: str
    sender_email: Optional[str] = None
    recipient_emails: Optional[List[str]] = None
    department: Optional[str] = None

    # 오류 정보
    error_message: Optional[str] = None


@router.post("/stt-completed")
async def stt_completed_webhook(
    webhook_data: STTCompletedWebhook,
    db: AsyncSession = Depends(get_db),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    STT 처리 완료 Webhook

    ex-GPT-STT가 음성 전사 및 회의록 생성을 완료하면 호출됩니다.
    결과를 채팅 히스토리에 저장하고 사내메일을 발송합니다.

    Args:
        webhook_data: STT 처리 결과 데이터
        db: 데이터베이스 세션
        x_api_key: API 키 (보안)

    Returns:
        Dict: 처리 결과
    """
    try:
        logger.info(f"📥 STT 완료 Webhook 수신: task_id={webhook_data.task_id}, status={webhook_data.status}")

        # API 키 검증 (간단한 보안)
        # TODO: 환경변수로 설정
        EXPECTED_API_KEY = "exgpt-stt-webhook-secret-key"
        if x_api_key != EXPECTED_API_KEY:
            logger.warning(f"⚠️ 잘못된 API 키: {x_api_key}")
            raise HTTPException(status_code=403, detail="Invalid API Key")

        # 처리 실패한 경우
        if not webhook_data.success or webhook_data.status == "failed":
            logger.error(
                f"❌ STT 처리 실패: task_id={webhook_data.task_id}, "
                f"error={webhook_data.error_message}"
            )
            return {
                "received": True,
                "processed": False,
                "message": f"STT 처리 실패: {webhook_data.error_message}"
            }

        # 필수 데이터 검증
        if not webhook_data.transcription or not webhook_data.meeting_minutes:
            raise HTTPException(
                status_code=400,
                detail="전사 텍스트 또는 회의록이 누락되었습니다"
            )

        # STT 결과를 채팅 히스토리에 저장
        integration_service = STTChatIntegrationService()

        # user_id는 sender_name에서 추출 또는 기본값 사용
        # TODO: 실제 사용자 인증 시스템과 연동
        user_id = "mobile_office_user"

        result = await integration_service.save_stt_result_to_chat_history(
            user_id=user_id,
            meeting_title=webhook_data.meeting_title,
            transcription_text=webhook_data.transcription,
            meeting_minutes=webhook_data.meeting_minutes,
            sender_name=webhook_data.sender_name,
            sender_email=webhook_data.sender_email,
            recipient_emails=webhook_data.recipient_emails,
            db=db
        )

        if result['success']:
            logger.info(
                f"✅ STT 결과 저장 완료: "
                f"cnvs_idt_id={result['cnvs_idt_id']}, "
                f"mail_sent={result['mail_sent']}"
            )

            return {
                "received": True,
                "processed": True,
                "cnvs_idt_id": result['cnvs_idt_id'],
                "cnvs_id": result['cnvs_id'],
                "mail_sent": result['mail_sent'],
                "message": "STT 결과가 채팅 히스토리에 저장되고 사내메일이 발송되었습니다."
            }
        else:
            logger.error(f"❌ STT 결과 저장 실패: {result.get('error')}")
            return {
                "received": True,
                "processed": False,
                "message": result.get('message', 'STT 결과 저장 실패')
            }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Webhook 처리 중 오류: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Webhook 처리 중 오류 발생: {str(e)}"
        )
