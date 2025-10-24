# Apache 설정 수정 가이드

## 문제 1-2: Apache/SSL 설정 충돌 해결

### 현재 문제
- Port 8080은 GitLab이 사용 중
- 채팅 API(`/api/chat_stream`)가 Port 8080으로 프록시되고 있음
- 실제로는 Port 8010의 admin-api(chat_proxy)를 사용해야 함

### 수정 방법

**파일**: `/etc/httpd/conf.d/port-20443.conf`

#### 1. 백업 생성
```bash
sudo cp /etc/httpd/conf.d/port-20443.conf /etc/httpd/conf.d/port-20443.conf.bak.$(date +%Y%m%d_%H%M%S)
```

#### 2. 수정할 내용

**변경 전 (Line 35-47):**
```apache
# exGenBotDS Chat API proxy
ProxyPass /exGenBotDS/api/chat_stream http://localhost:8080/api/chat_stream
ProxyPassReverse /exGenBotDS/api/chat_stream http://localhost:8080/api/chat_stream
ProxyPass /exGenBotDS/api/chat/ http://localhost:8080/api/chat/
ProxyPassReverse /exGenBotDS/api/chat/ http://localhost:8080/api/chat/

ProxyPass /api/v1/admin/ http://localhost:8010/api/v1/admin/
ProxyPassReverse /api/v1/admin/ http://localhost:8010/api/v1/admin/

# Chat API proxy (user-api 8080)
ProxyPass /api/chat_stream http://localhost:8080/api/chat_stream
ProxyPassReverse /api/chat_stream http://localhost:8080/api/chat_stream
ProxyPass /api/chat/ http://localhost:8080/api/chat/
ProxyPassReverse /api/chat/ http://localhost:8080/api/chat/
```

**변경 후:**
```apache
# Admin API 프록시 (관리자 대시보드용)
ProxyPass /api/v1/admin/ http://localhost:8010/api/v1/admin/
ProxyPassReverse /api/v1/admin/ http://localhost:8010/api/v1/admin/

# Chat API 프록시 (채팅 UI용 - FastAPI chat_proxy 사용)
ProxyPass /api/chat_stream http://localhost:8010/api/chat_stream
ProxyPassReverse /api/chat_stream http://localhost:8010/api/chat_stream
ProxyPass /api/chat/ http://localhost:8010/api/chat/
ProxyPassReverse /api/chat/ http://localhost:8010/api/chat/
```

#### 3. 수정 명령어
```bash
sudo vi /etc/httpd/conf.d/port-20443.conf
```

또는:
```bash
sudo nano /etc/httpd/conf.d/port-20443.conf
```

#### 4. Apache 재시작
```bash
# 설정 테스트
sudo apachectl configtest

# 재시작
sudo systemctl reload httpd
```

#### 5. 검증
```bash
# Port 확인
netstat -tuln | grep -E ":(8010|8080)"

# 로그 확인
sudo tail -f /var/log/httpd/error_log
```

## 최종 수정된 설정 파일 (전체)

```apache
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
```

## 주의사항
- Port 8080은 GitLab이 사용 중이므로 절대 사용하지 마세요
- Port 8010은 admin-api (FastAPI)로 chat_proxy 포함
- 수정 후 반드시 `apachectl configtest`로 검증하세요

## 완료 확인
수정 후 다음 URL로 테스트:
- https://ui.datastreams.co.kr:20443/exGenBotDS/ai
- https://ui.datastreams.co.kr:20443/admin
