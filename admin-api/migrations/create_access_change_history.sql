-- Migration: 권한 변경 이력 테이블 생성 (감사 로그)
-- Purpose: GPT 접근 권한 부여/회수/모델 변경 이력을 추적

-- Step 1: ENUM 타입 생성
CREATE TYPE accesschangeaction AS ENUM ('grant', 'revoke', 'model_change', 'approve', 'reject');

-- Step 2: 권한 변경 이력 테이블 생성
CREATE TABLE IF NOT EXISTS access_change_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action accesschangeaction NOT NULL,
    changed_by INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    old_value VARCHAR(200),
    new_value VARCHAR(200),
    reason VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Step 3: 인덱스 생성 (조회 성능 향상)
CREATE INDEX IF NOT EXISTS idx_access_history_user_id ON access_change_history(user_id);
CREATE INDEX IF NOT EXISTS idx_access_history_changed_at ON access_change_history(changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_access_history_action ON access_change_history(action);
CREATE INDEX IF NOT EXISTS idx_access_history_changed_by ON access_change_history(changed_by);

-- Step 4: 코멘트 추가
COMMENT ON TABLE access_change_history IS 'GPT 접근 권한 변경 이력 (감사 로그)';
COMMENT ON COLUMN access_change_history.user_id IS '대상 사용자 ID';
COMMENT ON COLUMN access_change_history.action IS '수행 액션 (grant/revoke/model_change/approve/reject)';
COMMENT ON COLUMN access_change_history.changed_by IS '변경 수행자 (관리자) ID';
COMMENT ON COLUMN access_change_history.changed_at IS '변경 일시';
COMMENT ON COLUMN access_change_history.old_value IS '이전 값 (모델명 등)';
COMMENT ON COLUMN access_change_history.new_value IS '새 값 (모델명 등)';
COMMENT ON COLUMN access_change_history.reason IS '변경 사유';

-- Verification query
-- SELECT
--     h.id,
--     h.action,
--     h.changed_at,
--     u.full_name as user_name,
--     h.old_value,
--     h.new_value,
--     a.full_name as admin_name,
--     h.reason
-- FROM access_change_history h
-- JOIN users u ON h.user_id = u.id
-- JOIN users a ON h.changed_by = a.id
-- ORDER BY h.changed_at DESC
-- LIMIT 20;
