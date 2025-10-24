-- 사전 관리 테이블 생성 SQL
-- 실행: docker-compose exec -T postgres psql -U wisenut_dev -d AGENAI < migrations/create_dictionary_tables.sql

-- 1. DictType enum 생성
CREATE TYPE IF NOT EXISTS dicttype AS ENUM ('synonym', 'user');

-- 2. dictionary 테이블 생성
CREATE TABLE IF NOT EXISTS dictionary (
    dict_id SERIAL PRIMARY KEY,
    dict_type dicttype NOT NULL,
    dict_name VARCHAR(200) NOT NULL,
    dict_desc TEXT,
    use_yn BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE dictionary IS '사전 기본 정보';
COMMENT ON COLUMN dictionary.dict_id IS '사전 ID';
COMMENT ON COLUMN dictionary.dict_type IS '사전 종류 (synonym: 동의어사전, user: 사용자사전)';
COMMENT ON COLUMN dictionary.dict_name IS '사전명';
COMMENT ON COLUMN dictionary.dict_desc IS '사전 설명';
COMMENT ON COLUMN dictionary.use_yn IS '사용 여부';

CREATE INDEX IF NOT EXISTS ix_dictionary_dict_type ON dictionary(dict_type);
CREATE INDEX IF NOT EXISTS ix_dictionary_use_yn ON dictionary(use_yn);

-- 3. dictionary_term 테이블 생성
CREATE TABLE IF NOT EXISTS dictionary_term (
    term_id SERIAL PRIMARY KEY,
    dict_id INTEGER NOT NULL REFERENCES dictionary(dict_id) ON DELETE CASCADE,
    main_term VARCHAR(200) NOT NULL,
    main_alias VARCHAR(200),
    alias_1 VARCHAR(200),
    alias_2 VARCHAR(200),
    alias_3 VARCHAR(200),
    english_name VARCHAR(500),
    english_alias VARCHAR(100),
    category VARCHAR(100),
    definition TEXT,
    use_yn BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE dictionary_term IS '사전 용어';
COMMENT ON COLUMN dictionary_term.term_id IS '용어 ID';
COMMENT ON COLUMN dictionary_term.dict_id IS '사전 ID';
COMMENT ON COLUMN dictionary_term.main_term IS '정식명칭 (예: 기획재정부)';
COMMENT ON COLUMN dictionary_term.main_alias IS '주요약칭 (예: 기재부)';
COMMENT ON COLUMN dictionary_term.alias_1 IS '추가약칭1';
COMMENT ON COLUMN dictionary_term.alias_2 IS '추가약칭2';
COMMENT ON COLUMN dictionary_term.alias_3 IS '추가약칭3';
COMMENT ON COLUMN dictionary_term.english_name IS '영문명 (예: Ministry of Economy and Finance)';
COMMENT ON COLUMN dictionary_term.english_alias IS '영문약칭 (예: MOEF)';
COMMENT ON COLUMN dictionary_term.category IS '분류 (예: 중앙정부부처, 출연연, 공기업)';
COMMENT ON COLUMN dictionary_term.definition IS '정의/설명';
COMMENT ON COLUMN dictionary_term.use_yn IS '사용 여부';

CREATE INDEX IF NOT EXISTS ix_dictionary_term_dict_id ON dictionary_term(dict_id);
CREATE INDEX IF NOT EXISTS ix_dictionary_term_category ON dictionary_term(category);
CREATE INDEX IF NOT EXISTS ix_dictionary_term_use_yn ON dictionary_term(use_yn);
CREATE INDEX IF NOT EXISTS ix_dictionary_term_main_term ON dictionary_term(main_term);

-- 4. updated_at 자동 업데이트 트리거 함수 (이미 있으면 재사용)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 5. 트리거 생성
CREATE TRIGGER update_dictionary_updated_at BEFORE UPDATE ON dictionary
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dictionary_term_updated_at BEFORE UPDATE ON dictionary_term
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
