# 폐쇄망 배포 빠른 시작 가이드

## TL;DR (요약)

✅ **안심하세요!** 이 시스템은 100% 폐쇄망(내부망) 반입이 가능합니다.

- **외부 인터넷 연결 불필요**
- **Docker로 패키징** → USB/DVD로 반입
- **모든 의존성 포함** (Python, Node.js, Docker 이미지)
- **3~5GB** 정도 용량 (압축 시)

---

## 외부망에서 (반출 준비)

```bash
# 1. 프로젝트 디렉토리로 이동
cd /home/aigen/admin-api

# 2. 패키지 생성 스크립트 실행
./scripts/export-airgap.sh

# 3. 생성된 파일을 USB/DVD에 복사
# admin-api-airgap-YYYYMMDD-HHMMSS.tar.gz (약 3~5GB)
```

**소요 시간**: 약 10~30분 (네트워크 속도에 따라)

---

## 내부망에서 (반입 설치)

```bash
# 1. USB/DVD에서 파일 복사
cp /media/usb/admin-api-airgap-*.tar.gz ~/

# 2. 압축 해제
tar -xzf admin-api-airgap-*.tar.gz
cd admin-api-airgap-*/

# 3. 설치 스크립트 실행
./import.sh

# 4. 환경 설정 수정
cd /opt/admin-api
vi .env  # 내부망 IP/도메인으로 수정

# 5. 서비스 시작
docker-compose up -d

# 6. 접속 확인
curl http://localhost:8010/admin
```

**소요 시간**: 약 10~20분

---

## 체크리스트

### 반출 준비 (외부망)

- [ ] Docker 설치 확인 (`docker --version`)
- [ ] Docker Compose 설치 확인 (`docker-compose --version`)
- [ ] Python 3.11 설치 확인 (`python3 --version`)
- [ ] Node.js 20+ 설치 확인 (`node --version`)
- [ ] 디스크 여유 공간 10GB 이상
- [ ] `./scripts/export-airgap.sh` 실행
- [ ] 생성된 `.tar.gz` 파일 USB/DVD에 복사

### 반입 설치 (내부망)

- [ ] Docker 설치 완료
- [ ] Docker Compose 설치 완료
- [ ] USB/DVD로 파일 반입 완료
- [ ] 보안 검토 완료 (악성코드 스캔 등)
- [ ] `./import.sh` 실행
- [ ] `.env` 파일 수정 (내부망 설정)
- [ ] Spring Boot URL 확인 (`SPRING_BOOT_URL`)
- [ ] 데이터베이스 비밀번호 변경
- [ ] 서비스 시작 확인 (`docker-compose ps`)

---

## 주요 의존성 (모두 오픈소스)

| 항목 | 버전 | 라이선스 | 용도 |
|------|------|---------|------|
| Python | 3.11 | PSF | 백엔드 런타임 |
| FastAPI | 0.109+ | MIT | 웹 프레임워크 |
| PostgreSQL | 15 | PostgreSQL | 데이터베이스 |
| Redis | 7 | BSD | 캐시/세션 |
| React | 19 | MIT | 프론트엔드 |
| Cerbos | latest | Apache 2.0 | 권한 관리 |

**모두 상업적 사용 가능합니다!**

---

## 패키지 내용물

```
admin-api-airgap-YYYYMMDD-HHMMSS/
├── docker-images/          # Docker 이미지 (tar.gz)
│   ├── python-3.11-slim.tar.gz
│   ├── postgres-15-alpine.tar.gz
│   ├── redis-7-alpine.tar.gz
│   ├── cerbos-latest.tar.gz
│   └── admin-api.tar.gz
├── offline_packages/       # Python/Node 패키지
│   ├── python/             # *.whl 파일들
│   └── frontend/           # node_modules.tar.gz
├── admin-api-source.tar.gz # 소스코드
├── README.md               # 상세 가이드
├── import.sh               # 설치 스크립트
└── checksums.txt           # SHA256 체크섬
```

---

## 네트워크 구성 (내부망)

```
┌─────────────────────────────────────────────┐
│           내부망 (Air-Gap 환경)              │
│                                             │
│  ┌──────────────┐      ┌─────────────────┐│
│  │  사용자 PC    │─────→│  Admin API      ││
│  │  (브라우저)   │      │  (Port 8010)    ││
│  └──────────────┘      └─────────────────┘│
│                               │            │
│                               ↓            │
│                        ┌─────────────────┐│
│                        │  Spring Boot    ││
│                        │  (Port 18180)   ││
│                        └─────────────────┘│
│                               │            │
│                               ↓            │
│                        ┌─────────────────┐│
│                        │  PostgreSQL     ││
│                        │  (Port 5444)    ││
│                        └─────────────────┘│
│                                             │
│  ⛔ 외부 인터넷 연결 불필요                   │
└─────────────────────────────────────────────┘
```

---

## 자주 묻는 질문 (FAQ)

### Q1. 인터넷 연결이 전혀 필요 없나요?

✅ **네, 전혀 필요 없습니다!**
- 모든 의존성이 패키지에 포함되어 있습니다.
- 외부 API 호출 없음
- AI 모델도 내부망에 이미 배포된 것 사용

### Q2. 용량이 얼마나 되나요?

📦 **약 3~5GB** (압축 시 1.5~3GB)
- Docker 이미지: 2~3GB
- Python 패키지: 500MB~1GB
- Node.js 패키지: 50~100MB (압축)
- 소스코드: 10~50MB

### Q3. 보안 승인 받을 수 있나요?

✅ **네, 가능합니다!**
- 모든 소스코드 오픈 (검토 가능)
- 오픈소스 라이선스 (상업적 사용 가능)
- 악성코드 없음 (스캔 가능)
- 개인정보 미포함
- 암호화 모듈 (bcrypt, JWT) 사용 승인 필요

### Q4. Spring Boot와 연동되나요?

✅ **네, 세션 기반 인증으로 연동됩니다!**
- JSESSIONID 쿠키 사용
- Spring Boot에 간단한 API만 추가하면 됨
- 자세한 내용: `docs/SPRING_BOOT_AUTH_INTEGRATION.md`

### Q5. GPU가 필요한가요?

❌ **Admin API는 GPU 불필요**
- CPU만으로 충분히 동작
- GPU는 AI 모델 서버(vLLM)에만 필요

### Q6. 업데이트는 어떻게 하나요?

🔄 **동일한 방법으로 재배포**
1. 외부망에서 새 패키지 생성
2. USB/DVD로 반입
3. 기존 버전 백업
4. 새 버전 설치

### Q7. 데이터베이스는 어떻게 되나요?

💾 **두 가지 방식 지원**
1. **Docker PostgreSQL** (패키지 포함)
2. **기존 내부 DB 연동** (.env에서 설정)

권장: 기존 내부 DB 연동

### Q8. 라이선스 비용이 있나요?

💰 **완전 무료!**
- 모든 구성요소 오픈소스
- 상업적 사용 가능
- 라이선스 비용 없음

---

## 문제 해결

### Docker 이미지 로드 실패

```bash
# 압축 파일 무결성 확인
gunzip -t admin-api.tar.gz

# 압축 해제 후 재시도
gunzip admin-api.tar.gz
docker load -i admin-api.tar
```

### 서비스 시작 실패

```bash
# 로그 확인
docker-compose logs admin-api

# 환경 변수 확인
cat .env

# 포트 충돌 확인
netstat -tlnp | grep 8010
```

### 인증 실패 (401 오류)

```bash
# Spring Boot URL 확인
grep SPRING_BOOT_URL .env

# Spring Boot 상태 확인
curl http://localhost:18180/exGenBotDS/

# 테스트 모드로 확인
curl -H "X-Test-Auth: admin" http://localhost:8010/api/v1/admin/dictionaries
```

---

## 지원 및 문의

- 📖 **상세 가이드**: `docs/AIRGAP_DEPLOYMENT_GUIDE.md`
- 🔐 **인증 통합**: `docs/SPRING_BOOT_AUTH_INTEGRATION.md`
- 🐛 **이슈 보고**: GitHub Issues
- 📧 **기술 지원**: [담당자 이메일]

---

## 마지막 확인사항

반출 전 확인:
- [ ] `export-airgap.sh` 실행 완료
- [ ] `.tar.gz` 파일 생성 확인
- [ ] 용량 확인 (3~5GB)
- [ ] 체크섬 파일 포함 확인

반입 후 확인:
- [ ] Docker 이미지 로드 완료
- [ ] `.env` 파일 수정 완료
- [ ] `docker-compose ps` 정상
- [ ] `http://localhost:8010/admin` 접속 가능
- [ ] Spring Boot 인증 연동 확인

---

**안심하고 배포하세요! 🚀**
