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

### 개발 환경
- **관리자 페이지**: http://localhost:8010/admin/
- **API 문서 (Swagger)**: http://localhost:8010/docs
- **API 문서 (ReDoc)**: http://localhost:8010/redoc
- **Health Check**: http://localhost:8010/health/ready

### 프로덕션 환경
- **관리자 페이지**: https://ui.datastreams.co.kr:20443/admin/
- **API 엔드포인트**: https://ui.datastreams.co.kr:20443/api/v1/admin/*

## 주요 기능

### 1. 대시보드 및 통계 📊
- **실시간 통계 대시보드**: 사용자 수, 대화 수, 만족도 등 핵심 지표
- **ex-GPT 사용 통계**: 일별/주별/월별 사용 추이 분석
- **서버 리소스 모니터링**: CPU, 메모리, 디스크, 네트워크 상태
- **반응형 전체 너비 레이아웃**: 1920px 제한 없이 화면 전체 활용

### 2. 배포 관리 시스템 🚀
- **모델 배포**: vLLM 기반 AI 모델 배포 및 관리
- **서비스 모니터링**: 실행 중인 서비스 상태 추적
- **GPU 리소스 관리**: GPU 사용률 및 메모리 모니터링
- **Docker 컨테이너 관리**: 컨테이너 상태 및 로그 확인
- **Health Check**: 서비스 헬스 체크 및 알림

### 3. 대화 및 사용자 관리 💬
- **대화내역 조회**: 필터링, 검색, 엑셀 다운로드
- **사용자 관리**: 사용자 정보, 권한, 승인 처리
- **카테고리 관리**: 대분류/소분류 자동 분류
- **만족도 조사**: 사용자 피드백 수집 및 분석

### 4. 학습 데이터 관리 📚
- **벡터 문서 관리**: RAG 시스템용 문서 업로드 및 관리
- **사전 관리**: 도메인 특화 용어 사전 관리
- **카테고리 생성**: 자동 카테고리 분류 및 관리
- **문서 권한 관리**: 부서별, 결재라인별 문서 접근 제어

### 5. 서비스 관리 ⚙️
- **공지사항 관리**: 공지사항 작성, 수정, 삭제
- **추천 질문 관리**: 자주 묻는 질문 관리
- **오류 보고 관리**: 사용자 오류 신고 처리
- **STT 음성 전사**: 음성 파일 자동 전사 배치 작업

### 6. 권한 및 승인 관리 🔐
- **문서 권한 관리**: 부서별 문서 접근 권한 설정
- **결재라인 관리**: 승인 워크플로우 관리
- **레거시 시스템 연계**: 제·개정 문서 자동 동기화

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

### 주요 문서
- **[ADMIN_TOOL_FEATURES_PRD.md](docs/ADMIN_TOOL_FEATURES_PRD.md)** - 관리 도구 기능 명세
- **[FRONTEND_INTEGRATION_GUIDE.md](docs/FRONTEND_INTEGRATION_GUIDE.md)** - 프론트엔드 통합 가이드
- **[PRODUCTION_DEPLOYMENT_GUIDE.md](docs/PRODUCTION_DEPLOYMENT_GUIDE.md)** - 프로덕션 배포 가이드
- **[STT_INTEGRATION_ARCHITECTURE.md](docs/STT_INTEGRATION_ARCHITECTURE.md)** - STT 통합 아키텍처
- **[STORE_USAGE_GUIDE.md](docs/STORE_USAGE_GUIDE.md)** - 데이터 저장소 사용 가이드

### 아카이브 문서
과거 문서는 `docs/archive/` 디렉토리에서 확인할 수 있습니다.

## 스크린샷

### 메인 대시보드
실시간 통계 및 주요 지표를 한눈에 확인

### 배포 관리
vLLM 모델 배포 및 GPU 리소스 모니터링

### 대화내역 관리
대화 검색, 필터링, 엑셀 다운로드

## 기술적 특징

### 프론트엔드
- ✅ **전체 너비 반응형 레이아웃** - 1920px 제한 제거, 화면 전체 활용
- ✅ **Material-UI 테마** - 라이트/다크 모드 지원
- ✅ **CoreUI 스타일** - 모던하고 직관적인 UI/UX
- ✅ **한국어 지역화** - 완전한 한국어 인터페이스

### 백엔드
- ✅ **비동기 처리** - FastAPI의 async/await 활용
- ✅ **타입 안전성** - Pydantic 스키마 검증
- ✅ **자동 API 문서** - OpenAPI/Swagger 자동 생성
- ✅ **마이그레이션 관리** - Alembic을 통한 DB 버전 관리

## 트러블슈팅

### 전체 너비 레이아웃이 안 보일 때
1. 브라우저 캐시 삭제 (Ctrl+Shift+Delete)
2. 개발자 도구에서 "Disable cache" 활성화
3. 강력 새로고침 (Ctrl+Shift+R)

### Docker 컨테이너 실행 오류
```bash
# 로그 확인
docker-compose logs admin-api

# 컨테이너 재시작
docker-compose restart admin-api
```

### 데이터베이스 연결 오류
```bash
# PostgreSQL 상태 확인
docker-compose ps postgres

# 마이그레이션 재실행
poetry run alembic upgrade head
```

## 라이선스

Copyright (c) 2025 한국도로공사

---

**🎯 프로젝트 상태**: Production Ready
**📅 최종 업데이트**: 2025-10-24
**👥 개발**: 한국도로공사 ex-GPT 팀
