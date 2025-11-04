#!/bin/bash
# Apache 설정을 10/22 12:00 (정오) 기준으로 복원

set -e

echo "======================================"
echo "Apache 설정 복원: 10/22 12:00 기준"
echo "======================================"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 1. 현재 설정 백업
echo "1. 현재 설정 백업 중..."
sudo cp /etc/httpd/conf/httpd.conf /etc/httpd/conf/httpd.conf.bak.$TIMESTAMP
sudo cp /etc/httpd/conf.d/ssl.conf /etc/httpd/conf.d/ssl.conf.bak.$TIMESTAMP
if [ -f /etc/httpd/conf.d/port-20443.conf ]; then
    sudo cp /etc/httpd/conf.d/port-20443.conf /etc/httpd/conf.d/port-20443.conf.bak.$TIMESTAMP
fi
echo "✅ 백업 완료"

# 2. httpd.conf에서 Listen 20443 제거
echo "2. httpd.conf에서 Listen 20443 제거 중..."
sudo sed -i '/^Listen 20443$/d' /etc/httpd/conf/httpd.conf
echo "✅ httpd.conf 수정 완료"

# 3. ssl.conf를 10/20 백업으로 복원
echo "3. ssl.conf를 10/20 백업으로 복원 중..."
if [ -f /etc/httpd/conf.d/ssl.conf.backup.20251020_203713 ]; then
    sudo cp /etc/httpd/conf.d/ssl.conf.backup.20251020_203713 /etc/httpd/conf.d/ssl.conf
    echo "✅ ssl.conf 복원 완료"
else
    echo "❌ 10/20 백업을 찾을 수 없습니다"
    exit 1
fi

# 4. port-20443.conf 삭제 (10/22 12:00에는 존재하지 않았음)
echo "4. port-20443.conf 삭제 중..."
if [ -f /etc/httpd/conf.d/port-20443.conf ]; then
    sudo rm /etc/httpd/conf.d/port-20443.conf
    echo "✅ port-20443.conf 삭제 완료"
else
    echo "⚠️ port-20443.conf가 이미 없습니다"
fi

# 5. 설정 테스트
echo "5. Apache 설정 테스트 중..."
if sudo apachectl configtest; then
    echo "✅ 설정 파일 검증 완료"
else
    echo "❌ 설정 파일 오류! 롤백 중..."
    sudo cp /etc/httpd/conf/httpd.conf.bak.$TIMESTAMP /etc/httpd/conf/httpd.conf
    sudo cp /etc/httpd/conf.d/ssl.conf.bak.$TIMESTAMP /etc/httpd/conf.d/ssl.conf
    if [ -f /etc/httpd/conf.d/port-20443.conf.bak.$TIMESTAMP ]; then
        sudo cp /etc/httpd/conf.d/port-20443.conf.bak.$TIMESTAMP /etc/httpd/conf.d/port-20443.conf
    fi
    exit 1
fi

# 6. Apache 재시작
echo "6. Apache 재시작 중..."
sudo systemctl reload httpd
echo "✅ Apache 재시작 완료"

echo ""
echo "======================================"
echo "복원 완료!"
echo "======================================"
echo ""
echo "✅ 10/22 12:00 (정오) 기준으로 복원 완료"
echo ""
echo "변경사항:"
echo "  - httpd.conf: Listen 20443 제거됨"
echo "  - ssl.conf: 10/20 백업으로 복원됨"
echo "  - port-20443.conf: 삭제됨"
echo ""
echo "원본 설정 (10/20 백업):"
echo "  - Port 443: ssl.conf"
echo "  - ProxyPass /exGenBotDS/ → Tomcat (18180)"
echo "  - ProxyPass /api/chat_stream → FastAPI (8010)"
echo ""
echo "백업 파일: *.$TIMESTAMP"
echo ""
