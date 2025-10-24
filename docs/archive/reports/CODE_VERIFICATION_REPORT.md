# 코드 검증 보고서 (Code Verification Report)

**작성일**: 2025-10-22
**검증 범위**: Spring Boot Chat System (new-exgpt-feature-chat)
**검증 목적**: 백엔드 팀 피드백과 무관하게 실제 코드 기준으로 독립적 검증

---

## 📋 Executive Summary

백엔드 팀의 피드백이 코드에 대한 완전한 이해 없이 제공된 것으로 확인되었습니다. 실제 코드 분석 결과, **2개의 치명적인 오류**와 **1개의 권장 수정사항**을 발견했습니다.

### 🚨 Critical Issues Found

1. **TB_QUES_HIS 테이블 참조 오류** - 존재하지 않거나 사용되지 않는 테이블 참조
2. **createNewRoomId() 폴백 로직의 데이터 불일치 위험** - DB INSERT 없이 Room ID 생성

---

## 1️⃣ CRITICAL: TB_QUES_HIS 테이블 참조 오류

### 발견된 문제

**ChatMapper.xml (line 94-100)** 의 `isValidRoomIdForUser` 쿼리가 **TB_QUES_HIS** 테이블을 참조하고 있습니다:

```xml
<!-- roomId 검증: 해당 사용자의 대화방인지 확인 (Stateless 방식) -->
<select id="isValidRoomIdForUser" parameterType="map" resultType="boolean">
    SELECT CASE WHEN COUNT(*) > 0 THEN 1 ELSE 0 END
    FROM TB_QUES_HIS
    WHERE CNVS_IDT_ID = #{roomId}
      AND USR_ID = #{userId}
    LIMIT 1
</select>
```

### 검증 결과

전체 프로젝트에서 **TB_QUES_HIS 참조는 단 2곳**입니다:

```bash
# 전체 프로젝트 검색 결과
src/main/java/com/datastreams/gpt/chat/controller/ChatController.java:306
    # 주석: "SELECT COUNT(*) FROM TB_QUES_HIS WHERE CNVS_IDT_ID = ? AND USR_ID = ?"

src/main/resources/mappers/chat/ChatMapper.xml:96
    # 실제 쿼리: FROM TB_QUES_HIS
```

**중요**: **TB_QUES_HIS 테이블에 대한 INSERT 문은 전체 프로젝트에서 0건**입니다.

```bash
# INSERT 검색 결과
$ grep -r "INSERT INTO TB_QUES" --include="*.xml" -n
# (결과 없음)
```

### 실제 사용되는 테이블

모든 MyBatis Mapper에서 실제 사용되는 테이블은 다음과 같습니다:

```sql
-- 대화 요약 (Room 정보)
USR_CNVS_SMRY (CNVS_IDT_ID, CNVS_SMRY_TXT, USR_ID, USE_YN, REG_DT, ...)

-- 대화 상세 (메시지)
USR_CNVS (CNVS_ID, CNVS_IDT_ID, QUES_TXT, ANS_TXT, USE_YN, ...)

-- 참조 문서
USR_CNVS_REF_DOC_LST (CNVS_IDT_ID, CNVS_ID, DOC_CHNK_TXT, ...)

-- 추가 질문
USR_CNVS_ADD_QUES_LST (CNVS_IDT_ID, CNVS_ID, ADD_QUES_TXT, ...)

-- 업로드 파일
USR_UPLD_DOC_MNG (CNVS_IDT_ID, FILE_NM, FILE_UID, ...)
```

### 실제 Room 생성 위치

**QuerySaveMapper.xml (line 21-30)** 에서 USR_CNVS_SMRY에 Room 생성:

```xml
INS_USR_CNVS_SMRY AS (
    INSERT INTO USR_CNVS_SMRY (CNVS_IDT_ID, CNVS_SMRY_TXT, USR_ID, MENU_IDT_ID, ...)
    SELECT
        -- ✅ ACTUAL ROOM ID GENERATION
        CD.USR_ID||'_'||TO_CHAR(CURRENT_TIMESTAMP, 'YYYYMMDDHH24MISS')||
        LPAD(EXTRACT(MICROSECONDS FROM CURRENT_TIMESTAMP)::INTEGER % 1000000, 6, '0'),
        CD.QUES_TXT AS CNVS_SMRY_TXT,
        CD.USR_ID,
        ...
    FROM USR_CNVS_DATA CD
    WHERE (CD.CNVS_IDT_ID IS NULL OR TRIM(CD.CNVS_IDT_ID) = '')
    RETURNING USR_CNVS_SMRY.*
)
```

### 실제 Room 조회 위치

**ConversationHistoryMapper.xml (line 38-49)** selectConversationList:

```xml
<select id="selectConversationList" ...>
    SELECT
        CNVS_IDT_ID as cnvsIdtId,
        NVL(CNVS_SMRY_TXT, '대화 요약 없음') as cnvsSmryTxt,
        USR_ID as usrId,
        TO_CHAR(REG_DT, 'YYYY-MM-DD HH24:MI:SS') as regDt
    FROM USR_CNVS_SMRY
    WHERE 1=1
    AND USR_ID = #{usrId}
    ORDER BY REG_DT DESC
</select>
```

### 영향 분석

| 현재 상태 | 영향 |
|---------|------|
| TB_QUES_HIS 테이블이 존재하지 않는 경우 | **RuntimeException 발생** - 모든 room validation 실패 |
| TB_QUES_HIS 테이블이 존재하나 데이터 없는 경우 | **항상 false 반환** - 정상적인 room도 거부됨 |
| USE_YN 필터 누락 | 삭제된 대화방(USE_YN='N')도 유효하다고 판단 |

### ✅ 수정 방안

**ChatMapper.xml** 수정:

```xml
<!-- ❌ BEFORE (WRONG) -->
<select id="isValidRoomIdForUser" parameterType="map" resultType="boolean">
    SELECT CASE WHEN COUNT(*) > 0 THEN 1 ELSE 0 END
    FROM TB_QUES_HIS
    WHERE CNVS_IDT_ID = #{roomId}
      AND USR_ID = #{userId}
    LIMIT 1
</select>

<!-- ✅ AFTER (CORRECT) -->
<select id="isValidRoomIdForUser" parameterType="map" resultType="boolean">
    SELECT CASE WHEN COUNT(*) > 0 THEN 1 ELSE 0 END
    FROM USR_CNVS_SMRY
    WHERE CNVS_IDT_ID = #{roomId}
      AND USR_ID = #{userId}
      AND USE_YN = 'Y'
    LIMIT 1
</select>
```

**변경 사항**:
1. `TB_QUES_HIS` → `USR_CNVS_SMRY` (실제 사용되는 테이블)
2. `USE_YN = 'Y'` 조건 추가 (삭제된 대화방 제외)

---

## 2️⃣ CRITICAL: createNewRoomId() 폴백 로직의 데이터 불일치

### 발견된 문제

**ChatController.java (line ~327-348)** createNewRoomId() 메서드:

```java
private String createNewRoomId(UserInfoDto userInfo, HttpSession session) {
    try {
        // ✅ 올바른 방식: QuerySaveService를 통해 DB에서 CNVS_IDT_ID 생성
        QuerySaveRequestDto requestDto = new QuerySaveRequestDto();
        requestDto.setCnvsIdtId(""); // 빈 값으로 설정하여 새 대화 생성
        requestDto.setQuesTxt("새 대화 시작"); // 임시 질의
        requestDto.setSesnId(session.getId());
        requestDto.setUsrId(userInfo.getUsrId());
        requestDto.setMenuIdtId("DEFAULT");
        requestDto.setRcmQuesYn("N");

        QuerySaveResponseDto response = querySaveService.saveQuery(requestDto);

        logger.info("DB에서 CNVS_IDT_ID 생성 완료: {}", response.getCnvsIdtId());
        return response.getCnvsIdtId();

    } catch (Exception e) {
        logger.error("DB에서 CNVS_IDT_ID 생성 실패: {}", e.getMessage());
        // ❌ 문제: 실패 시 기존 방식으로 폴백
        return generateRoomId(userInfo.getUsrId());
    }
}
```

### generateRoomId() 폴백 메서드

**ChatController.java** generateRoomId() 메서드:

```java
private String generateRoomId(String userId) {
    // CWE-476: NULL Pointer Dereference 방지
    if (userId == null || userId.trim().isEmpty()) {
        logger.error("사용자 ID가 null이거나 비어있습니다.");
        throw new IllegalArgumentException("사용자 ID가 유효하지 않습니다.");
    }

    // DB 쿼리와 동일한 형식으로 생성: USR_ID_yyyymmddhh24missus
    LocalDateTime now = LocalDateTime.now();
    String timestamp = now.format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
    // 마이크로초 추가 (DB의 missus 형식과 동일하게)
    String microseconds = String.format("%06d", now.getNano() / 1000);
    return userId + "_" + timestamp + microseconds;
}
```

### 문제점 분석

| 단계 | 정상 경로 (try) | 폴백 경로 (catch) |
|------|----------------|------------------|
| 1. Room ID 생성 | QuerySaveMapper.insertQuerySave() 호출 | generateRoomId() 호출 |
| 2. DB INSERT | ✅ USR_CNVS_SMRY에 INSERT | ❌ **DB INSERT 없음** |
| 3. 반환값 | DB에서 생성된 CNVS_IDT_ID | Java에서 생성된 ID |
| 4. DB 상태 | Room 존재 (검증 가능) | **Room 없음 (검증 불가)** |

### 시나리오: 폴백 경로 실행 시

```
1. querySaveService.saveQuery() 실패 (DB 오류, 네트워크 등)
   ↓
2. generateRoomId("user123") 호출
   → 반환: "user123_20251022143052123456"
   ↓
3. Room ID가 클라이언트로 전송됨
   ↓
4. 클라이언트가 다음 메시지 전송 시 이 Room ID 사용
   ↓
5. validateRoomIdFromDB() 호출
   ↓
6. ChatMapper.isValidRoomIdForUser() 실행
   → SELECT COUNT(*) FROM USR_CNVS_SMRY
     WHERE CNVS_IDT_ID = 'user123_20251022143052123456'
   ↓
7. ❌ COUNT = 0 (DB에 레코드 없음)
   ↓
8. IllegalArgumentException 발생: "유효하지 않은 대화방 ID이거나 접근 권한이 없습니다."
```

### 데이터 불일치 사례

```
DB 상태:
┌──────────────────────────────┬──────────────┬──────────────┐
│ CNVS_IDT_ID                  │ USR_ID       │ CNVS_SMRY_TXT│
├──────────────────────────────┼──────────────┼──────────────┤
│ user123_20251022140000123456 │ user123      │ 이전 대화    │
└──────────────────────────────┴──────────────┴──────────────┘

메모리 상태 (폴백 실행 후):
roomId = "user123_20251022143052987654"  ← DB에 없는 ID!
```

### 영향 분석

| 시나리오 | 확률 | 영향 |
|---------|------|------|
| DB 일시 장애 | 낮음 | **대화 연속성 실패** - 첫 메시지 이후 모든 메시지 거부 |
| DB 트랜잭션 오류 | 중간 | **고아 Room ID 생성** - 클라이언트 혼란 |
| 잘못된 requestDto 설정 | 높음 | **검증되지 않은 Room 생성** - 보안 위험 |

### ✅ 수정 방안

**Option 1: 폴백 제거 (권장)**

```java
private String createNewRoomId(UserInfoDto userInfo, HttpSession session) throws Exception {
    // QuerySaveService를 통해 DB에서 실제 CNVS_IDT_ID 생성
    QuerySaveRequestDto requestDto = new QuerySaveRequestDto();
    requestDto.setCnvsIdtId("");
    requestDto.setQuesTxt("새 대화 시작");
    requestDto.setSesnId(session.getId());
    requestDto.setUsrId(userInfo.getUsrId());
    requestDto.setMenuIdtId("DEFAULT");
    requestDto.setRcmQuesYn("N");

    // ✅ 예외를 상위로 전파 - 폴백 없음
    QuerySaveResponseDto response = querySaveService.saveQuery(requestDto);

    logger.info("DB에서 CNVS_IDT_ID 생성 완료: {}", response.getCnvsIdtId());
    return response.getCnvsIdtId();

    // ❌ catch 블록 제거
}
```

**Option 2: 폴백에서도 DB INSERT 수행**

```java
private String createNewRoomId(UserInfoDto userInfo, HttpSession session) {
    try {
        // Primary 방식
        QuerySaveResponseDto response = querySaveService.saveQuery(requestDto);
        return response.getCnvsIdtId();

    } catch (Exception e) {
        logger.error("DB에서 CNVS_IDT_ID 생성 실패, 재시도: {}", e.getMessage());

        // ✅ 폴백에서도 DB INSERT 시도 (재시도 로직)
        try {
            Thread.sleep(100); // 짧은 대기
            QuerySaveResponseDto response = querySaveService.saveQuery(requestDto);
            return response.getCnvsIdtId();
        } catch (Exception retryException) {
            // 재시도도 실패 시 예외 전파
            throw new RuntimeException("Room ID 생성 실패", retryException);
        }
    }
}
```

**권장**: **Option 1 (폴백 제거)**
- DB INSERT 실패 시 명확한 오류 응답
- 데이터 불일치 위험 제거
- 클라이언트가 재시도 가능

---

## 3️⃣ RECOMMENDATION: QuerySaveRequestDto 유효성 검증 강화

### 현재 구현

**ChatController.java** createNewRoomId():

```java
QuerySaveRequestDto requestDto = new QuerySaveRequestDto();
requestDto.setCnvsIdtId("");
requestDto.setQuesTxt("새 대화 시작"); // ⚠️ 하드코딩된 메시지
requestDto.setSesnId(session.getId());
requestDto.setUsrId(userInfo.getUsrId());
requestDto.setMenuIdtId("DEFAULT"); // ⚠️ 하드코딩된 메뉴
requestDto.setRcmQuesYn("N");
```

### 개선 방안

**Option 1: 실제 사용자 메시지 사용**

```java
private String createNewRoomId(UserInfoDto userInfo, HttpSession session, String firstMessage) {
    QuerySaveRequestDto requestDto = new QuerySaveRequestDto();
    requestDto.setCnvsIdtId("");
    requestDto.setQuesTxt(firstMessage); // ✅ 실제 사용자 질의
    requestDto.setSesnId(session.getId());
    requestDto.setUsrId(userInfo.getUsrId());
    requestDto.setMenuIdtId(userInfo.getMenuIdtId()); // ✅ 사용자 메뉴
    requestDto.setRcmQuesYn("N");

    QuerySaveResponseDto response = querySaveService.saveQuery(requestDto);
    return response.getCnvsIdtId();
}
```

**Option 2: 별도 Room 생성 API**

```java
// POST /api/chat/room/create
public String createRoom(@RequestBody RoomCreateRequestDto request) {
    validateUser(request.getUserId());

    QuerySaveRequestDto requestDto = new QuerySaveRequestDto();
    requestDto.setCnvsIdtId("");
    requestDto.setQuesTxt(request.getTitle()); // 사용자 지정 제목
    requestDto.setSesnId(request.getSessionId());
    requestDto.setUsrId(request.getUserId());
    requestDto.setMenuIdtId(request.getMenuId());
    requestDto.setRcmQuesYn("N");

    QuerySaveResponseDto response = querySaveService.saveQuery(requestDto);
    return response.getCnvsIdtId();
}
```

---

## 📊 종합 검증 결과

### 발견된 문제 요약

| 우선순위 | 문제 | 위치 | 타입 | 영향도 |
|---------|------|------|------|--------|
| 🔴 P0 | TB_QUES_HIS 테이블 참조 오류 | ChatMapper.xml:96 | Critical | **High** - 모든 validation 실패 |
| 🔴 P0 | createNewRoomId() 폴백의 데이터 불일치 | ChatController.java:~344 | Critical | **High** - DB 불일치 발생 |
| 🟡 P1 | QuerySaveRequestDto 하드코딩 | ChatController.java:~332 | Recommendation | Medium - UX 저하 |

### 수정 우선순위

1. **즉시 수정 필요 (P0)**:
   - ✅ ChatMapper.xml: TB_QUES_HIS → USR_CNVS_SMRY 변경
   - ✅ ChatController.java: createNewRoomId() 폴백 제거

2. **단기 개선 (P1)**:
   - QuerySaveRequestDto 구성 로직 개선
   - 실제 사용자 메시지 전달

---

## 🔧 Fast Track Fix

**최소 수정으로 문제 해결**:

### 1. ChatMapper.xml 수정

```bash
# File: src/main/resources/mappers/chat/ChatMapper.xml
# Line: 96
```

```xml
<!-- BEFORE -->
FROM TB_QUES_HIS

<!-- AFTER -->
FROM USR_CNVS_SMRY
WHERE CNVS_IDT_ID = #{roomId}
  AND USR_ID = #{userId}
  AND USE_YN = 'Y'  <!-- 추가 -->
```

### 2. ChatController.java 수정

```bash
# File: src/main/java/com/datastreams/gpt/chat/controller/ChatController.java
# Line: ~340-348
```

```java
// BEFORE
} catch (Exception e) {
    logger.error("DB에서 CNVS_IDT_ID 생성 실패: {}", e.getMessage());
    return generateRoomId(userInfo.getUsrId());
}

// AFTER
} catch (Exception e) {
    logger.error("DB에서 CNVS_IDT_ID 생성 실패: {}", e.getMessage());
    throw new RuntimeException("대화방 생성에 실패했습니다. 잠시 후 다시 시도해주세요.", e);
}
```

---

## 📝 테스트 계획

### Unit Test 추가 필요

```java
@Test
public void testIsValidRoomIdForUser_WithValidRoom() {
    // Given
    String roomId = "user123_20251022140000123456";
    String userId = "user123";

    // When
    boolean result = chatMapper.isValidRoomIdForUser(roomId, userId);

    // Then
    assertTrue(result);
}

@Test
public void testIsValidRoomIdForUser_WithDeletedRoom() {
    // Given: USE_YN = 'N'인 Room
    String roomId = "user123_20251022140000999999";
    String userId = "user123";

    // When
    boolean result = chatMapper.isValidRoomIdForUser(roomId, userId);

    // Then
    assertFalse(result); // 삭제된 Room은 유효하지 않음
}

@Test
public void testCreateNewRoomId_WhenDbFails_ShouldThrowException() {
    // Given
    when(querySaveService.saveQuery(any())).thenThrow(new RuntimeException("DB Error"));

    // When & Then
    assertThrows(RuntimeException.class, () -> {
        chatController.createNewRoomId(userInfo, session);
    });
}
```

---

## 🎯 결론

1. **TB_QUES_HIS → USR_CNVS_SMRY 변경 필수**
   - 현재 코드는 존재하지 않거나 사용되지 않는 테이블 참조
   - 모든 MyBatis Mapper에서 USR_CNVS_SMRY 사용 확인

2. **createNewRoomId() 폴백 제거 권장**
   - 폴백 로직이 DB와 메모리 불일치 초래
   - 명확한 오류 처리로 클라이언트 재시도 유도

3. **백엔드 팀 피드백과 실제 코드 불일치**
   - 피드백은 코드 완전 이해 없이 제공됨
   - 실제 코드 분석이 정확한 마이그레이션 기준

---

**검증자**: Claude Code
**검증 방법**: 전체 프로젝트 소스 코드 분석 (Grep, Read, Bash tools)
**신뢰도**: High (실제 코드 기반)
