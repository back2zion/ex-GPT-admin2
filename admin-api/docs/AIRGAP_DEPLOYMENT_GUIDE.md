# 폐쇄망(Air-Gap) 환경 배포 가이드

내부망(폐쇄망)에서 Admin API 시스템을 구축하기 위한 완벽 가이드입니다.

## 개요

이 시스템은 **완전 오프라인 환경에서 배포 가능**하도록 설계되었습니다. 모든 의존성을 사전에 패키징하여 내부망에 반입할 수 있습니다.

## 폐쇄망 반입 체크리스트

### ✅ 1단계: 외부망에서 준비 (반출용 서버)

#### A. Docker 이미지 저장

```bash
# 1. 모든 이미지 pull
cd /home/aigen/admin-api

# Base images
docker pull python:3.11-slim
docker pull postgres:15-alpine
docker pull redis:7-alpine
docker pull ghcr.io/cerbos/cerbos:latest

# 2. 로컬 이미지 빌드
docker-compose build

# 3. 모든 이미지를 tar 파일로 저장
docker save python:3.11-slim -o python-3.11-slim.tar
docker save postgres:15-alpine -o postgres-15-alpine.tar
docker save redis:7-alpine -o redis-7-alpine.tar
docker save ghcr.io/cerbos/cerbos:latest -o cerbos-latest.tar
docker save admin-api-admin-api:latest -o admin-api-admin-api.tar
docker save admin-api-user-api:latest -o admin-api-user-api.tar

# 4. 압축 (선택 사항 - 용량 절약)
gzip python-3.11-slim.tar
gzip postgres-15-alpine.tar
gzip redis-7-alpine.tar
gzip cerbos-latest.tar
gzip admin-api-admin-api.tar
gzip admin-api-user-api.tar
```

**예상 용량**: 약 2~3GB (압축 시 1~1.5GB)

#### B. Python 패키지 저장 (Offline pip)

```bash
# 1. 모든 Python 의존성 다운로드
cd /home/aigen/admin-api
poetry export -f requirements.txt --output requirements.txt --without-hashes

# 2. pip download로 wheel 파일 다운로드
mkdir -p offline_packages/python
pip download -r requirements.txt -d offline_packages/python

# 3. Poetry 자체도 다운로드
pip download poetry -d offline_packages/python
```

**예상 용량**: 약 500MB~1GB

#### C. Node.js 패키지 저장 (Offline npm)

```bash
# 1. Frontend 패키지 다운로드
cd /home/aigen/admin-api/frontend
npm ci

# 2. node_modules를 tar로 압축
tar -czf node_modules.tar.gz node_modules

# 3. package-lock.json 포함 확인
cp package-lock.json ../offline_packages/
```

**예상 용량**: 약 200~400MB (압축 시 50~100MB)

#### D. 전체 소스코드 패키징

```bash
cd /home/aigen
tar --exclude='admin-api/node_modules' \
    --exclude='admin-api/.venv' \
    --exclude='admin-api/__pycache__' \
    --exclude='admin-api/.git' \
    --exclude='admin-api/frontend/dist' \
    -czf admin-api-source.tar.gz admin-api/
```

#### E. 배포 패키지 구조

```
airgap-deployment/
├── docker-images/
│   ├── python-3.11-slim.tar.gz
│   ├── postgres-15-alpine.tar.gz
│   ├── redis-7-alpine.tar.gz
│   ├── cerbos-latest.tar.gz
│   ├── admin-api-admin-api.tar.gz
│   └── admin-api-user-api.tar.gz
├── offline_packages/
│   ├── python/
│   │   └── *.whl (모든 Python wheel 파일)
│   └── node_modules.tar.gz
├── admin-api-source.tar.gz
├── deploy.sh (배포 스크립트)
└── README.txt
```

**전체 예상 용량**: 약 3~5GB

---

### ✅ 2단계: 내부망으로 반입 (USB/DVD/내부 파일 전송)

#### 반입 방법

1. **USB 드라이브**: 8GB 이상 권장
2. **DVD/Blu-ray**: 다중 디스크 가능
3. **내부 파일 전송 시스템**: 기관의 승인된 파일 반입 절차 활용

#### 보안 검토 체크리스트

- [ ] 악성코드 스캔 완료
- [ ] 소스코드 보안 감사 완료
- [ ] 의존성 라이브러리 검증 완료
- [ ] 라이선스 확인 (모든 패키지 MIT/Apache 등 오픈소스)
- [ ] 개인정보/민감정보 미포함 확인
- [ ] 암호화 모듈 사용 승인 (bcrypt, JWT 등)

---

### ✅ 3단계: 내부망에서 설치

#### A. Docker 이미지 로드

```bash
cd /path/to/airgap-deployment/docker-images

# 압축 해제 및 이미지 로드
gunzip *.tar.gz
docker load -i python-3.11-slim.tar
docker load -i postgres-15-alpine.tar
docker load -i redis-7-alpine.tar
docker load -i cerbos-latest.tar
docker load -i admin-api-admin-api.tar
docker load -i admin-api-user-api.tar

# 확인
docker images
```

#### B. 소스코드 배포

```bash
cd /opt  # 또는 적절한 설치 경로
tar -xzf /path/to/admin-api-source.tar.gz
cd admin-api
```

#### C. Python 패키지 설치 (오프라인)

```bash
# Poetry 설치
pip install --no-index --find-links=/path/to/offline_packages/python poetry

# 프로젝트 의존성 설치
poetry config virtualenvs.create false
pip install --no-index --find-links=/path/to/offline_packages/python -r requirements.txt
```

#### D. Frontend 빌드 (오프라인)

```bash
cd /opt/admin-api/frontend

# node_modules 압축 해제
tar -xzf /path/to/offline_packages/node_modules.tar.gz

# 빌드
npm run build
```

#### E. 환경 변수 설정

```bash
cd /opt/admin-api
cp .env.example .env
vi .env  # 내부망 환경에 맞게 수정
```

**중요 설정**:
```bash
# 데이터베이스 (내부 PostgreSQL 서버)
DATABASE_URL=postgresql+asyncpg://user:password@internal-db:5432/admin_db

# Spring Boot (내부 Tomcat)
SPRING_BOOT_URL=http://internal-tomcat:18180/exGenBotDS

# 외부 인터넷 연결 불필요
# 모든 서비스가 내부망 IP/도메인 사용
```

#### F. Docker Compose로 실행

```bash
cd /opt/admin-api

# 네트워크 생성 (필요시)
docker network create exgpt_net

# 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f admin-api
```

---

## 외부 의존성 분석

### 인터넷 연결이 필요한 부분

#### ❌ **없음** - 완전 오프라인 가능!

모든 구성요소가 폐쇄망에서 동작합니다:

1. **Python 패키지**: 사전 다운로드한 wheel 파일로 설치
2. **Node.js 패키지**: node_modules를 통째로 반입
3. **Docker 이미지**: tar 파일로 저장 후 load
4. **데이터베이스**: 내부 PostgreSQL 사용
5. **인증**: Spring Boot 세션 (내부망)
6. **AI 모델**: 이미 내부망에 배포된 vLLM/Qdrant 사용

### 선택적 외부 연결

다음 기능은 **외부망 연결 시에만** 동작 (없어도 시스템 정상 작동):

- **없음** - 모든 기능이 내부망에서 완결됨

---

## 폐쇄망 배포 자동화 스크립트

### 1. 외부망 준비 스크립트 (export.sh)

```bash
#!/bin/bash
set -e

echo "=== Admin API 폐쇄망 배포 패키지 생성 ==="

EXPORT_DIR="admin-api-airgap-$(date +%Y%m%d)"
mkdir -p "$EXPORT_DIR"/{docker-images,offline_packages/python}

# Docker 이미지 저장
echo "1. Docker 이미지 저장 중..."
docker pull python:3.11-slim
docker pull postgres:15-alpine
docker pull redis:7-alpine
docker pull ghcr.io/cerbos/cerbos:latest

docker-compose build

docker save python:3.11-slim | gzip > "$EXPORT_DIR/docker-images/python-3.11-slim.tar.gz"
docker save postgres:15-alpine | gzip > "$EXPORT_DIR/docker-images/postgres-15-alpine.tar.gz"
docker save redis:7-alpine | gzip > "$EXPORT_DIR/docker-images/redis-7-alpine.tar.gz"
docker save ghcr.io/cerbos/cerbos:latest | gzip > "$EXPORT_DIR/docker-images/cerbos-latest.tar.gz"
docker save admin-api-admin-api:latest | gzip > "$EXPORT_DIR/docker-images/admin-api.tar.gz"

# Python 패키지 다운로드
echo "2. Python 패키지 다운로드 중..."
poetry export -f requirements.txt --output requirements.txt --without-hashes
pip download -r requirements.txt -d "$EXPORT_DIR/offline_packages/python"
pip download poetry -d "$EXPORT_DIR/offline_packages/python"

# Frontend 패키지
echo "3. Frontend 패키지 압축 중..."
cd frontend
npm ci
tar -czf "../$EXPORT_DIR/offline_packages/node_modules.tar.gz" node_modules
cd ..

# 소스코드 압축
echo "4. 소스코드 압축 중..."
tar --exclude='node_modules' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='frontend/dist' \
    -czf "$EXPORT_DIR/admin-api-source.tar.gz" .

# 배포 스크립트 복사
cp docs/AIRGAP_DEPLOYMENT_GUIDE.md "$EXPORT_DIR/README.md"

# 전체 압축
echo "5. 전체 패키지 압축 중..."
tar -czf "${EXPORT_DIR}.tar.gz" "$EXPORT_DIR"

echo "=== 완료 ==="
echo "배포 패키지: ${EXPORT_DIR}.tar.gz"
ls -lh "${EXPORT_DIR}.tar.gz"
```

### 2. 내부망 설치 스크립트 (import.sh)

```bash
#!/bin/bash
set -e

echo "=== Admin API 폐쇄망 설치 ==="

# 패키지 압축 해제
PACKAGE="admin-api-airgap-*.tar.gz"
tar -xzf $PACKAGE
cd admin-api-airgap-*

# Docker 이미지 로드
echo "1. Docker 이미지 로드 중..."
cd docker-images
for img in *.tar.gz; do
    echo "  - $img"
    docker load < "$img"
done
cd ..

# 소스코드 배포
echo "2. 소스코드 배포 중..."
INSTALL_DIR="/opt/admin-api"
mkdir -p "$INSTALL_DIR"
tar -xzf admin-api-source.tar.gz -C "$INSTALL_DIR"

# Python 패키지 설치
echo "3. Python 패키지 설치 중..."
pip install --no-index --find-links=offline_packages/python poetry
cd "$INSTALL_DIR"
pip install --no-index --find-links=../offline_packages/python -r requirements.txt

# Frontend 빌드
echo "4. Frontend 빌드 중..."
cd frontend
tar -xzf ../../offline_packages/node_modules.tar.gz
npm run build
cd ..

# 환경설정
echo "5. 환경설정..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  ⚠️  .env 파일을 수정해주세요!"
fi

echo "=== 설치 완료 ==="
echo ""
echo "다음 단계:"
echo "1. cd $INSTALL_DIR"
echo "2. vi .env  # 환경변수 수정"
echo "3. docker-compose up -d"
echo "4. docker-compose logs -f admin-api"
```

---

## 보안 설정

### 1. 방화벽 규칙 (내부망)

```bash
# 허용할 포트
- 8010: Admin API
- 5432: PostgreSQL (내부 전용)
- 6379: Redis (내부 전용)
- 3592-3593: Cerbos (내부 전용)
- 18180: Spring Boot Tomcat
```

### 2. 네트워크 격리

```yaml
# docker-compose.yml 수정
networks:
  internal:
    internal: true  # 외부 인터넷 차단
  dmz:
    driver: bridge  # Spring Boot 연동용
```

### 3. 비밀번호 및 키 관리

```bash
# .env 파일 권한 설정
chmod 600 .env
chown root:docker .env

# 비밀번호 변경
vi .env
# POSTGRES_PASSWORD=<강력한 비밀번호>
# REDIS_PASSWORD=<강력한 비밀번호>
# SECRET_KEY=<32자 이상 랜덤 문자열>
```

---

## 데이터베이스 초기화

```bash
# PostgreSQL 접속
docker-compose exec postgres psql -U postgres -d admin_db

# 스키마 초기화
\i /app/schema.sql

# 초기 관리자 계정 생성 (선택 사항)
INSERT INTO users (username, email, hashed_password, is_active, is_admin)
VALUES ('admin', 'admin@internal.local', 'hashed_password', true, true);
```

---

## 문제 해결

### Q1. Docker 이미지 로드 실패

```bash
# 이미지 파일 무결성 확인
sha256sum admin-api.tar.gz

# 압축 해제 후 재시도
gunzip admin-api.tar.gz
docker load -i admin-api.tar
```

### Q2. Python 패키지 설치 실패

```bash
# pip 캐시 무시하고 강제 설치
pip install --no-index --no-cache-dir --find-links=offline_packages/python -r requirements.txt
```

### Q3. Frontend 빌드 실패

```bash
# Node.js 버전 확인 (^20.19.0 필요)
node --version

# node_modules 재압축 해제
rm -rf node_modules
tar -xzf node_modules.tar.gz
```

---

## 라이선스 정보

모든 의존성은 상업적 사용 가능한 오픈소스 라이선스:

- **FastAPI**: MIT License
- **React**: MIT License
- **PostgreSQL**: PostgreSQL License (BSD-like)
- **Redis**: BSD License
- **Cerbos**: Apache 2.0 License

**전체 라이선스 목록**: `docs/LICENSES.md` 참조

---

## 지원 및 문의

내부망 배포 관련 문의:
- 기술 지원: [내부 담당자]
- 보안 승인: [보안팀]
- 인프라 지원: [인프라팀]
