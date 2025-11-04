#!/bin/bash
set -e

echo "======================================"
echo "  Admin API 폐쇄망 배포 패키지 생성"
echo "======================================"
echo ""

# 작업 디렉토리 확인
if [ ! -f "pyproject.toml" ]; then
    echo "❌ 오류: admin-api 프로젝트 루트에서 실행해주세요"
    exit 1
fi

# 날짜 기반 패키지명
EXPORT_DIR="admin-api-airgap-$(date +%Y%m%d-%H%M%S)"
echo "📦 패키지명: $EXPORT_DIR"
echo ""

# 디렉토리 생성
mkdir -p "$EXPORT_DIR"/{docker-images,offline_packages/{python,frontend}}

# ==========================================
# 1. Docker 이미지 저장
# ==========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Docker 이미지 Pull & Save"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

IMAGES=(
    "python:3.11-slim"
    "postgres:15-alpine"
    "redis:7-alpine"
    "ghcr.io/cerbos/cerbos:latest"
)

for image in "${IMAGES[@]}"; do
    echo "  📥 Pulling $image..."
    docker pull "$image"

    filename=$(echo "$image" | tr '/:' '-')
    echo "  💾 Saving to ${filename}.tar.gz..."
    docker save "$image" | gzip > "$EXPORT_DIR/docker-images/${filename}.tar.gz"
done

# Admin API 이미지 빌드 및 저장
echo ""
echo "  🔨 Building admin-api..."
docker-compose build admin-api
echo "  💾 Saving admin-api..."
docker save admin-api-admin-api:latest | gzip > "$EXPORT_DIR/docker-images/admin-api-admin-api.tar.gz"

echo "✅ Docker 이미지 저장 완료"
echo ""

# ==========================================
# 2. Python 패키지 다운로드
# ==========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Python 패키지 다운로드"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# requirements.txt 생성
echo "  📝 Exporting requirements.txt..."
poetry export -f requirements.txt --output requirements.txt --without-hashes

# pip download
echo "  📥 Downloading Python packages..."
pip download -r requirements.txt -d "$EXPORT_DIR/offline_packages/python" --no-deps
pip download -r requirements.txt -d "$EXPORT_DIR/offline_packages/python"

# Poetry 자체도 다운로드
echo "  📥 Downloading Poetry..."
pip download poetry -d "$EXPORT_DIR/offline_packages/python"

echo "✅ Python 패키지 다운로드 완료"
echo ""

# ==========================================
# 3. Frontend 패키지 압축
# ==========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  Frontend 패키지 압축"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d "frontend" ]; then
    cd frontend

    # node_modules가 없으면 설치
    if [ ! -d "node_modules" ]; then
        echo "  📦 Installing npm packages..."
        npm ci
    fi

    echo "  🗜️  Compressing node_modules..."
    tar -czf "../$EXPORT_DIR/offline_packages/frontend/node_modules.tar.gz" node_modules

    echo "  📄 Copying package files..."
    cp package.json package-lock.json "../$EXPORT_DIR/offline_packages/frontend/"

    cd ..
    echo "✅ Frontend 패키지 압축 완료"
else
    echo "⚠️  frontend 디렉토리가 없습니다. 건너뜁니다."
fi
echo ""

# ==========================================
# 4. 소스코드 압축
# ==========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  소스코드 압축"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "  🗜️  Compressing source code..."
tar --exclude='node_modules' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='.git' \
    --exclude='frontend/dist' \
    --exclude='frontend/node_modules' \
    --exclude="$EXPORT_DIR" \
    -czf "$EXPORT_DIR/admin-api-source.tar.gz" \
    app/ \
    frontend/ \
    docs/ \
    scripts/ \
    policies/ \
    pyproject.toml \
    poetry.lock \
    Dockerfile \
    docker-compose.yml \
    README.md \
    .env.example \
    alembic.ini 2>/dev/null || true

echo "✅ 소스코드 압축 완료"
echo ""

# ==========================================
# 5. 배포 문서 복사
# ==========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  배포 문서 복사"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cp docs/AIRGAP_DEPLOYMENT_GUIDE.md "$EXPORT_DIR/README.md"
cp scripts/import-airgap.sh "$EXPORT_DIR/import.sh"
chmod +x "$EXPORT_DIR/import.sh"

echo "✅ 배포 문서 복사 완료"
echo ""

# ==========================================
# 6. 체크섬 생성
# ==========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  체크섬 생성"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "  🔐 Generating SHA256 checksums..."
cd "$EXPORT_DIR"
find . -type f -exec sha256sum {} \; > checksums.txt
cd ..

echo "✅ 체크섬 생성 완료"
echo ""

# ==========================================
# 7. 최종 패키징
# ==========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7️⃣  최종 패키징"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "  🗜️  Creating final archive..."
tar -czf "${EXPORT_DIR}.tar.gz" "$EXPORT_DIR"

# 용량 정보
TOTAL_SIZE=$(du -sh "${EXPORT_DIR}.tar.gz" | cut -f1)

echo ""
echo "======================================"
echo "  ✅ 패키지 생성 완료!"
echo "======================================"
echo ""
echo "📦 패키지 파일: ${EXPORT_DIR}.tar.gz"
echo "📊 전체 용량: $TOTAL_SIZE"
echo ""
echo "📋 포함 내용:"
echo "  - Docker 이미지 (Python, PostgreSQL, Redis, Cerbos, Admin API)"
echo "  - Python 패키지 (Poetry + 모든 의존성)"
echo "  - Frontend 패키지 (node_modules)"
echo "  - 소스코드 (전체)"
echo "  - 배포 가이드 (README.md)"
echo "  - 설치 스크립트 (import.sh)"
echo ""
echo "🚀 다음 단계:"
echo "  1. ${EXPORT_DIR}.tar.gz를 USB/DVD에 복사"
echo "  2. 내부망 서버로 반입"
echo "  3. tar -xzf ${EXPORT_DIR}.tar.gz 압축 해제"
echo "  4. cd ${EXPORT_DIR} && ./import.sh 실행"
echo ""
echo "📚 자세한 내용: ${EXPORT_DIR}/README.md"
echo ""
