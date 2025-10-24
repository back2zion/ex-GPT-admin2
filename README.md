# ex-GPT Admin API

한국도로공사 ex-GPT AI 시스템 관리자 도구

## 프로젝트 구조

```
admin-api/
├── app/                    # FastAPI 백엔드 애플리케이션
│   ├── api/               # API 엔드포인트
│   ├── core/              # 핵심 설정 및 보안
│   ├── models/            # SQLAlchemy 모델
│   ├── schemas/           # Pydantic 스키마
│   ├── routers/           # 라우터 (admin, user API)
│   ├── services/          # 비즈니스 로직
│   └── middleware/        # 미들웨어
├── frontend/              # React Admin 프론트엔드
│   ├── src/               # React 소스 코드
│   ├── public/            # 정적 파일
│   ├── package.json       # npm 의존성
│   └── vite.config.js     # Vite 빌드 설정
├── migrations/            # Alembic 데이터베이스 마이그레이션
├── policies/              # Cerbos 권한 정책 파일
├── tests/                 # 테스트 코드
├── docs/                  # 프로젝트 문서
├── scripts/               # 유틸리티 스크립트
├── deployment/            # 배포 설정 (Apache, Nginx 등)
├── docker-compose.yml     # Docker Compose 설정
└── pyproject.toml         # Python 의존성 (Poetry)
```

## 기술 스택

### 백엔드
- **Framework**: FastAPI
- **Database**: PostgreSQL 15
- **Authorization**: Cerbos (PBAC)
- **Cache**: Redis 7
- **Migration**: Alembic
- **Authentication**: JWT

### 프론트엔드
- **Framework**: React 19 + React Admin 5
- **Build Tool**: Vite
- **UI Library**: Material-UI (MUI)
- **Language**: JavaScript (ES6+)

## 설치 및 실행

### Docker로 실행 (권장)

```bash
# 1. 환경 변수 설정
cp .env.example .env
# .env 파일 편집

# 2. Docker Compose로 전체 서비스 실행
docker-compose up -d

# 3. 서비스 확인
docker-compose ps
```

### 로컬에서 실행

#### 백엔드 (FastAPI)

```bash
# 1. 의존성 설치
poetry install

# 2. 데이터베이스 마이그레이션
poetry run alembic upgrade head

# 3. 개발 서버 실행
poetry run uvicorn app.main:app --reload --port 8001
```

#### 프론트엔드 (React)

```bash
# 1. 프론트엔드 디렉토리로 이동
cd frontend

# 2. 의존성 설치
npm install

# 3. 개발 서버 실행
npm run dev

# 4. 프로덕션 빌드
npm run build
```

## 접속 URL

- **관리자 페이지**: http://localhost:8010/admin/
- **API 문서 (Swagger)**: http://localhost:8010/docs
- **API 문서 (ReDoc)**: http://localhost:8010/redoc

## 주요 기능

### 1. 레거시 시스템 연계
- 제·개정 문서 변경 감지 및 동기화
- 법령, 사규, 업무기준 등 문서 관리
- 변경된 부분만 자동 전처리 반영

### 2. 서비스 관리
- 사용 이력 추적 (질문/답변/시각)
- 문서 접근 권한 관리 (부서별, 결재라인별)
- 이용만족도 조사
- 공지메시지 관리
- STT(음성인식) 배치 작업 관리

### 3. 권한 관리
- Cerbos 기반 정책 기반 접근 제어 (PBAC)
- 역할 기반 접근 제어 (RBAC)
- 세분화된 리소스별 권한 관리

### 4. 통계 및 모니터링
- ex-GPT 사용 통계 대시보드
- 서버 리소스 모니터링
- 오류 보고 및 추적

## 개발 가이드

### 백엔드 API 추가

1. `app/models/` - SQLAlchemy 모델 정의
2. `app/schemas/` - Pydantic 스키마 정의
3. `app/routers/admin/` - API 라우터 구현
4. `migrations/` - 데이터베이스 마이그레이션 생성

```bash
poetry run alembic revision --autogenerate -m "설명"
poetry run alembic upgrade head
```

### 프론트엔드 리소스 추가

1. `frontend/src/resources/` - React Admin 리소스 컴포넌트
2. `frontend/src/App.jsx` - Resource 등록
3. `frontend/src/layout/CoreUIMenu.jsx` - 메뉴 추가

### 유틸리티 스크립트

```bash
# 관리자 계정 생성
python scripts/create_admin_user.py

# 테스트 데이터 삽입
python scripts/insert_test_data.py

# 관리자 비밀번호 재설정
python scripts/reset_admin_password.py
```

## 문서

프로젝트 관련 상세 문서는 `docs/` 디렉토리를 참조하세요:

- `docs/MIGRATION_PRD.md` - 마이그레이션 PRD
- `docs/IMPLEMENTATION_PLAN.md` - 구현 계획
- `docs/DATABASE_SCHEMA.md` - 데이터베이스 스키마
- `docs/PRODUCTION_DEPLOYMENT_GUIDE.md` - 프로덕션 배포 가이드

## 라이선스

Copyright (c) 2025 한국도로공사
