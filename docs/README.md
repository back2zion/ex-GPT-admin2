# ex-GPT 시스템 문서

한국도로공사 ex-GPT 시스템 (MSA 아키텍처) 개발 문서입니다.

---

## 🎯 핵심 문서

### 1. 필수 읽기 ⭐

| 문서 | 설명 |
|------|------|
| **[PRD.md](./PRD.md)** | 전체 시스템 요구사항, MSA 아키텍처, 기술 스택 |
| **[AIRGAP_DEPLOYMENT_GUIDE.md](./AIRGAP_DEPLOYMENT_GUIDE.md)** | 폐쇄망 배포 가이드 (Docker 기반) |

### 2. 기술 문서

| 문서 | 설명 |
|------|------|
| **[DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md)** | PostgreSQL 스키마 (공유 DB) |
| **[SPRING_BOOT_AUTH_INTEGRATION.md](./SPRING_BOOT_AUTH_INTEGRATION.md)** | Spring Session 인증 통합 |
| **[SECURITY_IMPROVEMENTS.md](./SECURITY_IMPROVEMENTS.md)** | 시큐어 코딩 및 OWASP 대응 |

### 3. 운영 문서 (2025-10-25 추가)

| 문서 | 설명 |
|------|------|
| **[SUCCESS_CHAT_API.md](./SUCCESS_CHAT_API.md)** | ✅ layout.html ↔ admin 연결 성공 사례 |
| **[AUTO_CATEGORIZATION_IMPLEMENTATION.md](./AUTO_CATEGORIZATION_IMPLEMENTATION.md)** | ✅ 대화 자동 분류 구현 (P0 요구사항 완료) |
| **[FAILURE_LOG.md](./FAILURE_LOG.md)** | ❌ 실패 사례 및 교훈 정리 |
| **[FRONT_SERVER_SETUP.md](./FRONT_SERVER_SETUP.md)** | 프론트 서버 설정 가이드 |
| **[AI_PATH_DEBUG.md](./AI_PATH_DEBUG.md)** | /exGenBotDS/ai 경로 디버깅 로그 |

### 4. 참고 문서

| 문서 | 설명 |
|------|------|
| **[AIRGAP_QUICKSTART.md](./AIRGAP_QUICKSTART.md)** | 폐쇄망 빠른 시작 가이드 |
| **[ADMIN_TOOL_FEATURES_PRD.md](./ADMIN_TOOL_FEATURES_PRD.md)** | 관리 도구 상세 기능 명세 |

---

## 🏗️ 시스템 구조

```
ex-GPT System (MSA)
├── 사용자 UI (Spring Boot)
│   └── https://ui.datastreams.co.kr:20443/exGenBotDS/
│       ├── /testOld  (기존 UI)
│       └── /ai       (신규 UI)
│
├── 관리자 도구 (FastAPI)
│   └── https://ui.datastreams.co.kr:20443/admin/
│       ├── / (대시보드)
│       ├── /#/conversations (대화내역)
│       ├── /#/dictionaries (사전 관리)
│       └── /#/notices (공지사항)
│
└── 공유 데이터베이스 (PostgreSQL)
    ├── usage_history (대화 이력)
    ├── users (사용자)
    ├── satisfaction (만족도)
    └── dictionaries (사전)
```

---

## 📖 API 문서

실시간 API 문서:
- **Swagger UI**: http://localhost:8010/docs
- **ReDoc**: http://localhost:8010/redoc

---

## 📦 개발 환경 설정

### 1. 관리자 도구 (FastAPI)
```bash
cd /home/aigen/admin-api
docker-compose up -d
```

### 2. 사용자 UI (Spring Boot)
```bash
# Spring Boot 서버 실행 (포트 18180)
```

---

## 📂 Archive

레거시 문서 및 과거 보고서는 `archive/` 디렉토리에 보관:
- 진행 상황 보고서 (20개)
- 개발 가이드 (구버전)
- 테스트 문서

**총 문서 수**:
- 핵심 문서: **13개** (필수 2 + 기술 3 + 운영 5 + 참고 2 + RFP 1)
- Archive: **20개**
- Scripts: **12개** (Apache 설정 스크립트)

---

## 🚀 빠른 시작

1. **시스템 이해**: [PRD.md](./PRD.md) 읽기
2. **배포 준비**: [AIRGAP_DEPLOYMENT_GUIDE.md](./AIRGAP_DEPLOYMENT_GUIDE.md) 참고
3. **개발 시작**: API 문서 확인 (http://localhost:8010/docs)

---

**최종 업데이트**: 2025-10-25
