#!/bin/bash
# pg_hba.conf 업데이트 스크립트
# Docker 네트워크 (172.31.0.0/16)를 EDB에 추가

PG_HBA_CONF="/var/lib/edb/as14/data/pg_hba.conf"
DOCKER_NETWORK="host    all             all             172.31.0.0/16           md5"

echo "=== EDB pg_hba.conf 업데이트 ==="
echo "Docker 네트워크 172.31.0.0/16을 추가합니다."
echo ""

# 백업 생성
echo "1. 백업 생성 중..."
sudo cp "$PG_HBA_CONF" "$PG_HBA_CONF.backup.$(date +%Y%m%d_%H%M%S)"

# 이미 추가되어 있는지 확인
if sudo grep -q "172.31.0.0/16" "$PG_HBA_CONF"; then
    echo "✓ 이미 Docker 네트워크가 설정되어 있습니다."
else
    echo "2. Docker 네트워크 추가 중..."
    # IPv4 host 섹션 뒤에 추가
    sudo sed -i '/^host.*127.0.0.1\/32.*md5/a\'"$DOCKER_NETWORK" "$PG_HBA_CONF"
    echo "✓ Docker 네트워크가 추가되었습니다."
fi

# 설정 파일 확인
echo ""
echo "3. 현재 설정:"
sudo grep -E "^host" "$PG_HBA_CONF" | head -10

# EDB 재시작
echo ""
echo "4. EDB 설정 리로드 중..."
sudo systemctl reload edb-as-14

# 상태 확인
echo ""
echo "5. EDB 상태 확인:"
sudo systemctl status edb-as-14 --no-pager | head -10

echo ""
echo "=== 완료 ==="
echo "이제 Docker 컨테이너에서 EDB에 접속할 수 있습니다."
