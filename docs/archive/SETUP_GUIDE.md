# AI Streams 관리도구 설정 가이드

## 프로젝트 개요

과업지시서의 요구사항을 충족하는 엔터프라이즈 AI 플랫폼 관리 시스템입니다.

### 구현된 기능

#### 1. 레거시 시스템 연계
- ✅ 문서 변경 감지를 위한 DB 스키마
- ✅ 제·개정 문서 관리 시스템
- 🔄 자동 동기화 및 승인 기능 (구현 예정)

#### 2. 서비스 관리
- ✅ 사용 이력 추적 시스템
- ✅ 문서 접근 권한 관리 (부서별, 결재라인별)
- ✅ 이용만족도 조사 시스템
- ✅ 공지메시지 관리 시스템

#### 3. 권한 관리
- ✅ Cerbos 정책 기반 접근 제어
- ✅ 역할 기반 접근 제어 (RBAC)
- ✅ 세분화된 리소스 권한

## 프로젝트 구조

```
/home/aigen/
├── admin-api/                 # 백엔드 API 서버
│   ├── app/
│   │   ├── api/              # API 엔드포인트
│   │   │   └── endpoints/
│   │   │       ├── auth.py           # 인증
│   │   │       ├── documents.py      # 문서 관리
│   │   │       ├── usage.py          # 사용 이력
│   │   │       ├── permissions.py    # 권한 관리
│   │   │       ├── notices.py        # 공지사항
│   │   │       └── satisfaction.py   # 만족도 조사
│   │   ├── core/             # 핵심 설정
│   │   │   ├── config.py     # 환경 설정
│   │   │   ├── security.py   # 보안 (JWT, 비밀번호)
│   │   │   └── database.py   # DB 연결
│   │   ├── models/           # SQLAlchemy 모델
│   │   │   ├── user.py       # 사용자
│   │   │   ├── document.py   # 문서
│   │   │   ├── usage.py      # 사용 이력
│   │   │   ├── permission.py # 권한
│   │   │   ├── notice.py     # 공지사항
│   │   │   └── satisfaction.py # 만족도
│   │   ├── schemas/          # Pydantic 스키마
│   │   ├── services/         # 비즈니스 로직
│   │   └── middleware/       # 미들웨어
│   ├── migrations/           # Alembic 마이그레이션
│   ├── policies/             # Cerbos 정책 파일
│   │   ├── config.yaml
│   │   ├── document_policy.yaml
│   │   ├── usage_policy.yaml
│   │   └── notice_policy.yaml
│   ├── tests/                # 테스트
│   ├── docs/                 # 문서
│   │   ├── DATABASE_SCHEMA.md
│   │   └── SETUP_GUIDE.md
│   ├── pyproject.toml        # Poetry 의존성
│   ├── docker-compose.yml    # Docker 설정
│   └── Dockerfile
│
└── html/admin/               # 프론트엔드 (HTML/JS)
    ├── index.html
    ├── css/
    │   └── admin.css
    ├── js/
    │   └── admin.js
    └── pages/
```

## 설치 및 실행

### 1. 환경 설정

```bash
cd /home/aigen/admin-api

# .env 파일 생성
cp .env.example .env

# .env 파일 수정 (데이터베이스 URL, 시크릿 키 등)
```

### 2. Docker로 실행 (권장)

```bash
# 모든 서비스 실행 (PostgreSQL, Redis, Cerbos, API)
docker-compose up -d

# 로그 확인
docker-compose logs -f admin-api

# 중지
docker-compose down
```

### 3. 로컬에서 실행

```bash
# Poetry 설치
curl -sSL https://install.python-poetry.org | python3 -

# 의존성 설치
poetry install

# 데이터베이스 마이그레이션
poetry run alembic upgrade head

# 개발 서버 실행
poetry run uvicorn app.main:app --reload --port 8001
```

### 4. Cerbos 실행 (별도)

```bash
docker run --rm -p 3592:3592 -p 3593:3593 \
  -v $(pwd)/policies:/policies \
  ghcr.io/cerbos/cerbos:latest \
  server --config=/policies/config.yaml
```

## API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## 프론트엔드 접근

관리자 페이지는 다음 경로에서 접근할 수 있습니다:

- 관리자 대시보드: http://localhost/admin/index.html

## 데이터베이스 스키마

전체 데이터베이스 스키마는 `docs/DATABASE_SCHEMA.md` 파일을 참조하세요.

### 주요 테이블

1. **users** - 사용자 정보
2. **documents** - 문서 정보
3. **document_versions** - 문서 버전 관리
4. **document_changes** - 문서 변경 이력
5. **usage_history** - 사용 이력
6. **roles** - 역할
7. **departments** - 부서
8. **approval_lines** - 결재라인
9. **document_permissions** - 문서 권한
10. **notices** - 공지사항
11. **satisfaction_surveys** - 만족도 조사

## Cerbos 정책

### 문서 권한 (document_policy.yaml)

- **admin**: 모든 작업 가능
- **manager**: 읽기, 수정, 승인 가능
- **user**: 자신의 부서 문서만 읽기 가능
- **viewer**: 읽기만 가능

### 사용 이력 권한 (usage_policy.yaml)

- **admin, manager**: 모든 이력 조회 및 내보내기 가능
- **user**: 자신의 이력만 조회 가능

### 공지사항 권한 (notice_policy.yaml)

- **admin, manager**: 생성, 수정, 삭제 가능
- **모든 사용자**: 읽기 가능

## 다음 단계

### 구현 예정 기능

1. **레거시 시스템 연계**
   - 레거시 DB 연결 설정
   - 문서 자동 동기화 스케줄러
   - 변경 감지 알고리즘
   - 관리자 승인 워크플로우

2. **사용 이력 관리**
   - 실시간 이력 수집
   - 통계 대시보드
   - 데이터 내보내기 기능

3. **권한 관리 시스템**
   - Cerbos 통합 완료
   - 부서별 권한 설정 UI
   - 결재라인 관리 UI

4. **만족도 조사**
   - 사용자 피드백 수집
   - 통계 분석 및 시각화

5. **공지사항 관리**
   - 공지사항 CRUD
   - 대상 사용자 지정
   - 표시 기간 관리

## 개발 가이드

### 새로운 API 엔드포인트 추가

1. `app/api/endpoints/`에 새 파일 생성
2. `app/api/__init__.py`에 라우터 등록
3. 필요시 `app/models/`에 모델 추가
4. `app/schemas/`에 Pydantic 스키마 추가

### 데이터베이스 마이그레이션

```bash
# 모델 변경 후 마이그레이션 생성
poetry run alembic revision --autogenerate -m "변경 설명"

# 마이그레이션 적용
poetry run alembic upgrade head

# 롤백
poetry run alembic downgrade -1
```

### Cerbos 정책 추가

1. `policies/` 디렉토리에 YAML 파일 생성
2. Cerbos 서버 재시작 (또는 자동 감지 대기)

## 보안 고려사항

1. `.env` 파일의 `SECRET_KEY`를 반드시 변경
2. 프로덕션 환경에서는 강력한 데이터베이스 비밀번호 사용
3. CORS 설정을 실제 도메인에 맞게 수정
4. JWT 토큰 만료 시간 적절히 설정

## 트러블슈팅

### 데이터베이스 연결 오류

```bash
# PostgreSQL 서비스 확인
docker-compose ps postgres

# 데이터베이스 연결 테스트
docker-compose exec postgres psql -U postgres -d admin_db
```

### Cerbos 연결 오류

```bash
# Cerbos 서비스 확인
docker-compose ps cerbos

# Cerbos 로그 확인
docker-compose logs cerbos
```

## 문의

기술 지원이 필요한 경우 Datastreams 기술팀에 문의하세요.
