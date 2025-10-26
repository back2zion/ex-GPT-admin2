#!/bin/bash
# 완전히 새로운 경로로 React 앱 서빙 (기존 설정 절대 건드리지 않음)

echo "=== 안전한 AI 경로 설정 ==="
echo ""
echo "⚠️  이 스크립트는:"
echo "   - 기존 파일 (ssl.conf, port-20443.conf) 절대 수정 안 함"
echo "   - 새 파일만 생성: /etc/httpd/conf.d/z-exgpt-ai.conf"
echo "   - /testOld에 영향 0%"
echo ""

# 1. 백업 확인
echo "1. /testOld 작동 확인..."
TEST_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://localhost:20443/exGenBotDS/testOld -k)
if [ "$TEST_STATUS" != "200" ]; then
    echo "   ❌ /testOld가 정상 작동하지 않습니다 (HTTP $TEST_STATUS)"
    echo "   먼저 원복 스크립트를 실행하세요: sudo bash /home/aigen/restore_ssl.sh"
    exit 1
fi
echo "   ✅ /testOld 정상 작동 중 (HTTP 200)"

# 2. 새 설정 파일 생성
echo ""
echo "2. 새 설정 파일 생성: /etc/httpd/conf.d/z-exgpt-ai.conf"
cat > /etc/httpd/conf.d/z-exgpt-ai.conf << 'APACHECONF'
# ex-GPT AI 신규 UI (React 앱)
# 기존 /exGenBotDS 경로와 완전히 독립적
# 파일명: z-exgpt-ai.conf (알파벳 순서상 마지막에 로드)

<VirtualHost *:20443>
    ServerName ui.datastreams.co.kr:20443
    
    # React 앱 정적 파일 서빙
    Alias /exgpt-ai /var/www/html/exGenBotDS
    
    <Directory "/var/www/html/exGenBotDS">
        Options -Indexes +FollowSymLinks
        AllowOverride None
        Require all granted
        DirectoryIndex index.html
        
        # React Router를 위한 Rewrite
        RewriteEngine On
        RewriteBase /exgpt-ai
        RewriteRule ^index\.html$ - [L]
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteRule . /exgpt-ai/index.html [L]
    </Directory>
</VirtualHost>
APACHECONF

echo "   ✅ 설정 파일 생성 완료"

# 3. Apache 설정 테스트
echo ""
echo "3. Apache 설정 테스트..."
httpd -t
if [ $? -ne 0 ]; then
    echo "   ❌ Apache 설정 오류!"
    echo "   설정 파일 삭제 중..."
    rm /etc/httpd/conf.d/z-exgpt-ai.conf
    exit 1
fi
echo "   ✅ Apache 설정 정상"

# 4. Apache Reload (재시작 아님)
echo ""
echo "4. Apache Reload (재시작 아님 - 더 안전)..."
systemctl reload httpd
if [ $? -ne 0 ]; then
    echo "   ❌ Apache reload 실패, 설정 파일 삭제 중..."
    rm /etc/httpd/conf.d/z-exgpt-ai.conf
    exit 1
fi
echo "   ✅ Apache reload 완료"

# 5. /testOld 재확인
echo ""
echo "5. /testOld 재확인..."
sleep 1
TEST_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://localhost:20443/exGenBotDS/testOld -k)
if [ "$TEST_STATUS" != "200" ]; then
    echo "   ❌ /testOld 작동 중단! (HTTP $TEST_STATUS)"
    echo "   설정 파일 삭제 및 rollback..."
    rm /etc/httpd/conf.d/z-exgpt-ai.conf
    systemctl reload httpd
    exit 1
fi
echo "   ✅ /testOld 정상 작동 유지 (HTTP 200)"

# 6. 새 경로 테스트
echo ""
echo "6. 새 경로 테스트..."
AI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://localhost:20443/exgpt-ai/ -k)
echo "   /exgpt-ai/ → HTTP $AI_STATUS"

# 7. 완료
echo ""
echo "=== ✅ 완료 ==="
echo ""
echo "📋 결과:"
echo "   /testOld: ✅ 정상 작동 (영향 없음)"
echo "   /exgpt-ai/: HTTP $AI_STATUS"
echo ""
echo "🌐 브라우저에서 테스트:"
echo "   기존: https://ui.datastreams.co.kr:20443/exGenBotDS/testOld"
echo "   신규: https://ui.datastreams.co.kr:20443/exgpt-ai/"
echo ""
echo "🔄 문제 발생 시 롤백:"
echo "   sudo rm /etc/httpd/conf.d/z-exgpt-ai.conf"
echo "   sudo systemctl reload httpd"
