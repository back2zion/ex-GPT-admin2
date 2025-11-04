#!/bin/bash
# RQ Worker 시작 스크립트 (H100 2대 활용)
# 각 GPU에 2개씩 총 4개 Worker 실행

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "🚀 Starting RQ Workers for STT Batch Processing"
echo "🎮 GPU Configuration: H100 x 2"
echo "👷 Worker Configuration: 4 workers (2 per GPU)"
echo ""

# Redis 연결 확인
echo "🔍 Checking Redis connection..."
redis-cli ping > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Redis is not running!"
    echo "   Start Redis first: sudo systemctl start redis"
    exit 1
fi
echo "✅ Redis is running"
echo ""

# 기존 Worker 중지
echo "🛑 Stopping existing workers..."
pkill -f "rq worker stt-queue" || true
sleep 2

# Worker 로그 디렉토리
LOG_DIR="/var/log/rq-workers"
sudo mkdir -p "$LOG_DIR"
sudo chown aigen:aigen "$LOG_DIR"

# Worker 1: GPU 0
echo "👷 Starting Worker 1 (GPU 0)..."
CUDA_VISIBLE_DEVICES=0 nohup rq worker stt-queue \
    --url redis://localhost:6379/0 \
    --name worker-gpu0-1 \
    --with-scheduler \
    > "$LOG_DIR/worker-gpu0-1.log" 2>&1 &

# Worker 2: GPU 0
echo "👷 Starting Worker 2 (GPU 0)..."
CUDA_VISIBLE_DEVICES=0 nohup rq worker stt-queue \
    --url redis://localhost:6379/0 \
    --name worker-gpu0-2 \
    > "$LOG_DIR/worker-gpu0-2.log" 2>&1 &

# Worker 3: GPU 1
echo "👷 Starting Worker 3 (GPU 1)..."
CUDA_VISIBLE_DEVICES=1 nohup rq worker stt-queue \
    --url redis://localhost:6379/0 \
    --name worker-gpu1-1 \
    > "$LOG_DIR/worker-gpu1-1.log" 2>&1 &

# Worker 4: GPU 1
echo "👷 Starting Worker 4 (GPU 1)..."
CUDA_VISIBLE_DEVICES=1 nohup rq worker stt-queue \
    --url redis://localhost:6379/0 \
    --name worker-gpu1-2 \
    > "$LOG_DIR/worker-gpu1-2.log" 2>&1 &

sleep 3

# Worker 상태 확인
echo ""
echo "📊 Worker Status:"
ps aux | grep "rq worker stt-queue" | grep -v grep | awk '{print "   " $2, $11, $12, $13, $14}'

echo ""
echo "✅ All workers started!"
echo ""
echo "📝 Logs:"
echo "   GPU 0 Worker 1: tail -f $LOG_DIR/worker-gpu0-1.log"
echo "   GPU 0 Worker 2: tail -f $LOG_DIR/worker-gpu0-2.log"
echo "   GPU 1 Worker 1: tail -f $LOG_DIR/worker-gpu1-1.log"
echo "   GPU 1 Worker 2: tail -f $LOG_DIR/worker-gpu1-2.log"
echo ""
echo "🛑 To stop workers:"
echo "   pkill -f 'rq worker stt-queue'"
