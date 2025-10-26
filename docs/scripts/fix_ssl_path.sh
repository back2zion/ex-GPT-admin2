#!/bin/bash
# SSL 인증서를 /etc/pki/tls/로 생성하고 Apache 설정 변경

echo "=== SSL 인증서 생성 및 Apache 설정 수정 ==="

# 1. SSL 인증서 생성 (/etc/pki/tls/ 디렉토리 - Apache 기본 경로)
echo "1. SSL 인증서 생성중..."
openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout /etc/pki/tls/private/server.key \
  -out /etc/pki/tls/certs/server.crt \
  -subj "/C=KR/ST=Seoul/L=Seoul/O=Korea Expressway Corporation/CN=ui.datastreams.co.kr"

chmod 600 /etc/pki/tls/private/server.key
chmod 644 /etc/pki/tls/certs/server.crt

echo "   ✅ SSL 인증서 생성 완료"
ls -lh /etc/pki/tls/certs/server.crt
ls -lh /etc/pki/tls/private/server.key

# 2. Apache 설정 수정
echo "2. Apache 설정 파일 수정..."
sed -i 's|SSLCertificateFile /root/server.crt|SSLCertificateFile /etc/pki/tls/certs/server.crt|g' /etc/httpd/conf.d/port-20443.conf
sed -i 's|SSLCertificateKeyFile /root/server.key|SSLCertificateKeyFile /etc/pki/tls/private/server.key|g' /etc/httpd/conf.d/port-20443.conf

echo "   ✅ 설정 파일 수정 완료"

# 3. Apache 설정 테스트
echo "3. Apache 설정 테스트..."
httpd -t
if [ $? -ne 0 ]; then
    echo "   ❌ Apache 설정 오류!"
    exit 1
fi

echo "   ✅ Apache 설정 정상"

# 4. Apache 재시작
echo "4. Apache 재시작..."
systemctl restart httpd
if [ $? -eq 0 ]; then
    echo "   ✅ Apache 재시작 완료"
else
    echo "   ❌ Apache 재시작 실패"
    exit 1
fi

# 5. VirtualHost 확인
echo "5. VirtualHost 설정 확인..."
httpd -S 2>&1 | grep -A5 "20443"

echo ""
echo "=== ✅ 완료 ==="
echo ""
echo "테스트 명령어:"
echo "  curl -I https://localhost:20443/exGenBotDS/ai -k"
