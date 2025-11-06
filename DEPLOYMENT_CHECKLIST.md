# 한국도로공사 내부망 반입 체크리스트

## 📋 문서 개요

이 문서는 외부 개발 환경에서 개발된 **모바일 오피스 STT 사내메일 연동 기능**을 한국도로공사 내부망으로 반입하여 배포하기 위한 체크리스트입니다.

**프로젝트**: ex-GPT 모바일 오피스 STT 통합
**날짜**: 2025-11-06
**작성자**: AI Development Team

---

## 🎯 반입 대상 기능

### 기능 설명
모바일 오피스에서 녹음한 음성을 STT 처리하고, 자동으로 회의록을 생성한 후 사내메일로 발송하는 통합 기능

### 아키텍처
```
모바일 오피스 (음성 녹음)
  ↓ HTTP POST
ex-GPT-STT API (포트 9200)
  ├─ STT 처리 (faster-whisper)
  ├─ 회의록 생성 (Qwen LLM)
  └─ Webhook 호출 ↓
admin-api (포트 8010)
  ├─ PostgreSQL: 채팅 히스토리 저장
  └─ Oracle: 사내메일 발송 (MAIL_DOC, MAIL_INBOX)
```

---

## ✅ Part 1: 사전 준비 (외부 개발 환경에서 완료)

### 1.1 코드 준비
- [x] **InternalMailService** 구현 완료
  - 파일: `admin-api/app/services/internal_mail_service.py`
  - Oracle DB 연결 및 MAIL_DOC/MAIL_INBOX 테이블 INSERT

- [x] **STTChatIntegrationService** 구현 완료
  - 파일: `admin-api/app/services/stt_chat_integration_service.py`
  - PostgreSQL 채팅 히스토리 저장 (USR_CNVS_SMRY, USR_CNVS)

- [x] **Webhook 라우터** 구현 완료
  - 파일: `admin-api/app/routers/webhooks/stt_webhook.py`
  - ex-GPT-STT 완료 알림 수신 및 처리

- [x] **ex-GPT-STT Webhook 호출** 구현 완료
  - 파일: `ex-GPT-STT/src/api/api_server.py`
  - STT 처리 완료 후 admin-api webhook 호출

### 1.2 환경 설정 템플릿
- [x] `.env` 파일 템플릿 준비
  - `MAIL_ORACLE_HOST`, `MAIL_ORACLE_PORT`, `MAIL_ORACLE_USER`, etc.

- [x] `config.py` 업데이트
  - 사내메일용 Oracle 설정 추가

### 1.3 테스트
- [x] **단위 테스트** 작성 및 통과
  - 파일: `tests/test_internal_mail_service.py`
  - 11개 테스트 모두 통과 (Mock 사용)

- [x] **Oracle 연결 테스트 스크립트** 작성
  - 파일: `app/test_oracle_connection.py`
  - 내부망에서 실행 가능

### 1.4 문서화
- [x] **prd_STT.md** 참조 문서 확인
  - Oracle DB 정보, 테이블 구조, 권한 요구사항

- [x] **배포 가이드** 작성
- [x] **체크리스트** 작성 (본 문서)

---

## 📦 Part 2: 반입 파일 목록

### 2.1 소스 코드
```bash
# admin-api 관련
admin-api/app/services/internal_mail_service.py
admin-api/app/services/stt_chat_integration_service.py
admin-api/app/routers/webhooks/__init__.py
admin-api/app/routers/webhooks/stt_webhook.py
admin-api/app/core/config.py
admin-api/app/main.py  # webhook router 등록 추가
admin-api/tests/test_internal_mail_service.py
admin-api/app/test_oracle_connection.py

# ex-GPT-STT 관련
ex-GPT-STT/src/api/api_server.py  # webhook 호출 로직 추가

# 환경 설정
admin-api/.env  # 템플릿 (실제 계정 정보는 내부망에서 입력)
admin-api/pyproject.toml  # oracledb, httpx 의존성 추가
```

### 2.2 문서
```bash
prd_STT.md  # Oracle 사내메일 연동 인터페이스 설계서
DEPLOYMENT_CHECKLIST.md  # 본 문서
DEPLOYMENT_GUIDE.md  # 상세 배포 가이드
```

### 2.3 패키지 (오프라인 설치용)
```bash
# Python 패키지 (pip wheel 파일)
oracledb-3.4.0-*.whl
httpx-0.28.1-*.whl
# + 의존성 패키지들
```

---

## 🔧 Part 3: 내부망 배포 작업

### 3.1 사전 요청 사항

#### ✅ DBA팀 지원 요청
- [ ] **Oracle DB 계정 발급**
  - 계정명 예: `exgpt_user`
  - 용도: 사내메일 연동 (MAIL_DOC, MAIL_INBOX INSERT)

- [ ] **테이블 접근 권한 부여**
  ```sql
  -- MAIL_DOC: 메일 본문 저장
  GRANT INSERT ON EXGWMAIN.MAIL_DOC TO exgpt_user;

  -- MAIL_INBOX: 수신자 정보 저장
  GRANT INSERT ON EXGWMAIN.MAIL_INBOX TO exgpt_user;

  -- PT_USER: 사용자 정보 조회 (필요 시)
  GRANT SELECT ON EXGWMAIN.PT_USER TO exgpt_user;

  -- XFMAIL_SEQ: 메일 번호 생성용 시퀀스
  GRANT SELECT ON EXGWMAIN.XFMAIL_SEQ TO exgpt_user;
  ```

#### ✅ 네트워크팀 지원 요청
- [ ] **방화벽 포트 개방**
  - Source: ex-GPT 서버 (172.16.164.100)
  - Destination: Oracle DB 서버 (172.16.164.32)
  - Port: 1669
  - Protocol: TCP

- [ ] **네트워크 라우팅 확인**
  - ex-GPT 서버 → Oracle DB 서버 통신 가능 여부 확인

### 3.2 환경 설정

#### Step 1: 패키지 설치
```bash
# 1. admin-api 컨테이너에 oracledb 설치
docker exec admin-api-admin-api-1 pip install oracledb

# 2. ex-GPT-STT에 httpx 설치
cd /home/aigen/ex-GPT-STT
source .venv/bin/activate
uv pip install httpx
```

#### Step 2: 환경 변수 설정
```bash
# /home/aigen/admin-api/.env 파일 수정
vi /home/aigen/admin-api/.env

# 다음 항목 추가/수정:
MAIL_ORACLE_HOST=172.16.164.32
MAIL_ORACLE_PORT=1669
MAIL_ORACLE_USER=<DBA팀에서_발급받은_계정>
MAIL_ORACLE_PASSWORD=<DBA팀에서_발급받은_비밀번호>
MAIL_ORACLE_SERVICE=ANKHCG
```

#### Step 3: 컨테이너 재시작
```bash
# admin-api 재시작
cd /home/aigen/admin-api/admin-api
docker compose restart admin-api

# 로그 확인
docker logs -f admin-api-admin-api-1
```

#### Step 4: ex-GPT-STT 재시작
```bash
# ex-GPT-STT 프로세스 재시작
ps aux | grep api_server.py
kill -9 <PID>

cd /home/aigen/ex-GPT-STT
uv run python src/api/api_server.py &
```

### 3.3 연결 테스트

#### Test 1: Oracle DB 연결 테스트
```bash
# Oracle DB 연결 및 권한 확인
docker exec admin-api-admin-api-1 python -m app.test_oracle_connection

# 예상 출력:
# ✅ 연결 성공!
# ✅ EXGWMAIN.MAIL_DOC - 테이블 접근 가능
# ✅ EXGWMAIN.MAIL_INBOX - 테이블 접근 가능
# ✅ EXGWMAIN.XFMAIL_SEQ - 접근 가능
```

#### Test 2: admin-api Health Check
```bash
curl http://localhost:8010/health

# 예상 출력:
# {"status":"healthy","admin_api":null,"database":null}
```

#### Test 3: ex-GPT-STT Health Check
```bash
curl http://localhost:9200/health

# 예상 출력:
# {"status":"healthy"}
```

### 3.4 기능 테스트

#### Test 4: Webhook 엔드포인트 테스트 (수동)
```bash
curl -X POST "http://localhost:8010/api/v1/webhooks/stt-completed" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: exgpt-stt-webhook-secret-key" \
  -d '{
    "task_id": "test-001",
    "status": "completed",
    "success": true,
    "transcription": "테스트 회의 전사 내용입니다.",
    "meeting_minutes": "<html><body><h1>회의록</h1><p>회의 내용...</p></body></html>",
    "duration": 120.5,
    "language": "ko",
    "meeting_title": "테스트 회의",
    "sender_name": "테스트관리자",
    "sender_email": "test@example.com",
    "recipient_emails": ["recipient1@example.com"],
    "department": "테스트부서"
  }'

# 예상 출력:
# {
#   "received": true,
#   "processed": true,
#   "cnvs_idt_id": "stt_xxxx",
#   "cnvs_id": 123,
#   "mail_sent": true,
#   "message": "STT 결과가 채팅 히스토리에 저장되고 사내메일이 발송되었습니다."
# }
```

#### Test 5: E2E 통합 테스트 (모바일 오피스 → STT → 메일)
```bash
# 1. 테스트 음성 파일 업로드 (ex-GPT-STT API)
curl -X POST "http://localhost:9200/api/stt/process" \
  -F "audio=@/path/to/test_audio.wav" \
  -F "meeting_title=통합테스트 회의" \
  -F "sender_name=테스트관리자" \
  -F "recipient_emails=test@example.com"

# 2. STT 처리 완료 대기 (약 1-5분 소요)

# 3. 결과 확인
#   - PostgreSQL: USR_CNVS_SMRY, USR_CNVS 테이블 확인
#   - Oracle: MAIL_DOC, MAIL_INBOX 테이블 확인
#   - 사내메일함에서 메일 수신 확인
```

---

## 🔍 Part 4: 검증 및 모니터링

### 4.1 데이터베이스 확인

#### PostgreSQL (채팅 히스토리)
```sql
-- 최근 STT 히스토리 확인
SELECT cnvs_idt_id, rep_cnvs_nm, cnvs_smry_txt, rgst_dt
FROM usr_cnvs_smry
WHERE cnvs_idt_id LIKE 'stt_%'
ORDER BY rgst_dt DESC
LIMIT 10;

-- 상세 내용 확인
SELECT cnvs_id, ques_txt, ans_txt
FROM usr_cnvs
WHERE cnvs_idt_id = 'stt_xxxx';
```

#### Oracle (사내메일)
```sql
-- 최근 발송 메일 확인
SELECT DOC_YEARMON, DOC_NUMBER, DOC_SUBJECT, DOC_WRITER, DOC_WRITERNAME
FROM EXGWMAIN.MAIL_DOC
WHERE DOC_REQ_SYSTEM = 'ex-GPT System'
ORDER BY DOC_YEARMON DESC, DOC_NUMBER DESC
FETCH FIRST 10 ROWS ONLY;

-- 수신자 확인
SELECT DOC_YEARMON, DOC_NUMBER, RECEIVER, RECV_NAME, SEND_DATE
FROM EXGWMAIN.MAIL_INBOX
WHERE DOC_NUMBER = 12345;  -- 위에서 조회한 DOC_NUMBER
```

### 4.2 로그 모니터링

#### admin-api 로그
```bash
# 실시간 로그 확인
docker logs -f admin-api-admin-api-1 | grep -E "(STT|webhook|mail)"

# 최근 오류 확인
docker logs admin-api-admin-api-1 --tail 100 | grep ERROR
```

#### ex-GPT-STT 로그
```bash
# 로그 파일 확인 (위치는 실제 설정에 따라 다를 수 있음)
tail -f /home/aigen/ex-GPT-STT/logs/api_server.log | grep webhook
```

### 4.3 성능 확인
```bash
# STT 처리 시간 측정
# - 음성 파일 크기별 처리 시간 확인
# - 동시 요청 시 처리 능력 확인

# 사내메일 발송 시간 측정
# - 단일 수신자 vs 다수 수신자 비교
```

---

## 🐛 Part 5: 트러블슈팅

### 5.1 Oracle 연결 문제

**증상**: `DPY-6005: cannot connect to database`
```bash
# 1. 네트워크 연결 확인
timeout 5 bash -c "echo > /dev/tcp/172.16.164.32/1669" && echo "연결 성공" || echo "연결 실패"

# 2. 방화벽 규칙 확인
sudo firewall-cmd --list-all | grep 1669

# 3. Oracle 리스너 상태 확인 (DBA 담당)
# lsnrctl status
```

**증상**: `ORA-01017: invalid username/password`
```bash
# .env 파일 확인
docker exec admin-api-admin-api-1 cat /app/.env | grep MAIL_ORACLE

# 계정 정보 재확인 (DBA팀)
```

**증상**: `ORA-00942: table or view does not exist`
```bash
# 권한 확인 (DBA팀)
# SELECT * FROM USER_TAB_PRIVS WHERE TABLE_NAME IN ('MAIL_DOC', 'MAIL_INBOX');
```

### 5.2 Webhook 호출 실패

**증상**: ex-GPT-STT에서 webhook 호출 시 타임아웃
```bash
# 1. admin-api 상태 확인
curl http://localhost:8010/health

# 2. 방화벽 확인 (ex-GPT-STT → admin-api)
docker exec admin-api-admin-api-1 netstat -tuln | grep 8010

# 3. 로그 확인
docker logs admin-api-admin-api-1 | tail -50
```

**증상**: `403 Forbidden` - API 키 불일치
```bash
# API 키 확인
# ex-GPT-STT: api_server.py의 WEBHOOK_API_KEY
# admin-api: stt_webhook.py의 EXPECTED_API_KEY
# 두 값이 일치해야 함: "exgpt-stt-webhook-secret-key"
```

### 5.3 사내메일 미발송

**증상**: Webhook은 성공했지만 사내메일함에 메일이 없음
```sql
-- Oracle DB에 데이터가 INSERT 되었는지 확인
SELECT * FROM EXGWMAIN.MAIL_DOC
WHERE DOC_REQ_SYSTEM = 'ex-GPT System'
ORDER BY DOC_YEARMON DESC, DOC_NUMBER DESC
FETCH FIRST 1 ROW ONLY;

-- MAIL_INBOX 확인
SELECT * FROM EXGWMAIN.MAIL_INBOX
WHERE DOC_NUMBER = <위에서_조회한_DOC_NUMBER>;
```

**원인 가능성**:
1. Worker 프로세스가 인터페이스 테이블을 읽지 못함 (DBA/전산팀 확인)
2. DOC_TYPE이 'I'가 아님
3. SEND_DONE이 'S'가 아님
4. 수신자 ID가 잘못됨

---

## 📊 Part 6: 성능 및 확장성 고려사항

### 6.1 예상 부하
- 모바일 오피스 사용자 수: 약 XXX명
- 일일 회의 녹음 건수: 약 XXX건
- 평균 음성 파일 크기: XX MB
- 평균 처리 시간: X분

### 6.2 모니터링 지표
- STT 처리 성공률
- Webhook 호출 성공률
- 사내메일 발송 성공률
- 평균 E2E 처리 시간

### 6.3 스케일링 전략
- ex-GPT-STT 인스턴스 증설 (GPU 서버)
- admin-api 컨테이너 복제 (수평 확장)
- Oracle 연결 풀 크기 조정

---

## 📝 Part 7: 최종 체크리스트

### 반입 전 (외부 개발 환경)
- [x] 모든 코드 커밋 및 푸시
- [x] 단위 테스트 통과 (11/11)
- [x] 문서 작성 완료
- [x] 반입 파일 목록 작성
- [ ] 코드 리뷰 완료
- [ ] 보안 검토 완료

### 반입 후 (내부망)
- [ ] DBA팀: Oracle 계정 발급 완료
- [ ] DBA팀: 테이블 권한 부여 완료
- [ ] 네트워크팀: 방화벽 포트 개방 완료
- [ ] 패키지 설치 완료 (oracledb, httpx)
- [ ] 환경 변수 설정 완료 (.env)
- [ ] 컨테이너 재시작 완료
- [ ] Oracle 연결 테스트 통과
- [ ] Webhook 테스트 통과
- [ ] E2E 통합 테스트 통과
- [ ] PostgreSQL 데이터 확인
- [ ] Oracle 데이터 확인
- [ ] 사내메일 수신 확인
- [ ] 로그 모니터링 설정
- [ ] 운영 매뉴얼 인수인계

---

## 📞 지원 연락처

### 기술 문의
- **ex-GPT 개발팀**: [담당자 연락처]
- **DBA팀**: [담당자 연락처]
- **네트워크팀**: [담당자 연락처]

### 긴급 장애 대응
- **1차**: ex-GPT 개발팀
- **2차**: 전산팀
- **에스컬레이션**: PM

---

## 📚 참고 문서

1. `prd_STT.md` - 전자문서시스템 사내메일 연동 인터페이스 설계서
2. `DEPLOYMENT_GUIDE.md` - 상세 배포 가이드
3. `DATABASE_SCHEMA.md` - 데이터베이스 스키마 문서
4. `API_SPECIFICATION.md` - API 명세서

---

**문서 버전**: 1.0
**최종 수정일**: 2025-11-06
**작성자**: AI Development Team
