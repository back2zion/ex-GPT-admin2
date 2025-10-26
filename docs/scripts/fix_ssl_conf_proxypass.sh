#!/bin/bash
# ssl.conf의 ProxyPass 규칙 수정

echo "=== ssl.conf ProxyPass 규칙 수정 ==="

# 백업
cp /etc/httpd/conf.d/ssl.conf /etc/httpd/conf.d/ssl.conf.backup_$(date +%Y%m%d_%H%M%S)

# /exGenBotDS/ ProxyPass 제거 (너무 포괄적)
sed -i 's|^ProxyPass /exGenBotDS/ http://localhost:18180/exGenBotDS/|#ProxyPass /exGenBotDS/ http://localhost:18180/exGenBotDS/  # Disabled - too broad|g' /etc/httpd/conf.d/ssl.conf

# 구체적인 ProxyPass 추가 (testOld만)
sed -i '/^#ProxyPass \/exGenBotDS\/ http/a\
# Specific ProxyPass rules (like port-20443.conf)\
ProxyPass /exGenBotDS/testOld http://localhost:18180/exGenBotDS/testOld\
ProxyPassReverse /exGenBotDS/testOld http://localhost:18180/exGenBotDS/testOld' /etc/httpd/conf.d/ssl.conf

echo "수정된 ProxyPass 규칙:"
grep -n "ProxyPass.*exGenBotDS" /etc/httpd/conf.d/ssl.conf

# Apache 재시작
echo ""
echo "Apache 재시작..."
systemctl restart httpd

if [ $? -eq 0 ]; then
    echo "✅ 완료!"
    echo ""
    echo "이제 브라우저에서 테스트:"
    echo "  https://ui.datastreams.co.kr:20443/exGenBotDS/ai"
    echo "  https://ui.datastreams.co.kr/exGenBotDS/ai (포트 없이)"
else
    echo "❌ Apache 재시작 실패"
fi
