#!/bin/bash
# 포트 20443 복원 및 Apache 재시작 스크립트

echo "=== ex-GPT 시스템 설정 시작 ==="

# 1. 새로운 설정 파일 적용 (ProxyPass 문제 해결)
echo "1. Apache 설정 파일 업데이트중..."
cp /home/aigen/port-20443-fixed.conf /etc/httpd/conf.d/port-20443.conf

# 2. Listen 20443 추가 (없으면)
echo "2. Listen 20443 설정 확인중..."
if ! grep -q "^Listen 20443" /etc/httpd/conf/httpd.conf; then
    echo "Listen 20443" >> /etc/httpd/conf/httpd.conf
    echo "   - Listen 20443 추가됨"
else
    echo "   - Listen 20443 이미 존재함"
fi

# 3. UI 파일 권한 확인
echo "3. UI 파일 권한 확인중..."
chown -R aigen:aigen /var/www/html/admin/
chown -R aigen:aigen /var/www/html/exGenBotDS/
chmod -R 755 /var/www/html/admin/
chmod -R 755 /var/www/html/exGenBotDS/
echo "   - 권한 설정 완료"

# 4. Apache 설정 테스트
echo "4. Apache 설정 테스트중..."
apachectl configtest
if [ $? -ne 0 ]; then
    echo "❌ Apache 설정 오류 발생!"
    exit 1
fi

# 5. Apache 재시작
echo "5. Apache 재시작중..."
systemctl restart httpd
if [ $? -eq 0 ]; then
    echo "✅ Apache가 성공적으로 재시작되었습니다!"
else
    echo "❌ Apache 재시작 실패!"
    systemctl status httpd
    exit 1
fi

# 6. 포트 리스닝 확인
echo "6. 포트 20443 리스닝 확인중..."
sleep 2
if ss -tlnp | grep -q ":20443"; then
    echo "✅ 포트 20443이 정상적으로 리스닝 중입니다!"
    ss -tlnp | grep ":20443"
else
    echo "❌ 포트 20443이 리스닝되지 않습니다!"
    exit 1
fi

# 7. 백엔드 API 확인
echo "7. 백엔드 API 서버 확인중..."
if curl -s http://localhost:8010/api/v1/admin/conversations/simple?page=1&limit=1 > /dev/null 2>&1; then
    echo "✅ Admin API 서버 정상 작동중 (포트 8010)"
else
    echo "⚠️  Admin API 서버 확인 필요 (포트 8010)"
fi

if curl -s http://localhost:8080/api/chat/health > /dev/null 2>&1; then
    echo "✅ User API 서버 정상 작동중 (포트 8080)"
else
    echo "⚠️  User API 서버 확인 필요 (포트 8080)"
fi

echo ""
echo "=== 🎉 설정 완료 ==="
echo ""
echo "📱 사용자 UI (ex-GPT 채팅):"
echo "   https://ui.datastreams.co.kr:20443/exGenBotDS/ai"
echo "   https://ui.datastreams.co.kr:20443/exGenBotDS/testOld"
echo ""
echo "🎛️  관리자 대시보드:"
echo "   https://ui.datastreams.co.kr:20443/admin/"
echo ""
echo "💬 대화내역 페이지 (5,014개 대화):"
echo "   https://ui.datastreams.co.kr:20443/admin/#/conversations"
echo ""
echo "📊 통계 대시보드:"
echo "   https://ui.datastreams.co.kr:20443/admin/#/"
echo ""
