#!/bin/bash
# Apache 설정 업데이트 스크립트

echo "Apache 설정 백업 중..."
sudo cp /etc/httpd/conf.d/ssl.conf /etc/httpd/conf.d/ssl.conf.backup.$(date +%Y%m%d_%H%M%S)

echo "Apache 설정 업데이트 중..."
sudo cp /tmp/ssl.conf.new /etc/httpd/conf.d/ssl.conf

echo "Apache 설정 검증 중..."
sudo apachectl configtest

if [ $? -eq 0 ]; then
    echo "Apache 재시작 중..."
    sudo systemctl restart httpd
    echo "✅ Apache 재시작 완료!"
else
    echo "❌ Apache 설정 오류 발생. 백업 파일로 복구하세요."
    exit 1
fi
