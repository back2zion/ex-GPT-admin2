#!/bin/bash
# 가장 간단한 해결책: SSL 인증서 생성 후 Apache 재시작

echo "=== SSL 인증서 생성 및 Apache 재시작 ==="

# 1. SSL 인증서 생성 (없을 경우에만)
if [ ! -f "/root/server.crt" ] || [ ! -f "/root/server.key" ]; then
    echo "1. SSL 인증서 생성중..."
    openssl req -x509 -nodes -days 365 \
      -newkey rsa:2048 \
      -keyout /root/server.key \
      -out /root/server.crt \
      -subj "/C=KR/ST=Seoul/L=Seoul/O=Korea Expressway Corporation/CN=ui.datastreams.co.kr" > /dev/null 2>&1

    chmod 600 /root/server.key
    chmod 644 /root/server.crt
    echo "   ✅ SSL 인증서 생성 완료"
else
    echo "1. SSL 인증서 이미 존재함"
fi

# 2. Apache 설정 테스트
echo "2. Apache 설정 테스트..."
httpd -t
if [ $? -ne 0 ]; then
    echo "   ❌ Apache 설정 오류!"
    exit 1
fi

# 3. Apache 재시작
echo "3. Apache 재시작..."
systemctl restart httpd
if [ $? -eq 0 ]; then
    echo "   ✅ Apache 재시작 완료"
else
    echo "   ❌ Apache 재시작 실패"
    exit 1
fi

# 4. 포트 확인
echo "4. 포트 리스닝 확인..."
sleep 2
ss -tlnp | grep -E ":443|:20443"

echo ""
echo "=== 완료 ==="
