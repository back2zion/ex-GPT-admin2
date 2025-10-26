#!/bin/bash
# 방법 변경: 기존 VirtualHost 내부에 Include로 추가

echo "=== 안전한 AI 경로 설정 (v2) ==="
echo ""

# 1. /testOld 확인
echo "1. /testOld 작동 확인..."
TEST_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://localhost:20443/exGenBotDS/testOld -k)
if [ "$TEST_STATUS" != "200" ]; then
    echo "   ❌ /testOld가 정상 작동하지 않습니다"
    exit 1
fi
echo "   ✅ /testOld 정상 작동 중"

# 2. 이전 설정 파일 삭제
echo ""
echo "2. 이전 설정 파일 정리..."
if [ -f /etc/httpd/conf.d/z-exgpt-ai.conf ]; then
    rm /etc/httpd/conf.d/z-exgpt-ai.conf
    echo "   ✅ z-exgpt-ai.conf 삭제"
fi

# 3. port-20443.conf 백업
echo ""
echo "3. port-20443.conf 백업..."
cp /etc/httpd/conf.d/port-20443.conf /etc/httpd/conf.d/port-20443.conf.backup_safe_$(date +%Y%m%d_%H%M%S)
echo "   ✅ 백업 완료"

# 4. port-20443.conf에 Alias 추가 (VirtualHost 내부, ProxyPass 이전)
echo ""
echo "4. port-20443.conf에 /exgpt-ai Alias 추가..."

# ProxyPass 라인 찾기
LINE_NUM=$(grep -n "# ProxyPass 순서가 중요" /etc/httpd/conf.d/port-20443.conf | cut -d: -f1)

if [ -z "$LINE_NUM" ]; then
    echo "   ❌ ProxyPass 섹션을 찾을 수 없습니다"
    exit 1
fi

# Alias 추가 (ProxyPass 바로 위에)
sed -i "${LINE_NUM}i\\
    # React 앱 - 새 경로 (기존 /exGenBotDS와 독립적)\\
    Alias /exgpt-ai /var/www/html/exGenBotDS\\
\\
    <Directory \"/var/www/html/exGenBotDS\">\\
        # /exgpt-ai 경로로 접근 시에만 적용됨\\
        RewriteEngine On\\
        RewriteBase /exgpt-ai\\
        RewriteCond %{REQUEST_URI} ^/exgpt-ai\\
        RewriteCond %{REQUEST_FILENAME} !-f\\
        RewriteCond %{REQUEST_FILENAME} !-d\\
        RewriteRule . /exgpt-ai/index.html [L]\\
    </Directory>\\
\\
" /etc/httpd/conf.d/port-20443.conf

echo "   ✅ Alias 추가 완료"

# 5. Apache 설정 테스트
echo ""
echo "5. Apache 설정 테스트..."
httpd -t
if [ $? -ne 0 ]; then
    echo "   ❌ 설정 오류! 백업에서 복원..."
    BACKUP=$(ls -t /etc/httpd/conf.d/port-20443.conf.backup_safe_* | head -1)
    cp "$BACKUP" /etc/httpd/conf.d/port-20443.conf
    exit 1
fi
echo "   ✅ 설정 정상"

# 6. Apache reload
echo ""
echo "6. Apache reload..."
systemctl reload httpd
echo "   ✅ Reload 완료"

# 7. 확인
echo ""
echo "7. 동작 확인..."
sleep 1
TEST_OLD=$(curl -s -o /dev/null -w "%{http_code}" https://localhost:20443/exGenBotDS/testOld -k)
TEST_AI=$(curl -s -o /dev/null -w "%{http_code}" https://localhost:20443/exgpt-ai/ -k)

echo "   /testOld: HTTP $TEST_OLD"
echo "   /exgpt-ai/: HTTP $TEST_AI"

if [ "$TEST_OLD" != "200" ]; then
    echo ""
    echo "   ❌ /testOld 작동 중단! 롤백..."
    BACKUP=$(ls -t /etc/httpd/conf.d/port-20443.conf.backup_safe_* | head -1)
    cp "$BACKUP" /etc/httpd/conf.d/port-20443.conf
    systemctl reload httpd
    exit 1
fi

echo ""
echo "=== ✅ 완료 ==="
echo ""
echo "📋 결과:"
echo "   /testOld: HTTP $TEST_OLD ✅"
echo "   /exgpt-ai/: HTTP $TEST_AI"
echo ""
echo "🌐 브라우저 테스트:"
echo "   https://ui.datastreams.co.kr:20443/exgpt-ai/"
