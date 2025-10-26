#!/bin/bash
# 모든 Apache 설정 파일의 SSL 인증서 경로 수정

echo "=== 모든 SSL 설정 수정 ==="

# 1. SSL 인증서 확인/생성
if [ ! -f /etc/pki/tls/certs/server.crt ]; then
    echo "1. SSL 인증서 생성중..."
    openssl req -x509 -nodes -days 365 \
      -newkey rsa:2048 \
      -keyout /etc/pki/tls/private/server.key \
      -out /etc/pki/tls/certs/server.crt \
      -subj "/C=KR/ST=Seoul/L=Seoul/O=Korea Expressway Corporation/CN=ui.datastreams.co.kr"
    
    chmod 600 /etc/pki/tls/private/server.key
    chmod 644 /etc/pki/tls/certs/server.crt
    echo "   ✅ SSL 인증서 생성 완료"
else
    echo "1. SSL 인증서 이미 존재"
fi

# 2. 모든 Apache 설정 파일에서 SSL 경로 수정
echo "2. Apache 설정 파일 수정..."

# port-20443.conf
sed -i 's|SSLCertificateFile /root/server.crt|SSLCertificateFile /etc/pki/tls/certs/server.crt|g' /etc/httpd/conf.d/port-20443.conf
sed -i 's|SSLCertificateKeyFile /root/server.key|SSLCertificateKeyFile /etc/pki/tls/private/server.key|g' /etc/httpd/conf.d/port-20443.conf

# ssl.conf
sed -i 's|SSLCertificateFile /root/server.crt|SSLCertificateFile /etc/pki/tls/certs/server.crt|g' /etc/httpd/conf.d/ssl.conf
sed -i 's|SSLCertificateKeyFile /root/server.key|SSLCertificateKeyFile /etc/pki/tls/private/server.key|g' /etc/httpd/conf.d/ssl.conf

echo "   ✅ 설정 파일 수정 완료"

# 3. 수정된 라인 확인
echo "3. 수정된 설정 확인..."
echo "   [port-20443.conf]"
grep "SSLCertificate" /etc/httpd/conf.d/port-20443.conf
echo "   [ssl.conf]"
grep "SSLCertificate" /etc/httpd/conf.d/ssl.conf | grep -v "^#" | head -5

# 4. Apache 설정 테스트
echo "4. Apache 설정 테스트..."
httpd -t
if [ $? -ne 0 ]; then
    echo "   ❌ Apache 설정 오류!"
    exit 1
fi

echo "   ✅ Apache 설정 정상"

# 5. Apache 재시작
echo "5. Apache 재시작..."
systemctl restart httpd
if [ $? -eq 0 ]; then
    echo "   ✅ Apache 재시작 완료"
else
    echo "   ❌ Apache 재시작 실패"
    exit 1
fi

# 6. VirtualHost 확인
echo "6. VirtualHost 설정 확인..."
httpd -S 2>&1 | grep -E "443|20443"

echo ""
echo "=== ✅ 완료 ==="
echo ""
echo "테스트:"
echo "  curl -I https://localhost:20443/exGenBotDS/ai -k"
echo "  curl -I https://localhost:443/admin/ -k"
