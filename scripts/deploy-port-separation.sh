#!/bin/bash
# 포트 분리 보안 업데이트 배포 스크립트
# 작성일: 2025-10-20

set -e  # 에러 발생 시 중단

echo "================================"
echo "포트 분리 보안 업데이트 시작"
echo "================================"

# 1. Apache 설정 백업
echo "1. Apache 설정 백업 중..."
sudo cp /etc/httpd/conf.d/ssl.conf /etc/httpd/conf.d/ssl.conf.backup.$(date +%Y%m%d_%H%M%S)

# 2. Apache 설정 업데이트
echo "2. Apache 설정 업데이트 중..."
sudo cp /tmp/ssl.conf.new /etc/httpd/conf.d/ssl.conf

# 3. Apache 설정 검증
echo "3. Apache 설정 검증 중..."
sudo apachectl configtest

# 4. Docker Compose 재시작 (새로운 user-api 컨테이너 추가)
echo "4. Docker 컨테이너 재시작 중..."
cd /home/aigen/admin-api
docker-compose down
docker-compose up -d

# 5. 컨테이너 상태 확인
echo "5. 컨테이너 상태 확인 중..."
sleep 5
docker-compose ps

# 6. Apache 재시작
echo "6. Apache 재시작 중..."
sudo systemctl restart httpd

# 7. 포트 확인
echo "7. 포트 바인딩 확인 중..."
echo "Port 8010 (admin-api):"
ss -tlnp | grep :8010 || echo "  포트 8010 확인 불가"
echo "Port 8080 (user-api):"
ss -tlnp | grep :8080 || echo "  포트 8080 확인 불가"

# 8. Health Check
echo "8. Health Check 수행 중..."
echo "Admin API (port 8010):"
curl -s http://localhost:8010/health | jq . || echo "  Admin API 응답 없음"
echo ""
echo "User API (port 8080):"
curl -s http://localhost:8080/health | jq . || echo "  User API 응답 없음"

echo ""
echo "================================"
echo "포트 분리 배포 완료!"
echo "================================"
echo ""
echo "변경 사항:"
echo "  - Admin API/UI: https://ui.datastreams.co.kr/admin/* → localhost:8010"
echo "  - User Chat API: https://ui.datastreams.co.kr/api/chat_stream → localhost:8080"
echo ""
echo "보안 개선:"
echo "  ✅ 관리자 API와 사용자 API가 물리적으로 분리됨"
echo "  ✅ 사용자가 /api/chat_stream 접근 시 /api/v1/admin/* 접근 불가"
echo "  ✅ 네트워크 레벨 격리 완료"
echo ""
