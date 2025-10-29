-- Migration: 권한 변경 이력 테이블 수정 (ENUM 타입 추가)
-- Purpose: PostgreSQL ENUM 타입 생성 및 테이블 재생성

-- Step 1: 기존 테이블 삭제
DROP TABLE IF EXISTS access_change_history CASCADE;

-- Step 2: ENUM 타입 생성 (이미 존재하면 무시)
DO $$ BEGIN
    CREATE TYPE accesschangeaction AS ENUM ('grant', 'revoke', 'model_change', 'approve', 'reject');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Step 3: 권한 변경 이력 테이블 생성
CREATE TABLE access_change_history (
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

-- Step 4: 인덱스 생성 (조회 성능 향상)
CREATE INDEX idx_access_history_user_id ON access_change_history(user_id);
CREATE INDEX idx_access_history_changed_at ON access_change_history(changed_at DESC);
CREATE INDEX idx_access_history_action ON access_change_history(action);
CREATE INDEX idx_access_history_changed_by ON access_change_history(changed_by);

-- Step 5: 코멘트 추가
COMMENT ON TABLE access_change_history IS 'GPT 접근 권한 변경 이력 (감사 로그)';
COMMENT ON COLUMN access_change_history.user_id IS '대상 사용자 ID';
COMMENT ON COLUMN access_change_history.action IS '수행 액션 (grant/revoke/model_change/approve/reject)';
COMMENT ON COLUMN access_change_history.changed_by IS '변경 수행자 (관리자) ID';
COMMENT ON COLUMN access_change_history.changed_at IS '변경 일시';
COMMENT ON COLUMN access_change_history.old_value IS '이전 값 (모델명 등)';
COMMENT ON COLUMN access_change_history.new_value IS '새 값 (모델명 등)';
COMMENT ON COLUMN access_change_history.reason IS '변경 사유';
