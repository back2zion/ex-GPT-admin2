-- 채팅 메시지 테이블 생성
CREATE TABLE IF NOT EXISTS chat_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    citations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);

-- 복합 인덱스
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_user ON chat_messages(session_id, user_id);

-- 코멘트 추가
COMMENT ON TABLE chat_messages IS '채팅 메시지 저장 테이블';
COMMENT ON COLUMN chat_messages.id IS '메시지 고유 ID';
COMMENT ON COLUMN chat_messages.session_id IS '채팅 세션 ID';
COMMENT ON COLUMN chat_messages.user_id IS '사용자 ID';
COMMENT ON COLUMN chat_messages.role IS '메시지 역할 (user/assistant/system)';
COMMENT ON COLUMN chat_messages.content IS '메시지 내용';
COMMENT ON COLUMN chat_messages.citations IS '인용 정보 (JSON 형태)';
COMMENT ON COLUMN chat_messages.created_at IS '생성 시간';
COMMENT ON COLUMN chat_messages.updated_at IS '수정 시간';
