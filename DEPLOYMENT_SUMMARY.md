# 🚀 ex-GPT 모바일 오피스 STT 사내메일 연동 - 반입 준비 완료

## ✅ 완료된 작업 요약

### 1. **코드 구현 완료** (100%)
- ✅ InternalMailService: Oracle 사내메일 연동
- ✅ STTChatIntegrationService: PostgreSQL 채팅 히스토리 저장
- ✅ Webhook 라우터: ex-GPT-STT 완료 알림 수신
- ✅ ex-GPT-STT 수정: admin-api webhook 호출
- ✅ 버그 수정: 예외 처리 개선

### 2. **테스트 완료** (100%)
- ✅ 단위 테스트: 11개 테스트 모두 통과 (Mock 사용)
- ✅ Oracle 연결 테스트 스크립트 작성
- ✅ Webhook 엔드포인트 테스트 시나리오

### 3. **문서화 완료** (100%)
- ✅ DEPLOYMENT_CHECKLIST.md: 상세 체크리스트
- ✅ DEPLOYMENT_GUIDE.md: Step-by-Step 배포 가이드
- ✅ test_oracle_connection.py: 자동화된 연결 테스트

---

## 📦 반입 파일 목록

### 소스 코드
```
admin-api/
├── app/
│   ├── services/
│   │   ├── internal_mail_service.py          (신규)
│   │   └── stt_chat_integration_service.py   (신규)
│   ├── routers/
│   │   └── webhooks/
│   │       ├── __init__.py                    (신규)
│   │       └── stt_webhook.py                 (신규)
│   ├── core/
│   │   └── config.py                          (수정)
│   ├── main.py                                (수정)
│   └── test_oracle_connection.py              (신규)
├── tests/
│   └── test_internal_mail_service.py          (신규)
├── .env                                       (템플릿)
├── pyproject.toml                             (수정)
├── DEPLOYMENT_CHECKLIST.md                    (신규)
└── DEPLOYMENT_GUIDE.md                        (신규)

ex-GPT-STT/
└── src/
    └── api/
        └── api_server.py                      (수정)
```

### 문서
- `prd_STT.md`: Oracle 사내메일 연동 인터페이스 설계서
- `DEPLOYMENT_CHECKLIST.md`: 반입 체크리스트
- `DEPLOYMENT_GUIDE.md`: 배포 가이드

---

## 🎯 내부망에서 해야 할 작업

### Phase 1: 사전 준비 (배포 전)
1. **DBA팀 요청**
   - [ ] Oracle DB 계정 발급 (exgpt_user)
   - [ ] 테이블 권한 부여 (MAIL_DOC, MAIL_INBOX, PT_USER)
   - [ ] 시퀀스 권한 부여 (XFMAIL_SEQ)

2. **네트워크팀 요청**
   - [ ] 방화벽 포트 개방 (172.16.164.100 → 172.16.164.32:1669)

### Phase 2: 배포 (약 30분 소요)
1. **파일 반입**
   ```bash
   # 압축 파일 복사 및 해제
   tar -xzf exgpt-stt-mail-integration.tar.gz
   ```

2. **패키지 설치**
   ```bash
   # admin-api
   docker exec admin-api-admin-api-1 pip install oracledb
   
   # ex-GPT-STT
   cd /home/aigen/ex-GPT-STT && source .venv/bin/activate
   uv pip install httpx
   ```

3. **환경 변수 설정**
   ```bash
   # .env 파일 수정
   vi /home/aigen/admin-api/.env
   
   # 추가:
   MAIL_ORACLE_USER=<실제_계정>
   MAIL_ORACLE_PASSWORD=<실제_비밀번호>
   ```

4. **재시작**
   ```bash
   # admin-api
   docker compose restart admin-api
   
   # ex-GPT-STT
   pkill -f api_server.py
   nohup uv run python src/api/api_server.py > logs/api_server.log 2>&1 &
   ```

### Phase 3: 테스트 (약 15분 소요)
1. **연결 테스트**
   ```bash
   docker exec admin-api-admin-api-1 python -m app.test_oracle_connection
   # 예상: ✅ 연결 성공! ✅ 모든 권한 확인 완료
   ```

2. **Webhook 테스트**
   ```bash
   curl -X POST http://localhost:8010/api/v1/webhooks/stt-completed \
     -H "X-API-Key: exgpt-stt-webhook-secret-key" \
     -H "Content-Type: application/json" \
     -d '{ ... }'
   # 예상: {"received":true, "processed":true, ...}
   ```

3. **E2E 통합 테스트**
   ```bash
   # 실제 음성 파일 업로드
   curl -X POST http://localhost:9200/api/stt/process \
     -F "audio=@test.wav" \
     -F "meeting_title=테스트"
   
   # 결과 확인:
   # - PostgreSQL: usr_cnvs_smry 테이블
   # - Oracle: MAIL_DOC, MAIL_INBOX 테이블
   # - 사내메일함: 메일 수신
   ```

---

## 📊 기대 효과

### 자동화된 워크플로우
```
모바일 오피스 녹음 → STT 처리 → 회의록 생성 → 사내메일 발송
(수동: 30분)          (자동: 3분)     (자동: 10초)    (자동: 즉시)
```

### 예상 생산성 향상
- **시간 절감**: 회의록 작성 시간 30분 → 3분 (90% 감소)
- **정확도**: AI 기반 전사로 누락 최소화
- **접근성**: 채팅 히스토리 및 사내메일로 다중 접근

---

## 🔍 핵심 검증 포인트

### 1. Oracle 연결 (최우선)
```bash
docker exec admin-api-admin-api-1 python -m app.test_oracle_connection
```
→ 모든 ✅가 나와야 함

### 2. Webhook 통신
```bash
curl -X POST http://localhost:8010/api/v1/webhooks/stt-completed \
  -H "X-API-Key: exgpt-stt-webhook-secret-key" ...
```
→ `{"received":true, "processed":true}` 확인

### 3. 데이터 저장
```sql
-- PostgreSQL
SELECT * FROM usr_cnvs_smry WHERE cnvs_idt_id LIKE 'stt_%';

-- Oracle
SELECT * FROM EXGWMAIN.MAIL_DOC WHERE DOC_REQ_SYSTEM = 'ex-GPT System';
```
→ 데이터 INSERT 확인

### 4. 사내메일 수신
사내메일함에서 `[회의록]` 제목의 메일 확인

---

## 📞 문제 발생 시 체크리스트

### ❌ Oracle 연결 실패
1. [ ] 방화벽 확인: `timeout 5 bash -c "echo > /dev/tcp/172.16.164.32/1669"`
2. [ ] 계정 정보 확인: `.env` 파일의 `MAIL_ORACLE_USER`, `MAIL_ORACLE_PASSWORD`
3. [ ] DBA팀 확인: 계정 활성화 및 권한 부여 상태

### ❌ Webhook 호출 실패
1. [ ] API 키 확인: ex-GPT-STT와 admin-api의 API 키 일치 여부
2. [ ] 네트워크 확인: ex-GPT-STT → admin-api (포트 8010) 통신
3. [ ] 로그 확인: `docker logs admin-api-admin-api-1`

### ❌ 메일 미발송
1. [ ] Oracle 데이터 확인: `SELECT * FROM EXGWMAIN.MAIL_DOC`
2. [ ] Worker 프로세스 확인 (DBA/전산팀)
3. [ ] 수신자 정보 확인: MAIL_INBOX 테이블

---

## 🎓 참고 문서

1. **DEPLOYMENT_CHECKLIST.md**: 상세 체크리스트 (본 문서의 확장판)
2. **DEPLOYMENT_GUIDE.md**: Step-by-Step 가이드 (FAQ 포함)
3. **prd_STT.md**: Oracle 인터페이스 설계서 (DBA 참조용)
4. **test_oracle_connection.py**: 자동화된 연결 테스트

---

## ✨ 준비 완료!

외부 개발 환경에서 할 수 있는 모든 작업이 완료되었습니다.
내부망 반입 후 위 체크리스트를 따라 배포하시면 됩니다.

**예상 배포 시간**: 1시간 (사전 준비 완료 시 30분)

**성공 기준**:
- ✅ Oracle 연결 테스트 통과
- ✅ Webhook 테스트 통과
- ✅ E2E 통합 테스트 통과
- ✅ 사내메일 수신 확인

---

**문서 작성일**: 2025-11-06
**작성자**: AI Development Team
