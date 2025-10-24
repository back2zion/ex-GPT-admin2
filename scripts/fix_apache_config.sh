#!/bin/bash
# Apache 설정 자동 수정 스크립트 (문제 1-2)

set -e

echo "======================================"
echo "Apache 설정 자동 수정 시작"
echo "======================================"

CONFIG_FILE="/etc/httpd/conf.d/port-20443.conf"
BACKUP_FILE="/etc/httpd/conf.d/port-20443.conf.bak.$(date +%Y%m%d_%H%M%S)"

# 1. 백업 생성
echo "1. 설정 파일 백업 중..."
sudo cp "$CONFIG_FILE" "$BACKUP_FILE"
echo "✅ 백업 완료: $BACKUP_FILE"

# 2. 새 설정 파일 작성
echo "2. 새 설정 파일 작성 중..."
sudo tee "$CONFIG_FILE" > /dev/null <<'EOF'
<VirtualHost *:20443>
    ServerName ui.datastreams.co.kr:20443
    ServerAlias 172.25.101.91:20443
    DocumentRoot /var/www/html

    # React UI
    Alias /exGenBotDS /var/www/html/exGenBotDS

    <Directory "/var/www/html/exGenBotDS">
        Options -Indexes +FollowSymLinks
        AllowOverride None
        Require all granted
        DirectoryIndex index.html

        RewriteEngine On
        RewriteBase /exGenBotDS
        RewriteRule ^index\.html$ - [L]
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteRule . /exGenBotDS/index.html [L]
    </Directory>

    <Directory "/var/www/html">
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>

    # API 프록시
    ProxyPreserveHost On
    ProxyPass /exGenBotDS/api/v1/ http://localhost:8010/api/v1/
    ProxyPassReverse /exGenBotDS/api/v1/ http://localhost:8010/api/v1/

    # Admin API 프록시 (관리자 대시보드용)
    ProxyPass /api/v1/admin/ http://localhost:8010/api/v1/admin/
    ProxyPassReverse /api/v1/admin/ http://localhost:8010/api/v1/admin/

    # Chat API 프록시 (채팅 UI용 - FastAPI chat_proxy 사용)
    ProxyPass /api/chat_stream http://localhost:8010/api/chat_stream
    ProxyPassReverse /api/chat_stream http://localhost:8010/api/chat_stream
    ProxyPass /api/chat/ http://localhost:8010/api/chat/
    ProxyPassReverse /api/chat/ http://localhost:8010/api/chat/

    # SSL 설정
    SSLEngine on
    SSLCertificateFile /root/server.crt
    SSLCertificateKeyFile /root/server.key
</VirtualHost>
EOF

echo "✅ 설정 파일 작성 완료"

# 3. 설정 테스트
echo "3. Apache 설정 테스트 중..."
if sudo apachectl configtest; then
    echo "✅ 설정 파일 검증 완료"
else
    echo "❌ 설정 파일 오류 발견!"
    echo "백업 파일로 복구합니다..."
    sudo cp "$BACKUP_FILE" "$CONFIG_FILE"
    exit 1
fi

# 4. Apache 재시작
echo "4. Apache 재시작 중..."
sudo systemctl reload httpd
echo "✅ Apache 재시작 완료"

# 5. 상태 확인
echo ""
echo "======================================"
echo "수정 완료!"
echo "======================================"
echo ""
echo "✅ Port 8080 → 8010으로 변경 완료"
echo "✅ 채팅 API가 FastAPI(8010)를 사용합니다"
echo ""
echo "백업 파일: $BACKUP_FILE"
echo ""
echo "포트 확인:"
netstat -tuln | grep -E ":(8010|8080)" || ss -tuln | grep -E ":(8010|8080)"
echo ""
echo "테스트 URL:"
echo "  - 채팅 UI: https://ui.datastreams.co.kr:20443/exGenBotDS/ai"
echo "  - 관리자: https://ui.datastreams.co.kr:20443/admin"
echo ""
