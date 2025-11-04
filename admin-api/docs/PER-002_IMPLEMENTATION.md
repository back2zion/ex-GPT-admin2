# PER-002 구현 문서

## 개요

RFP PER-002 요구사항을 L4 하드웨어 없이 소프트웨어 기반으로 구현한 세션 및 대기열 관리 시스템입니다.

## 요구사항

- **동시 처리 제한**: 최대 10개의 질의를 동시 처리
- **세션 제한**: 최대 20개의 활성 세션 유지
- **대기열 관리**: 20개 초과 시 FIFO 대기열로 관리
- **자동 승격**: 세션 종료 시 대기열의 다음 사용자 자동 활성화

## 아키텍처

### 1. Backend (FastAPI + Redis)

#### 1.1 서비스 레이어
**파일**: `/home/aigen/admin-api/app/services/session_queue_service.py`

- **SessionQueueService**: 핵심 세션 관리 서비스
  - Redis를 사용한 분산 세션 상태 관리
  - asyncio.Semaphore로 동시 요청 제한 (10개)
  - 30분 세션 타임아웃

**주요 기능**:
```python
- create_session(user_id, session_id)  # 세션 생성 또는 대기열 추가
- close_session(user_id)                # 세션 종료 및 대기열 처리
- get_queue_status()                    # 전체 상태 조회
- get_user_queue_position(user_id)      # 사용자 위치 확인
- cleanup_expired_sessions()            # 만료 세션 정리
- process_request_with_limit()          # Semaphore 기반 요청 처리
```

**Redis 키 구조**:
- `ex_gpt:active_sessions`: Hash - 활성 세션 목록
- `ex_gpt:session_queue`: List - FIFO 대기열
- `ex_gpt:session:{session_id}`: String - 개별 세션 데이터 (TTL 30분)

#### 1.2 API 레이어
**파일**: `/home/aigen/admin-api/app/routers/session_queue.py`

**엔드포인트**:
```
POST   /api/v1/session/create           # 세션 생성
DELETE /api/v1/session/close/{user_id}  # 세션 종료
GET    /api/v1/session/status            # 대기열 상태
GET    /api/v1/session/position/{user_id} # 사용자 위치
POST   /api/v1/session/cleanup           # 만료 세션 정리
```

### 2. Frontend (JavaScript + CSS)

#### 2.1 세션 관리 클라이언트
**파일**: `/var/www/html/js/session-queue.js`

- **SessionQueueManager**: 클라이언트 측 세션 관리
  - 자동 대기열 상태 폴링 (5초 간격)
  - 실시간 알림 표시
  - 페이지 종료 시 자동 세션 정리

**주요 메서드**:
```javascript
- createSession(userId, sessionId)     // 세션 생성 요청
- closeSession()                        // 세션 종료
- checkPosition()                       // 대기열 위치 폴링
- showQueueNotification(status)         // 대기 알림 표시
- showActivatedNotification()           // 활성화 알림
```

#### 2.2 UI 스타일
**파일**: `/var/www/html/styles/session-queue.css`

- 우측 상단 슬라이드 알림
- 다크모드 지원
- 모바일 반응형
- 접근성 개선 (prefers-reduced-motion)

#### 2.3 통합
**파일**: `/var/www/html/layout.html`

```javascript
// 페이지 로드 시 세션 초기화
initializeSessionWithQueue()

// 대화 초기화 시 세션 생성
async function resetConversation() {
    const sessionCreated = await initializeSessionWithQueue();
    if (!sessionCreated) {
        // 대기열 진입 처리
    }
}
```

## 설치 및 설정

### 1. 의존성

```bash
# Redis (이미 실행 중)
docker ps | grep redis

# Admin API 재시작
docker restart admin-api-admin-api-1
```

### 2. 환경 변수

`.env` 파일:
```bash
REDIS_URL=redis://localhost:6379
```

### 3. 파일 구조

```
/home/aigen/admin-api/
├── app/
│   ├── services/
│   │   └── session_queue_service.py   # 세션 관리 서비스
│   └── routers/
│       └── session_queue.py            # API 엔드포인트
│
/var/www/html/
├── js/
│   └── session-queue.js                # 클라이언트 라이브러리
├── styles/
│   └── session-queue.css               # UI 스타일
└── layout.html                         # 메인 페이지 (통합됨)
```

## 테스트

### 기본 테스트

```bash
# 대기열 상태 확인
curl http://localhost:8010/api/v1/session/status

# 세션 생성
curl -X POST http://localhost:8010/api/v1/session/create \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "session_id": "test_session"}'

# 세션 종료
curl -X DELETE http://localhost:8010/api/v1/session/close/test_user
```

### 통합 테스트

```bash
# 전체 시스템 테스트
/tmp/test-per002.sh

# 대기열 진입 테스트
/tmp/test-queue-entry.sh
```

### 테스트 결과

✅ **성공적으로 검증된 기능**:
1. 20개 세션 제한 (MAX_ACTIVE_SESSIONS)
2. 21번째 세션부터 대기열 진입
3. 세션 종료 시 자동 대기열 승격
4. 실시간 위치 추적
5. FIFO 순서 보장

## 사용 예시

### JavaScript (클라이언트)

```javascript
// 세션 생성
const userId = 'user123';
const sessionId = generateSessionId();
const result = await sessionQueueManager.createSession(userId, sessionId);

if (result.status === 'active') {
    console.log('세션 활성화');
} else if (result.status === 'queued') {
    console.log(`대기 순번: ${result.position}`);
}

// 세션 종료
await sessionQueueManager.closeSession();
```

### Python (백엔드 통합)

```python
# 채팅 요청 처리 시
async def process_chat_request(user_id: str, message: str):
    queue_service = await get_session_queue_service()

    # Semaphore로 동시 처리 제한
    async def _process():
        # 실제 채팅 로직
        return await generate_response(message)

    return await queue_service.process_request_with_limit(
        user_id,
        _process
    )
```

## 모니터링

### Redis 상태 확인

```bash
# 활성 세션 수
redis-cli HLEN ex_gpt:active_sessions

# 대기열 길이
redis-cli LLEN ex_gpt:session_queue

# 특정 세션 조회
redis-cli HGET ex_gpt:active_sessions user123
```

### API 로그

```bash
docker logs -f admin-api-admin-api-1 | grep SessionQueue
```

## 성능 특성

- **동시 요청 처리**: 10개 (asyncio.Semaphore)
- **세션 제한**: 20개 (Redis Hash)
- **세션 타임아웃**: 30분 (자동 정리)
- **대기열 폴링**: 5초 간격 (클라이언트)
- **Redis 메모리**: ~1KB per session

## 보안 고려사항

1. **세션 ID**: UUID v4 사용 권장
2. **User ID**: 인증된 사용자만 세션 생성
3. **Rate Limiting**: 추가 구현 권장 (per-user)
4. **Redis 인증**: 프로덕션 환경에서 비밀번호 설정 필요

## 향후 개선 사항

1. **WebSocket 지원**: 실시간 대기열 업데이트
2. **Priority Queue**: VIP 사용자 우선 처리
3. **분산 환경**: Redis Cluster 지원
4. **메트릭 수집**: Prometheus + Grafana 연동
5. **Alert 시스템**: 대기열 길이 임계값 알림

## 문제 해결

### 세션이 생성되지 않음

```bash
# Redis 연결 확인
docker ps | grep redis

# API 로그 확인
docker logs admin-api-admin-api-1 | tail -50
```

### 대기열이 처리되지 않음

```python
# 수동 대기열 처리
curl -X POST http://localhost:8010/api/v1/session/cleanup
```

### Redis 메모리 부족

```bash
# 만료된 세션 정리
redis-cli FLUSHDB  # 주의: 개발 환경에서만 사용
```

## 관련 문서

- **RFP**: `/home/aigen/admin-api/docs/RFP.txt` (PER-002)
- **PRD**: `/home/aigen/admin-api/docs/PRD.md`
- **DB Schema**: `/home/aigen/admin-api/docs/DATABASE_SCHEMA.md`

## 변경 이력

- **2025-11-04**: 초기 구현 완료
  - Redis 기반 세션 관리
  - FastAPI API 엔드포인트
  - JavaScript 클라이언트 라이브러리
  - UI 컴포넌트 및 스타일
  - 통합 테스트 통과
