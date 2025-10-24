#!/bin/bash
# Apache 설정을 Tomcat 18080 포트로 수정

set -e

echo "======================================"
echo "Apache 설정 수정: Port 18080"
echo "======================================"

CONFIG_FILE="/etc/httpd/conf.d/port-20443.conf"
BACKUP_FILE="/etc/httpd/conf.d/port-20443.conf.bak.$(date +%Y%m%d_%H%M%S)"

# 1. 백업
echo "1. 백업 생성 중..."
sudo cp "$CONFIG_FILE" "$BACKUP_FILE"
echo "✅ 백업: $BACKUP_FILE"

# 2. 설정 파일 수정
echo "2. Apache 설정 파일 작성 중..."
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

    # Admin API 프록시 (관리자 대시보드용 - FastAPI 8010)
    ProxyPass /api/v1/admin/ http://localhost:8010/api/v1/admin/
    ProxyPassReverse /api/v1/admin/ http://localhost:8010/api/v1/admin/

    # Spring Boot/Tomcat WAS 프록시 (채팅, 파일, 공지사항, 만족도 등 - Port 18080)
    ProxyPass /exGenBotDS/ http://localhost:18080/exGenBotDS/
    ProxyPassReverse /exGenBotDS/ http://localhost:18080/exGenBotDS/

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
    echo "❌ 설정 파일 오류!"
    sudo cp "$BACKUP_FILE" "$CONFIG_FILE"
    exit 1
fi

# 4. Apache 재시작
echo "4. Apache 재시작 중..."
sudo systemctl reload httpd
echo "✅ Apache 재시작 완료"

echo ""
echo "======================================"
echo "수정 완료!"
echo "======================================"
echo ""
echo "✅ Apache → Tomcat (Port 18080) 프록시 설정 완료"
echo ""
echo "포트 확인:"
netstat -tuln | grep 18080 || ss -tuln | grep 18080 || echo "⚠️ Port 18080 확인 필요"
echo ""
echo "백업 파일: $BACKUP_FILE"
echo ""
echo "테스트 URL:"
echo "  - 채팅 UI: https://ui.datastreams.co.kr:20443/exGenBotDS/ai"
echo "  - 관리자: https://ui.datastreams.co.kr:20443/admin"
echo ""
