#!/bin/bash
# port-20443.conf에 localhost를 ServerAlias로 추가

echo "=== ServerAlias 추가 ==="

# 1. /testOld 확인
TEST_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://localhost:20443/exGenBotDS/testOld -k)
if [ "$TEST_STATUS" != "200" ]; then
    echo "❌ /testOld 작동 안 함"
    exit 1
fi
echo "✅ /testOld 정상"

# 2. 백업
cp /etc/httpd/conf.d/port-20443.conf /etc/httpd/conf.d/port-20443.conf.backup_localhost_$(date +%Y%m%d_%H%M%S)
echo "✅ 백업 완료"

# 3. localhost ServerAlias 추가
sed -i '/ServerAlias 172.25.101.91:20443/a\    ServerAlias localhost:20443' /etc/httpd/conf.d/port-20443.conf
echo "✅ ServerAlias localhost 추가"

# 4. 확인
echo ""
echo "수정된 내용:"
grep -A2 "ServerName" /etc/httpd/conf.d/port-20443.conf | head -4

# 5. Apache 테스트
httpd -t
if [ $? -ne 0 ]; then
    echo "❌ 설정 오류, 롤백..."
    BACKUP=$(ls -t /etc/httpd/conf.d/port-20443.conf.backup_localhost_* | head -1)
    cp "$BACKUP" /etc/httpd/conf.d/port-20443.conf
    exit 1
fi

# 6. Reload
systemctl reload httpd
echo "✅ Apache reload 완료"

# 7. 테스트
sleep 1
TEST_OLD=$(curl -s -o /dev/null -w "%{http_code}" https://localhost:20443/exGenBotDS/testOld -k)
echo ""
echo "/testOld: HTTP $TEST_OLD"

if [ "$TEST_OLD" != "200" ]; then
    echo "❌ /testOld 작동 중단! 롤백..."
    BACKUP=$(ls -t /etc/httpd/conf.d/port-20443.conf.backup_localhost_* | head -1)
    cp "$BACKUP" /etc/httpd/conf.d/port-20443.conf
    systemctl reload httpd
    exit 1
fi

echo "✅ 완료"
