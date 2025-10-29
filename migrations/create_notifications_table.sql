-- 알림 테이블 생성
-- PRD FUN-002: 제·개정 문서 알림

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,

    -- 알림 유형
    type VARCHAR(20) NOT NULL CHECK (type IN ('success', 'error', 'info', 'warning')),

    -- 알림 카테고리
    category VARCHAR(50) NOT NULL,

    -- 알림 내용
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    link VARCHAR(500),

    -- 읽음 상태
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,

    -- 대상 사용자 (NULL이면 전체 관리자)
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,

    -- 관련 엔티티
    related_entity_type VARCHAR(50),
    related_entity_id INTEGER,

    -- 타임스탬프
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_category ON notifications(category);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read);

-- 코멘트 추가
COMMENT ON TABLE notifications IS '알림 테이블 (PRD FUN-002: 제·개정 문서 알림)';
COMMENT ON COLUMN notifications.type IS '알림 유형: success, error, info, warning';
COMMENT ON COLUMN notifications.category IS '알림 카테고리: document_update, system, deployment, stt_batch';
COMMENT ON COLUMN notifications.title IS '알림 제목';
COMMENT ON COLUMN notifications.message IS '알림 메시지';
COMMENT ON COLUMN notifications.link IS '관련 페이지 링크';
COMMENT ON COLUMN notifications.is_read IS '읽음 여부';
COMMENT ON COLUMN notifications.read_at IS '읽은 시간';
COMMENT ON COLUMN notifications.user_id IS '특정 사용자 ID (NULL이면 전체)';
COMMENT ON COLUMN notifications.related_entity_type IS '관련 엔티티 타입 (document, batch 등)';
COMMENT ON COLUMN notifications.related_entity_id IS '관련 엔티티 ID';
