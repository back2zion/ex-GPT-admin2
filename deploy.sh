#!/bin/bash
# ex-GPT Admin 통합 배포 스크립트

set -e

echo "🚀 ex-GPT Admin 배포 시작..."

# 1. admin-ui (React) 빌드 및 배포
echo ""
echo "📦 1/3: admin-ui 빌드 중..."
cd admin-ui
npm run build
echo "✅ admin-ui 빌드 완료"

echo "📤 admin-ui 배포 중..."
rm -rf /var/www/html/admin/*
cp -r dist/* /var/www/html/admin/
echo "✅ admin-ui 배포 완료: /var/www/html/admin/"

# 2. admin-api (Python FastAPI) 재시작
echo ""
echo "🐍 2/3: admin-api 재시작 중..."
cd ../admin-api
docker restart admin-api 2>/dev/null || echo "⚠️  admin-api 컨테이너가 없습니다"
echo "✅ admin-api 재시작 완료"

# 3. user-app (Java Spring Boot) - 선택사항
echo ""
echo "☕ 3/3: user-app (필요 시 수동 재시작)"
echo "   cd user-app && ./mvnw spring-boot:restart"

echo ""
echo "✅ 배포 완료!"
echo "   - Admin UI: https://ui.datastreams.co.kr:20443/admin"
echo "   - Admin API: http://localhost:8010"
echo "   - User App: http://localhost:8080"
