#!/bin/bash
# 프론트 서버 (1.215.235.250)에 /ai 경로 설정 추가
# 이 스크립트를 1.215.235.250 서버에 복사해서 실행하세요

echo "=== 프론트 서버 /ai 경로 설정 ===" echo ""

# 1. /testOld 확인
echo "1. /testOld 작동 확인..."
TEST_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://localhost:20443/exGenBotDS/testOld -k)
if [ "$TEST_STATUS" != "200" ]; then
    echo "   ❌ /testOld가 정상 작동하지 않습니다 (HTTP $TEST_STATUS)"
    echo "   계속 진행하시겠습니까? (y/N)"
    read -r response
    if [ "$response" != "y" ]; then
        exit 1
    fi
else
    echo "   ✅ /testOld 정상 작동 중 (HTTP 200)"
fi

# 2. port-20443.conf 확인
echo ""
echo "2. Apache 설정 파일 확인..."
if [ ! -f /etc/httpd/conf.d/port-20443.conf ]; then
    echo "   ❌ port-20443.conf 파일이 없습니다"
    exit 1
fi
echo "   ✅ port-20443.conf 존재"

# 3. 이미 설정되어 있는지 확인
if grep -q "ProxyPass /exGenBotDS/ai !" /etc/httpd/conf.d/port-20443.conf; then
    echo "   ⚠️  port-20443.conf에 이미 설정되어 있습니다"
    PORT_CONF_DONE=true
else
    PORT_CONF_DONE=false
fi

if [ -f /etc/httpd/conf.d/ssl.conf ]; then
    if grep -q "ProxyPass /exGenBotDS/ai !" /etc/httpd/conf.d/ssl.conf; then
        echo "   ⚠️  ssl.conf에 이미 설정되어 있습니다"
        SSL_CONF_DONE=true
    else
        SSL_CONF_DONE=false
    fi
else
    SSL_CONF_DONE=true  # ssl.conf가 없으면 스킵
fi

if [ "$PORT_CONF_DONE" = true ] && [ "$SSL_CONF_DONE" = true ]; then
    echo "   ✅ 모든 설정이 이미 완료되어 있습니다"
    echo ""
    echo "=== 완료 ==="
    exit 0
fi

# 4. port-20443.conf 백업 및 수정
if [ "$PORT_CONF_DONE" = false ]; then
    echo ""
    echo "3. port-20443.conf 백업 및 수정..."
    cp /etc/httpd/conf.d/port-20443.conf /etc/httpd/conf.d/port-20443.conf.backup_ai_$(date +%Y%m%d_%H%M%S)
    echo "   ✅ 백업 완료"

    # ProxyPreserveHost On 다음 줄에 제외 규칙 추가
    sed -i '/ProxyPreserveHost On/a\
\
    # /exGenBotDS/ai는 프록시하지 않음 (React 정적 파일)\
    ProxyPass /exGenBotDS/ai !' /etc/httpd/conf.d/port-20443.conf

    echo "   ✅ ProxyPass 제외 규칙 추가"
fi

# 5. ssl.conf 백업 및 수정 (파일이 있으면)
if [ -f /etc/httpd/conf.d/ssl.conf ] && [ "$SSL_CONF_DONE" = false ]; then
    echo ""
    echo "4. ssl.conf 백업 및 수정..."
    cp /etc/httpd/conf.d/ssl.conf /etc/httpd/conf.d/ssl.conf.backup_ai_$(date +%Y%m%d_%H%M%S)
    echo "   ✅ 백업 완료"

    # ProxyPass /exGenBotDS/ 규칙 찾기
    LINE_NUM=$(grep -n "^ProxyPass /exGenBotDS/ " /etc/httpd/conf.d/ssl.conf | cut -d: -f1)

    if [ -n "$LINE_NUM" ]; then
        # 그 줄 바로 앞에 제외 규칙 추가
        sed -i "${LINE_NUM}i\\
# /ai는 프록시하지 않음 (React 정적 파일)\\
ProxyPass /exGenBotDS/ai !\\
" /etc/httpd/conf.d/ssl.conf
        echo "   ✅ ProxyPass 제외 규칙 추가"
    else
        echo "   ⚠️  ProxyPass /exGenBotDS/ 규칙을 찾을 수 없습니다 (건너뜀)"
    fi
fi

# 6. Apache 설정 테스트
echo ""
echo "5. Apache 설정 테스트..."
httpd -t 2>&1 | grep -q "Syntax OK"
if [ $? -ne 0 ]; then
    echo "   ❌ Apache 설정 오류!"
    httpd -t
    echo ""
    echo "   롤백 중..."

    if [ "$PORT_CONF_DONE" = false ]; then
        BACKUP=$(ls -t /etc/httpd/conf.d/port-20443.conf.backup_ai_* 2>/dev/null | head -1)
        if [ -n "$BACKUP" ]; then
            cp "$BACKUP" /etc/httpd/conf.d/port-20443.conf
        fi
    fi

    if [ -f /etc/httpd/conf.d/ssl.conf ] && [ "$SSL_CONF_DONE" = false ]; then
        BACKUP=$(ls -t /etc/httpd/conf.d/ssl.conf.backup_ai_* 2>/dev/null | head -1)
        if [ -n "$BACKUP" ]; then
            cp "$BACKUP" /etc/httpd/conf.d/ssl.conf
        fi
    fi

    exit 1
fi
echo "   ✅ 설정 정상"

# 7. Apache reload
echo ""
echo "6. Apache reload..."
systemctl reload httpd
if [ $? -ne 0 ]; then
    echo "   ❌ Apache reload 실패!"
    exit 1
fi
echo "   ✅ Reload 완료"

# 8. 확인
echo ""
echo "7. 동작 확인..."
sleep 2
TEST_OLD=$(curl -s -o /dev/null -w "%{http_code}" https://localhost:20443/exGenBotDS/testOld -k)
TEST_AI=$(curl -s -o /dev/null -w "%{http_code}" https://localhost:20443/exGenBotDS/ai -k)

echo "   /testOld: HTTP $TEST_OLD"
echo "   /ai: HTTP $TEST_AI"

if [ "$TEST_OLD" != "200" ]; then
    echo ""
    echo "   ❌ /testOld 작동 중단! 롤백..."

    if [ "$PORT_CONF_DONE" = false ]; then
        BACKUP=$(ls -t /etc/httpd/conf.d/port-20443.conf.backup_ai_* 2>/dev/null | head -1)
        if [ -n "$BACKUP" ]; then
            cp "$BACKUP" /etc/httpd/conf.d/port-20443.conf
        fi
    fi

    if [ -f /etc/httpd/conf.d/ssl.conf ] && [ "$SSL_CONF_DONE" = false ]; then
        BACKUP=$(ls -t /etc/httpd/conf.d/ssl.conf.backup_ai_* 2>/dev/null | head -1)
        if [ -n "$BACKUP" ]; then
            cp "$BACKUP" /etc/httpd/conf.d/ssl.conf
        fi
    fi

    systemctl reload httpd
    exit 1
fi

echo ""
echo "=== ✅ 완료 ===" echo ""
echo "📋 결과:"
echo "   /testOld: HTTP $TEST_OLD ✅"
echo "   /ai: HTTP $TEST_AI"
echo ""
echo "🌐 브라우저 테스트:"
echo "   https://ui.datastreams.co.kr:20443/exGenBotDS/ai"
echo ""
echo "📁 백업 파일:"
if [ "$PORT_CONF_DONE" = false ]; then
    BACKUP=$(ls -t /etc/httpd/conf.d/port-20443.conf.backup_ai_* 2>/dev/null | head -1)
    echo "   $BACKUP"
fi
if [ -f /etc/httpd/conf.d/ssl.conf ] && [ "$SSL_CONF_DONE" = false ]; then
    BACKUP=$(ls -t /etc/httpd/conf.d/ssl.conf.backup_ai_* 2>/dev/null | head -1)
    echo "   $BACKUP"
fi
