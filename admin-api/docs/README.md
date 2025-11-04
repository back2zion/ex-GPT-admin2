# ex-GPT 시스템 문서

한국도로공사 ex-GPT 시스템 (MSA 아키텍처) 개발 문서입니다.

---

## 🎯 핵심 문서

### 1. 필수 읽기 ⭐

| 문서 | 설명 | 크기 |
|------|------|------|
| **[PRD.md](./PRD.md)** | 전체 시스템 요구사항 명세서 (v3.0)<br>- RFP 요구사항 전면 반영<br>- 기능/성능/보안/데이터/테스트 요구사항<br>- 산출물 목록 | 55KB |
| **[RFP.txt](./RFP.txt)** | 계약 요구사항 원본 (발주처 제공)<br>- 기능 요구사항 (FUN-001~006)<br>- 성능/보안/품질 요구사항<br>- 프로젝트 관리 요구사항 | 49KB |

### 2. 기술 문서

| 문서 | 설명 | 크기 |
|------|------|------|
| **[DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md)** | PostgreSQL 스키마 정의<br>- 테이블 구조<br>- 관계도<br>- 인덱스 | 7KB |
| **[SPRING_BOOT_AUTH_INTEGRATION.md](./SPRING_BOOT_AUTH_INTEGRATION.md)** | Spring Session 인증 통합<br>- FastAPI ↔ Spring Boot 세션 공유<br>- Redis 기반 세션 관리 | 11KB |
| **[SECURITY_IMPROVEMENTS.md](./SECURITY_IMPROVEMENTS.md)** | 보안 개선 사항<br>- OWASP Top 10 대응<br>- 시큐어 코딩<br>- 입력 검증 | 11KB |

### 3. 배포 문서

| 문서 | 설명 | 크기 |
|------|------|------|
| **[AIRGAP_DEPLOYMENT_GUIDE.md](./AIRGAP_DEPLOYMENT_GUIDE.md)** | 폐쇄망 배포 가이드<br>- Docker 이미지 반입<br>- 오프라인 설치 절차<br>- 체크섬 검증 | 12KB |

---

## 🏗️ 시스템 구조

```
ex-GPT System (MSA)
├── 사용자 UI (Spring Boot 18180)
│   └── https://ui.datastreams.co.kr:20443/layout.html
│
├── 관리자 도구 (FastAPI 8010)
│   └── https://ui.datastreams.co.kr:20443/admin/
│       ├── /#/conversations (대화내역)
│       ├── /#/dictionaries (사전 관리)
│       └── /#/notices (공지사항)
│
├── Chat API (FastAPI 8080)
│   └── AI 대화 처리, RAG 검색
│
├── STT API (FastAPI 8085)
│   └── 음성 전사 (Whisper)
│
└── 공유 데이터베이스
    ├── PostgreSQL 15 (메타데이터)
    ├── Redis 7 (세션, 캐시)
    ├── Qdrant (벡터 DB)
    └── MinIO (파일 저장소)
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
cd /home/aigen/tomcat/webapps/
# Tomcat 시작
```

---

## 📂 Archive

참고용 문서는 `archive/` 디렉토리에 보관:

**archive/** (1개):
- **RFP_COMPLIANCE_CHECK.md** (16KB) - RFP 요구사항 준수 체크리스트
  - FUN-002, FUN-003 구현 현황
  - 미구현 기능 목록 및 우선순위
  - 감사/검수용 참고 자료

**총 문서 수**:
- 핵심 문서: **7개** (필수 2 + 기술 3 + 배포 1 + README 1)
- Archive: **1개** (RFP 체크리스트)

---

## 🚀 빠른 시작

1. **시스템 이해**: [PRD.md](./PRD.md) 읽기
2. **계약 요구사항**: [RFP.txt](./RFP.txt) 참조
3. **배포 준비**: [AIRGAP_DEPLOYMENT_GUIDE.md](./AIRGAP_DEPLOYMENT_GUIDE.md) 참고
4. **개발 시작**: API 문서 확인 (http://localhost:8010/docs)

---

## 📝 주요 변경사항

### 2025-10-28
- ✅ PRD v3.0 업데이트 (RFP 요구사항 전면 반영)
- ✅ 멀티모달 LLM, 모바일 연계, 레거시 연계 추가
- ✅ 성능/보안/데이터 요구사항 명시
- ✅ 산출물 목록 작성 (53개)
- ✅ 문서 대대적 정리 (66개 문서/디렉토리 삭제)
  - 30개 임시 보고서/로그 삭제 (setup, completion, daily reports)
  - 10개 통합 완료 문서 삭제 (PRD 통합, 구현 완료 기능)
  - 10개 중복/구버전 문서 삭제 (old PRD, migration docs)
  - 13개 실패한 Apache 스크립트 삭제
  - 3개 임시 파일 삭제 (구현 계획, STT 문서, 테스트 파일)
  - **최종 보관: 8개 핵심 문서만 유지** (7개 core + 1개 archive)

### 2025-10-27
- ✅ 개인 파일 업로드 시스템 구현
- ✅ Apache 리버스 프록시 설정 문서화
- ✅ 선택적 인증(Optional Auth) 추가

### 2025-10-26
- ✅ 대화 자동 분류 (LLM 기반, 100% 정확도)
- ✅ 조직도 기반 카테고리 체계

---

**최종 업데이트**: 2025-10-28
**문서 관리**: ex-GPT 개발팀
**검토자**: 한국도로공사 디지털계획처 AI데이터팀
