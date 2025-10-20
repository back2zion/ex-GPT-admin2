# Project Requirements Document (PRD)
## AI Streams 관리도구

**버전**: 1.0
**작성일**: 2025-10-18
**프로젝트 코드명**: admin-api

---

## 1. 프로젝트 개요

### 1.1 목적
AI Streams 엔터프라이즈 AI 플랫폼의 관리자 도구 개발
- 서비스 모니터링 및 관리
- 사용 이력 추적 및 분석
- 문서 권한 관리
- 시스템 운영 효율화

### 1.2 배경
과업지시서 요구사항:
1. 레거시 시스템(와이즈넛) DB 연계를 통한 제·개정 문서 확인
2. 서비스 평가 및 개선을 위한 사용 이력 관리
3. 접근 가능 문서 권한 관리 (부서별, 결재라인별)
4. 이용만족도 조사 기능
5. 공지메시지 표출 기능

### 1.3 프로젝트 범위
**In Scope:**
- ✅ 관리자 웹 인터페이스
- ✅ 레거시 DB 연동 및 문서 동기화
- ✅ 사용 이력 조회 및 통계
- ✅ 권한 관리 (Cerbos 기반)
- ✅ 공지사항 CRUD
- ✅ 만족도 조사 수집 및 분석

**Out of Scope:**
- ❌ 사용자용 프론트엔드 (이미 /home/aigen/html/layout.html에 존재)
- ❌ AI 모델 관리
- ❌ 벡터 DB 관리

---

## 2. 사용자 및 이해관계자

### 2.1 주요 사용자
| 역할 | 책임 | 권한 레벨 |
|------|------|-----------|
| **시스템 관리자** | 전체 시스템 관리, 설정 변경 | admin |
| **서비스 관리자** | 공지사항, 문서 승인, 통계 확인 | manager |
| **부서 관리자** | 부서별 사용 이력 조회 | user |
| **감사자** | 읽기 전용 접근 | viewer |

### 2.2 이해관계자
- **발주처**: 한국도로공사 (가정)
- **개발팀**: Datastreams
- **최종 사용자**: 공사 직원 (1,000+ 명)

---

## 3. 기능 요구사항

### 3.1 레거시 시스템 연계 (우선순위: P0 - 최고)

#### 3.1.1 문서 변경 감지
**목표**: 레거시 DB의 제·개정 문서를 자동으로 감지하여 관리자에게 알림

**기능**:
- [ ] 레거시 DB 연결 설정 (PostgreSQL/Oracle)
- [ ] 정기 스케줄러 (1시간 간격)
- [ ] 변경 문서 감지 (법령, 사규, 업무기준)
- [ ] 변경 내용 비교 (diff 생성)
- [ ] 관리자 승인 대기 목록 생성

**입력**:
- 레거시 DB 연결 정보
- 체크 대상 문서 카테고리
- 마지막 체크 시각

**출력**:
- 변경된 문서 목록
- 변경 차이점 (diff)
- 승인 대기 상태

**비기능 요구사항**:
- 성능: 1,000개 문서 비교 < 5분
- 신뢰성: 변경 감지 정확도 99%+

#### 3.1.2 문서 승인 워크플로우
**기능**:
- [ ] 변경 문서 상세 조회
- [ ] 변경 전/후 비교 뷰
- [ ] 승인/반려 처리
- [ ] 승인 시 자동 전처리 반영
- [ ] 승인 이력 기록

**사용자 스토리**:
```
AS A 서비스 관리자
I WANT TO 변경된 문서를 검토하고 승인/반려할 수 있다
SO THAT 부정확한 문서가 시스템에 반영되지 않도록 한다
```

**인수 조건**:
- Given: 변경 감지된 문서가 있을 때
- When: 관리자가 승인 버튼을 클릭하면
- Then: 문서가 벡터 DB에 자동 업데이트된다

---

### 3.2 사용 이력 관리 (우선순위: P0)

#### 3.2.1 이력 수집
**데이터 포인트**:
```json
{
  "user_id": "string",
  "session_id": "string",
  "question": "string",
  "answer": "string",
  "response_time_ms": "number",
  "referenced_documents": ["doc_id_1", "doc_id_2"],
  "model_name": "string",
  "timestamp": "datetime",
  "ip_address": "string"
}
```

**기능**:
- [ ] 실시간 로그 수집 (from ex-gpt API)
- [ ] DB 저장 (PostgreSQL)
- [ ] 개인정보 마스킹 (IP 뒷자리)

#### 3.2.2 이력 조회 및 검색
**필터 옵션**:
- 날짜 범위
- 사용자 ID
- 부서
- 모델명
- 키워드 (질문/답변 내)

**정렬**:
- 최신순/오래된순
- 응답 시간 빠른순/느린순

**페이지네이션**: 100개/페이지

#### 3.2.3 통계 대시보드
**지표**:
- 총 질문 수
- 일별/주별/월별 트렌드
- 평균 응답 시간
- 가장 많이 참조된 문서 TOP 10
- 사용자별 사용량 TOP 10

**시각화**: 차트 라이브러리 (Chart.js 또는 ApexCharts)

#### 3.2.4 데이터 내보내기
**포맷**: CSV, Excel
**필드**: 전체 또는 선택적
**날짜 범위**: 최대 1년

---

### 3.3 권한 관리 (우선순위: P1)

#### 3.3.1 부서 관리
**기능**:
- [ ] 부서 CRUD
- [ ] 부서 계층 구조 (트리)
- [ ] 부서원 할당

**데이터 모델**:
```python
Department:
  - id
  - name
  - code
  - parent_id (자기 참조)
  - description
```

#### 3.3.2 결재라인 관리
**기능**:
- [ ] 결재라인 정의
- [ ] 승인자 순서 설정
- [ ] 문서별 결재라인 매핑

**예시**:
```
결재라인: "계약 관련 문서"
  → 담당자 → 팀장 → 부서장 → 법무팀 검토 → 최종 승인
```

#### 3.3.3 문서 접근 권한 설정
**규칙**:
- 부서별 권한: "A부서는 계약 문서만 읽기"
- 결재라인별 권한: "법무팀은 모든 계약 문서 읽기"
- 사용자별 권한: "홍길동은 특정 문서 수정 가능"

**Cerbos 정책 예시**:
```yaml
resource: document
actions: [read, write, delete]
rules:
  - roles: [admin]
    effect: ALLOW
    actions: ['*']
  - roles: [user]
    effect: ALLOW
    actions: [read]
    condition: request.resource.department == request.principal.department
```

---

### 3.4 공지사항 관리 (우선순위: P2)

#### 3.4.1 공지사항 CRUD
**필드**:
- 제목
- 내용 (Rich Text Editor)
- 우선순위 (낮음/보통/높음/긴급)
- 대상 사용자 (전체/특정 부서/특정 사용자)
- 표시 기간 (시작일~종료일)
- 활성화 여부

**기능**:
- [ ] 목록 조회 (페이지네이션, 검색)
- [ ] 생성
- [ ] 수정
- [ ] 삭제 (soft delete)
- [ ] 미리보기

#### 3.4.2 사용자 페이지 표시
**통합 포인트**: `/home/aigen/html/layout.html`
- [ ] API 엔드포인트: `GET /api/v1/notices/active`
- [ ] 프론트엔드: 모달 또는 배너로 표시
- [ ] 읽음 처리 (쿠키 또는 localStorage)

---

### 3.5 만족도 조사 (우선순위: P2)

#### 3.5.1 피드백 수집
**수집 시점**: 대화 종료 후 (선택적)

**데이터**:
- 평점 (1-5 별)
- 피드백 (자유 텍스트)
- 카테고리 (응답 품질/속도/정확도)

#### 3.5.2 결과 분석
**지표**:
- 평균 평점
- 평점 분포 (1~5별 각각 몇 개)
- 주요 피드백 키워드 (워드클라우드)

**필터**: 날짜 범위, 카테고리

---

## 4. 비기능 요구사항

### 4.1 성능
- **응답 시간**: API 응답 < 200ms (P95)
- **동시 사용자**: 50명 이상 지원
- **대용량 데이터**: 100만 개 이력 조회 시 < 3초

### 4.2 보안
- **인증**: JWT 기반
- **권한**: Cerbos PBAC (Policy-Based Access Control)
- **데이터 암호화**: 민감 정보 (개인정보) 암호화
- **감사 로그**: 모든 관리자 작업 기록

### 4.3 확장성
- **수평 확장**: Docker 컨테이너 기반 (Kubernetes 가능)
- **DB 샤딩**: 사용 이력 테이블 파티셔닝

### 4.4 유지보수성
- **코드 품질**: Black, Ruff 린터 적용
- **테스트**: 단위 테스트 커버리지 > 70%
- **문서화**: API 자동 문서 (Swagger/ReDoc)

---

## 5. 기술 스택 평가

### 5.1 옵션 비교

| 항목 | **Flask-Admin** | **FastAPI (현재)** | **Django Admin** |
|------|----------------|-------------------|-----------------|
| **CRUD 자동화** | ⭐⭐⭐⭐⭐ 완벽 | ⭐⭐ 수동 구현 필요 | ⭐⭐⭐⭐⭐ 완벽 |
| **개발 속도** | ⭐⭐⭐⭐⭐ 매우 빠름 | ⭐⭐⭐ 보통 | ⭐⭐⭐⭐ 빠름 |
| **성능** | ⭐⭐⭐ 동기 | ⭐⭐⭐⭐⭐ 비동기 | ⭐⭐⭐ 동기 |
| **API 문서** | ⭐⭐ 수동 | ⭐⭐⭐⭐⭐ 자동 | ⭐⭐⭐ 수동 |
| **엑셀 내보내기** | ⭐⭐⭐⭐⭐ 기본 제공 | ⭐⭐ 직접 구현 | ⭐⭐⭐⭐ 패키지 |
| **검색/필터** | ⭐⭐⭐⭐⭐ 자동 | ⭐⭐ 직접 구현 | ⭐⭐⭐⭐⭐ 자동 |
| **커스터마이징** | ⭐⭐⭐⭐ 유연 | ⭐⭐⭐⭐⭐ 완전 자유 | ⭐⭐⭐ 제한적 |
| **학습 곡선** | ⭐⭐⭐⭐ 쉬움 | ⭐⭐⭐ 보통 | ⭐⭐ 어려움 |
| **Cerbos 통합** | ⭐⭐⭐⭐ 가능 | ⭐⭐⭐⭐⭐ 쉬움 | ⭐⭐⭐ 가능 |

### 5.2 추천 전략: **하이브리드 접근**

```
┌─────────────────────────────────────┐
│  FastAPI (현재 유지)                 │
│  - API 엔드포인트 제공                │
│  - Cerbos 권한 통합                  │
│  - 비동기 처리 (레거시 DB 동기화)     │
└─────────────────────────────────────┘
              ↓ REST API
┌─────────────────────────────────────┐
│  Flask-Admin (추가)                  │
│  - 빠른 CRUD UI 생성                 │
│  - 엑셀 내보내기                     │
│  - 검색/필터링                       │
└─────────────────────────────────────┘
```

**이유**:
1. **FastAPI**: 레거시 DB 동기화 같은 무거운 작업은 비동기가 유리
2. **Flask-Admin**: 단순 CRUD는 자동 UI로 시간 절약
3. **통합**: Flask-Admin이 FastAPI를 REST 클라이언트로 호출

**구현 방법**:
```python
# Flask-Admin (포트 8011)
from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)
admin = Admin(app)

# FastAPI의 DB 모델 재사용
from admin_api.app.models import Notice, UsageHistory

admin.add_view(ModelView(Notice, db.session))
admin.add_view(ModelView(UsageHistory, db.session))
```

---

## 6. 구현 우선순위 및 타임라인

### Phase 1: MVP (2주)
**목표**: 핵심 기능만 동작

| 기능 | 우선순위 | 예상 시간 |
|------|----------|-----------|
| Flask-Admin 기본 세팅 | P0 | 4시간 |
| 공지사항 CRUD | P0 | 3시간 |
| 사용 이력 조회 (읽기 전용) | P0 | 6시간 |
| 만족도 조사 결과 조회 | P0 | 4시간 |
| **총계** | | **17시간 (2일)** |

### Phase 2: 권한 관리 (1주)
| 기능 | 우선순위 | 예상 시간 |
|------|----------|-----------|
| Cerbos 정책 작성 | P1 | 8시간 |
| 부서 CRUD | P1 | 6시간 |
| 결재라인 CRUD | P1 | 8시간 |
| 문서 권한 설정 UI | P1 | 12시간 |
| **총계** | | **34시간 (4일)** |

### Phase 3: 레거시 연계 (2주)
| 기능 | 우선순위 | 예상 시간 |
|------|----------|-----------|
| 레거시 DB 연결 | P0 | 8시간 |
| 문서 변경 감지 스케줄러 | P0 | 16시간 |
| Diff 생성 (difflib) | P0 | 12시간 |
| 승인 워크플로우 | P0 | 20시간 |
| 자동 전처리 반영 | P0 | 24시간 |
| **총계** | | **80시간 (10일)** |

### Phase 4: 통합 테스트 및 배포 (1주)
| 작업 | 예상 시간 |
|------|-----------|
| 통합 테스트 | 16시간 |
| 버그 수정 | 16시간 |
| 문서화 | 8시간 |
| **총계** | **40시간 (5일)** |

**전체 타임라인**: **171시간 = 약 6주 (여유 포함)**

---

## 7. 성공 지표 (KPI)

### 7.1 개발 목표
- [ ] MVP 배포: 2주 내
- [ ] 전체 기능 완성: 6주 내
- [ ] 테스트 커버리지: > 70%

### 7.2 운영 목표 (출시 후)
- [ ] 관리자 만족도: > 4.0/5.0
- [ ] 시스템 가용성: > 99.5%
- [ ] 문서 변경 감지 정확도: > 99%

---

## 8. 리스크 및 완화 전략

| 리스크 | 영향도 | 확률 | 완화 전략 |
|--------|--------|------|-----------|
| 레거시 DB 스키마 불명확 | 높음 | 중간 | 사전 DB 스키마 문서 요청 |
| Cerbos 학습 곡선 | 중간 | 높음 | 튜토리얼 먼저 완료 (1일) |
| 문서 diff 정확도 낮음 | 높음 | 낮음 | 수동 검증 단계 추가 |
| 성능 이슈 (대용량 이력) | 중간 | 중간 | DB 인덱싱, 페이지네이션 |

---

## 9. 다음 단계

### 즉시 실행
1. ✅ **이 PRD 승인 받기**
2. [ ] **기술 스택 확정**: Flask-Admin 추가 여부 결정
3. [ ] **레거시 DB 접속 정보 확보**
4. [ ] **Phase 1 MVP 시작** (17시간)

### 승인 후
- [ ] Jira/GitHub Issues에 태스크 등록
- [ ] 일일 스탠드업 회의 시작
- [ ] 2주 후 MVP 데모

---

---

## 10. 실수 사례 및 트러블슈팅 가이드

### 10.1 실제 시스템 스펙

#### AI 모델 정보
**실제 사용 모델**: `Qwen/Qwen3-32B-AWQ`

```bash
# 모델 확인 명령
curl http://localhost:8000/v1/models | python3 -m json.tool
```

**환경 변수**:
```env
DEFAULT_MODEL=/models/Qwen3-32B
DEFAULT_EMBEDDINGS_MODEL=/models/Qwen3-Embedding-0.6B
DEFAULT_RERANK_MODEL=/models/bge-reranker-v2-m3
```

**⚠️ 실수 사례**:
- ❌ `Qwen2.5-72B-Instruct` (잘못된 모델명)
- ✅ `Qwen/Qwen3-32B-AWQ` (실제 모델명)

**교훈**: 하드코딩 전 실제 시스템 스펙 반드시 확인

---

### 10.2 Docker 네트워킹 실수

#### 문제 1: MinIO 연결 실패

**증상**: `Connection refused to localhost:10002`

**실수**:
```yaml
environment:
  - MINIO_ENDPOINT=localhost:10002  # ❌
```

**원인**: Docker 컨테이너 내부에서 `localhost`는 컨테이너 자신을 가리킴

**해결**:
```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"  # ⭐ 필수!
environment:
  - MINIO_ENDPOINT=host.docker.internal:10002  # ✅
  - MINIO_ACCESS_KEY=admin
  - MINIO_SECRET_KEY=admin123
```

**검증**:
```bash
# 컨테이너 내부에서 호스트 접근 테스트
docker exec admin-api-admin-api-1 curl -I http://host.docker.internal:10002/minio/health/live
```

**교훈**: Docker 컨테이너에서 호스트 서비스 접근 시 반드시 `host.docker.internal` 사용

---

#### 문제 2: 잘못된 MinIO 크레덴셜

**실수**: 기본 크레덴셜 `minioadmin/minioadmin` 사용

**확인 방법**:
```bash
docker exec ex-gpt-minio-1 env | grep MINIO_ROOT
```

**실제 크레덴셜**: `admin/admin123`

**교훈**: 환경 변수 확인 후 설정

---

### 10.3 데이터베이스 필드명 오류

#### 문제: AttributeError

**실수**:
```python
"version": doc.version  # ❌ AttributeError: 'Document' object has no attribute 'version'
```

**원인**: 모델 정의는 `current_version`인데 잘못된 필드명 사용

**해결**:
```python
"version": doc.current_version  # ✅
```

**검증**:
```bash
# 모델 정의 확인
grep -n "class Document" /home/aigen/admin-api/app/models/document.py -A 30
```

**교훈**: API 코드 작성 전 모델 정의 반드시 확인

---

### 10.4 nginx 프록시 설정 누락

#### 문제: 사용 이력 로깅 실패

**증상**: layout.html에서 질문했지만 admin 도구에 이력이 나타나지 않음

**브라우저 개발자 도구**:
```
POST https://ui.datastreams.co.kr:20443/api/v1/usage/log
Status: 404 Not Found
```

**실수**: `/api/v1/documents/`만 프록시 설정, `/api/v1/usage/` 누락

**해결**: `/opt/ex-gpt-admin/config/nginx.conf`
```nginx
# admin-api (사용 이력 로깅) ⭐ 이 부분 누락으로 인한 버그!
location /api/v1/usage/ {
    proxy_pass http://host.docker.internal:8010/api/v1/usage/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_connect_timeout 30s;
    proxy_read_timeout 30s;
    proxy_send_timeout 30s;
}
```

**재시작 필수**:
```bash
docker restart ex-gpt-admin-web
```

**검증**:
```bash
# nginx 설정 테스트
docker exec ex-gpt-admin-web nginx -t

# 프록시 동작 테스트
curl -X POST "http://localhost:28091/api/v1/usage/log" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"테스트","answer":"답변","response_time":500}'
```

**교훈**:
- 새 API 엔드포인트 추가 시 nginx 설정도 함께 업데이트
- 체크리스트 작성: [ ] API 구현 [ ] nginx 설정 [ ] 테스트

---

### 10.5 환경 변수 미반영

#### 문제: .env 수정 후에도 변경사항 적용 안 됨

**실수**:
```bash
# ❌ restart는 환경 변수를 다시 로드하지 않음
docker-compose restart admin-api
```

**해결**:
```bash
# ✅ 컨테이너를 완전히 재생성
cd /home/aigen/admin-api
docker-compose down
docker-compose up -d
```

**또는 직접 환경 변수 오버라이드**:
```python
# app/api/endpoints/documents.py
import os

storage_service = StorageService(
    endpoint=os.getenv("MINIO_ENDPOINT", settings.MINIO_ENDPOINT),
    access_key=os.getenv("MINIO_ACCESS_KEY", settings.MINIO_ACCESS_KEY),
    secret_key=os.getenv("MINIO_SECRET_KEY", settings.MINIO_SECRET_KEY),
    secure=os.getenv("MINIO_SECURE", "false").lower() == "true"
)
```

**교훈**: 환경 변수 변경 시 항상 `down` → `up -d`

---

### 10.6 테스트 데이터와 실제 데이터 혼용

#### 문제: 관리 도구에 더미 데이터가 표시됨

**증상**: `user_1`, `user_2`, `test_user` 같은 테스트 데이터가 섞여 있음

**해결**:
```bash
# 테스트 데이터 정리
docker exec admin-api-postgres-1 psql -U postgres -d admin_db -c "
DELETE FROM usage_history
WHERE user_id LIKE 'test%' OR user_id LIKE 'user_%' OR user_id = 'nginx_test';
"
```

**교훈**: 프로덕션 배포 전 테스트 데이터 완전 정리

---

### 10.7 layout.html 자동 로깅 누락

#### 문제: 실제 사용자 질문이 기록되지 않음

**원인**: layout.html의 `sendMessage()` 함수에 로깅 코드 누락

**해결**: `/home/aigen/html/layout.html` (line 4950~4986)
```javascript
// admin-api에 사용 이력 로깅 (관리 도구 연동)
try {
    const logUrl = `${CONFIG.API.ADMIN_API_URL}/api/v1/usage/log`;
    const logData = {
        user_id: CONFIG.API.USER_ID || 'anonymous',
        session_id: sessionId,
        question: message,
        answer: finalResponseText,
        response_time: endTime - startTime,  // 밀리초
        referenced_documents: sources.map(s => s.id || s.title).filter(Boolean),
        model_name: metadata?.model || 'Qwen/Qwen3-32B-AWQ',  // ⭐ 실제 모델명
        usage_metadata: {
            file_count: attachedFiles.length,
            source_count: sources.length,
            metadata: metadata
        }
    };

    fetch(logUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(logData)
    }).then(res => {
        if (res.ok) {
            console.log('✅ 사용 이력 로깅 성공');
        }
    }).catch(err => {
        console.warn('⚠️ 사용 이력 로깅 오류:', err);
    });
} catch (logError) {
    console.warn('⚠️ 사용 이력 로깅 예외:', logError);
}
```

**브라우저 디버깅**:
```javascript
// F12 → Console 탭에서 확인
// ✅ 사용 이력 로깅 성공
```

**교훈**: 프론트엔드와 백엔드 연동 시 실제 호출 여부 확인 필수

---

### 10.8 CORS 에러

#### 문제: Mixed Content 또는 CORS 차단

**증상**:
```
Access to fetch at 'http://localhost:8010/api/v1/usage/log' from origin 'https://ui.datastreams.co.kr:20443'
has been blocked by CORS policy
```

**원인**: HTTPS → HTTP 요청이 브라우저에서 차단됨

**해결 1**: nginx 프록시 사용 (권장)
```nginx
# 같은 도메인/프로토콜로 프록시
location /api/v1/usage/ {
    proxy_pass http://host.docker.internal:8010/api/v1/usage/;
}
```

**해결 2**: CORS 헤더 추가 (비권장 - 보안 이슈)
```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ui.datastreams.co.kr:20443"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**교훈**: HTTPS 환경에서는 항상 프록시 사용

---

### 10.9 pydantic ALLOWED_ORIGINS 파싱 에러

#### 문제: admin-api 컨테이너 시작 실패

**증상**:
```
pydantic_settings.exceptions.SettingsError: error parsing value for field "ALLOWED_ORIGINS" from source "EnvSettingsSource"
```

**원인**: pydantic v2는 comma-separated 문자열을 자동으로 List[str]로 파싱하지 않음

**실수 1**: docker-compose.yml에 환경 변수로 설정
```yaml
# ❌ 이렇게 하면 pydantic이 파싱 실패
environment:
  - ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

**실수 2**: .env 파일에 comma-separated 문자열
```env
# ❌ 이것도 파싱 실패
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

**해결**:
```yaml
# docker-compose.yml에서 ALLOWED_ORIGINS 제거
# config.py의 기본값 사용

# app/core/config.py
class Settings(BaseSettings):
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8010",
        "https://ui.datastreams.co.kr:20443",
        "http://ui.datastreams.co.kr:20443",
        "https://ui.datastreams.co.kr",
        "http://ui.datastreams.co.kr"
    ]
```

**재시작**:
```bash
cd /home/aigen/admin-api
docker-compose up -d admin-api
```

**검증**:
```bash
# admin-api 로그 확인
docker logs admin-api-admin-api-1 2>&1 | grep "Uvicorn running"
# ✅ INFO:     Uvicorn running on http://0.0.0.0:8001

# CORS 테스트
curl -X POST "http://localhost:8010/api/v1/usage/log" \
  -H "Origin: https://ui.datastreams.co.kr:20443" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"테스트","answer":"답변","response_time":500}' \
  -v 2>&1 | grep "access-control-allow-origin"
# ✅ < access-control-allow-origin: https://ui.datastreams.co.kr:20443
```

**교훈**:
- pydantic-settings v2에서는 List 타입은 기본값을 Python 리스트로 정의
- 환경 변수로 List를 전달하려면 JSON 형식 또는 field_validator 필요
- 간단한 경우 config.py에 기본값 정의하는 것이 가장 안전

---

### 10.10 잘못된 서버 IP 주소

#### 문제: 직접 IP 연결 시도 시 connection timeout

**증상**:
```bash
curl: (7) Failed to connect to 10.253.215.54 port 8010: 연결 시간 초과
```

**실수**: layout.html에 잘못된 IP 사용
```javascript
// ❌ 10.253.215.54는 Oracle 서버!
ADMIN_API_URL: window.location.hostname === 'localhost'
    ? 'http://localhost:8010'
    : 'http://10.253.215.54:8010',
```

**원인**: .env에서 LEGACY_ORACLE_HOST 값을 잘못 참조

**서버 IP 확인**:
```bash
ip addr show | grep "inet " | grep -v "127.0.0.1"
# inet 172.25.101.91/24 brd 172.25.101.255 scope global noprefixroute eno1
```

**해결**:
```javascript
// ✅ 올바른 서버 IP
ADMIN_API_URL: window.location.hostname === 'localhost'
    ? 'http://localhost:8010'
    : 'http://172.25.101.91:8010',  // 서버 내부 IP (10.253.215.54는 Oracle 서버)
```

**검증**:
```bash
# 올바른 IP로 테스트
curl -X POST "http://172.25.101.91:8010/api/v1/usage/log" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"테스트","answer":"답변","response_time":500}' \
  -w "\nHTTP Status: %{http_code}\n"
# HTTP Status: 200
```

**교훈**:
- IP 주소 하드코딩 전 반드시 `ip addr show` 또는 `ifconfig`로 확인
- .env 파일의 다른 서비스 IP를 잘못 참조하지 않도록 주의
- 가능하면 도메인 또는 nginx 프록시 사용 (IP 변경 시 영향 최소화)

---

## 11. 체크리스트

### 새 기능 추가 시

- [ ] 데이터베이스 모델 정의 확인
- [ ] API 엔드포인트 구현
- [ ] nginx 프록시 설정 추가
- [ ] 프론트엔드 연동 코드 작성
- [ ] 브라우저 개발자 도구로 API 호출 확인
- [ ] 데이터베이스에 실제 데이터 저장 확인
- [ ] 테스트 데이터 정리
- [ ] 문서 업데이트 (PRD.md)

### 배포 전

- [ ] 환경 변수 검증 (.env, docker-compose.yml)
- [ ] Docker 네트워킹 검증 (extra_hosts)
- [ ] nginx 설정 검증 (`nginx -t`)
- [ ] API 응답 테스트 (curl)
- [ ] 브라우저 E2E 테스트
- [ ] 로그 확인 (`docker logs`)
- [ ] 테스트 데이터 완전 삭제

---

## 12. 빠른 참조

### 자주 사용하는 명령어

```bash
# 1. 컨테이너 재시작
cd /home/aigen/admin-api && docker-compose down && docker-compose up -d

# 2. nginx 재시작
docker restart ex-gpt-admin-web

# 3. 로그 확인
docker logs -f admin-api-admin-api-1

# 4. DB 직접 조회
docker exec admin-api-postgres-1 psql -U postgres -d admin_db -c "SELECT * FROM usage_history ORDER BY created_at DESC LIMIT 5;"

# 5. 테스트 데이터 삭제
docker exec admin-api-postgres-1 psql -U postgres -d admin_db -c "DELETE FROM usage_history;"

# 6. API 테스트
curl http://localhost:8010/api/v1/usage/history | python3 -m json.tool
```

### 주요 파일 위치

```
/home/aigen/admin-api/
├── app/models/usage.py              # 사용 이력 모델
├── app/api/endpoints/usage.py       # 사용 이력 API
├── docker-compose.yml               # Docker 설정
└── .env                             # 환경 변수

/home/aigen/html/
├── layout.html                      # 사용자 화면 (로깅 코드: line 4950~4986)
└── admin/js/admin.js                # 관리 도구 UI

/opt/ex-gpt-admin/config/
└── nginx.conf                       # nginx 프록시 설정
```

---

**문서 버전 이력**:
- v1.0 (2025-10-18): 초안 작성
- v1.1 (2025-10-18): 실수 사례 및 트러블슈팅 가이드 추가
- v1.2 (2025-10-18): pydantic ALLOWED_ORIGINS 파싱 에러, 서버 IP 주소 오류 트러블슈팅 추가

**작성자**: Claude (Datastreams AI Assistant)
**검토자**: [이름]
**승인자**: [이름]
