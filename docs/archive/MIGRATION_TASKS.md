# 마이그레이션 즉시 실행 작업 (실제 코드 기반)

**버전**: 2.0 (실제 Spring Boot 코드 및 MyBatis Mapper 분석 결과)
**작성일**: 2025-10-22
**기준**: QuerySaveMapper.xml, AnswerSaveMapper.xml, ChatController.java 등

---

## ⚠️ 중요: 실제 구현과 다른 점

### 1. Room ID 생성 방식

**❌ 잘못된 가정:**
```java
// UUID 방식 (실제 코드와 다름)
String newRoomId = UUID.randomUUID().toString();
```

**✅ 실제 구현 (QuerySaveMapper.xml:27):**
```sql
-- CNVS_IDT_ID 자동 생성 로직
CD.USR_ID||'_'||TO_CHAR(CURRENT_TIMESTAMP, 'YYYYMMDDHH24MISS')||LPAD(EXTRACT(MICROSECONDS FROM CURRENT_TIMESTAMP)::INTEGER % 1000000, 6, '0')

-- 결과 예시: "user123_20251022104412345678"
-- 형식: {사용자ID}_{타임스탬프 14자리}{마이크로초 6자리}
```

### 2. 실제 테이블 구조

**❌ 잘못된 가정:**
```sql
CREATE TABLE conversations (...)  -- 존재하지 않음
CREATE TABLE rooms (...)          -- 존재하지 않음
```

**✅ 실제 테이블:**
```sql
USR_CNVS_SMRY        -- 대화 요약 (ChatHistory 목록)
USR_CNVS             -- 대화 상세 (질문-답변 쌍)
USR_CNVS_REF_DOC_LST -- 참조 문서
USR_CNVS_ADD_QUES_LST -- 추가 질의
USR_UPLD_DOC_MNG     -- 업로드 파일
chat_messages        -- 채팅 메시지 (추가 테이블)
```

### 3. 실제 API 경로

**❌ 잘못된 가정:**
```
POST /exGenBotDS/chat  # Context Path가 있다고 가정
```

**✅ 실제 경로:**
```
POST /api/chat/conversation  # Context Path 없음, SSE 스트리밍
POST /api/chat/history/list  # POST 방식 (GET 아님)
GET /api/chat/history/{roomId}
```

---

## 🔴 Phase 1: 즉시 실행 작업 (Spring Boot 코드 수정)

### ✅ 완료된 작업

#### 1. ChatRequestDto에 cnvsIdtId 추가 ✅
**파일**: `/home/aigen/new-exgpt-feature-chat/src/main/java/com/datastreams/gpt/chat/dto/ChatRequestDto.java`

```java
// ✅ 추가 완료
@JsonProperty("cnvsIdtId")
private String cnvsIdtId;

public String getCnvsIdtId() {
    return cnvsIdtId;
}

public void setCnvsIdtId(String cnvsIdtId) {
    this.cnvsIdtId = cnvsIdtId;
}
```

#### 2. ChatController Stateless 로직 추가 ✅
**파일**: `/home/aigen/new-exgpt-feature-chat/src/main/java/com/datastreams/gpt/chat/controller/ChatController.java`

```java
// ✅ Stateless 방식 구현 완료
@PostMapping("/conversation")
public void processChatMessage(
        @RequestBody(required = false) ChatRequestDto requestDto,
        HttpServletRequest request,
        HttpServletResponse response) {

    // ✅ RequestDto에서 cnvsIdtId 가져오기
    String cnvsIdtId = null;
    if (requestDto != null && requestDto.getCnvsIdtId() != null) {
        cnvsIdtId = requestDto.getCnvsIdtId();
    }

    // ✅ 빈 스트링 → null 처리
    if (cnvsIdtId != null && cnvsIdtId.trim().isEmpty()) {
        cnvsIdtId = null;
    }

    // ✅ Stateless: 매 요청마다 DB 검증
    String roomId;
    boolean isNewRoom = false;

    if (cnvsIdtId == null) {
        // 새 대화 - QuerySaveService 호출 (DB INSERT)
        roomId = createNewRoomId(userInfo, session);
        isNewRoom = true;
    } else {
        // 기존 대화 - DB에서 검증
        roomId = validateRoomIdFromDB(cnvsIdtId, userInfo);
    }

    // ... SSE 스트리밍 처리
}
```

#### 3. ChatMapper에 검증 메서드 추가 ✅
**파일**: `/home/aigen/new-exgpt-feature-chat/src/main/java/com/datastreams/gpt/chat/mapper/ChatMapper.java`

```java
// ✅ 추가 완료
boolean isValidRoomIdForUser(
    @Param("roomId") String roomId,
    @Param("userId") String userId
);
```

**파일**: `/home/aigen/new-exgpt-feature-chat/src/main/resources/mappers/chat/ChatMapper.xml`

```xml
<!-- ✅ 추가 완료 -->
<select id="isValidRoomIdForUser" parameterType="map" resultType="boolean">
    SELECT CASE WHEN COUNT(*) > 0 THEN 1 ELSE 0 END
    FROM TB_QUES_HIS
    WHERE CNVS_IDT_ID = #{roomId}
      AND USR_ID = #{userId}
    LIMIT 1
</select>
```

#### 4. HTTP 세션 저장 코드 Deprecated 처리 ✅
```java
// ✅ 다음 메서드들 @Deprecated 처리 완료:
@Deprecated
@PostMapping("/test")  // 테스트 엔드포인트

@Deprecated
@PostMapping("/reset")  // 룸 리셋

@Deprecated
@GetMapping("/room-id")  // 현재 룸 조회

// ⚠️ 클라이언트에서 roomIdStore로 관리
```

---

## 🔧 Phase 2: Room ID 생성 로직 구현 (실제 방식)

### ⚠️ 현재 임시 구현 → 실제 구현으로 변경 필요

#### 현재 코드 (ChatController.java:334)
```java
// ⚠️ 임시 폴백 방식 (실제 로직과 다름)
private String createNewRoomId(UserInfoDto userInfo, HttpSession session) {
    try {
        // QuerySaveService를 통해 DB에서 실제 CNVS_IDT_ID 생성
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
        // 실패 시 기존 방식으로 폴백
        return generateRoomId(userInfo.getUsrId());
    }
}

// ⚠️ 폴백 방식: 형식은 맞지만 DB INSERT 없음
private String generateRoomId(String userId) {
    LocalDateTime now = LocalDateTime.now();
    String timestamp = now.format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
    String microseconds = String.format("%06d", now.getNano() / 1000);
    return userId + "_" + timestamp + microseconds;
}
```

### ✅ 올바른 구현 (QuerySaveMapper 활용)

#### QuerySaveMapper.xml 분석 (실제 로직)
```xml
<!-- QuerySaveMapper.xml:18-34 -->
<mapper namespace="com.datastreams.gpt.chat.mapper.QuerySaveMapper">
    <select id="insertQuerySave" ...>
        WITH USR_CNVS_DATA AS (
            SELECT
                #{cnvsIdtId} AS CNVS_IDT_ID,  -- 빈 스트링 전달
                #{quesTxt} AS QUES_TXT,
                #{usrId} AS USR_ID,
                ...
        ),
        INS_USR_CNVS_SMRY AS (
            INSERT INTO USR_CNVS_SMRY (CNVS_IDT_ID, CNVS_SMRY_TXT, USR_ID, MENU_IDT_ID)
            SELECT
                -- ✅ 실제 CNVS_IDT_ID 생성 로직 (라인 27)
                CD.USR_ID||'_'||TO_CHAR(CURRENT_TIMESTAMP, 'YYYYMMDDHH24MISS')||
                LPAD(EXTRACT(MICROSECONDS FROM CURRENT_TIMESTAMP)::INTEGER % 1000000, 6, '0') AS CNVS_IDT_ID,
                CD.QUES_TXT AS CNVS_SMRY_TXT,
                CD.USR_ID,
                CD.MENU_IDT_ID
            FROM USR_CNVS_DATA CD
            WHERE (CD.CNVS_IDT_ID IS NULL OR TRIM(CD.CNVS_IDT_ID) = '')  -- 빈 스트링 체크
            RETURNING USR_CNVS_SMRY.*
        ),
        INS_USR_CNVS AS (
            INSERT INTO USR_CNVS (CNVS_IDT_ID, QUES_TXT, SESN_ID, RCM_QUES_YN)
            SELECT
                CASE WHEN CD.CNVS_IDT_ID IS NULL OR TRIM(CD.CNVS_IDT_ID) = ''
                     THEN S.CNVS_IDT_ID
                     ELSE CD.CNVS_IDT_ID
                END AS CNVS_IDT_ID,
                CD.QUES_TXT,
                CD.SESN_ID,
                CD.RCM_QUES_YN
            FROM USR_CNVS_DATA CD
            LEFT OUTER JOIN INS_USR_CNVS_SMRY S ON 1=1
            RETURNING USR_CNVS.*
        )
        SELECT 'INS_USR_CNVS' AS TXN_NM, CNVS_IDT_ID, CNVS_ID FROM INS_USR_CNVS
    </select>
</mapper>
```

#### 수정 필요 사항

**현재 문제:**
1. ✅ QuerySaveService 호출은 맞음
2. ⚠️ "새 대화 시작" 임시 질의 텍스트 → 실제 사용자 메시지 사용 필요
3. ⚠️ 폴백 로직의 `generateRoomId()`는 DB INSERT 없음 (위험)

**권장 수정:**
```java
private String createNewRoomId(UserInfoDto userInfo, HttpSession session, String firstMessage) {
    try {
        // ✅ QuerySaveService를 통해 DB에서 실제 CNVS_IDT_ID 생성
        QuerySaveRequestDto requestDto = new QuerySaveRequestDto();
        requestDto.setCnvsIdtId("");  // ✅ 빈 스트링: 새 대화 신호
        requestDto.setQuesTxt(firstMessage);  // ✅ 실제 사용자 첫 메시지 사용
        requestDto.setSesnId(session.getId());
        requestDto.setUsrId(userInfo.getUsrId());
        requestDto.setMenuIdtId("DEFAULT");
        requestDto.setRcmQuesYn("N");

        // ✅ QuerySaveMapper.insertQuerySave 호출
        // → USR_CNVS_SMRY에 INSERT (CNVS_IDT_ID 자동 생성)
        // → USR_CNVS에 INSERT (CNVS_ID 자동 생성)
        QuerySaveResponseDto response = querySaveService.saveQuery(requestDto);

        logger.info("DB에서 CNVS_IDT_ID 생성 완료: {}", response.getCnvsIdtId());
        return response.getCnvsIdtId();

    } catch (Exception e) {
        // ❌ 폴백 로직 제거 권장 - DB INSERT 실패는 치명적 오류
        logger.error("DB에서 CNVS_IDT_ID 생성 실패 (치명적): {}", e.getMessage());
        throw new IllegalStateException("대화방 생성 실패", e);
    }
}

// ❌ 폴백용 generateRoomId() 메서드 삭제 권장
// 이유: DB에 INSERT 없이 roomId만 생성하면 데이터 불일치 발생
```

---

## 🔍 Phase 3: 검증 로직 구현 (실제 테이블 기반)

### validateRoomIdFromDB() 메서드

**현재 구현 (ChatController.java:292):**
```java
// ✅ 로직은 맞음
private String validateRoomIdFromDB(String cnvsIdtId, UserInfoDto userInfo) {
    // CWE-476: NULL Pointer Dereference 방지
    if (cnvsIdtId == null || cnvsIdtId.trim().isEmpty()) {
        logger.error("cnvsIdtId가 null이거나 비어있습니다.");
        throw new IllegalArgumentException("대화방 ID가 유효하지 않습니다.");
    }

    if (userInfo == null || userInfo.getUsrId() == null) {
        logger.error("사용자 정보가 null입니다.");
        throw new IllegalArgumentException("사용자 정보가 유효하지 않습니다.");
    }

    try {
        // ✅ DB에서 roomId가 해당 사용자의 것인지 확인
        boolean isValid = chatMapper.isValidRoomIdForUser(cnvsIdtId, userInfo.getUsrId());

        if (!isValid) {
            logger.warn("유효하지 않은 roomId 또는 접근 거부 - roomId: {}, userId: {}",
                       cnvsIdtId, userInfo.getUsrId());
            throw new IllegalArgumentException("유효하지 않은 대화방 ID이거나 접근 권한이 없습니다.");
        }

        logger.info("roomId 검증 성공 - roomId: {}, userId: {}", cnvsIdtId, userInfo.getUsrId());
        return cnvsIdtId;

    } catch (IllegalArgumentException e) {
        throw e;
    } catch (Exception e) {
        logger.error("roomId 검증 중 DB 오류 발생 - roomId: {}, userId: {}, error: {}",
                    cnvsIdtId, userInfo.getUsrId(), e.getMessage());
        throw new IllegalArgumentException("대화방 ID 검증 중 오류가 발생했습니다.");
    }
}
```

**ChatMapper.xml 쿼리 (실제 테이블):**
```xml
<!-- ⚠️ 현재: TB_QUES_HIS 참조 (이게 맞는지 확인 필요) -->
<select id="isValidRoomIdForUser" parameterType="map" resultType="boolean">
    SELECT CASE WHEN COUNT(*) > 0 THEN 1 ELSE 0 END
    FROM TB_QUES_HIS
    WHERE CNVS_IDT_ID = #{roomId}
      AND USR_ID = #{userId}
    LIMIT 1
</select>

<!-- ✅ 권장: USR_CNVS_SMRY 테이블 사용 -->
<select id="isValidRoomIdForUser" parameterType="map" resultType="boolean">
    SELECT CASE WHEN COUNT(*) > 0 THEN 1 ELSE 0 END
    FROM USR_CNVS_SMRY
    WHERE CNVS_IDT_ID = #{roomId}
      AND USR_ID = #{userId}
      AND USE_YN = 'Y'  -- 소프트 삭제된 대화는 제외
    LIMIT 1
</select>
```

**확인 필요:**
- `TB_QUES_HIS` 테이블이 실제로 존재하는지?
- 아니면 `USR_CNVS_SMRY` 또는 `USR_CNVS`를 참조해야 하는지?

---

## 📋 FastAPI 마이그레이션 시 구현할 내용

### 1. Room ID 생성 (FastAPI)

```python
# app/utils/room_id_generator.py
from datetime import datetime

def generate_room_id(user_id: str) -> str:
    """
    실제 QuerySaveMapper.xml 로직과 동일한 Room ID 생성
    형식: {user_id}_{timestamp}{microseconds}
    예: "user123_20251022104412345678"
    """
    now = datetime.now()
    timestamp = now.strftime('%Y%m%d%H%M%S')  # 14자리
    microseconds = f"{now.microsecond % 1000000:06d}"  # 6자리
    return f"{user_id}_{timestamp}{microseconds}"

async def create_new_room(
    user_id: str,
    first_message: str,
    session_id: str,
    db: AsyncSession
) -> str:
    """
    새 대화방 생성 (QuerySaveMapper.insertQuerySave와 동일)
    """
    # 1. CNVS_IDT_ID 생성
    room_id = generate_room_id(user_id)

    # 2. USR_CNVS_SMRY에 INSERT
    await db.execute(
        """
        INSERT INTO USR_CNVS_SMRY (CNVS_IDT_ID, CNVS_SMRY_TXT, USR_ID, MENU_IDT_ID)
        VALUES (:room_id, :summary, :user_id, 'DEFAULT')
        """,
        {
            "room_id": room_id,
            "summary": first_message,  # 첫 질문으로 요약
            "user_id": user_id
        }
    )

    # 3. USR_CNVS에 INSERT
    result = await db.execute(
        """
        INSERT INTO USR_CNVS (CNVS_IDT_ID, QUES_TXT, SESN_ID, RCM_QUES_YN)
        VALUES (:room_id, :question, :session_id, 'N')
        RETURNING CNVS_ID
        """,
        {
            "room_id": room_id,
            "question": first_message,
            "session_id": session_id
        }
    )

    cnvs_id = result.scalar()

    await db.commit()

    logger.info(f"새 대화방 생성: room_id={room_id}, cnvs_id={cnvs_id}, user_id={user_id}")

    return room_id
```

### 2. Room ID 검증 (FastAPI)

```python
# app/services/chat_service.py
async def validate_room_id(
    room_id: str,
    user_id: str,
    db: AsyncSession
) -> bool:
    """
    Room ID 검증 (Stateless 방식)
    ChatMapper.isValidRoomIdForUser와 동일
    """
    result = await db.execute(
        """
        SELECT COUNT(*)
        FROM USR_CNVS_SMRY
        WHERE CNVS_IDT_ID = :room_id
          AND USR_ID = :user_id
          AND USE_YN = 'Y'
        """,
        {"room_id": room_id, "user_id": user_id}
    )

    count = result.scalar()
    is_valid = count > 0

    if not is_valid:
        logger.warning(f"유효하지 않은 roomId - room_id: {room_id}, user_id: {user_id}")

    return is_valid
```

### 3. 채팅 API (FastAPI, SSE 스트리밍)

```python
# app/routers/chat/chat.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import json

router = APIRouter()

class ChatRequest(BaseModel):
    cnvs_idt_id: str = ""  # 빈 스트링 = 새 대화
    message: str
    stream: bool = True
    history: List[dict] = []

async def generate_chat_stream(
    request: ChatRequest,
    user_id: str,
    session_id: str,
    db: AsyncSession
):
    """SSE 스트리밍 생성"""
    try:
        # 1. Room ID 생성 또는 검증
        if not request.cnvs_idt_id or request.cnvs_idt_id.strip() == "":
            # ✅ 새 대화 - DB에서 CNVS_IDT_ID 생성
            room_id = await create_new_room(
                user_id=user_id,
                first_message=request.message,
                session_id=session_id,
                db=db
            )
            is_new_room = True
        else:
            # ✅ 기존 대화 - DB 검증 (Stateless)
            room_id = request.cnvs_idt_id
            is_valid = await validate_room_id(room_id, user_id, db)

            if not is_valid:
                raise HTTPException(
                    status_code=403,
                    detail="유효하지 않은 대화방 ID이거나 접근 권한이 없습니다."
                )
            is_new_room = False

            # 기존 대화 - USR_CNVS에 새 질문 INSERT
            await db.execute(
                """
                INSERT INTO USR_CNVS (CNVS_IDT_ID, QUES_TXT, SESN_ID)
                VALUES (:room_id, :question, :session_id)
                """,
                {
                    "room_id": room_id,
                    "question": request.message,
                    "session_id": session_id
                }
            )
            await db.commit()

        # 2. 새 룸 생성 시 room_id 전송 (SSE)
        if is_new_room:
            yield f"data: {json.dumps({'type': 'room_created', 'room_id': room_id})}\n\n"

        # 3. AI 응답 스트리밍
        async for chunk in ai_service.stream_chat(
            message=request.message,
            history=request.history
        ):
            yield f"data: {json.dumps({'content': {'response': chunk}})}\n\n"

        # 4. 답변 저장 (USR_CNVS UPDATE)
        full_response = ai_service.get_full_response()
        await db.execute(
            """
            UPDATE USR_CNVS
            SET ANS_TXT = :answer,
                TKN_USE_CNT = :tokens,
                RSP_TIM_MS = :response_time,
                MOD_DT = CURRENT_TIMESTAMP
            WHERE CNVS_IDT_ID = :room_id
              AND QUES_TXT = :question
              AND ANS_TXT IS NULL
            ORDER BY REG_DT DESC
            LIMIT 1
            """,
            {
                "answer": full_response,
                "tokens": ai_service.token_count,
                "response_time": ai_service.response_time_ms,
                "room_id": room_id,
                "question": request.message
            }
        )
        await db.commit()

        # 5. 메타데이터 전송
        metadata = {
            "tokens": ai_service.token_count,
            "time_ms": ai_service.response_time_ms
        }
        yield f"data: {json.dumps({'metadata': metadata})}\n\n"

        # 6. 종료 신호
        yield "data: [DONE]\n\n"

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat processing error: {str(e)}", exc_info=True)
        yield f"data: {json.dumps({'error': '서버 오류가 발생했습니다'})}\n\n"
        yield "data: [DONE]\n\n"

@router.post("/api/v1/chat/send")
async def send_chat_message(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """채팅 메시지 전송 (SSE 스트리밍)"""
    return StreamingResponse(
        generate_chat_stream(
            request,
            current_user["user_id"],
            current_user["session_id"],
            db
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

---

## ✅ 검증 체크리스트

### Spring Boot 백엔드 (완료됨)
- [x] `ChatRequestDto`에 `cnvsIdtId` 필드 추가
- [x] Getter/Setter 추가
- [x] `toString()` 메서드 업데이트
- [x] `ChatController`에서 `cnvsIdtId` 파싱 로직 추가
- [x] 빈 스트링 → null 처리 로직 추가
- [x] `validateRoomIdFromDB()` 메서드 구현
- [x] `ChatMapper.isValidRoomIdForUser()` 쿼리 추가
- [x] HTTP 세션 저장 코드 Deprecated 처리
- [x] 로그 추가 (디버깅용)

### 확인 필요 사항
- [ ] `TB_QUES_HIS` 테이블 존재 여부 확인
  - `isValidRoomIdForUser()` 쿼리가 이 테이블 참조 중
  - `USR_CNVS_SMRY` 테이블로 변경 필요할 수 있음
- [ ] `createNewRoomId()` 폴백 로직 제거 검토
  - 현재: DB 실패 시 `generateRoomId()` 호출 (위험)
  - 권장: DB INSERT 실패는 예외 발생
- [ ] QuerySaveService 첫 메시지 전달 방식 확인
  - 현재: "새 대화 시작" 하드코딩
  - 권장: 실제 사용자 첫 메시지 사용

### FastAPI 마이그레이션 (예정)
- [ ] `generate_room_id()` 함수 구현 (실제 형식 반영)
- [ ] `create_new_room()` 함수 구현 (USR_CNVS_SMRY, USR_CNVS INSERT)
- [ ] `validate_room_id()` 함수 구현 (DB 검증)
- [ ] SSE 스트리밍 응답 처리
- [ ] 답변 저장 로직 (USR_CNVS UPDATE)
- [ ] 참조 문서 저장 (USR_CNVS_REF_DOC_LST)
- [ ] 추가 질의 저장 (USR_CNVS_ADD_QUES_LST)

### 프론트엔드 (React) - 변경 없음
- [x] `sendChat()` 함수에서 `cnvsIdtId` 전송 (이미 구현됨)
- [x] roomIdStore에서 빈 스트링 초기화 (이미 구현됨)
- [x] ChatHistory 클릭 시 roomId 설정 (이미 구현됨)
- [x] clearMessages() 호출 시 roomId 리셋 (이미 구현됨)

### 테스트
- [ ] 새 대화 시작 (cnvsIdtId: "" 전송) → DB에서 roomId 생성 확인
- [ ] 기존 대화 이어가기 (cnvsIdtId: "user123_..." 전송) → DB 검증 확인
- [ ] ChatHistory 클릭 → roomId 설정 → 다음 메시지 전송 확인
- [ ] 새 대화 버튼 클릭 → roomId 리셋 확인
- [ ] 다른 사용자의 roomId로 요청 → 403 에러 확인
- [ ] 존재하지 않는 roomId로 요청 → 403 에러 확인

---

## 📌 중요 사항 요약

### 1. Room ID 형식 (실제)
```
형식: {user_id}_{timestamp}{microseconds}
예시: user123_20251022104412345678
길이: 가변 (user_id 길이 + 20자리)
```

### 2. 실제 테이블 구조
```sql
USR_CNVS_SMRY (대화 요약)
├─ CNVS_IDT_ID (PK) - Room ID
├─ CNVS_SMRY_TXT - 대화 요약 (첫 질문)
├─ REP_CNVS_NM - 대표 대화명 (사용자 수정 가능)
├─ USR_ID - 사용자 ID
└─ USE_YN - 사용 여부 (소프트 삭제)

USR_CNVS (대화 상세)
├─ CNVS_IDT_ID (FK) - Room ID
├─ CNVS_ID (PK, Auto-increment) - 메시지 ID
├─ QUES_TXT - 질문 텍스트
├─ ANS_TXT - 답변 텍스트 (나중에 UPDATE)
├─ TKN_USE_CNT - 토큰 사용 수
└─ RSP_TIM_MS - 응답 시간 (밀리초)
```

### 3. 파라미터명
- **프론트엔드**: `cnvsIdtId` (camelCase)
- **DB 컬럼**: `CNVS_IDT_ID` (UPPER_SNAKE_CASE)
- **초기값**: 빈 스트링 `""` (null 아님)

### 4. API 엔드포인트 (실제)
```
POST /api/chat/conversation  (SSE 스트리밍)
POST /api/chat/history/list  (POST 방식, body에 userId)
GET /api/chat/history/{roomId}
```

### 5. Stateless 아키텍처
- ❌ HTTP 세션에 roomId 저장 안 함
- ✅ 매 요청마다 클라이언트가 roomId 전달
- ✅ 매 요청마다 DB에서 검증 (USR_CNVS_SMRY 조회)

### 6. 보안
- ✅ SQL Injection 방지 (파라미터 바인딩)
- ✅ 권한 검증 (USR_ID 일치 확인)
- ✅ Path Traversal 방지
- ✅ XSS 방지 (HTML 이스케이프)

---

## 🔧 디버깅 로그

### Spring Boot (ChatController.java)
```java
logger.info("=== Chat Request Debug ===");
logger.info("RequestDto cnvsIdtId: {}", requestDto != null ? requestDto.getCnvsIdtId() : "null");
logger.info("Parsed cnvsIdtId: {}", cnvsIdtId);
logger.info("Is new conversation: {}", cnvsIdtId == null);
logger.info("Final roomId: {}", roomId);
logger.info("User: {}", userInfo.getUsrId());
logger.info("========================");
```

### React (chat.js)
```javascript
console.log('=== Chat Request Debug ===');
console.log('roomId from store:', useRoomId.getState().roomId);
console.log('Is empty string:', useRoomId.getState().roomId === '');
console.log('Request body:', JSON.stringify({
  cnvsIdtId: roomId,
  message: message,
  ...
}));
console.log('========================');
```

---

**마지막 업데이트**: 2025-10-22 (실제 QuerySaveMapper.xml 분석 기반)
