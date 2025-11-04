#!/bin/bash
# Spring Boot WAS 복원 스크립트

set -e

echo "======================================"
echo "Spring Boot WAS 복원 시작"
echo "======================================"

# 1. Apache 설정을 Spring Boot (Port 20000)으로 변경
echo "1. Apache 설정 수정 중..."

CONFIG_FILE="/etc/httpd/conf.d/port-20443.conf"
BACKUP_FILE="/etc/httpd/conf.d/port-20443.conf.bak.$(date +%Y%m%d_%H%M%S)"

sudo cp "$CONFIG_FILE" "$BACKUP_FILE"
echo "✅ 백업 완료: $BACKUP_FILE"

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

    # API 프록시 - Spring Boot WAS (Port 20000)
    ProxyPreserveHost On

    # Admin API 프록시 (관리자 대시보드용 - FastAPI)
    ProxyPass /api/v1/admin/ http://localhost:8010/api/v1/admin/
    ProxyPassReverse /api/v1/admin/ http://localhost:8010/api/v1/admin/

    # Spring Boot WAS 프록시 (채팅, 파일, 공지사항, 만족도 등)
    ProxyPass /exGenBotDS/ http://localhost:20000/exGenBotDS/
    ProxyPassReverse /exGenBotDS/ http://localhost:20000/exGenBotDS/

    # SSL 설정
    SSLEngine on
    SSLCertificateFile /root/server.crt
    SSLCertificateKeyFile /root/server.key
</VirtualHost>
EOF

echo "✅ Apache 설정 변경 완료 (Port 20000으로)"

# 2. Apache 설정 테스트
echo "2. Apache 설정 테스트 중..."
if sudo apachectl configtest; then
    echo "✅ 설정 파일 검증 완료"
else
    echo "❌ 설정 파일 오류!"
    sudo cp "$BACKUP_FILE" "$CONFIG_FILE"
    exit 1
fi

# 3. Apache 재시작
echo "3. Apache 재시작 중..."
sudo systemctl reload httpd
echo "✅ Apache 재시작 완료"

echo ""
echo "======================================"
echo "Spring Boot WAS 실행 안내"
echo "======================================"
echo ""
echo "⚠️ Spring Boot WAS를 수동으로 실행해주세요:"
echo ""
echo "cd /home/aigen/new-exgpt-feature-chat"
echo "./mvnw spring-boot:run"
echo ""
echo "또는 백그라운드 실행:"
echo "nohup ./mvnw spring-boot:run > logs/spring-boot.log 2>&1 &"
echo ""
echo "포트 확인:"
netstat -tuln | grep 20000 || echo "❌ Port 20000 아직 실행 안됨"
echo ""
echo "백업 파일: $BACKUP_FILE"
echo ""
