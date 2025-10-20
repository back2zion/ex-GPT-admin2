# AI Streams 관리도구 PRD v2.0

**프로젝트**: AI Streams 관리자 도구
**버전**: 2.0 (RFP 요건 중심 재작성)
**작성일**: 2025-10-20
**개발 방법론**: TDD (Test-Driven Development)

---

## 📋 Executive Summary

한국도로공사 AI Streams 엔터프라이즈 플랫폼의 관리자 도구를 RFP 요건에 맞춰 개발합니다.

**핵심 가치**:
- ✅ **RFP 필수 요건 100% 충족**
- ✅ **TDD 기반 안정성 확보**
- ✅ **유지보수 용이성 극대화**
- ✅ **한국도로공사 브랜드 아이덴티티 반영**

---

## 🎯 RFP 필수 요건 (우선순위 순)

### P0: 레거시 시스템 연계 ⭐⭐⭐⭐⭐

#### 요구사항
> "레거시 시스템(와이즈넛) DB 연계를 통한 제·개정 문서 확인"

#### 구현 범위
1. **문서 변경 감지 시스템**
   - 레거시 DB (PostgreSQL/Oracle) 연결
   - 스케줄러 기반 자동 감지 (1시간 간격)
   - 제·개정 문서 추적 (법령, 사규, 업무기준)
   - 변경 내역 비교 (diff)

2. **승인 워크플로우**
   - 관리자 승인 대기 목록
   - 변경 전/후 비교 뷰
   - 승인/반려 처리
   - 승인 이력 기록

3. **자동 전처리 반영**
   - 승인 시 벡터 DB 업데이트
   - 문서 메타데이터 동기화

#### TDD 테스트 케이스
```python
# tests/test_legacy_sync.py
- test_detect_document_changes()
- test_compare_document_versions()
- test_approve_document_change()
- test_reject_document_change()
- test_auto_preprocessing_trigger()
```

#### 시큐어 코딩
- SQL Injection 방지: Parameterized queries
- DB 연결 정보 암호화: 환경변수 + Secrets Manager
- 권한 검증: Cerbos 기반 RBAC

---

### P0-1: 사용 이력 관리 - 대화내역 조회 ⭐⭐⭐⭐⭐ ✅ **구현 완료 (2025-10-20)**

#### 요구사항
> "서비스 평가 및 개선을 위한 사용 이력 관리"

#### 구현 범위 (Phase 1 완료)
1. **사용 이력 수집** ✅
   - 질문/답변 로깅 (`usage_history` 테이블)
   - 응답 시간 측정 (`response_time` 컬럼)
   - 세션 관리 (`session_id`, `user_id`)
   - Thinking 과정 저장 (`thinking_content` 컬럼)
   - layout.html 채팅 연동 (`/api/chat_stream` 프록시)
   - 중복 저장 방지 (thinking 전용 응답 필터링)

2. **대화내역 조회 UI** ✅
   - React 기반 ConversationsPage 컴포넌트
   - 날짜 범위 필터링 (기본: 최근 7일)
   - 페이지네이션 (50개씩)
   - 상세보기 모달 (질문, 답변, thinking, 참조 문서)
   - 실시간 로딩 상태 표시

3. **API 엔드포인트** ✅
   - `GET /api/v1/admin/conversations/simple` (목록 조회, 인증 불필요)
   - `GET /api/v1/admin/conversations/simple/{id}` (상세 조회, 인증 불필요)
   - `POST /api/chat_stream` (layout.html 프록시, SSE 스트리밍)
   - `GET /api/chat/sessions` (세션 목록)
   - `GET /api/chat/sessions/{session_id}` (세션 메시지)

4. **인프라 설정** ✅
   - Apache 프록시 설정 (`/admin/` 경로)
   - GitLab nginx 프록시 설정 (172.25.101.91:8010)
   - Docker 컨테이너 배포 (admin-api-admin-api-1)
   - PostgreSQL 연동 (admin_db)

#### Phase 2 (예정)
1. **통계 및 분석** 🔄
   - 일별/주별/월별 사용량
   - 시간대별 사용 패턴
   - 부서별 사용 통계
   - 인기 질문 TOP 10

2. **데이터 내보내기** 🔄
   - CSV/Excel 다운로드
   - 날짜 범위 필터
   - 부서별 필터

#### TDD 테스트 케이스
```python
# tests/test_usage_history.py
- test_log_usage_with_thinking()
- test_query_usage_by_date_range()
- test_usage_stats_by_department()
- test_export_usage_to_csv()
```

#### 시큐어 코딩
- PII 보호: 개인정보 마스킹
- 권한 검증: 부서별 조회 권한
- 입력 검증: 날짜/부서 파라미터 검증

---

### P0: 문서 권한 관리 ⭐⭐⭐⭐⭐

#### 요구사항
> "접근 가능 문서 권한 관리 (부서별, 결재라인별)"

#### 구현 범위
1. **부서별 권한**
   - 부서 CRUD
   - 사용자-부서 할당
   - 부서별 문서 접근 권한

2. **결재라인 기반 권한**
   - 결재라인 정의
   - 결재라인별 문서 접근 권한

3. **개별 사용자 권한**
   - 사용자별 추가 권한 부여
   - 권한 회수

#### TDD 테스트 케이스
```python
# tests/test_document_permissions.py
- test_grant_department_permission()
- test_grant_approval_line_permission()
- test_grant_user_permission()
- test_check_user_can_access_document()
- test_revoke_permission()
```

#### 시큐어 코딩
- 권한 검증: Cerbos 정책 기반
- 최소 권한 원칙: Least Privilege
- 권한 변경 감사 로그

---

### P0: 이용만족도 조사 ⭐⭐⭐⭐⭐

#### 요구사항
> "이용만족도 조사 기능"

#### 구현 범위
1. **만족도 설문**
   - 별점 평가 (1-5점)
   - 피드백 텍스트
   - 개선 의견 수집

2. **통계 분석**
   - 평균 만족도
   - 시간별 추이
   - 부서별 만족도

3. **알림 기능**
   - 낮은 만족도 알림
   - 주간/월간 리포트

#### TDD 테스트 케이스
```python
# tests/test_satisfaction.py
- test_submit_satisfaction_survey()
- test_query_satisfaction_stats()
- test_low_satisfaction_alert()
```

#### 시큐어 코딩
- 익명성 보장: 개인정보 분리
- 입력 검증: 별점 범위, 텍스트 길이
- XSS 방지: 피드백 텍스트 sanitization

---

### P0: 공지사항 관리 ⭐⭐⭐⭐⭐

#### 요구사항
> "공지메시지 표출 기능"

#### 구현 범위
1. **공지사항 CRUD**
   - 제목/내용 작성
   - 우선순위 설정
   - 노출 기간 설정

2. **대상 설정**
   - 전체 사용자
   - 특정 부서
   - 특정 사용자

3. **표출 제어**
   - 팝업 형식
   - 배너 형식
   - 다시 보지 않기

#### TDD 테스트 케이스
```python
# tests/test_notices.py
- test_create_notice()
- test_list_active_notices()
- test_filter_notices_by_department()
- test_mark_notice_as_read()
```

#### 시큐어 코딩
- XSS 방지: 내용 sanitization
- CSRF 방지: Token 검증
- 권한 검증: 작성자 확인

---

### P0: 개인정보 검출 및 관리 ⭐⭐⭐⭐⭐

#### 요구사항
> "전처리 데이터 개인정보 유무 검출" (FUN-003)

#### 구현 범위
1. **자동 개인정보 검출**
   - 주민등록번호 패턴 감지
   - 전화번호 패턴 감지
   - 이메일 주소 감지
   - 주소 정보 감지
   - 신용카드 번호 감지

2. **관리자 확인 시스템**
   - 의심 데이터 포함 원본 문서 목록
   - 검출된 데이터 하이라이트 표시
   - 승인/삭제/마스킹 처리
   - 처리 이력 기록

3. **알림 시스템**
   - 개인정보 검출 시 즉시 알림
   - 미처리 항목 주간 리포트

#### TDD 테스트 케이스
```python
# tests/test_pii_detection.py
- test_detect_resident_number()
- test_detect_phone_number()
- test_detect_email()
- test_detect_address()
- test_mask_pii_data()
- test_admin_approval_workflow()
```

#### 시큐어 코딩
- 개인정보 암호화: AES-256
- 접근 로그: 모든 조회 기록
- 마스킹 처리: 비식별화

---

### P0: 학습데이터 범위 관리 ⭐⭐⭐⭐⭐

#### 요구사항
> "부서별로 학습데이터 참조 범위를 지정할 수 있도록 구성" (FUN-001)

#### 구현 범위
1. **데이터 범위 설정**
   - 전체 공개 데이터 (모든 부서)
   - 부서별 제한 데이터
   - 결재라인별 제한 데이터
   - 예시 설정 인터페이스

2. **참조 범위 관리 UI**
   - 문서별 참조 범위 설정
   - 부서 다중 선택 (예: 국가계약법 → 전부서)
   - 단일 부서 제한 (예: 야생동물보호법 → 품질환경처)
   - 벌크 업데이트 기능

3. **검증 및 적용**
   - RAG 검색 시 권한 필터링
   - 사용자 부서 기반 문서 제한
   - 캐시 무효화 (권한 변경 시)

#### TDD 테스트 케이스
```python
# tests/test_data_scope.py
- test_set_document_scope_all_departments()
- test_set_document_scope_single_department()
- test_set_document_scope_multiple_departments()
- test_user_can_access_within_scope()
- test_user_cannot_access_outside_scope()
- test_rag_filtering_by_department()
```

#### 시큐어 코딩
- 권한 검증: 모든 RAG 쿼리에 부서 필터 적용
- Broken Access Control 방지: 서버 사이드 검증
- 감사 로그: 범위 변경 이력 기록

---

### P1: A/B 테스트 시스템 ⭐⭐⭐⭐

#### 요구사항
> "AI모델 또는 서비스 보완 전후 기존 모델(A)/신규 모델(B) 테스트 수행" (FUN-006)

#### 구현 범위
1. **A/B 테스트 설정**
   - 테스트 생성 (모델 A vs 모델 B)
   - 트래픽 분배 비율 설정 (예: 50:50, 70:30)
   - 사용자 그룹 할당 (부서별, 랜덤)
   - 테스트 기간 설정

2. **성능 비교 대시보드**
   - 답변 품질 비교
   - 응답 시간 비교
   - 사용자 만족도 비교
   - 오류율 비교

3. **통계 분석**
   - 통계적 유의성 검증 (T-test)
   - 신뢰구간 계산
   - 승자 자동 판정

#### TDD 테스트 케이스
```python
# tests/test_ab_testing.py
- test_create_ab_test()
- test_assign_users_to_groups()
- test_route_traffic_by_ratio()
- test_collect_metrics()
- test_statistical_significance()
- test_declare_winner()
```

#### 시큐어 코딩
- 공정성: 랜덤 할당 알고리즘
- 데이터 무결성: 그룹 간 격리
- 권한 검증: 테스트 생성/종료 권한

---

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

---

## 🧪 TDD 개발 전략

### 테스트 피라미드

```
    /\
   /E2E\        10% - Playwright (End-to-End)
  /------\
 /Integr.\      20% - API Integration Tests
/----------\
| Unit Tests|   70% - Pytest (Unit Tests)
```

### TDD Workflow

1. **RED**: 실패하는 테스트 작성
2. **GREEN**: 테스트를 통과하는 최소한의 코드 작성
3. **REFACTOR**: 코드 개선 및 최적화

### 테스트 커버리지 목표

- **전체 코드 커버리지**: 80% 이상
- **핵심 비즈니스 로직**: 90% 이상
- **시큐어 코딩 관련**: 100%

---

## 🔒 시큐어 코딩 체크리스트

### OWASP Top 10 대응

1. ✅ **A01: Broken Access Control**
   - Cerbos 기반 RBAC
   - 권한 검증 middleware

2. ✅ **A02: Cryptographic Failures**
   - 비밀번호 bcrypt 해싱
   - DB 연결 정보 암호화

3. ✅ **A03: Injection**
   - SQLAlchemy ORM 사용
   - Parameterized queries

4. ✅ **A04: Insecure Design**
   - TDD 기반 안전한 설계
   - Security by Design

5. ✅ **A05: Security Misconfiguration**
   - 환경변수 분리
   - 최소 권한 원칙

6. ✅ **A06: Vulnerable Components**
   - Dependabot 활성화
   - 정기 의존성 업데이트

7. ✅ **A07: Identification and Authentication**
   - JWT 토큰 기반 인증
   - 세션 타임아웃

8. ✅ **A08: Software and Data Integrity**
   - 입력 검증
   - 데이터 무결성 확인

9. ✅ **A09: Security Logging**
   - 감사 로그 기록
   - 이상 탐지

10. ✅ **A10: SSRF**
    - URL 화이트리스트
    - 내부 네트워크 접근 제한

---

## 📊 개발 우선순위 로드맵

### Phase 1: RFP 필수 기능 (P0) - 6주

**Week 1-2**: 레거시 연계 + 사용 이력
- 문서 변경 감지 시스템 (FUN-002)
- 사용 이력 수집 및 통계 (FUN-002)
- TDD: 테스트 먼저 작성 후 구현

**Week 3**: 문서 권한 관리 + 데이터 범위
- 부서별/결재라인별 권한 (FUN-002)
- 학습데이터 참조 범위 관리 (FUN-001)
- RAG 필터링 통합

**Week 4**: 개인정보 검출
- 자동 PII 검출 엔진 (FUN-003)
- 관리자 승인 워크플로우
- 마스킹/삭제 처리

**Week 5**: 만족도 + 공지사항
- 만족도 조사 시스템 (FUN-002)
- 공지사항 관리 (FUN-002)
- 알림 시스템 통합

**Week 6**: P0 통합 테스트
- End-to-End 테스트
- 성능 테스트
- 보안 감사

### Phase 2: 추가 기능 (P1) - 3주

**Week 7**: A/B 테스트 시스템
- A/B 테스트 프레임워크 (FUN-006)
- 트래픽 분배 로직
- 통계 분석 대시보드

**Week 8**: 고급 분석 기능
- 사용 패턴 분석
- 부서별 통계 대시보드
- 예측 분석 (사용량 예측)

**Week 9**: 추가 기능
- 고급 검색 (Elasticsearch 연동)
- 데이터 내보내기 (PDF, Excel)
- API 문서화 (OpenAPI/Swagger)

### Phase 3: 최적화 및 운영 준비 (P2) - 2주

**Week 10**: 성능 최적화
- DB 쿼리 최적화
- 캐싱 전략 (Redis)
- API 응답 시간 개선

**Week 11**: 운영 준비
- 모니터링 설정 (Prometheus + Grafana)
- 알림 설정 (Alertmanager)
- 운영 매뉴얼 작성
- 관리자 교육 자료

---

## 🛠 기술 스택

### Backend
- **Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0 (Async)
- **DB**: PostgreSQL 15
- **Auth**: Cerbos (RBAC)
- **Testing**: Pytest + Pytest-asyncio

### Frontend
- **Framework**: React 18.2+ (2025-10-20 변경)
- **Build Tool**: Vite 5.x
- **Router**: React Router v6
- **Styling**: CSS Modules + Custom CSS (한국도로공사 컬러)
- **Charts**: Chart.js (예정)

### DevOps
- **Container**: Docker + Docker Compose
- **CI/CD**: GitHub Actions (예정)
- **Monitoring**: Prometheus + Grafana (예정)

---

## 📈 성공 지표 (KPI)

### 기능 완성도
- 🔄 **RFP 필수 기능**: 진행 중 (FUN-001 ~ FUN-006)
- 🔄 **P0 기능**: 1/7 완료
  - ❌ 레거시 시스템 연계 (미구현)
  - ✅ **사용 이력 관리 - 대화내역 조회 (P0-1 완료)**
    - ✅ layout.html 채팅 연동 (/api/chat_stream)
    - ✅ 대화내역 수집 (usage_history 테이블)
    - ✅ React 조회 페이지 (ConversationsPage.jsx)
    - ✅ 날짜 범위 필터링, 페이지네이션
    - ✅ 상세보기 모달
    - ✅ thinking 중복 저장 방지
    - 🔄 통계 및 분석 (예정)
    - 🔄 데이터 내보내기 (예정)
  - ❌ 문서 권한 관리 (미구현)
  - ❌ 이용만족도 조사 (미구현)
  - ❌ 공지사항 관리 (미구현)
  - ❌ 개인정보 검출 (미구현)
  - ❌ 학습데이터 범위 관리 (미구현)

### 품질 지표
- **테스트 커버리지**:
  - 전체: 80% 이상
  - 핵심 비즈니스 로직: 90% 이상
  - 시큐어 코딩 관련: 100%
- **시큐어 코딩**: OWASP Top 10 완벽 대응
- **코드 리뷰**: 모든 PR에 대해 100% 리뷰

### 성능 지표
- **API 응답 시간**:
  - P50: < 100ms
  - P95: < 200ms
  - P99: < 500ms
- **DB 쿼리 시간**: < 50ms (평균)
- **동시 사용자**: 500명 이상 지원

### 운영 지표
- **가용성**: Uptime 99.9% (월간)
- **장애 복구 시간**: MTTR < 1시간
- **배포 빈도**: 주 1회 이상 (CI/CD)
- **모니터링**: 100% 엔드포인트 모니터링

---

## 📝 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|-----------|--------|
| 2.2 | 2025-10-20 | **기술 스택 업데이트**: Frontend Vanilla JS → React 18 + Vite<br>**P0-1 완료**: 대화내역 조회 기능 구현 완료<br>- ConversationsPage.jsx 추가<br>- /api/v1/admin/conversations/simple 엔드포인트<br>- /api/chat_stream 프록시 (layout.html 연동)<br>- thinking 중복 저장 방지<br>- Apache/GitLab nginx 프록시 설정 | Claude |
| 2.1 | 2025-10-20 | RFP 누락 기능 추가 (개인정보 검출, 학습데이터 범위, A/B 테스트)<br>로드맵 11주로 확장, KPI 상세화 | Claude |
| 2.0 | 2025-10-20 | RFP 요건 중심 재작성, TDD 전략 추가, 한국도로공사 컬러 적용 | Claude |
| 1.0 | 2025-10-18 | 초기 버전 작성 | - |

---

## 🔧 구현 상세 (P0-1: 대화내역 조회)

### 아키텍처

```
Browser (https://ui.datastreams.co.kr:20443)
  ↓
Apache HTTPS Proxy (port 20443)
  ↓ /admin/ → http://172.25.101.91:8010/admin/
Docker: admin-api (port 8010 → container 8001)
  ├── FastAPI Backend
  │   ├── /api/v1/admin/conversations/simple (GET)
  │   ├── /api/v1/admin/conversations/simple/{id} (GET)
  │   └── /api/chat_stream (POST) → vLLM (port 8000)
  └── React Frontend (Vite build)
      ├── /admin/ → index.html
      ├── /admin/assets/ → static files
      └── /admin/conversations → ConversationsPage.jsx
  ↓
PostgreSQL (port 5432)
  └── admin_db.usage_history
```

### 데이터베이스 스키마

```sql
-- usage_history 테이블
CREATE TABLE usage_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    session_id VARCHAR(255),
    conversation_title VARCHAR(255),
    question TEXT NOT NULL,
    answer TEXT,
    thinking_content TEXT,
    model_name VARCHAR(100),
    response_time INTEGER,
    ip_address VARCHAR(45),
    referenced_documents TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_usage_history_created_at ON usage_history(created_at);
CREATE INDEX idx_usage_history_user_id ON usage_history(user_id);
CREATE INDEX idx_usage_history_session_id ON usage_history(session_id);
```

### API 엔드포인트 상세

#### 1. 대화내역 목록 조회
```http
GET /api/v1/admin/conversations/simple?start=2025-10-13&end=2025-10-20&page=1&limit=50

Response 200 OK:
{
  "items": [
    {
      "id": 6055,
      "user_id": "test_user",
      "session_id": "anonymous_1760953031924",
      "question": "감동의 물결이 밀려온다. 라는 노래 가사 누가 부른거야?",
      "answer": "김건모의 노래 《물결》의 가사입니다...",
      "created_at": "2025-10-20T09:53:26.602111Z",
      "response_time": 10999
    }
  ],
  "total": 65,
  "page": 1,
  "limit": 50,
  "total_pages": 2
}
```

#### 2. 대화내역 상세 조회
```http
GET /api/v1/admin/conversations/simple/6055

Response 200 OK:
{
  "id": 6055,
  "user_id": "test_user",
  "session_id": "anonymous_1760953031924",
  "conversation_title": null,
  "question": "감동의 물결이 밀려온다. 라는 노래 가사 누가 부른거야?",
  "answer": "김건모의 노래 《물결》의 가사입니다...",
  "thinking_content": null,
  "model_name": "ex-GPT",
  "response_time": 10999,
  "ip_address": null,
  "referenced_documents": null,
  "created_at": "2025-10-20T09:53:26.602111Z",
  "updated_at": "2025-10-20T09:53:26.602111Z"
}
```

#### 3. 채팅 스트리밍 프록시
```http
POST /api/chat_stream
Content-Type: application/json

{
  "message": "안녕하세요",
  "user_id": "test_user",
  "session_id": "optional_session_id",
  "think_mode": false
}

Response 200 OK (Server-Sent Events):
data: {"type": "token", "content": "안녕"}
data: {"type": "token", "content": "하세요!"}
data: [DONE]
```

### React 컴포넌트 구조

```
react-project/src/
├── pages/
│   └── ConversationsPage.jsx     # 대화내역 조회 페이지
│       ├── 날짜 범위 필터
│       ├── 대화내역 테이블
│       ├── 페이지네이션
│       └── 상세보기 모달
├── utils/
│   └── api.js                     # API 클라이언트
│       ├── apiClient (axios)
│       ├── getConversations()
│       └── getConversationDetail()
└── App.jsx                        # 라우터 설정
    └── Route "/conversations"
```

### 중복 저장 방지 로직

**문제**: vLLM thinking mode에서 2개의 응답 발생
1. `<think>...</think>` (thinking 과정만)
2. 실제 답변

**해결**: app/routers/chat_proxy.py:175
```python
# 스트리밍 완료 후 DB에 저장
# thinking 내용만 있는 경우는 저장하지 않음
if accumulated_response and not accumulated_response.strip().startswith('<think>'):
    await save_usage_to_db(
        db=db,
        user_id=request.user_id,
        session_id=request.session_id,
        question=request.message,
        answer=accumulated_response
    )
```

### 배포 URL

- **Production**: https://ui.datastreams.co.kr:20443/admin/conversations
- **GitLab nginx** (port 443): 현재 미사용 (403 Forbidden 이슈로 20443 사용)
- **Admin API**: http://172.25.101.91:8010 (Docker 내부)
- **vLLM**: http://localhost:8000 (Docker host)

### 문제 해결 이력

1. **Apache ProxyPass 트레일링 슬래시 누락** (해결됨)
   - 문제: `/admin` → `/admin/` 리다이렉트 실패
   - 해결: `/etc/httpd/conf.d/ssl.conf` 수정

2. **GitLab nginx 403 Forbidden** (우회됨)
   - 문제: GitLab nginx가 `/admin/*` 차단
   - 해결: port 20443 사용 (Apache 직접 접근)
   - `/etc/gitlab/gitlab.rb` 수정 (향후 443 포트 활성화 예정)

3. **Thinking 내용 중복 저장** (해결됨)
   - 문제: 한 질문당 2개 레코드 저장 (thinking + 답변)
   - 해결: chat_proxy.py에서 `<think>` 시작 응답 필터링

4. **더미 데이터 표시** (해결됨)
   - 문제: 1,676개 더미 데이터가 실제 데이터 가림
   - 해결: `DELETE FROM usage_history WHERE answer = '답변 내용입니다. (샘플 데이터)';`

---

## 🔗 참조 문서

### RFP 과업지시서
- `/home/aigen/admin-api/docs/RFP.txt`
- FUN-001: 생성형AI 시스템 개선
- FUN-002: 관리도구 기능개선 ⭐ (본 PRD의 주요 대상)
- FUN-003: 학습데이터 갱신 및 추가
- FUN-004: LLM 학습데이터 반영
- FUN-005: 서비스 개선
- FUN-006: 서비스 운영 및 최적화

### 기술 문서
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)
- [OWASP Top 10 - 2021](https://owasp.org/Top10/)
- [Cerbos Authorization](https://cerbos.dev/docs)

### 브랜드 가이드라인
- 한국도로공사 웹사이트: https://www.ex.co.kr
- 주요 컬러: #0a2986 (네이비), #e64701 (오렌지)

### TDD 참고 자료
- [Test-Driven Development by Example](https://www.amazon.com/Test-Driven-Development-Kent-Beck/dp/0321146530)
- [Pytest Documentation](https://docs.pytest.org/)
- [Testing FastAPI Applications](https://fastapi.tiangolo.com/tutorial/testing/)

---

## 💡 추가 고려사항

### 유지보수 용이성을 위한 설계 원칙

1. **코드 가독성**
   - 명확한 네이밍 컨벤션
   - 한글 주석 필수 (한국도로공사 직원들을 위해)
   - Docstring 작성 (Google Style)

2. **모듈화**
   - 단일 책임 원칙 (SRP)
   - 의존성 주입 (Dependency Injection)
   - 레이어 분리 (Controller, Service, Repository)

3. **문서화**
   - API 문서 자동 생성 (OpenAPI/Swagger)
   - 아키텍처 다이어그램 (Mermaid)
   - 온보딩 가이드 작성

4. **버전 관리**
   - Semantic Versioning (MAJOR.MINOR.PATCH)
   - Git Flow 브랜칭 전략
   - 명확한 커밋 메시지 (Conventional Commits)

5. **설정 관리**
   - 환경별 설정 분리 (dev, staging, prod)
   - 12-Factor App 원칙 준수
   - Secrets 중앙 관리

### TDD 실천 가이드

```python
# 예시: 레거시 문서 변경 감지 기능 TDD

# 1단계: RED - 실패하는 테스트 작성
def test_detect_document_changes():
    """레거시 DB에서 변경된 문서를 감지한다"""
    # Given: 레거시 DB에 새로 변경된 문서가 있음
    legacy_db = setup_legacy_db_with_changes()

    # When: 변경 감지 함수 실행
    changes = detect_document_changes(legacy_db)

    # Then: 변경된 문서 목록이 반환됨
    assert len(changes) > 0
    assert changes[0].document_id == "LAW-001"
    assert changes[0].change_type == "updated"

# 2단계: GREEN - 테스트를 통과하는 최소 코드
def detect_document_changes(legacy_db):
    """레거시 DB에서 변경된 문서 감지"""
    # 최소한의 구현
    return legacy_db.query_recent_changes()

# 3단계: REFACTOR - 코드 개선
def detect_document_changes(
    legacy_db: LegacyDatabase,
    since: datetime = None
) -> List[DocumentChange]:
    """
    레거시 DB에서 변경된 문서를 감지합니다.

    Args:
        legacy_db: 레거시 데이터베이스 연결
        since: 이 시점 이후의 변경만 감지 (기본값: 1시간 전)

    Returns:
        변경된 문서 목록

    Raises:
        DatabaseConnectionError: DB 연결 실패 시
    """
    if since is None:
        since = datetime.now() - timedelta(hours=1)

    try:
        changes = legacy_db.query_changes_since(since)
        return [
            DocumentChange.from_db_row(row)
            for row in changes
        ]
    except Exception as e:
        logger.error(f"Failed to detect changes: {e}")
        raise DatabaseConnectionError(str(e))
```
**문서 작성**: 곽두일 PM
**최종 검토**: 곽두일 PM
**승인**: 곽두일 PM
