# PRD: Spring Boot Chat System → FastAPI 마이그레이션 (실제 코드 기반)

## 📋 문서 정보
- **버전**: 2.0 (실제 코드 분석 기반)
- **작성일**: 2025-10-22
- **프로젝트**: AI Streams Chat System Migration
- **목표**: Spring Boot 3.2.5 + React 19 → FastAPI + React 통합
- **기준**: 실제 Spring Boot 코드 및 MyBatis Mapper 분석 결과

---

## 🎯 프로젝트 개요

### 목적
기존 FastAPI 기반 관리 시스템(`admin-api`)에 새로운 채팅 기능(Spring Boot + React)을 마이그레이션하여 단일 백엔드 아키텍처로 통합

### 범위
1. **백엔드**: Spring Boot (Java) → FastAPI (Python) 포팅
2. **프론트엔드**: React 19 (Vite) → 기존 시스템과 공존
3. **데이터베이스**: PostgreSQL 스키마 통합 (실제 테이블 구조 반영)
4. **인증**: Spring Security SSO → FastAPI 인증 시스템 통합
5. **파일 스토리지**: MinIO 연동 유지

### 제약사항
- 기존 `layout.html` 시스템 100% 유지 (무중단 서비스)
- TDD 커버리지 80% 이상 달성
- OWASP Top 10 보안 취약점 제로
- 3주(21일) 내 완료

---

## 🏗️ 시스템 아키텍처

### 현재 시스템 (AS-IS)

#### 기존 Layout.html 시스템
```
프론트엔드: /var/www/html/layout.html (Vanilla JS + Thymeleaf)
├─ Apache Tomcat 10.1.43
├─ URL: https://ui.datastreams.co.kr:20443/layout.html
└─ 데이터 구조:
   - session_id 기반 메시지 관리
   - Conversation 개념 없음 (session_id로만 구분)
   - 메시지 계층: session → messages
```

#### 새 코드 (Spring Boot + React)
```
백엔드: Spring Boot 3.2.5 (Java 17)
├─ Spring Security + SSO (DreamSecurity)
├─ MyBatis + PostgreSQL (EDB: 1.215.235.250:25444/AGENAI)
├─ MinIO 파일 스토리지
├─ 포트: 20000
├─ ⚠️ Context Path: 없음 (직접 /api/chat/*)
└─ 데이터 구조:
   - CNVS_IDT_ID (대화 식별 ID) 중심 설계
   - 계층: CNVS_IDT_ID → CNVS_ID (메시지)
   - CNVS_IDT_ID 생성: user_id + timestamp + microseconds

프론트엔드: React 19 + Vite
├─ React Router (/ai, /govAi, /login)
├─ Zustand 상태 관리 (persist 없음)
├─ Components: Header, Aside, ChatPage, Modals
└─ API 연동:
   - POST /api/chat/conversation (SSE 스트리밍)
   - POST /api/chat/history/list (대화 목록)
   - GET /api/chat/history/{roomId} (룸별 히스토리)
```

### 목표 시스템 (TO-BE)

```
┌─────────────────────────────────────────────────────────────┐
│                Nginx (Port 20443) - SSL/TLS                 │
│  - Reverse Proxy                                            │
│  - Load Balancing                                           │
└──────────┬─────────────────────┬────────────────────────────┘
           │                     │
           │                     │
┌──────────▼──────────┐  ┌──────▼────────────────────────────┐
│  Apache Tomcat      │  │  FastAPI (Docker)                 │
│  (Port 8080)        │  │  (Port 8001 → 20443/api/*)        │
│                     │  │                                   │
│  프론트엔드:         │  │  백엔드 API:                      │
│  ├─ layout.html     │  │  ├─ /api/v1/admin/*  (기존)      │
│  │  (기존 유지)     │  │  ├─ /api/v1/chat/send (NEW, SSE) │
│  └─ /new-chat/*     │  │  ├─ /api/v1/chat/history (NEW)   │
│     (새 React UI)   │  │  ├─ /api/v1/files/*  (NEW)       │
│                     │  │  ├─ /api/v1/survey/* (NEW)       │
│                     │  │  ├─ /api/v1/notice/* (확장)      │
│                     │  │  └─ /api/v1/error-report/* (NEW) │
└─────────────────────┘  └───────────────────────────────────┘
                                  │
                         ┌────────▼─────────────────┐
                         │   PostgreSQL (통합)      │
                         │  ┌──────────────────┐   │
                         │  │ admin_db (기존)  │   │
                         │  ├──────────────────┤   │
                         │  │ USR_CNVS_SMRY    │ ← 실제 테이블
                         │  │ USR_CNVS         │ ← 실제 테이블
                         │  │ USR_CNVS_REF_DOC_LST │
                         │  │ USR_CNVS_ADD_QUES_LST │
                         │  │ USR_UPLD_DOC_MNG │
                         │  │ chat_messages    │
                         │  └──────────────────┘   │
                         └──────────────────────────┘
                                  │
                         ┌────────▼─────────────────┐
                         │   MinIO (파일 스토리지)  │
                         │  - 채팅 파일 업로드      │
                         │  - 문서 벡터화 대상      │
                         └──────────────────────────┘
```

---

## 🔑 핵심 개념: Room ID (CNVS_IDT_ID)

### ⚠️ 중요: 실제 구현과 다른 점

**잘못된 가정 (곽두일 PM 계획서):**
```python
# ❌ UUID 방식 (실제 코드와 다름)
room_id = str(uuid.uuid4())  # "abc-123-def-456"
```

**실제 코드 (QuerySaveMapper.xml:27):**
```sql
-- ✅ 실제 CNVS_IDT_ID 생성 로직
CD.USR_ID||'_'||TO_CHAR(CURRENT_TIMESTAMP, 'YYYYMMDDHH24MISS')||LPAD(EXTRACT(MICROSECONDS FROM CURRENT_TIMESTAMP)::INTEGER % 1000000, 6, '0')

-- 결과 예시: "user123_20251022104412345678"
-- 형식: {사용자ID}_{타임스탬프 14자리}{마이크로초 6자리}
```

### Room ID vs Session ID vs Conversation ID

| 개념 | 실제 컬럼명 | 설명 | 예시 | 생성 방식 |
|------|------------|------|------|-----------|
| **Room ID** | `CNVS_IDT_ID` | **대화방 식별자** (하나의 대화 스레드) | `user123_20251022104412345678` | DB에서 첫 질의 시 자동 생성 (QuerySaveMapper) |
| **Conversation ID** | `CNVS_ID` | **개별 메시지 ID** (질문-답변 1쌍) | `123456` (시퀀스) | DB Auto-increment (USR_CNVS.CNVS_ID) |
| **Session ID** | `SESN_ID` | HTTP 세션 ID (Spring Session) | `ABC123XYZ` | Spring Security 자동 생성 |

### Room ID 생명주기

```
┌─────────────────────────────────────────────────────────────┐
│  1. 새 대화 시작                                             │
│  ────────────────────────────────────────────────────────── │
│  프론트엔드 (Zustand):                                       │
│    roomId: ''  ← 초기값 (빈 스트링, null 아님!)             │
│                                                              │
│  API 요청:                                                   │
│    POST /api/chat/conversation                               │
│    { cnvsIdtId: "", message: "안녕하세요" }                  │
│                                                              │
│  백엔드 처리:                                                │
│    1) cnvsIdtId가 "" → 새 대화로 판단                       │
│    2) QuerySaveMapper 호출                                   │
│    3) USR_CNVS_SMRY에 INSERT (CNVS_IDT_ID 생성)             │
│       - SQL: USR_ID||'_'||TIMESTAMP||MICROSECONDS            │
│       - 예: "user123_20251022104412345678"                   │
│    4) USR_CNVS에 INSERT (CNVS_ID 자동 생성)                 │
│                                                              │
│  SSE 응답:                                                   │
│    data: {"type": "room_created",                            │
│            "room_id": "user123_20251022104412345678"}        │
│    data: {"content": {"response": "안녕하세요!"}}            │
│    data: [DONE]                                              │
│                                                              │
│  프론트엔드 처리:                                            │
│    roomIdStore.setCurrentRoomId("user123_...")               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  2. 기존 대화 이어가기                                       │
│  ────────────────────────────────────────────────────────── │
│  프론트엔드 (Zustand):                                       │
│    roomId: "user123_20251022104412345678"                    │
│                                                              │
│  API 요청:                                                   │
│    POST /api/chat/conversation                               │
│    { cnvsIdtId: "user123_20251022104412345678",              │
│      message: "추가 질문" }                                  │
│                                                              │
│  백엔드 처리 (Stateless):                                    │
│    1) cnvsIdtId가 있음 → DB에서 검증                        │
│    2) ChatMapper.isValidRoomIdForUser() 호출                 │
│       SELECT COUNT(*) FROM TB_QUES_HIS                       │
│       WHERE CNVS_IDT_ID = ? AND USR_ID = ?                   │
│    3) 유효하면 → USR_CNVS에 새 메시지 INSERT                │
│    4) 무효하면 → 403 Error 반환                             │
│                                                              │
│  SSE 응답:                                                   │
│    data: {"content": {"response": "답변입니다"}}             │
│    data: [DONE]                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  3. ChatHistory 클릭 (이전 대화 열기)                       │
│  ────────────────────────────────────────────────────────── │
│  API 요청:                                                   │
│    POST /api/chat/history/list                               │
│    { userId: "user123" }                                     │
│                                                              │
│  응답:                                                       │
│    [                                                         │
│      {                                                       │
│        "cnvsIdtId": "user123_20251022104412345678",          │
│        "cnvsSmryTxt": "대화 요약",                           │
│        "regDt": "2025-10-22 10:44:12"                        │
│      }                                                       │
│    ]                                                         │
│                                                              │
│  프론트엔드 처리 (ChatHistory.jsx):                         │
│    handleHistoryClick(item) {                                │
│      clearMessages();  // 메시지 초기화 + roomId 리셋       │
│      setCurrentRoomId(item.cnvsIdtId);  // roomId 설정      │
│    }                                                         │
│                                                              │
│  다음 메시지 전송:                                           │
│    { cnvsIdtId: "user123_20251022104412345678", ... }        │
└─────────────────────────────────────────────────────────────┘
```

### ⚠️ Stateless 방식: HTTP 세션에 저장 안 함

**기존 코드 (삭제됨):**
```java
// ❌ 제거된 코드 (Session-based)
session.setAttribute("roomId", newRoomId);
String roomId = (String) session.getAttribute("roomId");
```

**새 코드 (Stateless):**
```java
// ✅ Stateless: 매 요청마다 DB 검증
String cnvsIdtId = requestDto.getCnvsIdtId();
if (cnvsIdtId == null || cnvsIdtId.trim().isEmpty()) {
    roomId = createNewRoomId(userInfo);  // DB INSERT
} else {
    roomId = validateRoomIdFromDB(cnvsIdtId, userInfo);  // DB SELECT
}
```

**프론트엔드 (Zustand):**
```javascript
// roomIdStore.js
export const useRoomId = create(set => ({
  roomId: '',  // 초기값: 빈 스트링

  setCurrentRoomId: id => {
    set({ roomId: id });
  },

  clearRoomId: () => {
    set({ roomId: '' });  // 새 대화 시작
  }
}));

// ⚠️ persist 사용 안 함 - 브라우저 닫으면 사라짐
```

---

## 📊 데이터베이스 스키마 (실제 구조)

### ⚠️ 중요: 실제 테이블 구조

**잘못된 가정 (곽두일 PM 계획서):**
```sql
-- ❌ 존재하지 않는 테이블
CREATE TABLE rooms (
    room_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    name VARCHAR(500) DEFAULT '새 대화',
    ...
)
```

**실제 테이블 (QuerySaveMapper.xml, ConversationHistoryMapper.xml 분석):**

### 1. USR_CNVS_SMRY (대화 요약 테이블)

```sql
-- 목적: 대화방별 요약 정보 저장 (ChatHistory 목록에 표시)
CREATE TABLE USR_CNVS_SMRY (
    CNVS_IDT_ID VARCHAR(255) PRIMARY KEY,  -- 대화 식별 ID (user_id + timestamp)
    CNVS_SMRY_TXT TEXT,                     -- 대화 요약 (첫 질문으로 자동 생성)
    REP_CNVS_NM VARCHAR(500),               -- 대표 대화명 (사용자가 수정 가능)
    USR_ID VARCHAR(50) NOT NULL,            -- 사용자 ID
    MENU_IDT_ID VARCHAR(50),                -- 메뉴 식별 ID
    USE_YN CHAR(1) DEFAULT 'Y',             -- 사용 여부
    REG_DT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    MOD_DT TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_usr_cnvs_smry_usr_id ON USR_CNVS_SMRY(USR_ID);
CREATE INDEX idx_usr_cnvs_smry_reg_dt ON USR_CNVS_SMRY(REG_DT DESC);

-- 생성 시점: 첫 번째 질의 시 (QuerySaveMapper.insertQuerySave)
-- 업데이트: ConversationNameUpdateMapper.updateConversationName
```

### 2. USR_CNVS (대화 상세 테이블)

```sql
-- 목적: 질문-답변 쌍 (턴) 저장
CREATE TABLE USR_CNVS (
    CNVS_IDT_ID VARCHAR(255) NOT NULL,     -- FK: USR_CNVS_SMRY.CNVS_IDT_ID
    CNVS_ID BIGSERIAL PRIMARY KEY,         -- 대화 ID (Auto-increment)
    QUES_TXT TEXT NOT NULL,                -- 질문 텍스트
    ANS_TXT TEXT,                          -- 답변 텍스트 (처음에는 NULL, 나중에 UPDATE)
    QUES_SMRY_TXT TEXT,                    -- 질문 요약
    ANS_SMRY_TXT TEXT,                     -- 답변 요약
    INFR_TXT TEXT,                         -- 추론 (Think Mode)
    SESN_ID VARCHAR(255),                  -- 세션 ID
    RCM_QUES_YN CHAR(1) DEFAULT 'N',       -- 추천 질의 여부
    QUES_CAT_CD VARCHAR(50),               -- 질의 분류 코드
    QROUT_TYP_CD VARCHAR(50),              -- 쿼리 라우팅 유형 코드
    DOC_CAT_SYS_CD VARCHAR(50),            -- 문서 분류 체계 코드
    SRCH_TIM_MS INTEGER,                   -- 검색 시간 (밀리초)
    RSP_TIM_MS INTEGER,                    -- 응답 시간 (밀리초)
    TKN_USE_CNT INTEGER,                   -- 토큰 사용 수
    ANS_ABRT_YN CHAR(1) DEFAULT 'N',       -- 답변 중지 여부
    USE_YN CHAR(1) DEFAULT 'Y',            -- 사용 여부
    REG_DT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    MOD_DT TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_usr_cnvs_cnvs_idt_id ON USR_CNVS(CNVS_IDT_ID);
CREATE INDEX idx_usr_cnvs_reg_dt ON USR_CNVS(REG_DT);

-- 외래 키
ALTER TABLE USR_CNVS
    ADD CONSTRAINT fk_usr_cnvs_smry
    FOREIGN KEY (CNVS_IDT_ID)
    REFERENCES USR_CNVS_SMRY(CNVS_IDT_ID)
    ON DELETE CASCADE;

-- INSERT: QuerySaveMapper.insertQuerySave (질문만)
-- UPDATE: AnswerSaveMapper.insertAnswerSave (답변 추가)
```

### 3. USR_CNVS_REF_DOC_LST (참조 문서 목록)

```sql
-- 목적: RAG에서 검색된 참조 문서 저장
CREATE TABLE USR_CNVS_REF_DOC_LST (
    REF_DOC_ID BIGSERIAL PRIMARY KEY,
    CNVS_ID BIGINT NOT NULL,               -- FK: USR_CNVS.CNVS_ID
    REF_SEQ INTEGER NOT NULL,              -- 참조 순번 (0, 1, 2, ...)
    DOC_TYP_CD CHAR(1) DEFAULT 'N',        -- 문서 유형 (N: 일반, Q: 질의, A: 답변)
    ATT_DOC_NM VARCHAR(500),               -- 첨부 문서명
    ATT_DOC_ID VARCHAR(255),               -- 문서 ID
    FILE_UID VARCHAR(255),                 -- 파일 UID
    FILE_DOWN_URL TEXT,                    -- 다운로드 URL
    DOC_CHNK_NM VARCHAR(500),              -- 청크명 (섹션 제목)
    DOC_CHNK_TXT TEXT,                     -- 청크 텍스트 (상세 내용)
    SMLT_RTE DECIMAL(10,5),                -- 유사도 점수 (Relevance Score)
    REG_USR_ID VARCHAR(50),
    REG_DT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    MOD_DT TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_ref_doc_cnvs_id ON USR_CNVS_REF_DOC_LST(CNVS_ID);
CREATE INDEX idx_ref_doc_smlt_rte ON USR_CNVS_REF_DOC_LST(SMLT_RTE DESC);

-- 외래 키
ALTER TABLE USR_CNVS_REF_DOC_LST
    ADD CONSTRAINT fk_usr_cnvs
    FOREIGN KEY (CNVS_ID)
    REFERENCES USR_CNVS(CNVS_ID)
    ON DELETE CASCADE;

-- INSERT: AnswerSaveMapper.insertAnswerSave
```

### 4. USR_CNVS_ADD_QUES_LST (추가 질의 목록)

```sql
-- 목적: AI가 제안한 추가 질의 저장 (Suggested Questions)
CREATE TABLE USR_CNVS_ADD_QUES_LST (
    ADD_QUES_ID BIGSERIAL PRIMARY KEY,
    CNVS_ID BIGINT NOT NULL,               -- FK: USR_CNVS.CNVS_ID
    ADD_QUES_SEQ INTEGER NOT NULL,         -- 추가 질의 순번
    ADD_QUES_TXT TEXT NOT NULL,            -- 추가 질의 텍스트
    RAG_CLS_CD VARCHAR(50) DEFAULT 'PUBLIC', -- RAG 구분 코드
    REG_USR_ID VARCHAR(50),
    REG_DT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    MOD_DT TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_add_ques_cnvs_id ON USR_CNVS_ADD_QUES_LST(CNVS_ID);

-- 외래 키
ALTER TABLE USR_CNVS_ADD_QUES_LST
    ADD CONSTRAINT fk_usr_cnvs_aq
    FOREIGN KEY (CNVS_ID)
    REFERENCES USR_CNVS(CNVS_ID)
    ON DELETE CASCADE;

-- INSERT: AnswerSaveMapper.insertAnswerSave
```

### 5. USR_UPLD_DOC_MNG (업로드 문서 관리)

```sql
-- 목적: 사용자가 업로드한 파일 관리
CREATE TABLE USR_UPLD_DOC_MNG (
    FILE_UPLD_ID BIGSERIAL PRIMARY KEY,
    CNVS_IDT_ID VARCHAR(255),              -- FK: USR_CNVS_SMRY.CNVS_IDT_ID
    CNVS_ID BIGINT,                        -- FK: USR_CNVS.CNVS_ID
    FILE_UPLD_SEQ INTEGER,                 -- 파일 업로드 순번
    FILE_NM VARCHAR(500) NOT NULL,         -- 파일명
    FILE_UID VARCHAR(255) NOT NULL,        -- MinIO 파일 UID
    FILE_DOWN_URL TEXT,                    -- 다운로드 URL
    FILE_SIZE BIGINT,                      -- 파일 크기 (bytes)
    FILE_TYP_CD VARCHAR(50),               -- 파일 유형 코드
    USR_ID VARCHAR(50) NOT NULL,
    REG_DT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    MOD_DT TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_upld_doc_cnvs_idt_id ON USR_UPLD_DOC_MNG(CNVS_IDT_ID);
CREATE INDEX idx_upld_doc_cnvs_id ON USR_UPLD_DOC_MNG(CNVS_ID);
CREATE INDEX idx_upld_doc_usr_id ON USR_UPLD_DOC_MNG(USR_ID);

-- 외래 키
ALTER TABLE USR_UPLD_DOC_MNG
    ADD CONSTRAINT fk_usr_cnvs_smry_upld
    FOREIGN KEY (CNVS_IDT_ID)
    REFERENCES USR_CNVS_SMRY(CNVS_IDT_ID)
    ON DELETE CASCADE;
```

### 6. chat_messages (채팅 메시지 - 추가 테이블)

```sql
-- 목적: Spring Boot ChatController에서 사용하는 간단한 메시지 저장
-- ⚠️ USR_CNVS와 중복될 수 있음 (향후 통합 검토 필요)
CREATE TABLE chat_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255),               -- HTTP 세션 ID
    user_id VARCHAR(50) NOT NULL,
    role VARCHAR(20) NOT NULL,             -- 'user' or 'assistant'
    content TEXT NOT NULL,
    room_id VARCHAR(255),                  -- CNVS_IDT_ID와 동일
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_chat_msg_room_id ON chat_messages(room_id);
CREATE INDEX idx_chat_msg_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_msg_user_id ON chat_messages(user_id);

-- INSERT: ChatController.saveChatHistory()
```

### ⚠️ 테이블 관계도 (실제 구조)

```
USR_CNVS_SMRY (대화 요약)
    │ CNVS_IDT_ID (PK)
    │
    ├──> USR_CNVS (대화 상세)
    │       │ CNVS_IDT_ID (FK)
    │       │ CNVS_ID (PK, Auto-increment)
    │       │
    │       ├──> USR_CNVS_REF_DOC_LST (참조 문서)
    │       │       CNVS_ID (FK)
    │       │
    │       └──> USR_CNVS_ADD_QUES_LST (추가 질의)
    │               CNVS_ID (FK)
    │
    └──> USR_UPLD_DOC_MNG (업로드 파일)
            CNVS_IDT_ID (FK)
            CNVS_ID (FK, Optional)

chat_messages (별도 테이블)
    room_id → CNVS_IDT_ID 참조 (FK 없음)
```

### 데이터 흐름 예시

```sql
-- 1. 첫 질의: "AI Streams란 무엇인가요?"
-- QuerySaveMapper.insertQuerySave 호출

-- 1-1) USR_CNVS_SMRY에 INSERT
INSERT INTO USR_CNVS_SMRY (CNVS_IDT_ID, CNVS_SMRY_TXT, USR_ID)
VALUES (
    'user123_20251022104412345678',  -- 자동 생성
    'AI Streams란 무엇인가요?',      -- 첫 질문으로 요약
    'user123'
);

-- 1-2) USR_CNVS에 INSERT
INSERT INTO USR_CNVS (CNVS_IDT_ID, QUES_TXT, SESN_ID)
VALUES (
    'user123_20251022104412345678',
    'AI Streams란 무엇인가요?',
    'ABC123XYZ'
);
-- CNVS_ID = 1 (자동 생성)

-- 2. AI 응답 후
-- AnswerSaveMapper.insertAnswerSave 호출

-- 2-1) USR_CNVS 업데이트
UPDATE USR_CNVS
SET ANS_TXT = 'AI Streams는 ...',
    TKN_USE_CNT = 1234,
    RSP_TIM_MS = 567
WHERE CNVS_ID = 1;

-- 2-2) 참조 문서 INSERT
INSERT INTO USR_CNVS_REF_DOC_LST (CNVS_ID, REF_SEQ, ATT_DOC_NM, DOC_CHNK_TXT, SMLT_RTE)
VALUES
    (1, 0, 'manual.pdf', '페이지 1 내용...', 95.5),
    (1, 1, 'guide.pdf', '페이지 3 내용...', 87.2);

-- 2-3) 추가 질의 INSERT
INSERT INTO USR_CNVS_ADD_QUES_LST (CNVS_ID, ADD_QUES_SEQ, ADD_QUES_TXT)
VALUES
    (1, 1, 'AI Streams의 주요 기능은?'),
    (1, 2, 'AI Streams 설치 방법은?');

-- 3. 추가 질의: "주요 기능은?"
-- QuerySaveMapper.insertQuerySave 호출 (CNVS_IDT_ID 전달)

INSERT INTO USR_CNVS (CNVS_IDT_ID, QUES_TXT)
VALUES (
    'user123_20251022104412345678',  -- 동일한 CNVS_IDT_ID
    'AI Streams의 주요 기능은?'
);
-- CNVS_ID = 2 (자동 생성)

-- 4. 대화 목록 조회
-- ConversationHistoryMapper.selectConversationList

SELECT
    CNVS_IDT_ID,
    NVL(CNVS_SMRY_TXT, '대화 요약 없음') as cnvsSmryTxt,
    TO_CHAR(REG_DT, 'YYYY-MM-DD HH24:MI:SS') as regDt
FROM USR_CNVS_SMRY
WHERE USR_ID = 'user123'
ORDER BY REG_DT DESC;

-- 결과:
-- CNVS_IDT_ID: user123_20251022104412345678
-- cnvsSmryTxt: AI Streams란 무엇인가요?
-- regDt: 2025-10-22 10:44:12

-- 5. 특정 대화의 메시지 조회
-- ConversationHistoryMapper.selectUserConversation

SELECT
    CNVS_ID,
    QUES_TXT,
    ANS_TXT,
    TO_CHAR(REG_DT, 'YYYY-MM-DD HH24:MI:SS') AS REG_YMD
FROM USR_CNVS
WHERE CNVS_IDT_ID = 'user123_20251022104412345678'
  AND USE_YN = 'Y'
ORDER BY REG_DT, CNVS_ID;

-- 결과:
-- CNVS_ID: 1
-- QUES_TXT: AI Streams란 무엇인가요?
-- ANS_TXT: AI Streams는 ...
--
-- CNVS_ID: 2
-- QUES_TXT: AI Streams의 주요 기능은?
-- ANS_TXT: 주요 기능은 ...
```

---

## 🔌 API 엔드포인트 매핑 (실제 코드 기반)

### ⚠️ 중요: 실제 API 경로

**잘못된 가정 (곽두일 PM 계획서):**
```
POST /exGenBotDS/chat → /api/v1/chat/send  # ❌ 틀림
```

**실제 API 경로:**
```
POST /api/chat/conversation → /api/v1/chat/send  # ✅ 맞음 (SSE 스트리밍)
POST /api/chat/history/list → /api/v1/chat/history/list
GET /api/chat/history/{roomId} → /api/v1/chat/history/{room_id}
```

### 1. 채팅 메시지 전송 (스트리밍)

#### Spring Boot (AS-IS)
```
POST /api/chat/conversation
Content-Type: application/json

{
  "cnvsIdtId": "",  // 새 대화: "" / 기존 대화: "user123_..."
  "message": "안녕하세요",
  "stream": true,
  "history": [],
  "search_documents": true,
  "department": "D001",
  "search_scope": ["manual", "faq"],
  "max_context_tokens": 4000,
  "temperature": 0.7,
  "suggest_questions": true,
  "think_mode": false,
  "current_time": "2025-10-22 10:44:12"
}

# 응답 (SSE)
Content-Type: text/event-stream

data: {"type": "room_created", "room_id": "user123_20251022104412345678"}

data: {"content": {"response": "안녕하세요!"}}

data: {"content": {"response": " 무엇을 도와드릴까요?"}}

data: {"metadata": {"tokens": 1234, "time_ms": 567}}

data: {"suggested_questions": ["질문1", "질문2"]}

data: [DONE]
```

#### FastAPI (TO-BE)
```
POST /api/v1/chat/send
Content-Type: application/json
Authorization: Bearer {token}

{
  "cnvs_idt_id": "",  // 새 대화: "" / 기존 대화: "user123_..."
  "message": "안녕하세요",
  "stream": true,
  "history": [],
  "search_documents": true,
  "department": "D001",
  "search_scope": ["manual", "faq"],
  "max_context_tokens": 4000,
  "temperature": 0.7,
  "suggest_questions": true,
  "think_mode": false
}

# 응답 (SSE)
Content-Type: text/event-stream

data: {"type": "room_created", "room_id": "user123_20251022104412345678"}

data: {"content": {"response": "안녕하세요!"}}

data: {"content": {"response": " 무엇을 도와드릴까요?"}}

data: {"metadata": {"tokens": 1234, "time_ms": 567}}

data: {"suggested_questions": ["질문1", "질문2"]}

data: [DONE]
```

**FastAPI 구현 예시:**
```python
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import json

router = APIRouter()

class ChatRequest(BaseModel):
    cnvs_idt_id: str = ""  # 빈 스트링 = 새 대화
    message: str
    stream: bool = True
    history: List[dict] = []
    search_documents: bool = False
    department: Optional[str] = None
    search_scope: Optional[List[str]] = None
    max_context_tokens: int = 4000
    temperature: float = 0.7
    suggest_questions: bool = False
    think_mode: bool = False

async def generate_chat_stream(
    request: ChatRequest,
    user_id: str,
    db_session
):
    """SSE 스트리밍 생성"""
    try:
        # 1. Room ID 생성 또는 검증
        if not request.cnvs_idt_id or request.cnvs_idt_id.strip() == "":
            # 새 대화 - DB에서 CNVS_IDT_ID 생성
            room_id = await create_room_id(user_id, db_session)
            is_new_room = True
        else:
            # 기존 대화 - DB 검증
            room_id = request.cnvs_idt_id
            is_valid = await validate_room_id(room_id, user_id, db_session)
            if not is_valid:
                raise HTTPException(
                    status_code=403,
                    detail="유효하지 않은 대화방 ID이거나 접근 권한이 없습니다."
                )
            is_new_room = False

        # 2. 새 룸 생성 시 room_id 전송
        if is_new_room:
            yield f"data: {json.dumps({'type': 'room_created', 'room_id': room_id})}\n\n"

        # 3. AI 응답 스트리밍
        async for chunk in ai_service.stream_chat(
            message=request.message,
            history=request.history,
            search_documents=request.search_documents,
            # ... 기타 파라미터
        ):
            yield f"data: {json.dumps({'content': {'response': chunk}})}\n\n"

        # 4. 메타데이터 전송
        metadata = {
            "tokens": ai_service.token_count,
            "time_ms": ai_service.response_time_ms
        }
        yield f"data: {json.dumps({'metadata': metadata})}\n\n"

        # 5. 추천 질문 (옵션)
        if request.suggest_questions:
            suggested = await ai_service.generate_suggested_questions()
            yield f"data: {json.dumps({'suggested_questions': suggested})}\n\n"

        # 6. 종료 신호
        yield "data: [DONE]\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

@router.post("/api/v1/chat/send")
async def send_chat_message(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """채팅 메시지 전송 (SSE 스트리밍)"""
    return StreamingResponse(
        generate_chat_stream(request, current_user["user_id"], db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

async def create_room_id(user_id: str, db: AsyncSession) -> str:
    """
    Room ID 생성 (실제 로직 반영)
    형식: {user_id}_{timestamp}{microseconds}
    """
    from datetime import datetime

    now = datetime.now()
    timestamp = now.strftime('%Y%m%d%H%M%S')
    microseconds = f"{now.microsecond % 1000000:06d}"
    room_id = f"{user_id}_{timestamp}{microseconds}"

    # DB에 USR_CNVS_SMRY INSERT
    await db.execute(
        """
        INSERT INTO USR_CNVS_SMRY (CNVS_IDT_ID, CNVS_SMRY_TXT, USR_ID)
        VALUES (:room_id, '새 대화', :user_id)
        """,
        {"room_id": room_id, "user_id": user_id}
    )
    await db.commit()

    return room_id

async def validate_room_id(room_id: str, user_id: str, db: AsyncSession) -> bool:
    """
    Room ID 검증 (Stateless 방식)
    DB에서 해당 사용자의 대화방인지 확인
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
    return count > 0
```

### 2. 대화 목록 조회

#### Spring Boot (AS-IS)
```
POST /api/chat/history/list
Content-Type: application/json

{
  "userId": "user123"
}

# 응답
{
  "result": "success",
  "data": [
    {
      "cnvsIdtId": "user123_20251022104412345678",
      "cnvsSmryTxt": "AI Streams란 무엇인가요?",
      "regDt": "2025-10-22 10:44:12"
    },
    {
      "cnvsIdtId": "user123_20251021093025123456",
      "cnvsSmryTxt": "데이터 분석 방법",
      "regDt": "2025-10-21 09:30:25"
    }
  ]
}
```

#### FastAPI (TO-BE)
```
POST /api/v1/chat/history/list
Content-Type: application/json
Authorization: Bearer {token}

{
  "user_id": "user123"
}

# 응답
{
  "conversations": [
    {
      "cnvs_idt_id": "user123_20251022104412345678",
      "cnvs_smry_txt": "AI Streams란 무엇인가요?",
      "reg_dt": "2025-10-22T10:44:12"
    },
    {
      "cnvs_idt_id": "user123_20251021093025123456",
      "cnvs_smry_txt": "데이터 분석 방법",
      "reg_dt": "2025-10-21T09:30:25"
    }
  ],
  "total": 2
}
```

**FastAPI 구현:**
```python
from pydantic import BaseModel
from typing import List
from datetime import datetime

class ConversationSummary(BaseModel):
    cnvs_idt_id: str
    cnvs_smry_txt: str
    reg_dt: datetime

class HistoryListResponse(BaseModel):
    conversations: List[ConversationSummary]
    total: int

@router.post("/api/v1/chat/history/list", response_model=HistoryListResponse)
async def get_conversation_list(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """대화 목록 조회"""
    # 권한 검증: 본인 데이터만 조회 가능
    if user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    # ConversationHistoryMapper.selectConversationList와 동일한 쿼리
    result = await db.execute(
        """
        SELECT
            CNVS_IDT_ID as cnvs_idt_id,
            NVL(CNVS_SMRY_TXT, '대화 요약 없음') as cnvs_smry_txt,
            REG_DT as reg_dt
        FROM USR_CNVS_SMRY
        WHERE USR_ID = :user_id
          AND USE_YN = 'Y'
        ORDER BY REG_DT DESC
        """,
        {"user_id": user_id}
    )

    conversations = result.fetchall()

    return HistoryListResponse(
        conversations=[
            ConversationSummary(
                cnvs_idt_id=row.cnvs_idt_id,
                cnvs_smry_txt=row.cnvs_smry_txt,
                reg_dt=row.reg_dt
            )
            for row in conversations
        ],
        total=len(conversations)
    )
```

### 3. 특정 대화의 메시지 조회

#### Spring Boot (AS-IS)
```
GET /api/chat/history/user123_20251022104412345678

# 응답
{
  "result": "success",
  "data": [
    {
      "role": "user",
      "content": "AI Streams란 무엇인가요?",
      "timestamp": "2025-10-22 10:44:12"
    },
    {
      "role": "assistant",
      "content": "AI Streams는 ...",
      "timestamp": "2025-10-22 10:44:15"
    }
  ],
  "room_id": "user123_20251022104412345678"
}
```

#### FastAPI (TO-BE)
```
GET /api/v1/chat/history/{room_id}
Authorization: Bearer {token}

# 응답
{
  "cnvs_idt_id": "user123_20251022104412345678",
  "messages": [
    {
      "cnvs_id": 1,
      "role": "user",
      "content": "AI Streams란 무엇인가요?",
      "timestamp": "2025-10-22T10:44:12",
      "metadata": {
        "tokens": 0,
        "search_time_ms": 0
      }
    },
    {
      "cnvs_id": 1,
      "role": "assistant",
      "content": "AI Streams는 ...",
      "timestamp": "2025-10-22T10:44:15",
      "metadata": {
        "tokens": 1234,
        "search_time_ms": 456,
        "response_time_ms": 567
      },
      "references": [
        {
          "ref_seq": 0,
          "doc_name": "manual.pdf",
          "chunk_text": "페이지 1 내용...",
          "similarity": 95.5
        }
      ],
      "suggested_questions": [
        "AI Streams의 주요 기능은?",
        "AI Streams 설치 방법은?"
      ]
    }
  ],
  "total_messages": 2
}
```

**FastAPI 구현:**
```python
from pydantic import BaseModel
from typing import List, Optional

class MessageReference(BaseModel):
    ref_seq: int
    doc_name: str
    chunk_text: str
    similarity: float

class MessageMetadata(BaseModel):
    tokens: int
    search_time_ms: int
    response_time_ms: Optional[int] = None

class ChatMessage(BaseModel):
    cnvs_id: int
    role: str
    content: str
    timestamp: datetime
    metadata: MessageMetadata
    references: Optional[List[MessageReference]] = None
    suggested_questions: Optional[List[str]] = None

class HistoryDetailResponse(BaseModel):
    cnvs_idt_id: str
    messages: List[ChatMessage]
    total_messages: int

@router.get("/api/v1/chat/history/{room_id}", response_model=HistoryDetailResponse)
async def get_conversation_detail(
    room_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """특정 대화의 메시지 상세 조회"""
    user_id = current_user["user_id"]

    # 권한 검증
    is_valid = await validate_room_id(room_id, user_id, db)
    if not is_valid:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    # ConversationHistoryMapper.selectUserConversation와 동일한 쿼리
    result = await db.execute(
        """
        SELECT
            C.CNVS_ID,
            C.QUES_TXT,
            C.ANS_TXT,
            C.TKN_USE_CNT,
            C.SRCH_TIM_MS,
            C.RSP_TIM_MS,
            C.REG_DT
        FROM USR_CNVS C
        WHERE C.CNVS_IDT_ID = :room_id
          AND C.USE_YN = 'Y'
        ORDER BY C.REG_DT, C.CNVS_ID
        """,
        {"room_id": room_id}
    )

    conversations = result.fetchall()
    messages = []

    for row in conversations:
        # 질문 메시지
        messages.append(ChatMessage(
            cnvs_id=row.CNVS_ID,
            role="user",
            content=row.QUES_TXT,
            timestamp=row.REG_DT,
            metadata=MessageMetadata(
                tokens=0,
                search_time_ms=0
            )
        ))

        # 답변 메시지
        if row.ANS_TXT:
            # 참조 문서 조회
            refs_result = await db.execute(
                """
                SELECT REF_SEQ, ATT_DOC_NM, DOC_CHNK_TXT, SMLT_RTE
                FROM USR_CNVS_REF_DOC_LST
                WHERE CNVS_ID = :cnvs_id
                ORDER BY REF_SEQ
                """,
                {"cnvs_id": row.CNVS_ID}
            )
            references = [
                MessageReference(
                    ref_seq=r.REF_SEQ,
                    doc_name=r.ATT_DOC_NM,
                    chunk_text=r.DOC_CHNK_TXT,
                    similarity=r.SMLT_RTE
                )
                for r in refs_result.fetchall()
            ]

            # 추가 질의 조회
            sugg_result = await db.execute(
                """
                SELECT ADD_QUES_TXT
                FROM USR_CNVS_ADD_QUES_LST
                WHERE CNVS_ID = :cnvs_id
                ORDER BY ADD_QUES_SEQ
                """,
                {"cnvs_id": row.CNVS_ID}
            )
            suggested = [r.ADD_QUES_TXT for r in sugg_result.fetchall()]

            messages.append(ChatMessage(
                cnvs_id=row.CNVS_ID,
                role="assistant",
                content=row.ANS_TXT,
                timestamp=row.REG_DT,
                metadata=MessageMetadata(
                    tokens=row.TKN_USE_CNT or 0,
                    search_time_ms=row.SRCH_TIM_MS or 0,
                    response_time_ms=row.RSP_TIM_MS
                ),
                references=references if references else None,
                suggested_questions=suggested if suggested else None
            ))

    return HistoryDetailResponse(
        cnvs_idt_id=room_id,
        messages=messages,
        total_messages=len(messages)
    )
```

### 4. 대화명 변경

#### Spring Boot (AS-IS)
```
POST /api/conversation/update-name
Content-Type: application/json

{
  "cnvsIdtId": "user123_20251022104412345678",
  "repCnvsNm": "AI 관련 질문들"
}

# 응답
{
  "result": "success",
  "message": "대화명이 변경되었습니다."
}
```

#### FastAPI (TO-BE)
```
PATCH /api/v1/chat/rooms/{room_id}/name
Content-Type: application/json
Authorization: Bearer {token}

{
  "name": "AI 관련 질문들"
}

# 응답
{
  "cnvs_idt_id": "user123_20251022104412345678",
  "name": "AI 관련 질문들",
  "updated_at": "2025-10-22T11:00:00"
}
```

**FastAPI 구현:**
```python
@router.patch("/api/v1/chat/rooms/{room_id}/name")
async def update_room_name(
    room_id: str,
    name: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """대화명 변경"""
    user_id = current_user["user_id"]

    # 권한 검증
    is_valid = await validate_room_id(room_id, user_id, db)
    if not is_valid:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    # ConversationNameUpdateMapper.updateConversationName와 동일
    await db.execute(
        """
        UPDATE USR_CNVS_SMRY
        SET REP_CNVS_NM = :name,
            MOD_DT = CURRENT_TIMESTAMP
        WHERE CNVS_IDT_ID = :room_id
        """,
        {"name": name, "room_id": room_id}
    )
    await db.commit()

    # 업데이트된 정보 조회
    result = await db.execute(
        """
        SELECT REP_CNVS_NM, MOD_DT
        FROM USR_CNVS_SMRY
        WHERE CNVS_IDT_ID = :room_id
        """,
        {"room_id": room_id}
    )
    row = result.fetchone()

    return {
        "cnvs_idt_id": room_id,
        "name": row.REP_CNVS_NM,
        "updated_at": row.MOD_DT
    }
```

### 5. 대화 삭제 (소프트 삭제)

#### Spring Boot (AS-IS)
```
POST /api/conversation/delete
Content-Type: application/json

{
  "cnvsIdtId": "user123_20251022104412345678"
}

# 응답
{
  "result": "success",
  "message": "대화가 삭제되었습니다."
}
```

#### FastAPI (TO-BE)
```
DELETE /api/v1/chat/rooms/{room_id}
Authorization: Bearer {token}

# 응답
{
  "cnvs_idt_id": "user123_20251022104412345678",
  "deleted": true,
  "deleted_at": "2025-10-22T11:05:00"
}
```

**FastAPI 구현:**
```python
@router.delete("/api/v1/chat/rooms/{room_id}")
async def delete_room(
    room_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """대화 삭제 (소프트 삭제)"""
    user_id = current_user["user_id"]

    # 권한 검증
    is_valid = await validate_room_id(room_id, user_id, db)
    if not is_valid:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    # 소프트 삭제: USE_YN = 'N'
    await db.execute(
        """
        UPDATE USR_CNVS_SMRY
        SET USE_YN = 'N',
            MOD_DT = CURRENT_TIMESTAMP
        WHERE CNVS_IDT_ID = :room_id
        """,
        {"room_id": room_id}
    )

    # 하위 메시지도 소프트 삭제
    await db.execute(
        """
        UPDATE USR_CNVS
        SET USE_YN = 'N',
            MOD_DT = CURRENT_TIMESTAMP
        WHERE CNVS_IDT_ID = :room_id
        """,
        {"room_id": room_id}
    )

    await db.commit()

    return {
        "cnvs_idt_id": room_id,
        "deleted": True,
        "deleted_at": datetime.now()
    }
```

---

## 📝 전체 API 매핑 표 (실제 코드 기반)

| 기능 | Spring Boot (AS-IS) | FastAPI (TO-BE) | 메서드 | 응답 형식 |
|------|---------------------|-----------------|--------|-----------|
| 채팅 전송 | `POST /api/chat/conversation` | `POST /api/v1/chat/send` | POST | SSE 스트리밍 |
| 대화 목록 | `POST /api/chat/history/list` | `POST /api/v1/chat/history/list` | POST | JSON |
| 메시지 조회 | `GET /api/chat/history/{roomId}` | `GET /api/v1/chat/history/{room_id}` | GET | JSON |
| 대화명 변경 | `POST /api/conversation/update-name` | `PATCH /api/v1/chat/rooms/{room_id}/name` | PATCH | JSON |
| 대화 삭제 | `POST /api/conversation/delete` | `DELETE /api/v1/chat/rooms/{room_id}` | DELETE | JSON |
| 룸 리셋 (Deprecated) | `POST /api/chat/reset` | ❌ (클라이언트에서 처리) | - | - |
| 현재 룸 조회 (Deprecated) | `GET /api/chat/room-id` | ❌ (클라이언트에서 처리) | - | - |

**⚠️ 중요한 차이점:**
1. **Context Path 없음**: `/exGenBotDS` 사용 안 함
2. **SSE 스트리밍**: `/api/chat/conversation`은 `text/event-stream` 응답
3. **Stateless**: 서버에서 roomId 저장 안 함 (매 요청마다 클라이언트가 전송)
4. **POST /api/chat/history/list**: GET이 아닌 POST 방식 (body에 userId 전달)

---

## 🔐 보안 요구사항 (OWASP Top 10)

### 구현된 보안 (실제 코드)

#### 1. SQL Injection 방지
```java
// ChatMapper.xml - 파라미터 바인딩 사용
<select id="isValidRoomIdForUser" parameterType="map" resultType="boolean">
    SELECT CASE WHEN COUNT(*) > 0 THEN 1 ELSE 0 END
    FROM TB_QUES_HIS
    WHERE CNVS_IDT_ID = #{roomId}  <!-- ✅ 파라미터 바인딩 -->
      AND USR_ID = #{userId}        <!-- ✅ 파라미터 바인딩 -->
    LIMIT 1
</select>
```

**FastAPI 구현:**
```python
# ✅ SQLAlchemy 파라미터 바인딩
result = await db.execute(
    """
    SELECT COUNT(*)
    FROM USR_CNVS_SMRY
    WHERE CNVS_IDT_ID = :room_id
      AND USR_ID = :user_id
    """,
    {"room_id": room_id, "user_id": user_id}  # 파라미터 바인딩
)
```

#### 2. XSS (Cross-Site Scripting) 방지
```java
// ChatController.java - HTML 이스케이프
import org.springframework.web.util.HtmlUtils;

String sanitizedMessage = HtmlUtils.htmlEscape(requestDto.getMessage());
```

**FastAPI 구현:**
```python
from markupsafe import escape

@router.post("/api/v1/chat/send")
async def send_chat_message(request: ChatRequest):
    # ✅ HTML 이스케이프
    sanitized_message = escape(request.message)

    # 응답에서도 이스케이프
    async for chunk in ai_service.stream_chat(sanitized_message):
        yield f"data: {json.dumps({'content': {'response': escape(chunk)}})}\n\n"
```

#### 3. Path Traversal 방지
**기존 파일 브라우저 (file_browser.py) 보안 패턴 참조:**
```python
def validate_path(path: str) -> Path:
    """경로 검증 (Path Traversal 방지)"""
    # 위험한 패턴 감지
    dangerous_patterns = ['../', '..\\', '%2e%2e', '....']
    for pattern in dangerous_patterns:
        if pattern in path.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Invalid path: Path traversal detected"
            )

    # 절대 경로로 정규화
    path_obj = Path(path).resolve()

    # 허용된 디렉토리 확인
    ALLOWED_ROOT_DIRECTORIES = ["/data/audio", "/tmp/test-audio"]
    is_allowed = False
    for allowed_root in ALLOWED_ROOT_DIRECTORIES:
        allowed_root_path = Path(allowed_root).resolve()
        if path_obj == allowed_root_path or allowed_root_path in path_obj.parents:
            is_allowed = True
            break

    if not is_allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: Path must be under allowed directories"
        )

    return path_obj
```

#### 4. 인증 및 권한 검증

**Spring Boot (AS-IS):**
```java
// ChatController.java
HttpSession session = request.getSession(false);
if (session == null) {
    response.setContentType("text/event-stream; charset=UTF-8");
    out.write("data: {\"error\":\"세션이 만료되었습니다\"}\n\n".getBytes("UTF-8"));
    return;
}

UserInfoDto userInfo = (UserInfoDto) session.getAttribute("userInfo");
if (userInfo == null) {
    out.write("data: {\"error\":\"사용자 정보를 찾을 수 없습니다\"}\n\n".getBytes("UTF-8"));
    return;
}

// ✅ Stateless 검증: 매 요청마다 DB에서 roomId 소유권 확인
boolean isValid = chatMapper.isValidRoomIdForUser(cnvsIdtId, userInfo.getUsrId());
if (!isValid) {
    throw new IllegalArgumentException("유효하지 않은 대화방 ID이거나 접근 권한이 없습니다.");
}
```

**FastAPI (TO-BE):**
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """JWT 토큰 검증"""
    token = credentials.credentials

    try:
        # JWT 토큰 디코딩
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰")

        # DB에서 사용자 확인
        result = await db.execute(
            "SELECT USR_ID, DEPT_CD FROM USERS WHERE USR_ID = :user_id",
            {"user_id": user_id}
        )
        user = result.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다")

        return {
            "user_id": user.USR_ID,
            "department": user.DEPT_CD
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="토큰 검증 실패")

@router.post("/api/v1/chat/send")
async def send_chat_message(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),  # ✅ 인증 필수
    db: AsyncSession = Depends(get_db)
):
    """채팅 메시지 전송 (인증 필요)"""
    # ✅ Stateless 검증: 매 요청마다 DB에서 roomId 소유권 확인
    if request.cnvs_idt_id:
        is_valid = await validate_room_id(
            request.cnvs_idt_id,
            current_user["user_id"],
            db
        )
        if not is_valid:
            raise HTTPException(
                status_code=403,
                detail="유효하지 않은 대화방 ID이거나 접근 권한이 없습니다."
            )

    # ... 처리 계속
```

#### 5. 정보 노출 방지 (CWE-209)
```java
// ChatController.java - 에러 메시지 제한
} catch (Exception e) {
    // ✅ 상세 오류는 로그에만 기록
    logger.error("Chat processing error: ", e);

    // ✅ 클라이언트에는 일반적인 메시지만 전송
    out.write("data: {\"error\":\"서버 오류가 발생했습니다\"}\n\n".getBytes("UTF-8"));
}
```

**FastAPI 구현:**
```python
@router.post("/api/v1/chat/send")
async def send_chat_message(...):
    try:
        # ... 처리
    except HTTPException:
        raise  # HTTP 예외는 그대로 전파
    except Exception as e:
        # ✅ 상세 오류는 로그에만 기록
        logger.error(f"Chat processing error: {str(e)}", exc_info=True)

        # ✅ 클라이언트에는 일반적인 메시지만
        raise HTTPException(
            status_code=500,
            detail="서버 오류가 발생했습니다"
        )
```

#### 6. 디버그 코드 제거 (CWE-489)
```java
// ChatController.java
// ❌ 제거: logger.debug("Request body: {}", jsonBody);
// ✅ 운영 환경용 로그만 유지
logger.info("Chat API 요청 - 사용자: {}, 질문 길이: {} 문자",
           userInfo.getUsrId(), query.length());
```

**FastAPI 구현:**
```python
# ✅ 운영 환경에서는 INFO 레벨 이상만 로깅
logger.info(f"Chat request - user: {user_id}, message length: {len(message)}")

# ❌ DEBUG 로그는 개발 환경에서만
# logger.debug(f"Full request: {request.dict()}")  # 운영 환경에서 제거
```

#### 7. Rate Limiting

**FastAPI 구현 (Recommended):**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

@router.post("/api/v1/chat/send")
@limiter.limit("10/minute")  # ✅ 1분당 10회 제한
async def send_chat_message(
    request: Request,
    chat_request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """채팅 메시지 전송 (Rate Limiting)"""
    # ... 처리
```

#### 8. CORS 설정

**FastAPI 구현:**
```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ✅ CORS 설정 (보안)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ui.datastreams.co.kr:20443",  # 운영
        "http://localhost:5173",                # 개발 (Vite)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
    max_age=600,  # 10분
)
```

---

## 📅 마이그레이션 계획 (3주, 21일)

### Phase 1: 준비 및 환경 설정 (Day 1-3)

#### Day 1: 프로젝트 구조 설정
- [ ] FastAPI 프로젝트 생성 (`/home/aigen/admin-api` 하위)
- [ ] 디렉토리 구조 설계:
  ```
  admin-api/
  ├── app/
  │   ├── routers/
  │   │   ├── admin/  (기존)
  │   │   └── chat/   (NEW)
  │   │       ├── __init__.py
  │   │       ├── chat.py          # 채팅 메시지
  │   │       ├── rooms.py         # 대화방 관리
  │   │       ├── history.py       # 히스토리
  │   │       ├── files.py         # 파일 업로드
  │   │       └── survey.py        # 설문/에러 리포트
  │   ├── models/
  │   │   └── chat_models.py       # SQLAlchemy 모델
  │   ├── schemas/
  │   │   └── chat_schemas.py      # Pydantic 스키마
  │   ├── services/
  │   │   ├── chat_service.py      # 채팅 비즈니스 로직
  │   │   ├── ai_service.py        # AI 연동
  │   │   └── file_service.py      # 파일 처리
  │   └── utils/
  │       ├── room_id_generator.py # CNVS_IDT_ID 생성
  │       └── security.py          # 인증/검증
  ├── tests/
  │   ├── test_chat_api.py
  │   ├── test_room_management.py
  │   └── test_security.py
  └── alembic/
      └── versions/
          └── 001_create_chat_tables.py
  ```
- [ ] Poetry 의존성 추가:
  ```toml
  [tool.poetry.dependencies]
  fastapi = "^0.104.0"
  uvicorn = {extras = ["standard"], version = "^0.24.0"}
  sqlalchemy = {extras = ["asyncio"], version = "^2.0.0"}
  asyncpg = "^0.29.0"
  pydantic = "^2.5.0"
  python-jose = {extras = ["cryptography"], version = "^3.3.0"}
  passlib = {extras = ["bcrypt"], version = "^1.7.4"}
  aiofiles = "^23.2.0"
  slowapi = "^0.1.9"  # Rate limiting
  ```

#### Day 2: 데이터베이스 설정
- [ ] PostgreSQL 연결 확인 (1.215.235.250:25444/AGENAI)
- [ ] SQLAlchemy 모델 작성 (USR_CNVS_SMRY, USR_CNVS 등)
- [ ] Alembic 마이그레이션 스크립트 작성
- [ ] 기존 데이터와의 호환성 확인

#### Day 3: 인증 시스템 통합
- [ ] Spring Security SSO → FastAPI JWT 변환 로직
- [ ] 사용자 세션 검증 로직
- [ ] 권한 검증 미들웨어

### Phase 2: 코어 API 구현 (Day 4-10)

#### Day 4-5: Room ID 생성 및 검증
- [ ] `room_id_generator.py` 구현
  - 형식: `{user_id}_{timestamp}{microseconds}`
  - QuerySaveMapper.xml 로직과 동일
- [ ] `validate_room_id()` 함수 구현
  - DB 검증 (Stateless)
  - 사용자 권한 확인
- [ ] 테스트 작성:
  - `test_room_id_generation.py`
  - `test_room_id_validation.py`

#### Day 6-7: 채팅 API 구현
- [ ] `POST /api/v1/chat/send` (SSE 스트리밍)
  - 새 대화 생성 로직
  - 기존 대화 검증 로직
  - AI 서비스 연동
  - 스트리밍 응답 처리
- [ ] 질문 저장 로직 (USR_CNVS INSERT)
- [ ] 답변 저장 로직 (USR_CNVS UPDATE)
- [ ] 테스트 작성:
  - `test_chat_streaming.py`
  - `test_new_conversation.py`
  - `test_existing_conversation.py`

#### Day 8-9: 히스토리 API 구현
- [ ] `POST /api/v1/chat/history/list` (대화 목록)
- [ ] `GET /api/v1/chat/history/{room_id}` (메시지 조회)
- [ ] `PATCH /api/v1/chat/rooms/{room_id}/name` (대화명 변경)
- [ ] `DELETE /api/v1/chat/rooms/{room_id}` (소프트 삭제)
- [ ] 테스트 작성:
  - `test_history_list.py`
  - `test_history_detail.py`
  - `test_room_management.py`

#### Day 10: 파일 업로드 API
- [ ] MinIO 연동 (기존 `file_upload.py` 참고)
- [ ] `POST /api/v1/files/upload`
- [ ] 파일 메타데이터 저장 (USR_UPLD_DOC_MNG)
- [ ] 테스트 작성:
  - `test_file_upload.py`

### Phase 3: 참조 문서 및 추가 기능 (Day 11-14)

#### Day 11-12: RAG 연동
- [ ] 참조 문서 저장 (USR_CNVS_REF_DOC_LST)
- [ ] 추가 질의 저장 (USR_CNVS_ADD_QUES_LST)
- [ ] 벡터 DB 연동 (Qdrant)
- [ ] 문서 검색 로직

#### Day 13: 설문 및 에러 리포트
- [ ] 설문 API 포팅 (SurveyMapper.xml 참고)
- [ ] 에러 리포트 API 포팅 (ErrorReportSaveMapper.xml)
- [ ] 테스트 작성

#### Day 14: 공지사항 및 메뉴 관리
- [ ] 공지사항 API 확장 (NoticeMapper.xml)
- [ ] 메뉴 관리 API (MenuMapper.xml)
- [ ] 테스트 작성

### Phase 4: React 프론트엔드 통합 (Day 15-17)

#### Day 15: API 클라이언트 업데이트
- [ ] `chat.js` 수정:
  - `/api/chat/conversation` → `/api/v1/chat/send`
- [ ] `history.js` 수정:
  - `/api/chat/history/list` → `/api/v1/chat/history/list`
- [ ] 인증 토큰 헤더 추가
- [ ] 에러 핸들링 개선

#### Day 16: Zustand Store 검증
- [ ] roomIdStore.js 동작 확인
- [ ] messageStore.js 통합 테스트
- [ ] fileStore.js 파일 업로드 연동

#### Day 17: UI 컴포넌트 테스트
- [ ] ChatPage.jsx E2E 테스트
- [ ] ChatHistory.jsx 클릭 동작 확인
- [ ] 새 대화 버튼 동작 확인
- [ ] SSE 스트리밍 표시 확인

### Phase 5: 테스트 및 보안 검증 (Day 18-19)

#### Day 18: TDD 커버리지 달성
- [ ] Unit Tests: 60%+ 커버리지
- [ ] Integration Tests: 80%+ 커버리지
- [ ] E2E Tests: 주요 시나리오
- [ ] pytest-cov 리포트 생성

#### Day 19: 보안 검증
- [ ] OWASP Top 10 체크리스트:
  - [ ] SQL Injection 테스트
  - [ ] XSS 테스트
  - [ ] Path Traversal 테스트
  - [ ] 인증/권한 테스트
  - [ ] Rate Limiting 테스트
- [ ] Bandit 정적 분석
- [ ] Safety 의존성 취약점 검사

### Phase 6: 배포 및 모니터링 (Day 20-21)

#### Day 20: 스테이징 배포
- [ ] Docker 이미지 빌드
- [ ] docker-compose.yaml 업데이트
- [ ] 스테이징 환경 배포
- [ ] 통합 테스트 실행

#### Day 21: 운영 배포 및 문서화
- [ ] 운영 환경 배포
- [ ] Nginx 설정 업데이트
- [ ] 모니터링 대시보드 설정
- [ ] 배포 가이드 작성
- [ ] API 문서 생성 (Swagger)

---

## 🧪 테스트 전략 (TDD, 80%+ 커버리지)

### 테스트 구조

```
tests/
├── unit/
│   ├── test_room_id_generator.py
│   ├── test_validators.py
│   ├── test_security.py
│   └── test_utils.py
├── integration/
│   ├── test_chat_api.py
│   ├── test_room_management.py
│   ├── test_history_api.py
│   └── test_file_upload.py
├── e2e/
│   ├── test_chat_flow.py
│   ├── test_history_flow.py
│   └── test_stateless_flow.py
└── conftest.py
```

### 핵심 테스트 시나리오

#### 1. Room ID 생성 및 검증 테스트

```python
# tests/unit/test_room_id_generator.py
import pytest
from datetime import datetime
from app.utils.room_id_generator import generate_room_id, parse_room_id

def test_generate_room_id_format():
    """Room ID 형식 테스트"""
    user_id = "user123"
    room_id = generate_room_id(user_id)

    # 형식: user123_20251022104412345678
    assert room_id.startswith(f"{user_id}_")
    parts = room_id.split("_")
    assert len(parts) == 2
    assert len(parts[1]) == 20  # 14자리 timestamp + 6자리 microseconds

def test_generate_room_id_uniqueness():
    """Room ID 고유성 테스트"""
    user_id = "user123"
    room_ids = [generate_room_id(user_id) for _ in range(100)]

    # 모두 고유해야 함
    assert len(room_ids) == len(set(room_ids))

def test_parse_room_id():
    """Room ID 파싱 테스트"""
    room_id = "user123_20251022104412345678"
    parsed = parse_room_id(room_id)

    assert parsed["user_id"] == "user123"
    assert parsed["timestamp"] == "20251022104412"
    assert parsed["microseconds"] == "345678"

@pytest.mark.asyncio
async def test_validate_room_id_valid(async_db_session):
    """유효한 Room ID 검증 테스트"""
    # Given: DB에 존재하는 roomId
    user_id = "user123"
    room_id = "user123_20251022104412345678"

    await async_db_session.execute(
        """
        INSERT INTO USR_CNVS_SMRY (CNVS_IDT_ID, USR_ID, CNVS_SMRY_TXT)
        VALUES (:room_id, :user_id, '테스트 대화')
        """,
        {"room_id": room_id, "user_id": user_id}
    )
    await async_db_session.commit()

    # When: 검증 수행
    from app.services.chat_service import validate_room_id
    is_valid = await validate_room_id(room_id, user_id, async_db_session)

    # Then: 유효해야 함
    assert is_valid is True

@pytest.mark.asyncio
async def test_validate_room_id_invalid_user(async_db_session):
    """다른 사용자의 Room ID 검증 실패 테스트"""
    # Given: 다른 사용자의 roomId
    room_id = "user123_20251022104412345678"

    await async_db_session.execute(
        """
        INSERT INTO USR_CNVS_SMRY (CNVS_IDT_ID, USR_ID)
        VALUES (:room_id, 'user123')
        """,
        {"room_id": room_id}
    )
    await async_db_session.commit()

    # When: 다른 사용자로 검증
    from app.services.chat_service import validate_room_id
    is_valid = await validate_room_id(room_id, "attacker", async_db_session)

    # Then: 무효해야 함
    assert is_valid is False

@pytest.mark.asyncio
async def test_validate_room_id_nonexistent(async_db_session):
    """존재하지 않는 Room ID 검증 실패 테스트"""
    # When: 존재하지 않는 roomId 검증
    from app.services.chat_service import validate_room_id
    is_valid = await validate_room_id(
        "nonexistent_20251022104412345678",
        "user123",
        async_db_session
    )

    # Then: 무효해야 함
    assert is_valid is False
```

#### 2. 채팅 API 테스트 (SSE 스트리밍)

```python
# tests/integration/test_chat_api.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_new_conversation_creates_room_id(async_client: AsyncClient, auth_headers):
    """새 대화 시작 시 Room ID 생성 테스트"""
    # Given: 새 대화 요청 (cnvs_idt_id = "")
    request_data = {
        "cnvs_idt_id": "",
        "message": "안녕하세요",
        "stream": False  # 테스트 편의를 위해 스트리밍 비활성화
    }

    # When: POST /api/v1/chat/send
    response = await async_client.post(
        "/api/v1/chat/send",
        json=request_data,
        headers=auth_headers
    )

    # Then: 201 Created, room_id 반환
    assert response.status_code == 201
    data = response.json()
    assert "room_id" in data
    assert data["room_id"].startswith("user123_")
    assert "response" in data

    # DB 확인: USR_CNVS_SMRY에 INSERT 되었는지
    # DB 확인: USR_CNVS에 INSERT 되었는지

@pytest.mark.asyncio
async def test_existing_conversation_validates_room_id(
    async_client: AsyncClient,
    auth_headers,
    existing_room_id
):
    """기존 대화 이어가기 시 Room ID 검증 테스트"""
    # Given: 기존 roomId
    request_data = {
        "cnvs_idt_id": existing_room_id,
        "message": "추가 질문입니다",
        "stream": False
    }

    # When: POST /api/v1/chat/send
    response = await async_client.post(
        "/api/v1/chat/send",
        json=request_data,
        headers=auth_headers
    )

    # Then: 200 OK, 동일한 room_id
    assert response.status_code == 200
    data = response.json()
    assert data["room_id"] == existing_room_id

@pytest.mark.asyncio
async def test_invalid_room_id_returns_403(async_client: AsyncClient, auth_headers):
    """유효하지 않은 Room ID로 요청 시 403 에러 테스트"""
    # Given: 존재하지 않는 roomId
    request_data = {
        "cnvs_idt_id": "nonexistent_20251022104412345678",
        "message": "질문",
        "stream": False
    }

    # When: POST /api/v1/chat/send
    response = await async_client.post(
        "/api/v1/chat/send",
        json=request_data,
        headers=auth_headers
    )

    # Then: 403 Forbidden
    assert response.status_code == 403
    assert "유효하지 않은 대화방 ID" in response.json()["detail"]

@pytest.mark.asyncio
async def test_other_users_room_id_returns_403(
    async_client: AsyncClient,
    auth_headers,
    other_users_room_id
):
    """다른 사용자의 Room ID로 요청 시 403 에러 테스트"""
    # Given: 다른 사용자의 roomId
    request_data = {
        "cnvs_idt_id": other_users_room_id,  # user456의 대화방
        "message": "질문",
        "stream": False
    }

    # When: user123으로 요청
    response = await async_client.post(
        "/api/v1/chat/send",
        json=request_data,
        headers=auth_headers  # user123 토큰
    )

    # Then: 403 Forbidden
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_sse_streaming_response(async_client: AsyncClient, auth_headers):
    """SSE 스트리밍 응답 테스트"""
    # Given: 스트리밍 요청
    request_data = {
        "cnvs_idt_id": "",
        "message": "긴 답변이 필요한 질문",
        "stream": True
    }

    # When: POST /api/v1/chat/send (스트리밍)
    async with async_client.stream(
        "POST",
        "/api/v1/chat/send",
        json=request_data,
        headers=auth_headers
    ) as response:
        # Then: Content-Type 확인
        assert response.headers["content-type"] == "text/event-stream"

        # SSE 데이터 수집
        chunks = []
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = line[6:]  # "data: " 제거
                if data == "[DONE]":
                    break
                chunks.append(json.loads(data))

        # 첫 번째 청크는 room_created
        assert chunks[0]["type"] == "room_created"
        assert "room_id" in chunks[0]

        # 나머지 청크들은 content
        for chunk in chunks[1:]:
            assert "content" in chunk or "metadata" in chunk
```

#### 3. Stateless 아키텍처 테스트

```python
# tests/e2e/test_stateless_flow.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_stateless_conversation_flow(async_client: AsyncClient, auth_headers):
    """
    Stateless 대화 흐름 E2E 테스트
    서버에 세션 저장 없이 매 요청마다 roomId 전달 및 검증
    """
    # Step 1: 새 대화 시작 (cnvs_idt_id = "")
    response1 = await async_client.post(
        "/api/v1/chat/send",
        json={"cnvs_idt_id": "", "message": "첫 질문", "stream": False},
        headers=auth_headers
    )
    assert response1.status_code == 201
    room_id = response1.json()["room_id"]

    # Step 2: 동일한 대화에 추가 메시지 (roomId 전달)
    response2 = await async_client.post(
        "/api/v1/chat/send",
        json={"cnvs_idt_id": room_id, "message": "두 번째 질문", "stream": False},
        headers=auth_headers
    )
    assert response2.status_code == 200
    assert response2.json()["room_id"] == room_id

    # Step 3: 히스토리 조회 (roomId로 검증)
    response3 = await async_client.get(
        f"/api/v1/chat/history/{room_id}",
        headers=auth_headers
    )
    assert response3.status_code == 200
    messages = response3.json()["messages"]
    assert len(messages) == 4  # 질문2개 + 답변2개

    # Step 4: 다른 브라우저/세션에서 동일한 roomId로 접근
    #         (서버에 세션이 없어도 동작해야 함)
    new_auth_headers = get_new_auth_token("user123")  # 새 토큰
    response4 = await async_client.post(
        "/api/v1/chat/send",
        json={"cnvs_idt_id": room_id, "message": "세 번째 질문", "stream": False},
        headers=new_auth_headers  # 새 세션
    )
    assert response4.status_code == 200
    assert response4.json()["room_id"] == room_id

    # Step 5: 히스토리 재조회 (3개 메시지 추가)
    response5 = await async_client.get(
        f"/api/v1/chat/history/{room_id}",
        headers=new_auth_headers
    )
    assert len(response5.json()["messages"]) == 6  # 질문3개 + 답변3개
```

#### 4. 보안 테스트

```python
# tests/security/test_security.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_sql_injection_prevention(async_client: AsyncClient, auth_headers):
    """SQL Injection 방지 테스트"""
    # Given: SQL Injection 시도
    malicious_room_id = "'; DROP TABLE USR_CNVS_SMRY; --"

    # When: POST 요청
    response = await async_client.post(
        "/api/v1/chat/send",
        json={"cnvs_idt_id": malicious_room_id, "message": "test"},
        headers=auth_headers
    )

    # Then: 400 또는 403 (파라미터 바인딩으로 차단)
    assert response.status_code in [400, 403]

    # DB 확인: 테이블이 여전히 존재하는지
    # (테이블이 삭제되지 않았음을 검증)

@pytest.mark.asyncio
async def test_xss_prevention(async_client: AsyncClient, auth_headers):
    """XSS 방지 테스트"""
    # Given: XSS 스크립트 포함 메시지
    xss_message = "<script>alert('XSS')</script>"

    # When: POST 요청
    response = await async_client.post(
        "/api/v1/chat/send",
        json={"cnvs_idt_id": "", "message": xss_message, "stream": False},
        headers=auth_headers
    )

    # Then: HTML 이스케이프 확인
    assert response.status_code == 201
    room_id = response.json()["room_id"]

    # 히스토리 조회
    history_response = await async_client.get(
        f"/api/v1/chat/history/{room_id}",
        headers=auth_headers
    )
    messages = history_response.json()["messages"]
    user_message = next(m for m in messages if m["role"] == "user")

    # 이스케이프된 문자열인지 확인
    assert "&lt;script&gt;" in user_message["content"]
    assert "<script>" not in user_message["content"]

@pytest.mark.asyncio
async def test_path_traversal_prevention(async_client: AsyncClient, auth_headers):
    """Path Traversal 방지 테스트"""
    # Given: Path Traversal 시도
    malicious_room_id = "../../etc/passwd"

    # When: GET 요청
    response = await async_client.get(
        f"/api/v1/chat/history/{malicious_room_id}",
        headers=auth_headers
    )

    # Then: 400 또는 403
    assert response.status_code in [400, 403]

@pytest.mark.asyncio
async def test_rate_limiting(async_client: AsyncClient, auth_headers):
    """Rate Limiting 테스트"""
    # Given: 1분당 10회 제한

    # When: 11번 요청
    responses = []
    for i in range(11):
        response = await async_client.post(
            "/api/v1/chat/send",
            json={"cnvs_idt_id": "", "message": f"test {i}", "stream": False},
            headers=auth_headers
        )
        responses.append(response)

    # Then: 처음 10개는 성공, 11번째는 429 Too Many Requests
    assert all(r.status_code in [200, 201] for r in responses[:10])
    assert responses[10].status_code == 429

@pytest.mark.asyncio
async def test_unauthorized_access(async_client: AsyncClient):
    """인증 없는 접근 차단 테스트"""
    # Given: 인증 헤더 없음

    # When: POST 요청
    response = await async_client.post(
        "/api/v1/chat/send",
        json={"cnvs_idt_id": "", "message": "test"}
    )

    # Then: 401 Unauthorized
    assert response.status_code == 401
```

### pytest 설정

```python
# conftest.py
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base

# 테스트 DB 연결
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"

@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프 fixture"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def async_db_session():
    """비동기 DB 세션 fixture"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest.fixture
async def async_client():
    """비동기 HTTP 클라이언트 fixture"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def auth_headers():
    """인증 헤더 fixture"""
    # 테스트용 JWT 토큰 생성
    token = create_test_jwt_token(user_id="user123", department="D001")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def existing_room_id(async_db_session):
    """기존 roomId fixture"""
    room_id = "user123_20251022104412345678"

    await async_db_session.execute(
        """
        INSERT INTO USR_CNVS_SMRY (CNVS_IDT_ID, USR_ID, CNVS_SMRY_TXT)
        VALUES (:room_id, 'user123', '테스트 대화')
        """,
        {"room_id": room_id}
    )
    await async_db_session.commit()

    return room_id

@pytest.fixture
async def other_users_room_id(async_db_session):
    """다른 사용자의 roomId fixture"""
    room_id = "user456_20251022120000123456"

    await async_db_session.execute(
        """
        INSERT INTO USR_CNVS_SMRY (CNVS_IDT_ID, USR_ID, CNVS_SMRY_TXT)
        VALUES (:room_id, 'user456', '다른 사용자 대화')
        """,
        {"room_id": room_id}
    )
    await async_db_session.commit()

    return room_id
```

### 커버리지 목표

```bash
# pytest-cov 실행
pytest --cov=app --cov-report=html --cov-report=term-missing

# 목표:
# - Unit Tests: 60%+ 커버리지
# - Integration Tests: 80%+ 커버리지
# - E2E Tests: 주요 시나리오 100% 커버
```

---

## 📚 참고 자료

### 실제 코드 분석 결과

1. **MyBatis Mapper 파일:**
   - `QuerySaveMapper.xml` - 질의 저장 및 CNVS_IDT_ID 생성
   - `AnswerSaveMapper.xml` - 답변 저장 및 참조 문서
   - `ConversationHistoryMapper.xml` - 대화 목록 및 상세
   - `ConversationNameUpdateMapper.xml` - 대화명 변경
   - `ChatMapper.xml` - 채팅 메시지 (chat_messages 테이블)

2. **Controller 파일:**
   - `ChatController.java` - 채팅 메시지 처리 (SSE)
   - `ConversationHistoryController.java` - 히스토리 조회
   - `ConversationNameUpdateController.java` - 대화명 변경

3. **프론트엔드 파일:**
   - `roomIdStore.js` - Room ID 상태 관리 (Zustand)
   - `messageStore.js` - 메시지 상태 관리
   - `ChatHistory.jsx` - 이전 대화 목록
   - `chat.js` - API 클라이언트
   - `history.js` - 히스토리 API 클라이언트

### 주요 차이점 요약

| 항목 | 잘못된 가정 (곽두일 PM) | 실제 코드 |
|------|------------------------|----------|
| **DB 테이블** | `rooms` | `USR_CNVS_SMRY` |
| **Room ID 생성** | UUID | `user_id + timestamp + microseconds` |
| **API 경로** | `/exGenBotDS/chat` | `/api/chat/conversation` |
| **응답 형식** | JSON | SSE (text/event-stream) |
| **Context Path** | `/exGenBotDS` | 없음 (직접 /api/*) |
| **히스토리 API** | GET `/api/chat/history/` | POST `/api/chat/history/list` |
| **세션 저장** | HTTP 세션 사용 | Stateless (DB 검증) |

---

## ✅ 체크리스트

### 개발 완료 체크
- [ ] Room ID 생성 로직 구현 (user_id + timestamp + microseconds)
- [ ] Room ID 검증 로직 구현 (DB 기반, Stateless)
- [ ] SSE 스트리밍 응답 처리
- [ ] USR_CNVS_SMRY, USR_CNVS 등 실제 테이블 사용
- [ ] 참조 문서 저장 (USR_CNVS_REF_DOC_LST)
- [ ] 추가 질의 저장 (USR_CNVS_ADD_QUES_LST)
- [ ] 파일 업로드 (USR_UPLD_DOC_MNG)
- [ ] 대화명 변경 (REP_CNVS_NM)
- [ ] 소프트 삭제 (USE_YN = 'N')

### 보안 체크
- [ ] SQL Injection 방지 (파라미터 바인딩)
- [ ] XSS 방지 (HTML 이스케이프)
- [ ] Path Traversal 방지
- [ ] 인증/권한 검증
- [ ] Rate Limiting
- [ ] CORS 설정
- [ ] 정보 노출 방지 (에러 메시지)

### 테스트 체크
- [ ] Unit Tests (60%+)
- [ ] Integration Tests (80%+)
- [ ] E2E Tests (주요 시나리오)
- [ ] Security Tests (OWASP Top 10)

### 문서 체크
- [ ] API 문서 (Swagger)
- [ ] 배포 가이드
- [ ] 데이터베이스 스키마 문서
- [ ] 보안 체크리스트

---

## 📞 연락처

- **프로젝트 매니저**: 곽두일 PM
- **개발팀**: AI Streams Development Team
- **긴급 연락**: [연락처]

---

**마지막 업데이트**: 2025-10-22 (실제 코드 분석 기반 전면 개정)
# MIGRATION_PRD 추가 섹션 (실제 코드 분석 기반)

## 🔐 인증 시스템 통합 (실제 구현 기반)

### 현재 상태 (AS-IS)

**Spring Boot 인증:**
```java
// SecurityConfig.java:30-36
.sessionManagement(session -> session
    .sessionCreationPolicy(SessionCreationPolicy.ALWAYS)
    .maximumSessions(1)
    .maxSessionsPreventsLogin(false)
)

// application.yml:97
ds.ssoUse: false  # SSO는 아직 미구현
```

**주요 특징:**
- HTTP 세션 기반 인증 (Spring Session)
- DreamSecurity SSO 미구현 (주석에 "담에 SSO 할 때" 표시)
- 세션 만료 시 `/api/auth/login` 리다이렉트
- **사용자 답변**: 백엔드에서만 가능, 기존 사용자는 로그인 없이 마이그레이션 불가

### FastAPI 마이그레이션 전략 (TO-BE)

#### 방안 1: HTTP 세션 유지 (단기 - 빠른 마이그레이션)

**장점:**
- 기존 사용자 영향 최소화 (세션 공유 가능)
- 로그인 시스템 변경 불필요
- 빠른 배포 가능 (1-2주)

**단점:**
- Stateful 서버 (수평 확장 제한)
- Redis 세션 스토어 필요
- 세션 동기화 복잡도

**구현 예시:**
```python
# app/core/session.py
from fastapi import Cookie, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
import redis.asyncio as redis
import json

# Redis 세션 스토어
redis_client = redis.from_url("redis://localhost:6379")

async def get_current_user_from_session(
    session_id: str = Cookie(None, alias="JSESSIONID"),
    db: AsyncSession = Depends(get_db)
):
    """HTTP 세션에서 사용자 정보 조회"""
    if not session_id:
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다")

    # Redis에서 세션 조회
    user_data = await redis_client.get(f"session:{session_id}")
    if not user_data:
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다")

    user_info = json.loads(user_data)
    return user_info

# app/routers/chat/chat.py
@router.post("/api/v1/chat/send")
async def send_chat_message(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user_from_session)
):
    """HTTP 세션 기반 인증"""
    user_id = current_user["usr_id"]
    department = current_user["dept_cd"]
    # ... 처리
```

#### 방안 2: JWT 토큰 (중기 - 권장)

**장점:**
- Stateless 서버 (수평 확장 가능)
- 마이크로서비스 친화적
- Redis 불필요

**단점:**
- 기존 사용자 재로그인 필요
- 로그인 시스템 수정 필요

**구현 예시:**
```python
# app/core/security.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = "your-secret-key-change-this"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8시간

security = HTTPBearer()

def create_access_token(user_info: dict) -> str:
    """JWT 토큰 생성"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": user_info["usr_id"],
        "dept": user_info["dept_cd"],
        "name": user_info["usr_nm"],
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """JWT 토큰 검증"""
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰")

        return {
            "user_id": user_id,
            "department": payload.get("dept"),
            "name": payload.get("name")
        }

    except JWTError:
        raise HTTPException(status_code=401, detail="토큰 검증 실패")

# app/routers/auth/login.py
@router.post("/api/v1/auth/login")
async def login(
    username: str,
    password: str,
    db: AsyncSession = Depends(get_db)
):
    """로그인 (JWT 발급)"""
    # 사용자 인증 (DB 조회)
    user = await authenticate_user(db, username, password)

    if not user:
        raise HTTPException(status_code=401, detail="인증 실패")

    # JWT 토큰 생성
    access_token = create_access_token({
        "usr_id": user.usr_id,
        "dept_cd": user.dept_cd,
        "usr_nm": user.usr_nm
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": {
            "user_id": user.usr_id,
            "name": user.usr_nm,
            "department": user.dept_cd
        }
    }
```

**프론트엔드 변경 (React):**
```javascript
// src/api/auth.js
export const login = async (username, password) => {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });

  const data = await response.json();

  // 토큰 저장 (localStorage)
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('user_info', JSON.stringify(data.user_info));

  return data;
};

// src/api/chat.js
const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };
};

export const sendChatMessage = async (message, roomId) => {
  const response = await fetch('/api/v1/chat/send', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      cnvs_idt_id: roomId,
      message: message
    })
  });

  return response;
};
```

#### 권장: 단계별 마이그레이션

**Week 1-2: HTTP 세션 유지**
- 빠른 배포 및 검증
- Redis 세션 스토어 구성

**Week 3-4: JWT 전환 준비**
- 로그인 API 개발 (`/api/v1/auth/login`)
- 프론트엔드 토큰 관리 코드 추가
- 병렬 운영 (세션 + JWT 모두 지원)

**Week 5: 완전 전환**
- HTTP 세션 제거
- JWT만 사용

---

## 🤖 AI 서비스 연동 (vLLM + RAG)

### 실제 환경 분석

**ex-gpt AI 서버 (사용자 답변):**
```yaml
# ex-gpt/template.env
CHAT_MODEL_ENDPOINT=http://vllm:8000/v1
EMBEDDING_MODEL_ENDPOINT=http://vllm-embeddings:8000/v1
RERANK_MODEL_ENDPOINT=http://vllm-rerank:8000/v1

# 모델 선택
DEFAULT_MODEL=Qwen/Qwen2.5-32B-Instruct  # 외부망
# 내부망: Qwen/Qwen3-235B-A22B-AWQ
```

**Spring Boot AI 호출 방식:**
```java
// ChatController.java:109
String targetUrl = aiServerUrl + "/v1/chat/";  // http://localhost:8083/v1/chat/

// POST 요청 (SSE 스트리밍)
HttpPost post = new HttpPost(targetUrl);
post.setHeader("Content-Type", "application/json");
post.setHeader("X-API-Key", apiKey);

// 요청 본문
{
  "user_id": "user123",
  "department": "D001",
  "authorization": "Bearer <api-key>",
  "stream": true,
  "message": "질문 내용",
  "history": [],
  "search_documents": true,
  "max_context_tokens": 4000,
  "temperature": 0.7
}
```

**기존 admin-api AI 호출 방식 (chat_proxy.py 참고):**
```python
# app/routers/chat_proxy.py:141
async with client.stream(
    "POST",
    f"{LLM_API_URL}/v1/chat/completions",  # vLLM OpenAI-compatible API
    json=llm_payload,
    headers={"Content-Type": "application/json"}
) as response:
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            data_str = line[6:].strip()
            if data_str == "[DONE]":
                break

            data = json.loads(data_str)
            token = data["choices"][0]["delta"]["content"]
            yield f"data: {json.dumps({'content': token})}\n\n"
```

### FastAPI 구현 (TO-BE)

#### AI 서비스 클래스 (완전한 구현)

```python
# app/services/ai_service.py
import httpx
import json
from typing import AsyncGenerator, List, Dict, Any, Optional
from app.core.config import settings

class AIService:
    """vLLM OpenAI-compatible API 연동"""

    def __init__(self):
        self.llm_url = settings.LLM_API_URL  # http://localhost:8000/v1
        self.model = settings.LLM_MODEL  # Qwen/Qwen2.5-32B-Instruct
        self.embedding_url = settings.EMBEDDING_MODEL_ENDPOINT

    async def stream_chat(
        self,
        message: str,
        history: List[Dict[str, str]] = None,
        search_documents: bool = False,
        department: Optional[str] = None,
        search_scope: Optional[List[str]] = None,
        max_context_tokens: int = 4000,
        temperature: float = 0.7,
        think_mode: bool = False
    ) -> AsyncGenerator[str, None]:
        """AI 채팅 스트리밍 (vLLM OpenAI-compatible)"""

        # RAG: 문서 검색 (Qdrant)
        search_results = []
        if search_documents:
            search_results = await self._search_documents(
                message,
                department=department,
                search_scope=search_scope,
                max_results=5
            )

        # 컨텍스트 생성
        messages = self._build_messages(message, history, search_results)

        # vLLM 요청 페이로드
        llm_payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "max_tokens": 2000,
            "temperature": temperature
        }

        # Think Mode 활성화
        if think_mode:
            llm_payload["extra_body"] = {
                "enable_thinking": True,
                "thinking_budget": 2000
            }

        # 스트리밍 호출
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.llm_url}/chat/completions",
                json=llm_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status_code != 200:
                    error_msg = f"AI 서버 오류: {response.status_code}"
                    yield json.dumps({"error": error_msg})
                    return

                # SSE 파싱 및 전달
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                token = delta.get("content", "")

                                if token:
                                    yield token
                        except json.JSONDecodeError:
                            pass

    async def _search_documents(
        self,
        query: str,
        department: Optional[str] = None,
        search_scope: Optional[List[str]] = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Qdrant 벡터 검색 (RAG)"""
        from qdrant_client import QdrantClient
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        # Qdrant 클라이언트
        client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            api_key=settings.QDRANT_API_KEY
        )

        # 쿼리 임베딩 생성
        query_vector = await self._get_embedding(query)

        # 필터 구성
        query_filter = None
        if department or search_scope:
            conditions = []

            if department:
                conditions.append(
                    FieldCondition(key="department", match=MatchValue(value=department))
                )

            if search_scope:
                conditions.append(
                    FieldCondition(key="category", match=MatchValue(any=search_scope))
                )

            if conditions:
                query_filter = Filter(must=conditions)

        # 벡터 검색
        search_results = client.search(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=max_results
        )

        # 결과 변환
        results = []
        for hit in search_results:
            results.append({
                "document_id": hit.payload.get("document_id"),
                "chunk_text": hit.payload.get("chunk_text"),
                "score": hit.score,
                "metadata": {
                    "title": hit.payload.get("title"),
                    "category": hit.payload.get("category"),
                    "department": hit.payload.get("department")
                }
            })

        return results

    async def _get_embedding(self, text: str) -> List[float]:
        """텍스트 임베딩 생성 (vLLM embeddings API)"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.embedding_url}/embeddings",
                json={
                    "model": "default-embeddings",
                    "input": text
                }
            )

            data = response.json()
            return data["data"][0]["embedding"]

    def _build_messages(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]],
        search_results: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """LLM 프롬프트 생성 (RAG 컨텍스트 포함)"""
        messages = []

        # 시스템 프롬프트
        system_prompt = "당신은 AI Streams의 전문적인 AI 어시스턴트입니다."

        # RAG 컨텍스트 추가
        if search_results:
            context = "\n\n참조 문서:\n"
            for idx, doc in enumerate(search_results, 1):
                context += f"\n[문서 {idx}] {doc['metadata']['title']}\n{doc['chunk_text'][:500]}...\n"

            system_prompt += f"\n\n{context}\n\n위 참조 문서를 바탕으로 답변해주세요."

        messages.append({"role": "system", "content": system_prompt})

        # 대화 이력
        if history:
            messages.extend(history)

        # 현재 질문
        messages.append({"role": "user", "content": message})

        return messages


# Singleton
ai_service = AIService()
```

#### 환경 변수 설정

```python
# app/core/config.py
class Settings(BaseSettings):
    # AI Service (vLLM)
    LLM_API_URL: str = "http://localhost:8000/v1"
    LLM_MODEL: str = "Qwen/Qwen2.5-32B-Instruct"
    EMBEDDING_MODEL_ENDPOINT: str = "http://localhost:8001/v1"
    RERANK_MODEL_ENDPOINT: str = "http://localhost:8002/v1"

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6335
    QDRANT_COLLECTION: str = "130825-512-v3"
    QDRANT_API_KEY: str = "QFy9YlRTm0Y1yo6D"
```

```.env
# .env
LLM_API_URL=http://host.docker.internal:8000/v1
LLM_MODEL=Qwen/Qwen2.5-32B-Instruct
EMBEDDING_MODEL_ENDPOINT=http://host.docker.internal:8001/v1
QDRANT_HOST=localhost
QDRANT_PORT=6335
QDRANT_COLLECTION=130825-512-v3
QDRANT_API_KEY=QFy9YlRTm0Y1yo6D
```

---

## 📁 MinIO 파일 업로드 (실제 구현 기반)

### 기존 구현 분석

**admin-api/app/services/minio_service.py (이미 구현됨):**
```python
class MinIOService:
    """MinIO 파일 업로드 서비스"""

    def upload_file(
        self,
        file_obj: BinaryIO,
        filename: str,
        content_type: str = "application/octet-stream"
    ) -> Tuple[str, int]:
        """
        파일 업로드
        - Path Traversal 방지
        - 파일 크기 제한 (100MB)
        - UUID 기반 고유 경로 생성
        """
        safe_filename = self._sanitize_filename(filename)
        file_extension = os.path.splitext(safe_filename)[1]
        unique_id = str(uuid.uuid4())
        object_name = f"documents/{unique_id}{file_extension}"

        # Upload to MinIO
        self.client.put_object(
            self.bucket,
            object_name,
            file_obj,
            length=file_size,
            content_type=content_type
        )

        return object_name, file_size
```

### FastAPI 채팅 파일 업로드 구현

```python
# app/routers/chat/files.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from app.services.minio_service import minio_service
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/api/v1/files/upload")
async def upload_chat_file(
    file: UploadFile = File(...),
    room_id: str = Form(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    채팅 파일 업로드 (MinIO + DB)

    Security:
    - 파일 타입 검증 (허용: PDF, DOCX, XLSX, TXT, PNG, JPG)
    - 파일 크기 제한 (100MB)
    - Path Traversal 방지
    - 바이러스 스캔 (TODO)
    """
    # 1. 권한 검증: room_id가 사용자 소유인지 확인
    is_valid = await validate_room_id(room_id, current_user["user_id"], db)
    if not is_valid:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    # 2. 파일 타입 검증
    ALLOWED_EXTENSIONS = {
        '.pdf', '.docx', '.xlsx', '.txt',
        '.png', '.jpg', '.jpeg'
    }
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"허용되지 않은 파일 형식입니다: {file_ext}"
        )

    # 3. 파일 크기 확인
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > 100 * 1024 * 1024:  # 100MB
        raise HTTPException(
            status_code=400,
            detail="파일 크기가 100MB를 초과합니다."
        )

    # 4. MinIO 업로드
    try:
        object_name, uploaded_size = minio_service.upload_file(
            file.file,
            file.filename,
            file.content_type
        )
    except Exception as e:
        logger.error(f"MinIO upload error: {e}")
        raise HTTPException(
            status_code=500,
            detail="파일 업로드 실패"
        )

    # 5. DB에 메타데이터 저장 (USR_UPLD_DOC_MNG)
    file_uid = object_name  # "documents/uuid.pdf"
    file_download_url = minio_service.get_file_url(object_name)

    await db.execute(
        """
        INSERT INTO USR_UPLD_DOC_MNG (
            CNVS_IDT_ID, FILE_NM, FILE_UID, FILE_DOWN_URL,
            FILE_SIZE, FILE_TYP_CD, USR_ID, REG_DT
        ) VALUES (
            :room_id, :filename, :file_uid, :file_url,
            :file_size, :file_type, :user_id, CURRENT_TIMESTAMP
        )
        """,
        {
            "room_id": room_id,
            "filename": file.filename,
            "file_uid": file_uid,
            "file_url": file_download_url,
            "file_size": uploaded_size,
            "file_type": file_ext[1:],  # ".pdf" -> "pdf"
            "user_id": current_user["user_id"]
        }
    )
    await db.commit()

    # 6. 벡터화 트리거 (백그라운드 작업)
    from app.tasks.vectorization import trigger_vectorization
    await trigger_vectorization(file_uid, room_id)

    return {
        "success": True,
        "file_uid": file_uid,
        "filename": file.filename,
        "size": uploaded_size,
        "download_url": file_download_url
    }
```

**벡터화 트리거 (백그라운드 작업):**
```python
# app/tasks/vectorization.py
import asyncio
import httpx
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

async def trigger_vectorization(file_uid: str, room_id: str):
    """
    문서 벡터화 트리거 (비동기)

    1. MinIO에서 파일 다운로드
    2. 텍스트 추출 (PDF, DOCX 등)
    3. 청킹 (512 tokens per chunk)
    4. 임베딩 생성 (vLLM embeddings API)
    5. Qdrant 업로드
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.ADMIN_API_URL}/api/v1/admin/documents/upload",
                json={
                    "file_uid": file_uid,
                    "room_id": room_id
                },
                timeout=300.0
            )

            if response.status_code == 200:
                logger.info(f"Vectorization triggered: {file_uid}")
            else:
                logger.error(f"Vectorization failed: {response.text}")

    except Exception as e:
        logger.error(f"Vectorization trigger error: {e}")
```

---

## 📊 모니터링 및 로깅 전략

### 현재 상태 (AS-IS)

**Spring Boot 로깅:**
```yaml
# application.yml:66-75
logging:
  level:
    root: DEBUG
    com.datastreams.gpt: DEBUG
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n"
  file:
    name: logs/dsgpt.log
```

**admin-api 로깅:**
- 기본 로깅만 있음 (구조화된 로깅 없음)
- Prometheus metrics 없음

### FastAPI 모니터링 구현 (TO-BE)

#### 1. 구조화된 로깅 (JSON 포맷)

```python
# app/core/logging_config.py
import logging
import sys
from pythonjsonlogger import jsonlogger
from datetime import datetime
from app.core.config import settings

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """구조화된 JSON 로깅"""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        # 타임스탬프
        log_record['timestamp'] = datetime.utcnow().isoformat()

        # 로그 레벨
        log_record['level'] = record.levelname

        # 서비스 정보
        log_record['service'] = 'admin-api'
        log_record['environment'] = settings.ENVIRONMENT

        # 요청 정보 (컨텍스트에서 가져오기)
        from contextvars import ContextVar
        request_context: ContextVar = ContextVar('request_context', default={})
        context = request_context.get()

        if context:
            log_record['user_id'] = context.get('user_id')
            log_record['request_id'] = context.get('request_id')
            log_record['endpoint'] = context.get('endpoint')

def setup_logging():
    """로깅 설정"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # JSON 포맷 핸들러
    handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
```

#### 2. Request ID 미들웨어

```python
# app/middleware/logging.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import logging
from contextvars import ContextVar

request_context = ContextVar('request_context', default={})
logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """요청 로깅 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        # Request ID 생성
        request_id = str(uuid.uuid4())

        # 컨텍스트 설정
        context = {
            'request_id': request_id,
            'endpoint': f"{request.method} {request.url.path}",
            'user_id': None
        }
        request_context.set(context)

        # 요청 로깅
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host
            }
        )

        # 요청 처리
        response = await call_next(request)

        # 응답 로깅
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code
            }
        )

        # Response Header에 Request ID 추가
        response.headers["X-Request-ID"] = request_id

        return response
```

#### 3. Health Check API

```python
# app/routers/health.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.minio_service import minio_service
from app.core.config import settings
from qdrant_client import QdrantClient
import httpx

router = APIRouter()

@router.get("/health")
async def health_check():
    """기본 헬스 체크"""
    return {
        "status": "healthy",
        "service": "admin-api",
        "version": "0.1.0"
    }

@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """상세 헬스 체크 (DB, MinIO, Qdrant, vLLM)"""
    health = {
        "status": "healthy",
        "checks": {}
    }

    # 1. PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
        health["checks"]["database"] = {"status": "up"}
    except Exception as e:
        health["status"] = "degraded"
        health["checks"]["database"] = {"status": "down", "error": str(e)}

    # 2. MinIO
    try:
        minio_service.client.bucket_exists(minio_service.bucket)
        health["checks"]["minio"] = {"status": "up"}
    except Exception as e:
        health["status"] = "degraded"
        health["checks"]["minio"] = {"status": "down", "error": str(e)}

    # 3. Qdrant
    try:
        client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        client.get_collection(settings.QDRANT_COLLECTION)
        health["checks"]["qdrant"] = {"status": "up"}
    except Exception as e:
        health["status"] = "degraded"
        health["checks"]["qdrant"] = {"status": "down", "error": str(e)}

    # 4. vLLM
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.LLM_API_URL}/models", timeout=5)
            if response.status_code == 200:
                health["checks"]["vllm"] = {"status": "up"}
            else:
                raise Exception(f"Status {response.status_code}")
    except Exception as e:
        health["status"] = "degraded"
        health["checks"]["vllm"] = {"status": "down", "error": str(e)}

    return health
```

#### 4. 환경 변수 설정

```python
# app/core/config.py
class Settings(BaseSettings):
    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    ENVIRONMENT: str = "production"  # dev, staging, production
```

```.env
LOG_LEVEL=INFO
ENVIRONMENT=production
```

---

## 🔄 배포 전략 (사용자 답변 기반)

### 사용자 답변 정리

- **layout.html 유지 불필요**: 새 버전에서 모든 기능이 작동하면 됨
- **롤백 계획 없음**: 실패 시 그냥 실패 (재배포)
- **데이터 마이그레이션 없음**: 실패 시 그냥 실패

### 단일 배포 전략

**목표:**
- 새 버전에서 모든 기능 작동
- 기존 시스템 제거
- 빠른 배포 (롤백 없이)

#### Docker Compose 구성

```yaml
# docker-compose.yml
version: '3.8'

services:
  admin-api:
    build: .
    container_name: admin-api
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/admin_db
      - LLM_API_URL=http://vllm:8000/v1
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
      - MINIO_ENDPOINT=minio:9000
    depends_on:
      - postgres
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: admin_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

#### 배포 스크립트

```bash
#!/bin/bash
# deploy.sh

set -e

echo "🚀 Deploying admin-api (New Version)"

# 1. 코드 최신화
echo "📥 Pulling latest code..."
git pull origin main

# 2. 의존성 설치
echo "📦 Installing dependencies..."
poetry install --no-dev

# 3. 데이터베이스 마이그레이션
echo "🗄️ Running database migrations..."
alembic upgrade head

# 4. 프론트엔드 빌드
echo "🔨 Building frontend..."
cd frontend
npm install
npm run build
cd ..

# 5. Docker 이미지 빌드
echo "🐳 Building Docker image..."
docker compose build

# 6. 기존 컨테이너 중지
echo "⏸️ Stopping old containers..."
docker compose down

# 7. 새 컨테이너 시작
echo "▶️ Starting new containers..."
docker compose up -d

# 8. 헬스 체크
echo "🏥 Running health check..."
sleep 10
curl -f http://localhost:8001/health || exit 1

echo "✅ Deployment successful!"
```

---

**마지막 업데이트**: 2025-10-22 (실제 코드 분석 + 사용자 답변 기반 상세 구현 가이드)
