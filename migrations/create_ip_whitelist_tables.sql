-- IP 화이트리스트 테이블
-- adminpage.txt: 8. 설정 > 1) 관리자관리>IP접근권한 관리

CREATE TABLE IF NOT EXISTS ip_whitelist (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(45) UNIQUE NOT NULL,
    description VARCHAR(255),
    is_allowed BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_ip_whitelist_ip_address ON ip_whitelist(ip_address);
CREATE INDEX idx_ip_whitelist_is_allowed ON ip_whitelist(is_allowed);

-- 코멘트 추가
COMMENT ON TABLE ip_whitelist IS 'IP 화이트리스트 (접근 제어)';
COMMENT ON COLUMN ip_whitelist.ip_address IS 'IP 주소 (IPv4/IPv6)';
COMMENT ON COLUMN ip_whitelist.description IS '설명';
COMMENT ON COLUMN ip_whitelist.is_allowed IS '액세스 허용 여부';
COMMENT ON COLUMN ip_whitelist.created_by IS '등록한 관리자 ID';

-- Trigger: updated_at 자동 업데이트
CREATE TRIGGER trigger_update_ip_whitelist_updated_at
    BEFORE UPDATE ON ip_whitelist
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
