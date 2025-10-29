# RQ 기반 STT 병렬 처리 시스템 사용 가이드

**날짜**: 2025-10-28
**버전**: 1.0
**GPU**: H100 x 2
**Workers**: 4 (GPU당 2개)

---

## 📋 시스템 아키텍처

```
┌──────────────────────────────────────────────────────────┐
│                     Redis Queue (RQ)                     │
│              stt-queue (작업 큐)                         │
└──────────────────────────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼              ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │Worker 1 │    │Worker 2 │    │Worker 3 │    │Worker 4 │
    │ GPU 0   │    │ GPU 0   │    │ GPU 1   │    │ GPU 1   │
    └─────────┘    └─────────┘    └─────────┘    └─────────┘
          │              │              │              │
          └──────────────┴──────────────┴──────────────┘
                         ▼
                  ex-GPT-STT API
                  (localhost:9200)
                         │
                         ▼
                  Whisper large-v3
                  (H100 GPU 처리)
                         │
                         ▼
            /data/stt-results/batch_{id}/
               (txt 파일 저장)
```

---

## 🚀 1단계: Worker 시작

### 방법 1: 스크립트 사용 (권장)

```bash
cd /home/aigen/admin-api
bash scripts/start-rq-workers.sh
```

출력:
```
🚀 Starting RQ Workers for STT Batch Processing
🎮 GPU Configuration: H100 x 2
👷 Worker Configuration: 4 workers (2 per GPU)

✅ Redis is running

👷 Starting Worker 1 (GPU 0)...
👷 Starting Worker 2 (GPU 0)...
👷 Starting Worker 3 (GPU 1)...
👷 Starting Worker 4 (GPU 1)...

📊 Worker Status:
   12345 rq worker stt-queue --name worker-gpu0-1
   12346 rq worker stt-queue --name worker-gpu0-2
   12347 rq worker stt-queue --name worker-gpu1-1
   12348 rq worker stt-queue --name worker-gpu1-2

✅ All workers started!
```

### 방법 2: 수동 실행

```bash
# Terminal 1 (GPU 0 Worker 1)
CUDA_VISIBLE_DEVICES=0 rq worker stt-queue \
    --url redis://localhost:6379/0 \
    --name worker-gpu0-1 \
    --with-scheduler

# Terminal 2 (GPU 0 Worker 2)
CUDA_VISIBLE_DEVICES=0 rq worker stt-queue \
    --url redis://localhost:6379/0 \
    --name worker-gpu0-2

# Terminal 3 (GPU 1 Worker 1)
CUDA_VISIBLE_DEVICES=1 rq worker stt-queue \
    --url redis://localhost:6379/0 \
    --name worker-gpu1-1

# Terminal 4 (GPU 1 Worker 2)
CUDA_VISIBLE_DEVICES=1 rq worker stt-queue \
    --url redis://localhost:6379/0 \
    --name worker-gpu1-2
```

---

## 📤 2단계: 배치 작업 등록

### API: POST /api/v1/admin/stt-batches/{batch_id}/start-rq

```bash
# 1. 배치 생성
curl -X POST "http://localhost:8010/api/v1/admin/stt-batches" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "500만건 배치 처리",
    "source_path": "/data/audio",
    "file_pattern": "*.mp3",
    "created_by": "admin",
    "priority": "high"
  }'

# 응답: {"id": 1, "name": "500만건 배치 처리", ...}

# 2. 배치 시작 (RQ)
curl -X POST "http://localhost:8010/api/v1/admin/stt-batches/1/start-rq"

# 응답:
{
  "message": "배치 처리가 시작되었습니다 (RQ Worker 1000개 작업 등록)",
  "batch_id": 1,
  "total_files": 1000,
  "job_ids": ["abc123", "def456", ...],
  "total_jobs": 1000,
  "estimated_time_hours": 4.17,
  "workers": "4 workers (2 per GPU)"
}
```

---

## 📊 3단계: 진행 상황 모니터링

### API: GET /api/v1/admin/stt-batches/{batch_id}/rq-progress

```bash
curl "http://localhost:8010/api/v1/admin/stt-batches/1/rq-progress"
```

응답:
```json
{
  "batch_id": 1,
  "total": 1000,
  "queued": 850,        // 대기 중
  "started": 4,         // 처리 중 (4개 Worker)
  "finished": 146,      // 완료
  "failed": 0,          // 실패
  "progress_percentage": 14.6,
  "db_completed_files": 146,
  "batch_status": "processing"
}
```

### Worker 로그 확인

```bash
# GPU 0 Worker 1
tail -f /var/log/rq-workers/worker-gpu0-1.log

# GPU 1 Worker 1
tail -f /var/log/rq-workers/worker-gpu1-1.log

# 모든 Worker 로그
tail -f /var/log/rq-workers/*.log
```

---

## 📥 4단계: 결과 다운로드

### 개별 txt 파일 확인

```bash
ls /data/stt-results/batch_1/
# 출력:
# file001.txt
# file002.txt
# file003.txt
# ...
```

### ZIP 다운로드 (API)

```bash
# 전사 결과만
curl "http://localhost:8010/api/v1/admin/stt-batches/1/download-all" \
  -o batch_1_results.zip

# 전사 + 회의록
curl "http://localhost:8010/api/v1/admin/stt-batches/1/download-all?include_minutes=true" \
  -o batch_1_full_results.zip
```

### 결과 정보 조회

```bash
curl "http://localhost:8010/api/v1/admin/stt-batches/1/results-info"
```

응답:
```json
{
  "batch_id": 1,
  "results_available": true,
  "total_files": 2000,
  "transcription_files": 1000,
  "minutes_files": 1000,
  "total_size_mb": 156.78,
  "results_path": "/data/stt-results/batch_1"
}
```

---

## 🛑 작업 중단

### API: POST /api/v1/admin/stt-batches/{batch_id}/cancel-rq

```bash
curl -X POST "http://localhost:8010/api/v1/admin/stt-batches/1/cancel-rq"
```

응답:
```json
{
  "message": "850개 작업이 취소되었습니다",
  "cancelled_jobs": 850,
  "batch_id": 1
}
```

---

## 🔧 문제 해결

### 1. Worker가 시작되지 않음

```bash
# Redis 상태 확인
redis-cli ping
# 응답: PONG

# Redis 시작 (필요시)
sudo systemctl start redis

# Worker 프로세스 확인
ps aux | grep "rq worker"
```

### 2. GPU가 인식되지 않음

```bash
# GPU 상태 확인
nvidia-smi

# CUDA 환경변수 확인
echo $CUDA_VISIBLE_DEVICES

# Worker 재시작 (GPU 명시)
CUDA_VISIBLE_DEVICES=0,1 bash scripts/start-rq-workers.sh
```

### 3. 작업이 처리되지 않음

```bash
# RQ 큐 상태 확인
rq info --url redis://localhost:6379/0

# 출력:
# stt-queue: 850 jobs
# 4 workers online

# 실패한 작업 조회
rq info --url redis://localhost:6379/0 --only-failed
```

### 4. Worker 로그 확인

```bash
# 에러 로그만 필터링
grep "ERROR\|FAILED" /var/log/rq-workers/*.log

# 실시간 모니터링
tail -f /var/log/rq-workers/*.log | grep "Processing\|Saved\|Failed"
```

---

## 📈 성능 예측

### 현재 구성 (H100 2대, 4 Workers)

| 항목 | 값 |
|------|-----|
| STT 처리 속도 | ~10x realtime (37분 음성 → 4분) |
| 병렬 처리 능력 | 4개 파일 동시 처리 |
| 시간당 처리량 | ~60개 파일 |
| **100만 파일 예상 소요** | ~695일 (23개월) |
| **500만 파일 예상 소요** | ~3,472일 (9.5년) |

### 최적화 필요 시

1. **Worker 증설** (GPU당 4개 → 8개):
   - 시간당 처리량: ~120개 파일
   - 500만 파일: ~4.8년

2. **GPU 추가** (H100 4대):
   - 시간당 처리량: ~240개 파일
   - 500만 파일: ~2.4년

3. **클라우드 병렬화** (100개 Worker):
   - 시간당 처리량: ~1500개 파일
   - 500만 파일: ~4.7개월

---

## 🔒 보안 체크리스트

- ✅ Path Traversal 방지 (scan_audio_files)
- ✅ SQL Injection 방지 (SQLAlchemy ORM)
- ✅ 권한 검증 (Cerbos)
- ✅ 파일 크기 제한 (1GB)
- ✅ Redis 접근 제어

---

## 📚 관련 문서

- [STT_BATCH_PROCESSING_IMPLEMENTATION.md](./STT_BATCH_PROCESSING_IMPLEMENTATION.md) - 구현 상세
- [PRD.md](./PRD.md) - 요구사항
- [RQ Documentation](https://python-rq.org/) - RQ 공식 문서

---

**작성자**: Claude (RQ 병렬 처리 구현)
**검토자**: 한국도로공사 디지털계획처 AI데이터팀
