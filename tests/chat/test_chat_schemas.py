"""
Tests for chat_schemas.py
Pydantic 스키마 검증 테스트
"""
import pytest
from pydantic import ValidationError
from app.schemas.chat_schemas import (
    ChatRequest,
    ConversationSummary,
    ConversationListResponse,
    MessageReference,
    MessageMetadata,
    ChatMessage,
    HistoryDetailResponse,
    RoomNameUpdateRequest,
    FileUploadResponse
)


class TestChatRequest:
    """ChatRequest 스키마 테스트"""

    def test_chat_request_valid_minimal(self):
        """최소 필수 필드만으로 생성 가능한지 테스트"""
        data = {"message": "안녕하세요"}
        request = ChatRequest(**data)

        assert request.message == "안녕하세요"
        assert request.cnvs_idt_id == ""
        assert request.stream is True
        assert request.history == []
        assert request.search_documents is False

    def test_chat_request_valid_full(self):
        """모든 필드를 포함한 생성 테스트"""
        data = {
            "cnvs_idt_id": "user123_20251022104412345678",
            "message": "질문입니다",
            "stream": True,
            "history": [
                {"role": "user", "content": "이전 질문"},
                {"role": "assistant", "content": "이전 답변"}
            ],
            "search_documents": True,
            "department": "DEPT001",
            "search_scope": ["manual", "faq"],
            "max_context_tokens": 8000,
            "temperature": 0.5,
            "suggest_questions": True,
            "think_mode": False
        }
        request = ChatRequest(**data)

        assert request.cnvs_idt_id == "user123_20251022104412345678"
        assert request.message == "질문입니다"
        assert request.search_documents is True
        assert request.department == "DEPT001"
        assert len(request.search_scope) == 2
        assert request.max_context_tokens == 8000
        assert request.temperature == 0.5

    def test_chat_request_empty_message(self):
        """빈 메시지로 생성 시도 시 ValidationError 테스트"""
        with pytest.raises(ValidationError):
            ChatRequest(message="")

    def test_chat_request_temperature_range(self):
        """Temperature 범위 검증 테스트"""
        # 유효한 범위
        ChatRequest(message="test", temperature=0.0)
        ChatRequest(message="test", temperature=1.0)
        ChatRequest(message="test", temperature=2.0)

        # 범위 밖
        with pytest.raises(ValidationError):
            ChatRequest(message="test", temperature=-0.1)

        with pytest.raises(ValidationError):
            ChatRequest(message="test", temperature=2.1)

    def test_chat_request_default_values(self):
        """기본값이 올바르게 설정되는지 테스트"""
        request = ChatRequest(message="test")

        assert request.stream is True
        assert request.history == []
        assert request.search_documents is False
        assert request.department is None
        assert request.search_scope is None
        assert request.max_context_tokens == 4000
        assert request.temperature == 0.7
        assert request.suggest_questions is False
        assert request.think_mode is False


class TestConversationSummary:
    """ConversationSummary 스키마 테스트"""

    def test_conversation_summary_valid(self):
        """올바른 ConversationSummary 생성 테스트"""
        data = {
            "cnvs_idt_id": "user123_20251022104412345678",
            "cnvs_smry_txt": "첫 질문 요약",
            "reg_dt": "2025-10-22T10:44:12"
        }
        summary = ConversationSummary(**data)

        assert summary.cnvs_idt_id == "user123_20251022104412345678"
        assert summary.cnvs_smry_txt == "첫 질문 요약"

    def test_conversation_summary_optional_reg_dt(self):
        """reg_dt가 옵션인지 테스트"""
        data = {
            "cnvs_idt_id": "user123_20251022104412345678",
            "cnvs_smry_txt": "요약"
        }
        summary = ConversationSummary(**data)
        assert summary.reg_dt is None


class TestMessageReference:
    """MessageReference 스키마 테스트"""

    def test_message_reference_valid(self):
        """올바른 MessageReference 생성 테스트"""
        data = {
            "ref_seq": 0,
            "doc_name": "문서.pdf",
            "chunk_text": "참조 텍스트 내용",
            "similarity": 0.95
        }
        ref = MessageReference(**data)

        assert ref.ref_seq == 0
        assert ref.doc_name == "문서.pdf"
        assert ref.similarity == 0.95


class TestMessageMetadata:
    """MessageMetadata 스키마 테스트"""

    def test_message_metadata_valid(self):
        """올바른 MessageMetadata 생성 테스트"""
        data = {
            "tokens": 1500,
            "search_time_ms": 200,
            "response_time_ms": 3000
        }
        metadata = MessageMetadata(**data)

        assert metadata.tokens == 1500
        assert metadata.search_time_ms == 200
        assert metadata.response_time_ms == 3000

    def test_message_metadata_optional_response_time(self):
        """response_time_ms가 옵션인지 테스트"""
        data = {
            "tokens": 1500,
            "search_time_ms": 200
        }
        metadata = MessageMetadata(**data)
        assert metadata.response_time_ms is None


class TestChatMessage:
    """ChatMessage 스키마 테스트"""

    def test_chat_message_user(self):
        """사용자 메시지 생성 테스트"""
        data = {
            "cnvs_id": 123,
            "role": "user",
            "content": "질문입니다",
            "timestamp": "2025-10-22T10:44:12",
            "metadata": {
                "tokens": 10,
                "search_time_ms": 0
            }
        }
        message = ChatMessage(**data)

        assert message.role == "user"
        assert message.content == "질문입니다"
        assert message.references is None

    def test_chat_message_assistant_with_references(self):
        """참조 문서를 포함한 어시스턴트 메시지 테스트"""
        data = {
            "cnvs_id": 124,
            "role": "assistant",
            "content": "답변입니다",
            "timestamp": "2025-10-22T10:44:15",
            "metadata": {
                "tokens": 500,
                "search_time_ms": 150,
                "response_time_ms": 2000
            },
            "references": [
                {
                    "ref_seq": 0,
                    "doc_name": "문서1.pdf",
                    "chunk_text": "참조 내용",
                    "similarity": 0.95
                }
            ],
            "suggested_questions": [
                "추천 질문 1",
                "추천 질문 2"
            ]
        }
        message = ChatMessage(**data)

        assert message.role == "assistant"
        assert len(message.references) == 1
        assert len(message.suggested_questions) == 2


class TestRoomNameUpdateRequest:
    """RoomNameUpdateRequest 스키마 테스트"""

    def test_room_name_update_valid(self):
        """올바른 대화명 변경 요청 테스트"""
        data = {"name": "새로운 대화명"}
        request = RoomNameUpdateRequest(**data)

        assert request.name == "새로운 대화명"

    def test_room_name_update_empty(self):
        """빈 이름으로 변경 시도 시 ValidationError 테스트"""
        with pytest.raises(ValidationError):
            RoomNameUpdateRequest(name="")

    def test_room_name_update_too_long(self):
        """500자 초과 이름으로 변경 시도 시 ValidationError 테스트"""
        with pytest.raises(ValidationError):
            RoomNameUpdateRequest(name="x" * 501)

    def test_room_name_update_max_length(self):
        """500자 정확히 맞는 이름은 허용되는지 테스트"""
        request = RoomNameUpdateRequest(name="x" * 500)
        assert len(request.name) == 500


class TestFileUploadResponse:
    """FileUploadResponse 스키마 테스트"""

    def test_file_upload_response_valid(self):
        """올바른 파일 업로드 응답 테스트"""
        data = {
            "success": True,
            "file_uid": "documents/uuid-123.pdf",
            "filename": "문서.pdf",
            "size": 1024000,
            "download_url": "http://minio/documents/uuid-123.pdf"
        }
        response = FileUploadResponse(**data)

        assert response.success is True
        assert response.file_uid == "documents/uuid-123.pdf"
        assert response.size == 1024000


class TestConversationListResponse:
    """ConversationListResponse 스키마 테스트"""

    def test_conversation_list_response_empty(self):
        """빈 대화 목록 응답 테스트"""
        data = {
            "conversations": [],
            "total": 0
        }
        response = ConversationListResponse(**data)

        assert len(response.conversations) == 0
        assert response.total == 0

    def test_conversation_list_response_with_data(self):
        """대화가 포함된 목록 응답 테스트"""
        data = {
            "conversations": [
                {
                    "cnvs_idt_id": "user1_20251022104412345678",
                    "cnvs_smry_txt": "첫 번째 대화",
                    "reg_dt": "2025-10-22T10:44:12"
                },
                {
                    "cnvs_idt_id": "user1_20251022104500123456",
                    "cnvs_smry_txt": "두 번째 대화",
                    "reg_dt": "2025-10-22T10:45:00"
                }
            ],
            "total": 2
        }
        response = ConversationListResponse(**data)

        assert len(response.conversations) == 2
        assert response.total == 2


class TestHistoryDetailResponse:
    """HistoryDetailResponse 스키마 테스트"""

    def test_history_detail_response_valid(self):
        """올바른 히스토리 상세 응답 테스트"""
        data = {
            "cnvs_idt_id": "user123_20251022104412345678",
            "messages": [
                {
                    "cnvs_id": 1,
                    "role": "user",
                    "content": "질문",
                    "timestamp": "2025-10-22T10:44:12",
                    "metadata": {
                        "tokens": 10,
                        "search_time_ms": 0
                    }
                },
                {
                    "cnvs_id": 1,
                    "role": "assistant",
                    "content": "답변",
                    "timestamp": "2025-10-22T10:44:15",
                    "metadata": {
                        "tokens": 500,
                        "search_time_ms": 150,
                        "response_time_ms": 2000
                    }
                }
            ],
            "total_messages": 2
        }
        response = HistoryDetailResponse(**data)

        assert response.cnvs_idt_id == "user123_20251022104412345678"
        assert len(response.messages) == 2
        assert response.total_messages == 2
