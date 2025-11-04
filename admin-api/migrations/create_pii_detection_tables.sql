-- 개인정보 검출 결과 테이블
-- PRD_v2.md P0 요구사항: FUN-003

CREATE TYPE pii_status AS ENUM ('pending', 'approved', 'masked', 'deleted');

CREATE TABLE IF NOT EXISTS pii_detection_results (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    has_pii BOOLEAN DEFAULT FALSE,
    pii_data TEXT,  -- JSON 형식의 PII 검출 결과
    status pii_status DEFAULT 'pending',
    admin_note TEXT,
    processed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_pii_detection_document_id ON pii_detection_results(document_id);
CREATE INDEX idx_pii_detection_status ON pii_detection_results(status);
CREATE INDEX idx_pii_detection_has_pii ON pii_detection_results(has_pii);
CREATE INDEX idx_pii_detection_created_at ON pii_detection_results(created_at);

-- 코멘트 추가
COMMENT ON TABLE pii_detection_results IS '개인정보 검출 결과';
COMMENT ON COLUMN pii_detection_results.document_id IS '문서 ID';
COMMENT ON COLUMN pii_detection_results.has_pii IS '개인정보 포함 여부';
COMMENT ON COLUMN pii_detection_results.pii_data IS '검출된 개인정보 (JSON)';
COMMENT ON COLUMN pii_detection_results.status IS '처리 상태 (pending/approved/masked/deleted)';
COMMENT ON COLUMN pii_detection_results.admin_note IS '관리자 메모';
COMMENT ON COLUMN pii_detection_results.processed_by IS '처리한 관리자 ID';

-- Trigger: updated_at 자동 업데이트
CREATE OR REPLACE FUNCTION update_pii_detection_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_pii_detection_updated_at
    BEFORE UPDATE ON pii_detection_results
    FOR EACH ROW
    EXECUTE FUNCTION update_pii_detection_updated_at();
