# Docker Setup Guide - Fine-tuning MLOps

## 개요

Fine-tuning MLOps 시스템은 다음 컨테이너로 구성됩니다:

| 서비스 | 포트 | 용도 | GPU 필요 |
|--------|------|------|----------|
| `admin-api` | 8010:8001 | 관리자 API (FastAPI) | Optional |
| `user-api` | 8080:8001 | 사용자 API (FastAPI) | No |
| `celery-worker` | - | Fine-tuning 작업 처리 | **Required** |
| `postgres` | 5432 | 데이터베이스 (PostgreSQL) | No |
| `redis` | 6379 | Celery Broker/Backend | No |
| `mlflow` | 5000 | 실험 추적 서버 | No |
| `cerbos` | 3592, 3593 | 권한 관리 | No |

## 아키텍처

```
┌─────────────────┐     ┌─────────────────┐
│   Admin API     │────▶│  Celery Worker  │ (GPU)
│   (FastAPI)     │     │  Fine-tuning    │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ├───────────┬───────────┼───────────┐
         │           │           │           │
    ┌────▼───┐  ┌───▼────┐  ┌───▼────┐  ┌──▼──────┐
    │Postgres│  │ Redis  │  │ MLflow │  │ Qdrant  │
    │  (DB)  │  │(Broker)│  │(Tracking)│ │(Vector)│
    └────────┘  └────────┘  └────────┘  └─────────┘
```

## 시작하기

### 1. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 필수 환경 변수 설정
vi .env
```

**중요 환경 변수:**
- `DATABASE_URL`: PostgreSQL 연결 문자열
- `REDIS_URL`: Redis 연결 문자열
- `MLFLOW_TRACKING_URI`: MLflow 서버 URL
- `HF_TOKEN`: (Optional) Hugging Face 토큰 (Private 모델 사용 시)

### 2. 전체 스택 시작

```bash
# 모든 서비스 시작
docker compose up -d

# 로그 확인
docker compose logs -f

# 특정 서비스 로그 확인
docker compose logs -f celery-worker
```

### 3. Celery Worker만 시작 (개발/테스트)

```bash
# Worker만 시작 (의존성 서비스도 함께 시작)
docker compose up -d celery-worker

# Worker 로그 확인
docker compose logs -f celery-worker
```

## Docker 이미지

### 1. API 서버 이미지 (`Dockerfile`)

**특징:**
- Python 3.11 slim base
- Poetry 의존성 관리
- Uvicorn ASGI 서버
- 개발 모드: `--reload` 활성화

**빌드:**
```bash
docker build -t admin-api:latest .
```

### 2. Celery Worker 이미지 (`Dockerfile.worker`)

**특징:**
- Python 3.11 slim base
- GPU 지원 (NVIDIA Docker)
- 비루트 사용자 실행 (시큐어 코딩)
- 메모리 효율적 설정 (concurrency=1, max-tasks-per-child=1)

**빌드:**
```bash
docker build -f Dockerfile.worker -t admin-api-celery-worker:latest .
```

**시큐어 코딩:**
- 비루트 사용자 (UID 1000) 실행
- 읽기 전용 볼륨 마운트 (애플리케이션 코드)
- 환경 변수로 시크릿 관리 (하드코딩 금지)
- 최소 권한 원칙

## 볼륨 관리

### Named Volumes

| Volume | 용도 | 경로 |
|--------|------|------|
| `postgres_data` | PostgreSQL 데이터 | `/var/lib/postgresql/data` |
| `redis_data` | Redis 영속 데이터 | `/data` |
| `mlflow_artifacts` | MLflow 아티팩트 | `/mlflow/artifacts` |
| `finetuning_models` | Fine-tuned 모델 | `/data/models/finetuned` |
| `finetuning_logs` | 학습 로그 | `/data/logs/finetuning` |
| `finetuning_datasets` | 데이터셋 | `/data/datasets` |

### Host Volumes (Celery Worker)

```yaml
volumes:
  # Hugging Face 캐시 (호스트와 공유)
  - /home/aigen/.cache/huggingface:/home/celery/.cache/huggingface:rw

  # GPU 장치 접근
  - /usr/bin/nvidia-smi:/usr/bin/nvidia-smi:ro
  - /usr/lib/libnvidia-ml.so:/usr/lib/libnvidia-ml.so:ro
  - /usr/lib/libnvidia-ml.so.1:/usr/lib/libnvidia-ml.so.1:ro
```

**유지보수성:**
- Host와 HF 캐시 공유로 다운로드 중복 방지
- GPU 라이브러리를 호스트와 공유 (버전 일관성)

## GPU 설정

### NVIDIA Docker Runtime 확인

```bash
# Docker가 GPU를 인식하는지 확인
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Celery Worker에서 GPU 확인
docker compose exec celery-worker nvidia-smi
```

### GPU 할당 설정

**전체 GPU 사용 (기본값):**
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all  # 모든 GPU 사용
          capabilities: [gpu]
```

**특정 GPU만 사용:**
```yaml
environment:
  - NVIDIA_VISIBLE_DEVICES=0,1  # GPU 0, 1만 사용
```

## 모니터링

### Celery Worker 상태 확인

```bash
# Worker 상태 확인
docker compose exec celery-worker celery -A app.core.celery_app inspect ping

# 활성 작업 확인
docker compose exec celery-worker celery -A app.core.celery_app inspect active

# 등록된 작업 확인
docker compose exec celery-worker celery -A app.core.celery_app inspect registered
```

### MLflow UI 접속

```bash
# 브라우저에서 접속
http://localhost:5000
```

### Redis 상태 확인

```bash
# Redis CLI 접속
docker compose exec redis redis-cli

# Celery 큐 확인
127.0.0.1:6379> LLEN celery
127.0.0.1:6379> KEYS celery*
```

## 트러블슈팅

### 1. Worker가 작업을 처리하지 않음

**확인 사항:**
```bash
# Worker 로그 확인
docker compose logs -f celery-worker

# Redis 연결 확인
docker compose exec celery-worker ping redis

# Celery 브로커 확인
docker compose exec celery-worker celery -A app.core.celery_app inspect ping
```

### 2. GPU를 인식하지 못함

**확인 사항:**
```bash
# NVIDIA Docker 런타임 설치 확인
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# 환경 변수 확인
docker compose exec celery-worker env | grep NVIDIA
```

**해결 방법:**
```bash
# NVIDIA Container Toolkit 설치
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
```

### 3. 메모리 부족 (OOM)

**Worker 설정 조정:**
```yaml
environment:
  - WORKER_CONCURRENCY=1  # 동시 작업 수 감소
  - WORKER_MAX_TASKS_PER_CHILD=1  # 작업당 재시작 (메모리 누수 방지)
```

**Docker 메모리 제한:**
```yaml
deploy:
  resources:
    limits:
      memory: 16G  # Worker 메모리 제한
```

### 4. MLflow 연결 실패

**확인 사항:**
```bash
# MLflow 서버 상태 확인
docker compose logs -f mlflow

# MLflow API 접속 테스트
curl http://localhost:5000/health
```

## 보안 Best Practices

### 1. 비밀번호 관리

**절대 하지 말 것:**
```yaml
# ❌ 하드코딩
environment:
  - DATABASE_PASSWORD=my-secret-password
```

**권장 방법:**
```yaml
# ✅ 환경 변수 파일 사용
environment:
  - DATABASE_PASSWORD=${DATABASE_PASSWORD}
```

```bash
# .env 파일에 저장 (Git 제외)
DATABASE_PASSWORD=my-secret-password
```

### 2. 네트워크 격리

```yaml
# Admin API는 내부 네트워크만
networks:
  - default  # 내부 네트워크

# User API는 공개 포트 노출
ports:
  - "8080:8001"
```

### 3. 읽기 전용 마운트

```yaml
# 애플리케이션 코드는 읽기 전용
volumes:
  - ./app:/app/app:ro  # :ro = read-only
```

## 성능 최적화

### 1. Worker 동시성 설정

**GPU 작업 (Fine-tuning):**
```yaml
# GPU 메모리 제약으로 순차 처리
command: celery -A app.core.celery_app worker --concurrency=1 --pool=solo
```

**CPU 작업 (데이터 처리):**
```yaml
# 멀티프로세싱 활용
command: celery -A app.core.celery_app worker --concurrency=4 --pool=prefork
```

### 2. Redis 메모리 최적화

```yaml
redis:
  command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
```

### 3. PostgreSQL 연결 풀링

```python
# app/core/database.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,  # 연결 풀 크기
    max_overflow=10,  # 최대 추가 연결
    pool_pre_ping=True  # 연결 헬스체크
)
```

## 참고 자료

- [Docker Compose 문서](https://docs.docker.com/compose/)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)
- [Celery 문서](https://docs.celeryproject.org/)
- [MLflow 문서](https://mlflow.org/docs/latest/index.html)
