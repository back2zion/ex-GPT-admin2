#!/bin/bash
# ssl.conf에도 /ai 제외 규칙 추가 (안전하게)

echo "=== ssl.conf에 /ai 제외 규칙 추가 ==="

# 1. /testOld 확인
TEST_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://localhost:20443/exGenBotDS/testOld -k)
if [ "$TEST_STATUS" != "200" ]; then
    echo "❌ /testOld 작동 안 함"
    exit 1
fi
echo "✅ /testOld 정상 (HTTP 200)"

# 2. ssl.conf 백업
cp /etc/httpd/conf.d/ssl.conf /etc/httpd/conf.d/ssl.conf.backup_ai_exclude_$(date +%Y%m%d_%H%M%S)
echo "✅ ssl.conf 백업 완료"

# 3. ProxyPass /exGenBotDS/ 규칙 찾기
LINE_NUM=$(grep -n "^ProxyPass /exGenBotDS/ " /etc/httpd/conf.d/ssl.conf | cut -d: -f1)

if [ -z "$LINE_NUM" ]; then
    echo "❌ ProxyPass /exGenBotDS/ 를 찾을 수 없습니다"
    exit 1
fi

echo "✅ ProxyPass 규칙 찾음 (라인 $LINE_NUM)"

# 4. 그 줄 바로 앞에 제외 규칙 추가
sed -i "${LINE_NUM}i\\
# /ai는 프록시하지 않음 (React 정적 파일)\\
ProxyPass /exGenBotDS/ai !\\
" /etc/httpd/conf.d/ssl.conf

echo "✅ 제외 규칙 추가 완료"

# 5. 추가된 내용 확인
echo ""
echo "추가된 내용:"
sed -n "$((LINE_NUM-1)),$((LINE_NUM+2))p" /etc/httpd/conf.d/ssl.conf

# 6. Apache 테스트
echo ""
httpd -t
if [ $? -ne 0 ]; then
    echo "❌ Apache 설정 오류! 롤백..."
    BACKUP=$(ls -t /etc/httpd/conf.d/ssl.conf.backup_ai_exclude_* | head -1)
    cp "$BACKUP" /etc/httpd/conf.d/ssl.conf
    exit 1
fi
echo "✅ Apache 설정 정상"

# 7. Reload
systemctl reload httpd
echo "✅ Apache reload 완료"

# 8. /testOld 재확인
sleep 1
TEST_OLD=$(curl -s -o /dev/null -w "%{http_code}" https://localhost:20443/exGenBotDS/testOld -k)

echo ""
echo "결과:"
echo "  /testOld: HTTP $TEST_OLD"

if [ "$TEST_OLD" != "200" ]; then
    echo ""
    echo "❌ /testOld 작동 중단! 롤백..."
    BACKUP=$(ls -t /etc/httpd/conf.d/ssl.conf.backup_ai_exclude_* | head -1)
    cp "$BACKUP" /etc/httpd/conf.d/ssl.conf
    systemctl reload httpd
    exit 1
fi

echo ""
echo "=== ✅ 완료 ==="
echo ""
echo "브라우저에서 다시 테스트:"
echo "  https://ui.datastreams.co.kr:20443/exGenBotDS/ai"
echo ""
echo "롤백 (문제 발생 시):"
BACKUP=$(ls -t /etc/httpd/conf.d/ssl.conf.backup_ai_exclude_* | head -1)
echo "  sudo cp $BACKUP /etc/httpd/conf.d/ssl.conf"
echo "  sudo systemctl reload httpd"
