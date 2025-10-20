# AI Streams Admin API

관리자 도구 백엔드 API 서버

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

### 3. 권한 관리
- Cerbos 기반 정책 기반 접근 제어 (PBAC)
- 역할 기반 접근 제어 (RBAC)
- 세분화된 리소스별 권한 관리

## 기술 스택

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **Authorization**: Cerbos
- **Cache**: Redis
- **Migration**: Alembic
- **Authentication**: JWT

## 프로젝트 구조

```
admin-api/
├── app/
│   ├── api/              # API 엔드포인트
│   ├── core/             # 핵심 설정 및 보안
│   ├── models/           # SQLAlchemy 모델
│   ├── schemas/          # Pydantic 스키마
│   ├── services/         # 비즈니스 로직
│   └── middleware/       # 미들웨어
├── migrations/           # Alembic 마이그레이션
├── policies/             # Cerbos 정책 파일
└── tests/                # 테스트
```

## 설치 및 실행

### 1. 의존성 설치
```bash
poetry install
```

### 2. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일 수정
```

### 3. 데이터베이스 마이그레이션
```bash
poetry run alembic upgrade head
```

### 4. 개발 서버 실행
```bash
poetry run uvicorn app.main:app --reload --port 8001
```

## Docker 실행

```bash
docker-compose up -d
```

## API 문서

개발 서버 실행 후:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc
