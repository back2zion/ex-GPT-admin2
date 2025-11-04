-- 중복 레코드 정리 및 unique constraint 추가

-- 1. 기존 중복 레코드 중 카테고리가 없는 것 삭제
DELETE FROM usage_history
WHERE id IN (
    SELECT u1.id
    FROM usage_history u1
    WHERE EXISTS (
        SELECT 1
        FROM usage_history u2
        WHERE u2.session_id = u1.session_id
          AND u2.question = u1.question
          AND u2.id < u1.id
          AND u1.main_category IS NULL
          AND u2.main_category IS NOT NULL
    )
    AND u1.session_id NOT LIKE 'title_gen_%'
);

-- 2. 그 외 중복 레코드 중 나중 것 삭제 (ID가 큰 것)
DELETE FROM usage_history
WHERE id IN (
    SELECT u1.id
    FROM usage_history u1
    WHERE EXISTS (
        SELECT 1
        FROM usage_history u2
        WHERE u2.session_id = u1.session_id
          AND u2.question = u1.question
          AND u2.id < u1.id
    )
    AND u1.session_id NOT LIKE 'title_gen_%'
);

-- 3. 중복 확인
SELECT
    session_id,
    question,
    COUNT(*) as count
FROM usage_history
WHERE session_id NOT LIKE 'title_gen_%'
GROUP BY session_id, question
HAVING COUNT(*) > 1;

-- 4. Unique constraint 추가 (선택사항 - 주의: 같은 질문 두번 물으면 실패함)
-- CREATE UNIQUE INDEX idx_unique_session_question ON usage_history(session_id, question)
-- WHERE session_id NOT LIKE 'title_gen_%';
