# ex-GPT 시스템 PRD (Product Requirements Document)

**버전**: 2.0
**최종 수정일**: 2025-10-25
**프로젝트**: 한국도로공사 ex-GPT 관리 시스템

---

## 📋 프로젝트 개요

### 시스템 구성 (MSA 아키텍처)

```
┌─────────────────────────────────────────────────────────────┐
│                     ex-GPT System (MSA)                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────┐    ┌──────────────────────┐      │
│  │   사용자 UI          │    │   관리자 도구        │      │
│  │   (Spring Boot)      │    │   (FastAPI)          │      │
│  │                      │    │                      │      │
│  │  Java + React        │    │  Python + React      │      │
│  │  Port: 18180         │    │  Port: 8010          │      │
│  │                      │    │                      │      │
│  │  URL:                │    │  URL:                │      │
│  │  /exGenBotDS/testOld │    │  /admin/             │      │
│  │  /exGenBotDS/ai      │    │  /admin/#/...        │      │
│  └──────────────────────┘    └──────────────────────┘      │
│           │                            │                     │
│           └────────────┬───────────────┘                     │
│                        │                                     │
│                        ▼                                     │
│            ┌──────────────────────┐                         │
│            │   공유 데이터베이스   │                         │
│            │   (PostgreSQL)       │                         │
│            │   - usage_history    │                         │
│            │   - users            │                         │
│            │   - satisfaction     │                         │
│            └──────────────────────┘                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘

외부 접속:
- 사용자 UI: https://ui.datastreams.co.kr:20443/exGenBotDS/testOld
- 사용자 UI (신규): https://ui.datastreams.co.kr:20443/exGenBotDS/ai
- 관리자 대시보드: https://ui.datastreams.co.kr:20443/admin/
```

---

## 🎯 핵심 목표

1. **MSA 기반 분리**: 사용자 UI(Spring Boot)와 관리 도구(FastAPI) 독립 운영
2. **폐쇄망 배포**: 인터넷이 안 되는 내부망에 Docker로 반입 가능
3. **데이터 연동**: 사용자 UI에서 입력한 대화가 관리자 도구에 실시간 표시
4. **시큐어 코딩**: OWASP Top 10 대응, 입력 검증, 인증/인가
5. **유지보수성**: TDD 개발, 명확한 문서화, 모듈화 설계

---

## 🏗️ 기술 스택

### 사용자 UI (User Interface)
- **Backend**: Java Spring Boot 3.x
- **Frontend**: React (Vite)
- **서버**: Tomcat (Embedded)
- **포트**: 18180
- **경로**: `/exGenBotDS/testOld`, `/exGenBotDS/ai`

### 관리자 도구 (Admin Tool)
- **Backend**: Python 3.9+ / FastAPI
- **Frontend**: React 18+ (Vite)
- **ORM**: SQLAlchemy (AsyncIO)
- **인증**: Spring Boot Session 통합
- **포트**: 8010
- **경로**: `/admin/`

### 공통 인프라
- **Database**: PostgreSQL 15
- **Reverse Proxy**: Apache HTTP Server
- **Container**: Docker + Docker Compose
- **벡터 DB**: Qdrant (사용자 UI에서 사용)
- **스토리지**: MinIO (사용자 UI에서 사용)

---

## 📊 데이터 흐름

```
1. 사용자가 질문 입력
   URL: https://ui.datastreams.co.kr:20443/exGenBotDS/testOld

2. Spring Boot가 처리
   - LLM 응답 생성
   - usage_history 테이블에 저장
     * user_id
     * question
     * answer
     * main_category
     * sub_category
     * created_at

3. 관리자가 대화내역 조회
   URL: https://ui.datastreams.co.kr:20443/admin/#/conversations

4. FastAPI가 데이터 조회
   - usage_history 테이블에서 SELECT
   - 필터링 (날짜, 카테고리)
   - 페이지네이션
```

---

## ✅ 전제 조건 (Requirements)

### 1. 개발 방법론
- ✅ **TDD (Test-Driven Development)**: 테스트 우선 개발
  - 단위 테스트 (pytest, JUnit)
  - 통합 테스트
  - E2E 테스트

### 2. 시큐어 코딩
- ✅ **OWASP Top 10 대응**
  - SQL Injection 방지 (ORM 사용)
  - XSS 방지 (입력 검증, DOMPurify)
  - CSRF 방지 (토큰 검증)
  - 인증/인가 (Spring Session 통합)
- ✅ **입력 검증**: Pydantic, Bean Validation
- ✅ **에러 처리**: 민감 정보 노출 방지

### 3. 유지보수성
- ✅ **코드 품질**
  - 명확한 변수명/함수명
  - 적절한 주석
  - 모듈화 설계
- ✅ **문서화**
  - API 문서 (Swagger/OpenAPI)
  - README
  - 배포 가이드
- ✅ **버전 관리**: Git

### 4. 폐쇄망 배포
- ✅ **Docker 기반**: 모든 서비스 컨테이너화
- ✅ **오프라인 패키지**:
  - Docker 이미지 tar 파일
  - Python/Node 패키지 사전 다운로드
  - 체크섬 검증
- ✅ **배포 스크립트**: 자동화된 설치 스크립트

---

## 🎨 주요 기능

### 관리자 도구 (FastAPI)

#### 1. 대화내역 조회 ⭐ **P0**
- 목록 조회 (필터링, 페이지네이션)
- 상세 조회 (질문, 답변, 참조 문서)
- 엑셀 다운로드 (xlsx)
- **데이터 소스**: `usage_history` 테이블 (Spring Boot와 공유)

#### 2. 통계 대시보드 ⭐ **P0**
- 주요 지표 카드 (질문 수, 사용자 수, 응답 시간, 만족도)
- 사용 추이 차트 (일별/주별/월별)
- 시간대별 패턴
- 부서별 이용 통계
- 분야별 질의 통계

#### 3. 사전 관리 ⭐ **P0**
- 동의어 사전 CRUD
- CSV/Excel 업로드/다운로드
- 대소문자/띄어쓰기 구분 옵션

#### 4. 공지사항 관리 ⭐ **P0**
- CRUD 작업
- 상단 고정 기능
- 조회수 추적

#### 5. 만족도 조회 ⭐ **P0**
- 만족도 통계
- 피드백 조회

#### 6. STT 음성 전사 ⭐ **P1**
- 배치 업로드
- 전사 결과 조회

### 사용자 UI (Spring Boot)

#### 1. AI 채팅 인터페이스 ⭐ **P0**
- 질문/답변 처리
- 참조 문서 표시
- 스트리밍 응답
- 파일 업로드

#### 2. 세션 관리 ⭐ **P0**
- Spring Session 기반
- Redis 세션 저장소
- JSESSIONID 쿠키

#### 3. 사용 이력 저장 ⭐ **P0**
- `usage_history` 테이블에 자동 저장
- 대분류/소분류 자동 분류
- 응답 시간 기록

---

## 🔐 보안 요구사항

### 인증/인가
- **Spring Boot Session 통합**: FastAPI가 Spring Session 검증
- **JSESSIONID 쿠키**: 세션 기반 인증
- **Cerbos**: 권한 관리 (RBAC)

### 데이터 보호
- **SQL Injection 방지**: ORM 사용 (SQLAlchemy, JPA)
- **XSS 방지**: 입력 검증, sanitization
- **CSRF 방지**: 토큰 검증
- **민감 정보**: 환경 변수로 관리 (.env)

---

## 🚀 배포 요구사항

### 폐쇄망 배포 프로세스

1. **패키지 생성** (외부망)
```bash
./scripts/export-airgap.sh
```

2. **파일 반입** (USB 등)
```
airgap-deployment-YYYYMMDD.tar.gz
```

3. **설치 실행** (내부망)
```bash
./scripts/import-airgap.sh
```

4. **서비스 시작**
```bash
docker-compose up -d
```

### Docker 컨테이너 구성

```yaml
services:
  admin-api:      # FastAPI (포트 8010)
  user-api:       # Spring Boot (포트 18180)
  postgres:       # PostgreSQL 15
  redis:          # 세션 저장소
  qdrant:         # 벡터 DB
  minio:          # 오브젝트 스토리지
```

---

## 📈 성공 지표

### 기능 완성도
- ✅ P0 (필수) 기능: **90% 완료**
- ✅ P1 (중요) 기능: **55% 완료**
- ⬜ P2 (선택) 기능: **45% 완료**

### 품질 지표
- ✅ 테스트 커버리지: **>70%**
- ✅ 보안 점검: **OWASP Top 10 대응**
- ✅ 문서화: **핵심 문서 완비**
- ✅ 성능: **응답 시간 < 2초**

### 운영 지표
- ✅ 폐쇄망 배포 성공률: **100%**
- ✅ 시스템 가용성: **99%+**
- ✅ 데이터 동기화: **실시간**

---

## 📝 다음 단계

### 단기 (1주)
1. ⬜ `/exGenBotDS/ai` Spring Boot 엔드포인트 구현
2. ⬜ 사용자 UI → 관리자 도구 데이터 흐름 검증
3. ⬜ 공통 코드 관리 API 구현 (P0 마지막 필수 기능)

### 중기 (1개월)
1. ⬜ PII 검출 기능 (P1)
2. ⬜ 문서 중복 검출 (P1)
3. ⬜ 폐쇄망 배포 테스트

### 장기 (3개월)
1. ⬜ 사용자별 업로드 파일 관리 (P2)
2. ⬜ 연계 프로그램 스케줄 관리 (P2)
3. ⬜ 고도화 및 성능 최적화

---

## 📚 참고 문서

- [배포 가이드](./AIRGAP_DEPLOYMENT_GUIDE.md)
- [데이터베이스 스키마](./DATABASE_SCHEMA.md)
- [Spring Boot 인증 통합](./SPRING_BOOT_AUTH_INTEGRATION.md)
- [보안 개선 사항](./SECURITY_IMPROVEMENTS.md)

## 🎨 UI/UX 디자인 가이드

### 한국도로공사 컬러 스킴

```css
/* Primary Colors */
--ex-primary: #0a2986;      /* 네이비 블루 (메인) */
--ex-accent: #e64701;       /* 오렌지 (강조) */

/* Neutral Colors */
--ex-background: #f8f8f8;   /* 배경 */
--ex-border: #e4e4e4;       /* 테두리 */
--ex-text: #7b7b7b;         /* 본문 텍스트 */
--ex-text-dark: #333333;    /* 제목 텍스트 */

/* Status Colors */
--ex-success: #10b981;      /* 성공 */
--ex-warning: #f59e0b;      /* 경고 */
--ex-danger: #ef4444;       /* 위험 */
--ex-info: #3b82f6;         /* 정보 */
```

### 컴포넌트 스타일 원칙

1. **버튼**
   - Primary: `background: #0a2986`
   - Secondary: `background: #e64701`
   - Disabled: `background: #e4e4e4`

2. **테이블**
   - Header: `background: #0a2986; color: white`
   - Row hover: `background: #f8f8f8`
   - Border: `1px solid #e4e4e4`

3. **카드**
   - Background: `white`
   - Border: `1px solid #e4e4e4`
   - Shadow: `0 2px 4px rgba(10, 41, 134, 0.1)`
