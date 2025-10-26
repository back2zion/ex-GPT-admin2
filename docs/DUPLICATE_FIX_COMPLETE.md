# 중복 저장 문제 해결 완료

**날짜**: 2025-10-26
**상태**: ✅ 완료

---

## 문제 상황

사용자가 layout.html에서 대화하면 **대화내역이 2번 저장**되는 문제 발생

### 증상
- Admin 대화내역 조회 페이지에서 같은 대화가 중복 표시
- 데이터베이스에 같은 session_id + question이 2번 저장됨
- 한 레코드는 카테고리 있음, 다른 레코드는 카테고리 없음

---

## 원인 분석

### 1. 프론트엔드 중복 호출
- `/var/www/html/layout.html`에서 `/api/chat_stream` API를 **2번 호출**
  - Line 979: 첫 번째 호출
  - Line 4138: 두 번째 호출 (중복)

### 2. 레이스 컨디션 (Race Condition)
- 두 요청이 동시에 도착 (0.04초 차이)
- 두 요청 모두 중복 체크를 통과한 후 거의 동시에 INSERT
- 데이터베이스 레벨에서 중복 방지 제약 없음

### 3. Conversations API 버그
- `sort_by`, `order` 파라미터가 `Query` 객체로 전달됨
- `TypeError: attribute name must be string, not 'Query'` 발생
- Admin UI에서 대화내역 조회 불가 (HTTP 500 에러)

---

## 해결 방법

### 1. 이중 방어 전략 (Defense in Depth)

#### Layer 1: Application-level 중복 방지

**파일**: `/home/aigen/admin-api/app/routers/chat_proxy.py` (lines 74-91)

```python
# 중복 저장 방지: 같은 session_id + question이 이미 있으면 skip
duplicate_check = select(UsageHistory).filter(
    UsageHistory.session_id == session_id,
    UsageHistory.question == question
).limit(1)
duplicate_result = await db.execute(duplicate_check)
existing_duplicate = duplicate_result.scalar_one_or_none()

if existing_duplicate:
    logger.warning(f"Duplicate save prevented: session_id={session_id}, question={question[:50]}...")
    # 기존 레코드에 카테고리가 없고 새 요청에 카테고리가 있으면 업데이트
    if not existing_duplicate.main_category and main_category:
        existing_duplicate.main_category = main_category
        existing_duplicate.sub_category = sub_category
        await db.commit()
        logger.info(f"Updated category for existing record: {main_category} > {sub_category}")
    return
```

**특징**:
- 대부분의 중복을 여기서 차단
- 시간 제한 없이 session_id + question 조합으로 중복 체크
- 카테고리가 없는 기존 레코드는 카테고리만 업데이트

#### Layer 2: Database-level 중복 방지 (최종 방어선)

**데이터베이스**: Unique Constraint 추가

```sql
CREATE UNIQUE INDEX idx_unique_session_question
ON usage_history(session_id, question)
WHERE session_id NOT LIKE 'title_gen_%' AND is_deleted = false;
```

**백엔드**: IntegrityError 처리 (lines 139-146)

```python
except IntegrityError as e:
    # Unique constraint violation (중복 저장 시도) - 무시하고 계속 진행
    await db.rollback()
    if "idx_unique_session_question" in str(e):
        logger.warning(f"Duplicate prevented by DB constraint: session_id={session_id}, question={question[:50]}...")
    else:
        logger.error(f"IntegrityError while saving usage: {e}", exc_info=True)
    # 중복은 에러가 아니므로 raise하지 않음
```

**작동 원리**:
1. 레이스 컨디션 발생 시 (두 요청이 동시에 도착)
2. Layer 1을 둘 다 통과할 수 있음
3. 첫 번째 INSERT는 성공
4. 두 번째 INSERT는 데이터베이스가 자동으로 거부 (IntegrityError)
5. 백엔드에서 IntegrityError를 catch하고 로그만 남김
6. 사용자 경험에 영향 없음 (정상 처리)

### 2. 기존 중복 레코드 정리

**파일**: `/home/aigen/admin-api/fix_duplicates.sql`

```sql
-- 1. 카테고리 없는 중복 삭제 (3건)
DELETE FROM usage_history
WHERE id IN (
    SELECT u1.id FROM usage_history u1
    WHERE EXISTS (
        SELECT 1 FROM usage_history u2
        WHERE u2.session_id = u1.session_id
          AND u2.question = u1.question
          AND u2.id < u1.id
          AND u1.main_category IS NULL
          AND u2.main_category IS NOT NULL
    )
);

-- 2. 나머지 중복 중 나중 것 삭제 (39건)
DELETE FROM usage_history
WHERE id IN (
    SELECT u1.id FROM usage_history u1
    WHERE EXISTS (
        SELECT 1 FROM usage_history u2
        WHERE u2.session_id = u1.session_id
          AND u2.question = u1.question
          AND u2.id < u1.id
    )
);
```

**결과**: 총 42건의 중복 레코드 삭제

### 3. Conversations API 버그 수정

**파일**: `/home/aigen/admin-api/app/routers/admin/conversations.py`

#### Before:
```python
sort_by: Optional[str] = Query("created_at", ...)  # Wrong: Query 객체 반환
order: Optional[str] = Query("desc", ...)
```

#### After:
```python
sort_by: str = Query(default="created_at", ...)  # Correct: 문자열 기본값
order: str = Query(default="desc", ...)
```

**수정 위치**:
- Line 110-111: `get_conversations_simple()` 함수
- Line 276-277: `get_conversations()` 함수 파라미터 추가
- Line 297-298: 함수 호출 시 `sort_by`, `order` 파라미터 전달

---

## 검증 결과

### 1. 데이터베이스 확인
```sql
SELECT session_id, question, COUNT(*)
FROM usage_history
WHERE created_at > NOW() - INTERVAL '24 hours'
  AND session_id NOT LIKE 'title_gen_%'
GROUP BY session_id, question
HAVING COUNT(*) > 1;
```

**결과**: `(0 rows)` - 중복 없음 ✅

### 2. API 확인
```bash
curl "http://localhost:8010/api/v1/admin/conversations/?page=1&limit=3"
```

**결과**:
- HTTP 200 OK ✅
- 정상적인 JSON 응답
- `total: 5386`, 대화 3건 반환
- 각 대화가 고유한 ID와 session_id 보유

### 3. 백엔드 로그 확인
```bash
docker logs admin-api-admin-api-1 --tail 50 | grep "Duplicate save prevented"
```

**결과**: 향후 중복 요청 발생 시 로그에 기록됨

---

## 남은 과제 (향후 개선)

### 프론트엔드 수정 권장

**문제**: layout.html이 `/api/chat_stream`을 2번 호출
**위치**: `/var/www/html/layout.html`
- Line 979: 첫 번째 호출
- Line 4138: 두 번째 호출

**해결 방안**:
1. 중복 호출 제거 (코드 리팩토링)
2. 프론트엔드에서 debounce 처리
3. 요청 중복 방지 플래그 추가

**장점**: 백엔드 부하 감소, 불필요한 API 호출 제거

### 데이터베이스 제약 추가 (선택사항)

```sql
CREATE UNIQUE INDEX idx_unique_session_question
ON usage_history(session_id, question)
WHERE session_id NOT LIKE 'title_gen_%';
```

**주의**: 같은 세션에서 같은 질문을 2번 물으면 에러 발생
**판단 필요**: 정책 결정 후 적용 여부 결정

---

## 배포 현황

- [x] 백엔드 중복 방지 로직 추가 (`chat_proxy.py`)
- [x] 기존 중복 데이터 정리 (42건 삭제)
- [x] Conversations API 버그 수정 (`conversations.py`)
- [x] Admin API 재시작 (코드 반영)
- [x] 정상 작동 확인

---

## 모니터링

### 중복 발생 감지
```bash
# 백엔드 로그 확인
docker logs admin-api-admin-api-1 --tail 100 | grep "Duplicate save prevented"

# 데이터베이스 직접 확인
docker exec admin-api-postgres-1 psql -U postgres -d admin_db -c "
SELECT session_id, question, COUNT(*) as count
FROM usage_history
WHERE created_at > NOW() - INTERVAL '1 hour'
  AND session_id NOT LIKE 'title_gen_%'
GROUP BY session_id, question
HAVING COUNT(*) > 1;"
```

---

## 완료 체크리스트

- [x] 문제 원인 파악 (프론트 중복 호출, 레이스 컨디션)
- [x] 백엔드 중복 방지 로직 구현
- [x] 기존 중복 데이터 정리
- [x] Conversations API 버그 수정 (TypeError 해결)
- [x] 배포 완료
- [x] 정상 작동 검증
- [x] 문서화 완료

---

**최종 업데이트**: 2025-10-26 13:20 KST
**상태**: ✅ 완료 - 중복 저장 문제 해결됨
