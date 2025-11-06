# 한국도로공사 내부망 배포 가이드
## ex-GPT 모바일 오피스 STT 사내메일 연동

---

## 📖 목차

1. [개요](#1-개요)
2. [시스템 요구사항](#2-시스템-요구사항)
3. [사전 준비](#3-사전-준비)
4. [Step-by-Step 배포](#4-step-by-step-배포)
5. [테스트 및 검증](#5-테스트-및-검증)
6. [운영 가이드](#6-운영-가이드)
7. [FAQ](#7-faq)

---

## 1. 개요

### 1.1 프로젝트 설명

모바일 오피스에서 녹음한 회의 음성을 자동으로 텍스트로 변환하고(STT), AI를 통해 회의록을 생성한 후, 한국도로공사 사내메일로 자동 발송하는 통합 시스템입니다.

### 1.2 주요 기능

1. **음성 전사 (STT)**: faster-whisper 기반 한국어 음성 인식
2. **회의록 자동 생성**: Qwen LLM을 통한 요약 및 구조화
3. **채팅 히스토리 저장**: PostgreSQL에 대화 이력 저장
4. **사내메일 자동 발송**: Oracle DB를 통한 사내메일 시스템 연동

### 1.3 시스템 구조

```
┌─────────────────┐
│ 모바일 오피스   │ (음성 녹음)
└────────┬────────┘
         │ HTTP POST /api/stt/process
         ▼
┌─────────────────┐
│ ex-GPT-STT      │ (포트 9200)
│                 │
│ • STT 처리      │
│ • 회의록 생성   │
└────────┬────────┘
         │ HTTP POST /api/v1/webhooks/stt-completed
         ▼
┌─────────────────┐
│ admin-api       │ (포트 8010)
│                 │
│ • Webhook 수신  │
│ • 히스토리 저장 │───→ PostgreSQL (USR_CNVS_SMRY, USR_CNVS)
│ • 메일 발송     │───→ Oracle (MAIL_DOC, MAIL_INBOX)
└─────────────────┘
```

### 1.4 반입 범위

**수정된 파일**:
- `admin-api/app/services/internal_mail_service.py` (신규)
- `admin-api/app/services/stt_chat_integration_service.py` (신규)
- `admin-api/app/routers/webhooks/stt_webhook.py` (신규)
- `admin-api/app/core/config.py` (수정)
- `admin-api/app/main.py` (수정)
- `ex-GPT-STT/src/api/api_server.py` (수정)

**의존성 추가**:
- `oracledb` (Python Oracle 드라이버)
- `httpx` (HTTP 클라이언트)

---

## 2. 시스템 요구사항

### 2.1 하드웨어

| 구성요소 | 최소 사양 | 권장 사양 |
|---------|----------|----------|
| CPU | 4 cores | 8 cores |
| RAM | 8 GB | 16 GB |
| GPU | NVIDIA 1080 Ti | NVIDIA 3090/4090 |
| Disk | 100 GB | 500 GB |

### 2.2 소프트웨어

| 구성요소 | 버전 |
|---------|------|
| OS | Rocky Linux 8.x |
| Docker | 24.x |
| Docker Compose | 2.x |
| Python | 3.11 |
| PostgreSQL | 15 |
| Oracle Client | python-oracledb 3.4+ |

### 2.3 네트워크

| 구성요소 | 주소 | 포트 |
|---------|-----|------|
| ex-GPT-STT | 172.16.164.100 | 9200 |
| admin-api | 172.16.164.100 | 8010 |
| Oracle DB | 172.16.164.32 | 1669 |
| PostgreSQL | localhost | 5432 |

---

## 3. 사전 준비

### 3.1 DBA팀 지원 요청

#### 요청 내용
```
제목: ex-GPT 사내메일 연동을 위한 Oracle DB 계정 발급 요청

담당자님,

ex-GPT 시스템의 모바일 오피스 STT 회의록 자동 발송 기능을 위해
Oracle DB 접근 계정 및 권한을 요청드립니다.

[요청 사항]
1. 계정 발급
   - 시스템: ANKHCG (172.16.164.32:1669)
   - 계정명: exgpt_user (또는 별도 지정)
   - 용도: 사내메일 연동 (MAIL_DOC, MAIL_INBOX INSERT)

2. 권한 부여
   GRANT INSERT ON EXGWMAIN.MAIL_DOC TO exgpt_user;
   GRANT INSERT ON EXGWMAIN.MAIL_INBOX TO exgpt_user;
   GRANT SELECT ON EXGWMAIN.PT_USER TO exgpt_user;
   GRANT SELECT ON EXGWMAIN.XFMAIL_SEQ TO exgpt_user;

[참조 문서]
- prd_STT.md (전자문서시스템 사내메일 연동 인터페이스 설계서)

감사합니다.
```

### 3.2 네트워크팀 지원 요청

#### 요청 내용
```
제목: ex-GPT 서버 → Oracle DB 방화벽 포트 개방 요청

담당자님,

ex-GPT 시스템의 사내메일 연동을 위해 방화벽 규칙 추가를 요청드립니다.

[요청 사항]
- Source: 172.16.164.100 (ex-GPT 서버)
- Destination: 172.16.164.32 (Oracle DB 서버)
- Port: 1669
- Protocol: TCP
- 용도: 사내메일 연동 (MAIL_DOC, MAIL_INBOX INSERT)

[테스트 명령어]
timeout 5 bash -c "echo > /dev/tcp/172.16.164.32/1669" && echo "성공" || echo "실패"

감사합니다.
```

### 3.3 반입 파일 준비

#### 파일 체크리스트
```bash
# 1. 소스 코드 압축
cd /home/aigen
tar -czf exgpt-stt-mail-integration.tar.gz \
  admin-api/app/services/internal_mail_service.py \
  admin-api/app/services/stt_chat_integration_service.py \
  admin-api/app/routers/webhooks/ \
  admin-api/app/core/config.py \
  admin-api/app/main.py \
  admin-api/tests/test_internal_mail_service.py \
  admin-api/app/test_oracle_connection.py \
  admin-api/.env \
  admin-api/pyproject.toml \
  ex-GPT-STT/src/api/api_server.py \
  prd_STT.md \
  DEPLOYMENT_CHECKLIST.md \
  DEPLOYMENT_GUIDE.md

# 2. Python 패키지 다운로드 (오프라인 설치용)
pip download oracledb==3.4.0 -d packages/
pip download httpx==0.28.1 -d packages/
tar -czf python-packages.tar.gz packages/
```

---

## 4. Step-by-Step 배포

### Step 1: 파일 반입 및 압축 해제

```bash
# 1. 내부망 서버로 파일 복사 (USB 또는 승인된 방법)
# exgpt-stt-mail-integration.tar.gz
# python-packages.tar.gz

# 2. 압축 해제
cd /home/aigen
tar -xzf exgpt-stt-mail-integration.tar.gz

# 3. Python 패키지 압축 해제
tar -xzf python-packages.tar.gz
```

### Step 2: 패키지 설치

#### 2.1 admin-api 패키지 설치
```bash
# Docker 컨테이너에서 설치
docker exec admin-api-admin-api-1 pip install /tmp/packages/oracledb-3.4.0-*.whl

# 또는 requirements.txt 사용
docker exec admin-api-admin-api-1 pip install -r /app/requirements.txt
```

#### 2.2 ex-GPT-STT 패키지 설치
```bash
cd /home/aigen/ex-GPT-STT
source .venv/bin/activate
uv pip install /tmp/packages/httpx-0.28.1-*.whl

# 또는
pip install httpx==0.28.1
```

### Step 3: 환경 변수 설정

#### 3.1 .env 파일 수정
```bash
vi /home/aigen/admin-api/.env
```

#### 3.2 추가/수정할 내용
```bash
# Internal Mail System Oracle DB (사내메일 연동용)
MAIL_ORACLE_HOST=172.16.164.32
MAIL_ORACLE_PORT=1669
MAIL_ORACLE_USER=<DBA팀에서_발급받은_계정명>
MAIL_ORACLE_PASSWORD=<DBA팀에서_발급받은_비밀번호>
MAIL_ORACLE_SERVICE=ANKHCG
```

**⚠️ 중요**: 비밀번호는 반드시 DBA팀에서 발급받은 실제 비밀번호로 입력하세요.

### Step 4: 컨테이너 재시작

#### 4.1 admin-api 재시작
```bash
cd /home/aigen/admin-api/admin-api
docker compose restart admin-api

# 재시작 확인
docker ps | grep admin-api
```

#### 4.2 로그 확인
```bash
# 시작 로그 확인
docker logs admin-api-admin-api-1 --tail 50

# 오류 확인
docker logs admin-api-admin-api-1 | grep ERROR
```

### Step 5: ex-GPT-STT 재시작

#### 5.1 현재 프로세스 종료
```bash
# 현재 실행 중인 프로세스 찾기
ps aux | grep api_server.py

# 프로세스 종료 (PID 확인 후)
kill -9 <PID>
```

#### 5.2 재시작
```bash
cd /home/aigen/ex-GPT-STT
source .venv/bin/activate
nohup uv run python src/api/api_server.py > logs/api_server.log 2>&1 &

# 프로세스 확인
ps aux | grep api_server.py
```

---

## 5. 테스트 및 검증

### Test 1: Oracle DB 연결 테스트 ⭐ 필수

```bash
docker exec admin-api-admin-api-1 python -m app.test_oracle_connection
```

**예상 출력**:
```
============================================================
Oracle DB 연결 테스트 시작
============================================================

📋 연결 정보:
  - Host: 172.16.164.32
  - Port: 1669
  - Service: ANKHCG
  - User: exgpt_user
  - Password: **********

🔄 연결 시도 중...
✅ 연결 성공!

📊 Oracle 버전:
  Oracle Database 19c Enterprise Edition...

👤 현재 접속 사용자: EXGPT_USER

🔑 테이블 접근 권한 확인:
  ✅ EXGWMAIN.MAIL_DOC - 테이블 접근 가능
  ✅ EXGWMAIN.MAIL_INBOX - 테이블 접근 가능
  ✅ EXGWMAIN.PT_USER - SELECT 권한 있음

🔢 시퀀스 접근 확인:
  ✅ EXGWMAIN.XFMAIL_SEQ - 접근 가능 (현재 값: 12345)

============================================================
✅ Oracle DB 연결 테스트 완료!
============================================================
```

**실패 시 조치**:
- `Connection timed out` → 네트워크팀에 방화벽 확인 요청
- `invalid username/password` → DBA팀에 계정 정보 재확인
- `table or view does not exist` → DBA팀에 권한 부여 요청

### Test 2: API Health Check

```bash
# admin-api
curl http://localhost:8010/health
# 예상: {"status":"healthy"}

# ex-GPT-STT
curl http://localhost:9200/health
# 예상: {"status":"healthy"}
```

### Test 3: Webhook 엔드포인트 테스트

```bash
curl -X POST "http://localhost:8010/api/v1/webhooks/stt-completed" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: exgpt-stt-webhook-secret-key" \
  -d '{
    "task_id": "test-001",
    "status": "completed",
    "success": true,
    "transcription": "안녕하세요. 테스트 회의를 시작하겠습니다. 오늘 안건은 다음과 같습니다.",
    "meeting_minutes": "<html><body><h1>테스트 회의록</h1><ul><li>안건 1: 시스템 테스트</li></ul></body></html>",
    "duration": 120.5,
    "language": "ko",
    "meeting_title": "시스템 연동 테스트",
    "sender_name": "시스템관리자",
    "sender_email": null,
    "recipient_emails": null,
    "department": "정보화팀"
  }'
```

**예상 응답**:
```json
{
  "received": true,
  "processed": true,
  "cnvs_idt_id": "stt_1234567890abcdef",
  "cnvs_id": 123,
  "mail_sent": true,
  "message": "STT 결과가 채팅 히스토리에 저장되고 사내메일이 발송되었습니다."
}
```

### Test 4: E2E 통합 테스트 ⭐ 필수

#### 4.1 테스트 음성 파일 준비
```bash
# 테스트용 음성 파일 (1-2분 길이, WAV 형식)
# 예: test_meeting.wav
```

#### 4.2 STT API 호출
```bash
curl -X POST "http://localhost:9200/api/stt/process" \
  -F "audio=@/path/to/test_meeting.wav" \
  -F "meeting_title=E2E 통합 테스트 회의" \
  -F "sender_name=테스트관리자" \
  -F "sender_email=test@example.com" \
  -F "recipient_emails=recipient1@example.com,recipient2@example.com" \
  -F "auto_send_email=true"
```

#### 4.3 결과 확인 (약 1-5분 소요)

**PostgreSQL 확인**:
```sql
-- 채팅 히스토리 확인
SELECT * FROM usr_cnvs_smry
WHERE cnvs_idt_id LIKE 'stt_%'
ORDER BY rgst_dt DESC
LIMIT 1;

-- 상세 내용 확인
SELECT ques_txt, ans_txt FROM usr_cnvs
WHERE cnvs_idt_id = '<위에서_조회한_cnvs_idt_id>';
```

**Oracle 확인**:
```sql
-- 메일 본문 확인
SELECT DOC_YEARMON, DOC_NUMBER, DOC_SUBJECT, DOC_WRITERNAME
FROM EXGWMAIN.MAIL_DOC
WHERE DOC_REQ_SYSTEM = 'ex-GPT System'
ORDER BY DOC_YEARMON DESC, DOC_NUMBER DESC
FETCH FIRST 1 ROW ONLY;

-- 수신자 확인
SELECT RECEIVER, RECV_NAME, SEND_DATE
FROM EXGWMAIN.MAIL_INBOX
WHERE DOC_NUMBER = <위에서_조회한_DOC_NUMBER>;
```

**사내메일 확인**:
- 사내메일함에 접속하여 메일 수신 확인
- 제목: `[회의록] E2E 통합 테스트 회의`
- 본문: HTML 형식의 회의록

---

## 6. 운영 가이드

### 6.1 로그 모니터링

#### admin-api 로그
```bash
# 실시간 모니터링
docker logs -f admin-api-admin-api-1 | grep -E "(STT|webhook|mail)"

# 오류 확인
docker logs admin-api-admin-api-1 --since 1h | grep ERROR
```

#### ex-GPT-STT 로그
```bash
tail -f /home/aigen/ex-GPT-STT/logs/api_server.log
```

### 6.2 성능 모니터링

#### 시스템 리소스
```bash
# CPU/메모리 사용량
docker stats admin-api-admin-api-1

# GPU 사용량
nvidia-smi -l 1
```

#### 데이터베이스 성능
```sql
-- Oracle: 최근 메일 발송 통계
SELECT TO_CHAR(TO_DATE(DOC_YEARMON, 'YYYYMM'), 'YYYY-MM') AS 년월,
       COUNT(*) AS 발송건수
FROM EXGWMAIN.MAIL_DOC
WHERE DOC_REQ_SYSTEM = 'ex-GPT System'
GROUP BY DOC_YEARMON
ORDER BY DOC_YEARMON DESC;

-- PostgreSQL: STT 처리 통계
SELECT DATE(rgst_dt) AS 일자, COUNT(*) AS 처리건수
FROM usr_cnvs_smry
WHERE cnvs_idt_id LIKE 'stt_%'
  AND rgst_dt >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(rgst_dt)
ORDER BY 일자 DESC;
```

### 6.3 백업 및 복구

#### 설정 파일 백업
```bash
# .env 파일 백업
cp /home/aigen/admin-api/.env /home/aigen/admin-api/.env.backup.$(date +%Y%m%d)

# 데이터베이스 백업 (DBA팀)
# - Oracle: MAIL_DOC, MAIL_INBOX
# - PostgreSQL: USR_CNVS_SMRY, USR_CNVS
```

### 6.4 장애 대응

#### 일반적인 장애 상황

**상황 1: admin-api 컨테이너 중단**
```bash
# 재시작
docker start admin-api-admin-api-1

# 로그 확인
docker logs admin-api-admin-api-1 --tail 100
```

**상황 2: ex-GPT-STT 프로세스 중단**
```bash
cd /home/aigen/ex-GPT-STT
source .venv/bin/activate
nohup uv run python src/api/api_server.py > logs/api_server.log 2>&1 &
```

**상황 3: Oracle 연결 끊김**
```bash
# 연결 테스트
docker exec admin-api-admin-api-1 python -m app.test_oracle_connection

# 네트워크 확인
timeout 5 bash -c "echo > /dev/tcp/172.16.164.32/1669"
```

**상황 4: 사내메일 미발송**
```sql
-- Oracle에 데이터는 있는데 메일이 안 오는 경우
-- → Worker 프로세스 문제 (DBA/전산팀 확인)
SELECT * FROM EXGWMAIN.MAIL_DOC
WHERE DOC_NUMBER = <문제의_DOC_NUMBER>;
```

---

## 7. FAQ

### Q1: Oracle 연결 시 타임아웃이 발생합니다.
**A**: 네트워크 문제입니다.
1. 방화벽 규칙 확인: `sudo firewall-cmd --list-all | grep 1669`
2. 네트워크팀에 포트 개방 요청
3. Oracle 리스너 상태 확인 (DBA팀)

### Q2: "invalid username/password" 오류가 발생합니다.
**A**: 계정 정보를 확인하세요.
1. `.env` 파일의 `MAIL_ORACLE_USER`, `MAIL_ORACLE_PASSWORD` 확인
2. DBA팀에 계정 정보 재확인 요청

### Q3: Webhook은 성공했는데 사내메일이 안 옵니다.
**A**: Oracle 데이터를 확인하세요.
```sql
SELECT * FROM EXGWMAIN.MAIL_DOC
WHERE DOC_REQ_SYSTEM = 'ex-GPT System'
ORDER BY DOC_YEARMON DESC, DOC_NUMBER DESC;
```
- 데이터가 있으면: Worker 프로세스 문제 (DBA/전산팀)
- 데이터가 없으면: admin-api 로그 확인

### Q4: 테스트는 성공했는데 실제 사용 시 실패합니다.
**A**: 로그를 확인하세요.
```bash
docker logs admin-api-admin-api-1 | grep ERROR
tail -f /home/aigen/ex-GPT-STT/logs/api_server.log | grep error
```

### Q5: 성능이 느립니다.
**A**: 여러 원인이 있을 수 있습니다.
1. GPU 메모리 부족: `nvidia-smi` 확인
2. CPU/메모리 부족: `docker stats` 확인
3. Oracle 연결 풀 부족: DBA팀에 연결 수 확인 요청

### Q6: 배포 후 롤백하려면 어떻게 하나요?
**A**: 백업 파일로 복구하세요.
```bash
# .env 파일 복구
cp /home/aigen/admin-api/.env.backup.YYYYMMDD /home/aigen/admin-api/.env

# 이전 코드로 복구 (git)
git checkout <이전_커밋_해시>

# 컨테이너 재시작
docker compose restart admin-api
```

---

## 📞 지원 연락처

- **기술 문의**: ex-GPT 개발팀
- **DBA 지원**: DBA팀
- **네트워크 지원**: 네트워크팀
- **긴급 장애**: 전산팀

---

**문서 버전**: 1.0
**최종 수정일**: 2025-11-06
**작성자**: AI Development Team

**다음 문서**: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
