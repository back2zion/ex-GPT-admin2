"""
STT Client Service - ex-GPT-STT API HTTP 클라이언트
TDD 방식으로 구현: 테스트가 정의한 인터페이스 준수
"""
import re
import asyncio
from typing import Optional, Dict
import httpx
from app.services.stt_service import STTService


class STTClientService:
    """ex-GPT-STT API 클라이언트"""

    def __init__(
        self,
        api_base_url: str = "http://localhost:8001",
        poll_interval: float = 5.0,
        timeout: float = 120.0
    ):
        """
        Args:
            api_base_url: ex-GPT-STT API 서버 URL
            poll_interval: 상태 폴링 간격 (초)
            timeout: HTTP 요청 타임아웃 (초)
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.poll_interval = poll_interval
        self.timeout = timeout
        self.stt_service = STTService()  # Path validation용

    def _sanitize_text(self, text: str) -> str:
        """
        텍스트 정제 (XSS 방지)

        Args:
            text: 정제할 텍스트

        Returns:
            정제된 텍스트
        """
        # HTML 태그 제거
        text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<.*?>', '', text)
        return text

    async def submit_audio(
        self,
        audio_file_path: str,
        meeting_title: str,
        sender_name: str,
        sender_email: Optional[str] = None,
        recipient_emails: Optional[list] = None
    ) -> Dict:
        """
        오디오 파일 제출

        Args:
            audio_file_path: 오디오 파일 경로
            meeting_title: 회의 제목
            sender_name: 발신자 이름
            sender_email: 발신자 이메일 (선택)
            recipient_emails: 수신자 이메일 목록 (선택)

        Returns:
            dict: {"success": bool, "task_id": str, "message": str}

        Raises:
            ValueError: 잘못된 파일 경로 (Path Traversal)
            Exception: API 호출 실패
        """
        # 보안: Path Traversal 검증
        self.stt_service.validate_file_path(audio_file_path)

        # 보안: XSS 방지 - 특수문자 제거
        meeting_title = self._sanitize_text(meeting_title)
        sender_name = self._sanitize_text(sender_name)

        # API 요청 데이터 구성
        payload = {
            "sender_name": sender_name,
            "meeting_title": meeting_title,
            "auto_send_email": bool(recipient_emails)
        }

        if sender_email:
            payload["sender_email"] = sender_email

        if recipient_emails:
            payload["recipient_emails"] = recipient_emails

        # HTTP 요청
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Note: 실제 구현시 multipart/form-data로 파일 업로드
            # 지금은 파일 경로만 전송 (MinIO/S3에서 다운로드 가능하다고 가정)
            payload["audio_file_path"] = audio_file_path

            response = await client.post(
                f"{self.api_base_url}/process-audio",
                json=payload
            )

            # 에러 처리
            response.raise_for_status()

            return response.json()

    async def get_task_status(self, task_id: str) -> Dict:
        """
        작업 상태 조회

        Args:
            task_id: 작업 ID

        Returns:
            dict: {"task_id": str, "status": str, "progress": float}
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_base_url}/status/{task_id}"
            )
            response.raise_for_status()
            return response.json()

    async def get_task_result(self, task_id: str) -> Dict:
        """
        작업 결과 조회

        Args:
            task_id: 작업 ID

        Returns:
            dict: {
                "success": bool,
                "status": str,
                "transcription": str,
                "meeting_minutes": str,
                "duration": float,
                "language": str,
                "segment_count": int
            }
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_base_url}/result/{task_id}"
            )
            response.raise_for_status()
            return response.json()

    async def wait_for_completion(
        self,
        task_id: str,
        max_wait_time: float = 3600.0
    ) -> Dict:
        """
        작업 완료 대기 (폴링)

        Args:
            task_id: 작업 ID
            max_wait_time: 최대 대기 시간 (초)

        Returns:
            dict: 작업 결과

        Raises:
            TimeoutError: 대기 시간 초과
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            # 타임아웃 체크
            elapsed_time = asyncio.get_event_loop().time() - start_time
            if elapsed_time > max_wait_time:
                raise TimeoutError(
                    f"Task {task_id} did not complete within {max_wait_time} seconds"
                )

            # 상태 조회
            status = await self.get_task_status(task_id)

            # 완료 체크
            if status.get("status") == "completed":
                # 결과 조회
                return await self.get_task_result(task_id)

            elif status.get("status") == "failed":
                raise Exception(f"Task {task_id} failed")

            # 대기
            await asyncio.sleep(self.poll_interval)

    async def health_check(self) -> bool:
        """
        ex-GPT-STT API 헬스체크

        Returns:
            bool: 서버 정상 여부
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.api_base_url}/health"
                )
                return response.status_code == 200
        except Exception:
            return False
