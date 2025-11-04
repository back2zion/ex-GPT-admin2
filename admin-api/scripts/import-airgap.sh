#!/bin/bash
set -e

echo "======================================"
echo "  Admin API 폐쇄망 설치"
echo "======================================"
echo ""

# Root 권한 확인
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  경고: root 권한이 필요할 수 있습니다."
    echo "   sudo 없이 실행하려면 docker 그룹에 속해야 합니다."
    echo ""
fi

# Docker 설치 확인
if ! command -v docker &> /dev/null; then
    echo "❌ 오류: Docker가 설치되지 않았습니다."
    echo "   먼저 Docker를 설치해주세요."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ 오류: Docker Compose가 설치되지 않았습니다."
    echo "   먼저 Docker Compose를 설치해주세요."
    exit 1
fi

# 체크섬 검증
if [ -f "checksums.txt" ]; then
    echo "🔐 파일 무결성 검증 중..."
    if sha256sum -c checksums.txt --quiet 2>/dev/null; then
        echo "✅ 체크섬 검증 성공"
    else
        echo "⚠️  경고: 일부 파일의 체크섬이 일치하지 않습니다."
        read -p "계속 진행하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    echo ""
fi

# ==========================================
# 1. 설치 경로 선택
# ==========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  설치 경로 설정"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

DEFAULT_INSTALL_DIR="/opt/admin-api"
read -p "설치 경로를 입력하세요 [$DEFAULT_INSTALL_DIR]: " INSTALL_DIR
INSTALL_DIR=${INSTALL_DIR:-$DEFAULT_INSTALL_DIR}

if [ -d "$INSTALL_DIR" ]; then
    echo "⚠️  경고: $INSTALL_DIR 디렉토리가 이미 존재합니다."
    read -p "덮어쓰시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "설치를 취소합니다."
        exit 1
    fi
    echo "  🗑️  기존 디렉토리 백업 중..."
    mv "$INSTALL_DIR" "${INSTALL_DIR}.backup.$(date +%Y%m%d-%H%M%S)"
fi

echo "  📁 설치 경로: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
echo ""

# ==========================================
# 2. Docker 이미지 로드
# ==========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Docker 이미지 로드"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d "docker-images" ]; then
    cd docker-images
    for img in *.tar.gz; do
        if [ -f "$img" ]; then
            echo "  📥 Loading $img..."
            gunzip -c "$img" | docker load
        fi
    done
    cd ..
    echo "✅ Docker 이미지 로드 완료"
else
    echo "⚠️  docker-images 디렉토리가 없습니다."
fi
echo ""

# 이미지 확인
echo "  📋 로드된 이미지 목록:"
docker images | grep -E "python|postgres|redis|cerbos|admin-api" || echo "  (없음)"
echo ""

# ==========================================
# 3. 소스코드 배포
# ==========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  소스코드 배포"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "admin-api-source.tar.gz" ]; then
    echo "  📦 소스코드 압축 해제 중..."
    tar -xzf admin-api-source.tar.gz -C "$INSTALL_DIR"
    echo "✅ 소스코드 배포 완료"
else
    echo "❌ 오류: admin-api-source.tar.gz 파일이 없습니다."
    exit 1
fi
echo ""

# ==========================================
# 4. Python 패키지 설치
# ==========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  Python 패키지 설치"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Python 가상환경 생성 (선택사항)
read -p "Python 가상환경을 생성하시겠습니까? (Y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    USE_VENV=false
else
    USE_VENV=true
fi

cd "$INSTALL_DIR"

if [ "$USE_VENV" = true ]; then
    echo "  🐍 가상환경 생성 중..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

if [ -d "../offline_packages/python" ]; then
    echo "  📦 Python 패키지 설치 중..."

    # Poetry 설치
    pip install --no-index --find-links=../offline_packages/python poetry

    # 프로젝트 의존성 설치
    if [ -f "requirements.txt" ]; then
        pip install --no-index --find-links=../offline_packages/python -r requirements.txt
    else
        poetry config virtualenvs.create false
        poetry install --no-interaction --no-ansi
    fi

    echo "✅ Python 패키지 설치 완료"
else
    echo "⚠️  offline_packages/python 디렉토리가 없습니다."
    echo "   Docker 컨테이너 내에서 설치될 예정입니다."
fi

cd - > /dev/null
echo ""

# ==========================================
# 5. Frontend 빌드
# ==========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  Frontend 빌드"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d "$INSTALL_DIR/frontend" ]; then
    cd "$INSTALL_DIR/frontend"

    # node_modules 압축 해제
    if [ -f "../../offline_packages/frontend/node_modules.tar.gz" ]; then
        echo "  📦 node_modules 압축 해제 중..."
        tar -xzf "../../offline_packages/frontend/node_modules.tar.gz"

        # 빌드
        echo "  🔨 Frontend 빌드 중..."
        npm run build

        echo "✅ Frontend 빌드 완료"
    else
        echo "⚠️  node_modules.tar.gz 파일이 없습니다."
    fi

    cd - > /dev/null
else
    echo "⚠️  frontend 디렉토리가 없습니다."
fi
echo ""

# ==========================================
# 6. 환경 설정
# ==========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  환경 설정"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$INSTALL_DIR"

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "  📝 .env 파일 생성 중..."
        cp .env.example .env
        echo "✅ .env 파일이 생성되었습니다."
        echo ""
        echo "⚠️  중요: .env 파일을 내부망 환경에 맞게 수정해주세요!"
        echo ""
        read -p ".env 파일을 지금 편집하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${EDITOR:-vi} .env
        fi
    fi
else
    echo "  ℹ️  .env 파일이 이미 존재합니다."
fi

# 권한 설정
echo "  🔒 파일 권한 설정 중..."
chmod 600 .env 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true

cd - > /dev/null
echo ""

# ==========================================
# 7. 데이터베이스 초기화
# ==========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7️⃣  Docker Compose 서비스 시작"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$INSTALL_DIR"

read -p "Docker Compose로 서비스를 시작하시겠습니까? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    # 네트워크 생성
    echo "  🌐 Docker 네트워크 생성 중..."
    docker network create exgpt_net 2>/dev/null || echo "  (이미 존재함)"

    # 서비스 시작
    echo "  🚀 서비스 시작 중..."
    docker-compose up -d

    echo ""
    echo "  ⏳ 서비스가 준비될 때까지 대기 중..."
    sleep 10

    # 상태 확인
    echo ""
    echo "  📊 서비스 상태:"
    docker-compose ps

    echo ""
    echo "✅ 서비스 시작 완료"

    # 로그 확인 여부
    echo ""
    read -p "로그를 확인하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose logs -f admin-api
    fi
fi

cd - > /dev/null
echo ""

# ==========================================
# 완료
# ==========================================
echo "======================================"
echo "  ✅ 설치 완료!"
echo "======================================"
echo ""
echo "📁 설치 경로: $INSTALL_DIR"
echo "🌐 Admin UI: http://localhost:8010/admin"
echo "📖 API 문서: http://localhost:8010/docs"
echo ""
echo "🔧 유용한 명령어:"
echo "  cd $INSTALL_DIR"
echo "  docker-compose ps                # 서비스 상태 확인"
echo "  docker-compose logs -f admin-api # 로그 확인"
echo "  docker-compose restart admin-api # 서비스 재시작"
echo "  docker-compose down              # 서비스 중지"
echo ""
echo "📚 상세 가이드: $INSTALL_DIR/docs/"
echo ""
echo "⚠️  주의사항:"
echo "  1. .env 파일을 반드시 내부망 환경에 맞게 수정하세요"
echo "  2. Spring Boot URL 설정을 확인하세요"
echo "  3. 데이터베이스 비밀번호를 변경하세요"
echo ""
