#!/bin/bash
# SSL 인증서 경로만 수정 (기존 설정 유지)

echo "=== SSL 인증서 경로 수정 ==="

# 1. 백업
echo "1. 현재 설정 백업..."
cp /etc/httpd/conf.d/port-20443.conf /etc/httpd/conf.d/port-20443.conf.backup_$(date +%Y%m%d_%H%M%S)

# 2. SSL 인증서 경로 수정 (localhost.crt -> server.crt)
echo "2. SSL 인증서 경로 수정..."
sed -i 's|/etc/pki/tls/certs/localhost.crt|/root/server.crt|g' /etc/httpd/conf.d/port-20443.conf
sed -i 's|/etc/pki/tls/private/localhost.key|/root/server.key|g' /etc/httpd/conf.d/port-20443.conf

echo "   ✅ 경로 수정 완료"

# 3. 변경 내용 확인
echo "3. 변경 내용 확인..."
grep -n "SSLCertificate" /etc/httpd/conf.d/port-20443.conf

# 4. Apache 설정 테스트
echo "4. Apache 설정 테스트..."
httpd -t
if [ $? -ne 0 ]; then
    echo "   ❌ 설정 오류! 백업 복원..."
    cp /etc/httpd/conf.d/port-20443.conf.backup_* /etc/httpd/conf.d/port-20443.conf
    exit 1
fi

# 5. Apache 재시작
echo "5. Apache 재시작..."
systemctl restart httpd
if [ $? -eq 0 ]; then
    echo "   ✅ Apache 재시작 완료"
else
    echo "   ❌ Apache 재시작 실패"
    exit 1
fi

# 6. 포트 확인
echo "6. 포트 리스닝 확인..."
sleep 2
ss -tlnp | grep -E ":20443"

echo ""
echo "=== ✅ 완료 ==="
echo ""
echo "접속 URL:"
echo "  - https://ui.datastreams.co.kr:20443/exGenBotDS/testOld"
echo "  - https://ui.datastreams.co.kr:20443/exGenBotDS/ai"
echo "  - https://ui.datastreams.co.kr:20443/admin/"
