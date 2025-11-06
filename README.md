# ex-GPT Admin API

한국도로공사 생성형 AI 시스템 관리자 도구

## 📋 프로젝트 구조

```
/home/aigen/admin-api/
├── admin-api/              # FastAPI 백엔드
│   ├── app/               # 애플리케이션 코드
│   │   ├── routers/      # API 라우터
│   │   ├── services/     # 비즈니스 로직
│   │   ├── models/       # SQLAlchemy 모델
│   │   └── core/         # 설정, 데이터베이스
│   ├── docs/             # 프로젝트 문서
│   ├── migrations/       # Alembic 마이그레이션
│   └── tests/            # 테스트 코드
│
├── admin-ui/               # React Admin 프론트엔드 ⭐
│   ├── src/
│   │   ├── pages/        # 페이지 컴포넌트
│   │   ├── layout/       # 레이아웃 컴포넌트
│   │   ├── resources/    # React Admin 리소스
│   │   ├── styles/       # 스타일 (Templates 포함)
│   │   └── utils/        # 유틸리티
│   ├── public/
│   │   └── templates/    # 한국도로공사 Templates
│   └── package.json
│
└── scripts/                # 빌드/배포 스크립트
    ├── build-admin-ui.sh
    └── deploy-admin-ui.sh
```

## 🚀 빠른 시작

### 1. 프론트엔드 개발

```bash
cd /home/aigen/admin-api/admin-ui
npm install
npm run dev
```

개발 서버: http://localhost:5173

### 2. 프론트엔드 빌드

```bash
# 빌드만 실행
bash /home/aigen/admin-api/scripts/build-admin-ui.sh

# 빌드 + 배포
bash /home/aigen/admin-api/scripts/deploy-admin-ui.sh
```

### 3. 백엔드 실행

```bash
cd /home/aigen/admin-api/admin-api
python -m uvicorn app.main:app --reload --port 8010
```

백엔드 API: http://localhost:8010

## 🌐 배포 경로

| 항목 | 경로 |
|------|------|
| **개발 소스** | `/home/aigen/admin-api/admin-ui` |
| **빌드 결과** | `/home/aigen/admin-api/admin-ui/dist` |
| **배포 위치** | `/var/www/html/admin` ⭐ **중요** |
| **접속 URL** | `https://ui.datastreams.co.kr:20443/admin/` |
| **백엔드 API** | `http://localhost:8010/api/v1/admin/` |

⚠️ **주의**: 절대로 `/var/www/html/exGenBotDS/`에 배포하지 마세요!

## 🎨 Templates 디자인 시스템

한국도로공사 공식 디자인 시스템이 적용되어 있습니다.

### 적용된 컴포넌트

- **LoginPage**: 네이비 블루 배경, ex-GPT 로고
- **Button**: 공식 버튼 스타일
- **Input**: 공식 입력 필드 스타일
- **Table**: 공식 테이블 스타일
- **Menu**: 사이드바 메뉴 스타일

### Templates 리소스 위치

```
admin-ui/
├── src/styles/templates/   # CSS 컴포넌트
│   ├── Login/
│   ├── Button/
│   ├── Input/
│   ├── Table/
│   └── ...
└── public/templates/        # 이미지, 폰트
    ├── img/
    └── font/
```

## 🔧 스크립트 사용법

### 빌드 스크립트

```bash
bash /home/aigen/admin-api/scripts/build-admin-ui.sh
```

**기능**:
- 기존 빌드 삭제
- npm run build 실행
- 빌드 결과 확인

### 배포 스크립트

```bash
bash /home/aigen/admin-api/scripts/deploy-admin-ui.sh
```

**기능**:
1. 빌드 실행
2. 기존 파일 백업 (`/tmp/admin-ui-backup-YYYYMMDD-HHMMSS`)
3. 배포 디렉토리 정리
4. 파일 복사
5. 권한 설정
6. 배포 결과 확인

## 📦 주요 기능

### 인증 (Authentication)
- JWT 기반 인증
- 로그인 5회 실패 시 30분 계정 잠금
- 아이디 저장 기능
- 비밀번호 표시/숨기기

### 대시보드
- 실시간 통계
- 사용 현황 차트
- 최근 활동 이력

### 사용자 관리
- 사용자 CRUD
- 권한 관리
- 부서별 필터링

### 문서 관리
- 문서 업로드
- 벡터화 상태 모니터링
- 카테고리 관리

## 🔐 보안

### 구현된 보안 기능

- ✅ bcrypt 비밀번호 해싱
- ✅ JWT 토큰 인증
- ✅ 계정 잠금 (5회 실패 → 30분)
- ✅ XSS 방지 (DOMPurify)
- ✅ CSRF 방지
- ✅ SQL Injection 방지 (Parameterized Queries)

### 보안 설정

```python
# app/core/config.py
SECRET_KEY = "your-secret-key-here"  # 반드시 변경할 것
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
```

## 📚 문서

- [PRD.md](./admin-api/docs/PRD.md) - 제품 요구사항 문서
- [DATABASE_SCHEMA.md](./admin-api/docs/DATABASE_SCHEMA.md) - 데이터베이스 스키마
- [ADMIN_TOOL_FEATURES_PRD.md](./admin-api/docs/ADMIN_TOOL_FEATURES_PRD.md) - 관리도구 상세 기능

## 🐛 트러블슈팅

### 로그인 페이지가 옛날 버전으로 보일 때

```bash
# 1. 빌드 및 배포
bash /home/aigen/admin-api/scripts/deploy-admin-ui.sh

# 2. 브라우저 강제 새로고침
Ctrl+F5 (Windows/Linux)
Cmd+Shift+R (Mac)

# 3. 배포 파일 확인
ls -lah /var/www/html/admin/
```

### MLOps 메뉴가 다시 나타날 때

MLOps 메뉴는 삭제되었습니다. 브라우저 캐시를 삭제하고 강제 새로고침하세요.

### 빌드 실패

```bash
# node_modules 재설치
cd /home/aigen/admin-api/admin-ui
rm -rf node_modules package-lock.json
npm install
npm run build
```

## 🔄 Git 워크플로우

### 변경사항 커밋

```bash
cd /home/aigen/admin-api/admin-api
git add .
git commit -m "feat: 변경 내용 설명"
git push origin mlops-menu-order
```

### 브랜치

- `mlops-menu-order`: 현재 개발 브랜치
- `main`: 프로덕션 브랜치 (미사용)

## 👥 팀

- **개발**: DataStreams
- **발주처**: 한국도로공사 디지털계획처 AI데이터팀

## 📄 라이선스

© 2025 Korea Expressway Corporation Service Co., Ltd. All Rights Reserved.

---

**최종 업데이트**: 2025-11-06
**문서 버전**: 1.0.0
