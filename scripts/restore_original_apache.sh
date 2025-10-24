#!/bin/bash
# Apache 설정을 원본 백업으로 복원

set -e

echo "======================================"
echo "Apache 설정 복원"
echo "======================================"

CURRENT_CONFIG="/etc/httpd/conf.d/port-20443.conf"
BACKUP_CONFIG="/etc/httpd/conf.d/port-20443.conf.bak.20251023_190425"
NEW_BACKUP="/etc/httpd/conf.d/port-20443.conf.bak.$(date +%Y%m%d_%H%M%S)"

# 1. 현재 설정 백업
echo "1. 현재 설정 백업 중..."
sudo cp "$CURRENT_CONFIG" "$NEW_BACKUP"
echo "✅ 백업: $NEW_BACKUP"

# 2. 원본 백업으로 복원
echo "2. 원본 설정 복원 중..."
sudo cp "$BACKUP_CONFIG" "$CURRENT_CONFIG"
echo "✅ 원본 설정 복원 완료"

# 3. 설정 테스트
echo "3. Apache 설정 테스트 중..."
if sudo apachectl configtest; then
    echo "✅ 설정 파일 검증 완료"
else
    echo "❌ 설정 파일 오류!"
    sudo cp "$NEW_BACKUP" "$CURRENT_CONFIG"
    exit 1
fi

# 4. Apache 재시작
echo "4. Apache 재시작 중..."
sudo systemctl reload httpd
echo "✅ Apache 재시작 완료"

echo ""
echo "======================================"
echo "복원 완료!"
echo "======================================"
echo ""
echo "✅ 원본 Apache 설정으로 복원됨"
echo ""
echo "포트 구성:"
echo "  - Port 8080: ex-GPT Chat API"
echo "  - Port 8010: FastAPI Admin API"
echo ""
echo "프록시 규칙:"
echo "  - /api/chat/ → port 8080 (React 앱용)"
echo "  - /exGenBotDS/api/chat/ → port 8080 (내부 호출용)"
echo "  - /api/v1/admin/ → port 8010 (관리자)"
echo ""
echo "현재 백업: $NEW_BACKUP"
echo "원본 백업: $BACKUP_CONFIG"
echo ""
