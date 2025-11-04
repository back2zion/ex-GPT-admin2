# ex-GPT Admin Monorepo

한국도로공사 ex-GPT 프로젝트의 통합 저장소입니다.

## 📁 프로젝트 구조

```
ex-gpt-admin/
├── admin-ui/          # 관리자 도구 프론트엔드 (React + React Admin)
├── admin-api/         # 관리자 도구 백엔드 (Python FastAPI)
└── user-app/          # 사용자 UI (Java Spring Boot + HTML)
    └── new-exgpt-ui/  # 사용자 UI 프론트엔드
```

## 🚀 프로젝트별 설명

### admin-ui/ - 관리자 도구 프론트엔드
- **기술 스택**: React 19, React Admin 5, Vite, Material-UI
- **포트**: 개발 5173, 배포 /admin
- **배포 위치**: `/var/www/html/admin/`
- **상세**: [admin-ui/README.md](./admin-ui/README.md)

### admin-api/ - 관리자 도구 백엔드
- **기술 스택**: Python 3.11, FastAPI, PostgreSQL, Qdrant
- **포트**: 8010
- **주요 기능**:
  - 대화 내역 관리
  - 문서 업로드/벡터화
  - 사용자 권한 관리
  - 통계 대시보드
- **상세**: [admin-api/README.md](./admin-api/README.md)

### user-app/ - 사용자 UI
- **기술 스택**: Java 17, Spring Boot 3.2, Thymeleaf
- **포트**: 8080
- **주요 기능**:
  - SSO 인증
  - 채팅 인터페이스
  - 파일 업로드
  - 대화 히스토리
- **프론트엔드**: `new-exgpt-ui/` (HTML/CSS/JS)
- **상세**: [user-app/README.md](./user-app/README.md)

## 🔧 개발 환경 설정

### 1. admin-ui (React)
```bash
cd admin-ui
npm install
npm run dev    # http://localhost:5173
npm run build  # dist/ 폴더에 빌드
```

### 2. admin-api (Python)
```bash
cd admin-api
poetry install
poetry run uvicorn app.main:app --reload --port 8010
```

### 3. user-app (Java)
```bash
cd user-app
./mvnw spring-boot:run
```

## 📦 배포

### Apache 설정
```apache
# /etc/httpd/conf.d/exgpt.conf
<VirtualHost *:20443>
    # React 관리도구
    Alias /admin /var/www/html/admin

    # FastAPI 백엔드
    ProxyPass /api http://localhost:8010/api
    ProxyPassReverse /api http://localhost:8010/api

    # Java Spring Boot 사용자 UI
    ProxyPass / http://localhost:8080/
    ProxyPassReverse / http://localhost:8080/
</VirtualHost>
```

### 빌드 & 배포 스크립트
```bash
# admin-ui 빌드 및 배포
cd admin-ui && npm run build && cp -r dist/* /var/www/html/admin/

# admin-api 재시작
docker restart admin-api

# user-app 재시작
cd user-app && ./mvnw spring-boot:stop && ./mvnw spring-boot:start
```

## 🔐 환경 변수

각 프로젝트별 `.env.example` 파일 참조

## 📝 라이선스

Copyright (c) 2025 데이터스트림즈
