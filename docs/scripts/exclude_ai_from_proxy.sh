#!/bin/bash
# /exGenBotDS/ai를 ProxyPass에서 명시적으로 제외

echo "=== /ai 경로 ProxyPass 제외 설정 ==="

# 1. /testOld 확인
TEST_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://localhost:20443/exGenBotDS/testOld -k)
if [ "$TEST_STATUS" != "200" ]; then
    echo "❌ /testOld 작동 안 함"
    exit 1
fi
echo "✅ /testOld 정상"

# 2. 백업
cp /etc/httpd/conf.d/port-20443.conf /etc/httpd/conf.d/port-20443.conf.backup_exclude_$(date +%Y%m%d_%H%M%S)
echo "✅ 백업 완료"

# 3. ProxyPass 섹션 찾아서 제외 규칙 추가
# "ProxyPreserveHost On" 다음 줄에 추가
sed -i '/ProxyPreserveHost On/a\
\
    # /exGenBotDS/ai는 프록시하지 않음 (React 정적 파일)\
    ProxyPass /exGenBotDS/ai !' /etc/httpd/conf.d/port-20443.conf

echo "✅ ProxyPass 제외 규칙 추가"

# 4. 확인
echo ""
echo "추가된 내용:"
grep -A3 "ProxyPreserveHost On" /etc/httpd/conf.d/port-20443.conf

# 5. Apache 테스트
echo ""
httpd -t
if [ $? -ne 0 ]; then
    echo "❌ 설정 오류, 롤백..."
    BACKUP=$(ls -t /etc/httpd/conf.d/port-20443.conf.backup_exclude_* | head -1)
    cp "$BACKUP" /etc/httpd/conf.d/port-20443.conf
    exit 1
fi
echo "✅ Apache 설정 정상"

# 6. Reload
systemctl reload httpd
echo "✅ Apache reload 완료"

# 7. 테스트
sleep 1
TEST_OLD=$(curl -s -o /dev/null -w "%{http_code}" https://localhost:20443/exGenBotDS/testOld -k)
TEST_AI=$(curl -s -o /dev/null -w "%{http_code}" https://localhost:20443/exGenBotDS/ai -k)

echo ""
echo "결과:"
echo "  /testOld: HTTP $TEST_OLD"
echo "  /ai: HTTP $TEST_AI"

if [ "$TEST_OLD" != "200" ]; then
    echo ""
    echo "❌ /testOld 작동 중단! 롤백..."
    BACKUP=$(ls -t /etc/httpd/conf.d/port-20443.conf.backup_exclude_* | head -1)
    cp "$BACKUP" /etc/httpd/conf.d/port-20443.conf
    systemctl reload httpd
    exit 1
fi

echo ""
echo "=== ✅ 완료 ==="
echo ""
echo "브라우저에서 테스트:"
echo "  https://ui.datastreams.co.kr:20443/exGenBotDS/ai"
echo ""
echo "롤백 (문제 발생 시):"
BACKUP=$(ls -t /etc/httpd/conf.d/port-20443.conf.backup_exclude_* | head -1)
echo "  sudo cp $BACKUP /etc/httpd/conf.d/port-20443.conf"
echo "  sudo systemctl reload httpd"
