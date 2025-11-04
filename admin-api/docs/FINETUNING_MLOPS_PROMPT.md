# Fine-tuning MLOps 환경 구축 프로젝트

> **AI 협업 프롬프트**: 이 문서는 Gemini에게 전달하여 Claude Code와 협업하기 위한 상세 프롬프트입니다.

## 📋 목차

- [1. 프로젝트 개요](#1-프로젝트-개요)
- [2. 현재 인프라 환경](#2-현재-인프라-환경)
- [3. RFP 요구사항](#3-rfp-요구사항)
- [4. 구현 범위](#4-구현-범위)
- [5. 기술 아키텍처](#5-기술-아키텍처)
- [6. API 설계](#6-api-설계)
- [7. 데이터베이스 스키마](#7-데이터베이스-스키마)
- [8. 프론트엔드 UI 설계](#8-프론트엔드-ui-설계)
- [9. 성능 요구사항](#9-성능-요구사항)
- [10. 보안 요구사항](#10-보안-요구사항)
- [11. 테스트 요구사항](#11-테스트-요구사항)
- [12. 산출물](#12-산출물)
- [13. 일정](#13-일정)
- [14. 기술 스택 요약](#14-기술-스택-요약)
- [15. 참고 자료](#15-참고-자료)
- [16. 핵심 과제 및 해결 방안](#16-핵심-과제-및-해결-방안)
- [17. 성공 기준](#17-성공-기준)
- [18. 질문 사항](#18-질문-사항)

---

## 1. 프로젝트 개요

한국도로공사의 생성형 AI 시스템에서 **LLM 모델의 추가 학습(Fine-tuning) 및 실험 관리를 위한 MLOps 파이프라인**을 구축하는 프로젝트입니다.

데이터 과학자와 AI 엔지니어가 효율적으로 모델을 학습하고, 실험을 추적하며, 최적의 모델을 프로덕션에 배포할 수 있는 엔드-투-엔드 시스템을 개발합니다.

---

## 2. 현재 인프라 환경

### 2.1 하드웨어

```yaml
GPU: NVIDIA H100 NVL (95GB VRAM) × 2장
  # 실제 한국도로공사 내부망은 H100 8장
CPU: 2GHz × 56core × 2CPU
Memory: 2TB RAM
Storage: SSD 3.84TB × 8개
```

### 2.2 소프트웨어 스택

```yaml
운영체제: Rocky Linux 8
컨테이너: Docker + Docker Compose
LLM 서빙: vLLM v0.8.5.post1 (OpenAI 호환 API)
벡터 DB: Qdrant
  - Collection: 130825-512-v3
  - Vector Size: 1024-dim
메타데이터 DB: PostgreSQL 14
실험 추적: MLflow (http://mlflow:5000)
모델 저장소: Hugging Face Hub (오프라인 모드)
```

### 2.3 현재 운영 중인 모델

```yaml
LLM:
  - Qwen/Qwen3-32B-Instruct (기본 모델)
  - 다양한 크기의 Qwen 계열 모델

Embedding:
  - Qwen/Qwen3-Embedding-0.6B (1024-dim)

Reranker:
  - BAAI/bge-reranker-v2-m3
```

### 2.4 기존 시스템 구조

```
/home/aigen/
├── admin-api/                    # FastAPI 백엔드
│   ├── app/
│   │   ├── routers/admin/
│   │   │   └── deployment.py     # 배포 관리 API (MLflow 연동)
│   │   ├── models/deployment.py  # 배포 DB 모델
│   │   └── services/             # 비즈니스 로직
│   └── docs/
│       ├── RFP.txt               # 요구사항 정의서
│       └── DATABASE_SCHEMA.md    # DB 스키마
├── ex-gpt/
│   └── docker-compose-model-server.yaml  # vLLM 배포 설정
└── /data/
    └── models/                   # 모델 저장 경로
```

---

## 3. RFP 요구사항

### 3.1 핵심 요구사항

**RFP FUN-001: 생성형AI 시스템 개선**
> "생성형 AI 모델을 학습시킬 수 있는 환경 개선"
> - 학습데이터 관리 기능 개선
> - 사전 학습 모델 추가 학습 (Fine tuning) 기능 개선
> - RAG(Retrieval-Augmented Generation) 기반 검색 환경 개선

**RFP FUN-004: LLM 학습데이터 반영**
> "생성형AI 활용 서비스 및 학습데이터 유형에 따른 튜닝 방법 선정"
> - 검색 서비스를 위한 RAG 기법, 문서 생성을 위한 Fine Tuning
> - 필요 시, 용도에 따라 다르게 튜닝된 다수의 LLM 구축
> - 영어기반 모델이더라도 한국어로 원활한 소통이 되어야 함
> - 튜닝 결과에 따라 편향성 제거 및 재학습을 통한 모델 품질 유지

**RFP FUN-006: 서비스 운영 및 최적화**
> "AI모델 또는 서비스 보완 전후 기존 모델(A)/신규 모델(B) 테스트 수행"
> - A그룹, B그룹으로 구분하여 답변품질 비교·분석

**성능 요구사항 (PER-003)**
> "생성형AI 시스템은 테스트케이스에서 90% 이상의 정확도 확인"

---

## 4. 구현 범위

### Phase 1: 핵심 MLOps 파이프라인 (우선 구현)

#### 4.1 학습 데이터 관리 시스템

**목표**: 학습용 데이터셋의 생성, 버전 관리, 품질 검증

**주요 기능**:

1. **데이터셋 빌더**
   - 다양한 포맷 지원 (JSON, JSONL, Parquet, CSV)
   - Instruction-tuning 데이터셋 표준 포맷 정의

```json
{
  "messages": [
    {
      "role": "system",
      "content": "당신은 한국도로공사의 AI 어시스턴트입니다."
    },
    {
      "role": "user",
      "content": "국가계약법 제5조의 내용은?"
    },
    {
      "role": "assistant",
      "content": "..."
    }
  ],
  "metadata": {
    "source": "document_123",
    "category": "법령",
    "quality_score": 0.95
  }
}
```

2. **데이터 품질 검증**
   - 개인정보 자동 탐지 (주민등록번호, 이름, 전화번호 등)
   - 중복 제거 (MinHash LSH)
   - 품질 점수 산정 (길이, 다양성, 문법)
   - 독성/편향성 탐지

3. **데이터셋 버전 관리**
   - Git-like 버전 관리 (DVC 또는 자체 구현)
   - 데이터셋 lineage 추적
   - Train/Validation/Test 자동 분할 (stratified)

4. **데이터셋 통계 및 시각화**
   - 토큰 분포, 길이 분포
   - 카테고리별 비율
   - 품질 리포트 생성

#### 4.2 Fine-tuning 실험 관리

**지원하는 Fine-tuning 방법**:
1. **Full Fine-tuning** - 모든 파라미터 학습
2. **LoRA (Low-Rank Adaptation)** - 메모리 효율적
3. **QLoRA** - 양자화 + LoRA (더 효율적)

**학습 프레임워크**:
- **Hugging Face Transformers + PEFT**
- **Axolotl** (통합 학습 프레임워크, 권장)
- **LLaMA-Factory** (대안)

**실험 추적 (MLflow 연동)**:

```python
import mlflow

mlflow.set_experiment("qwen-legal-finetuning")

with mlflow.start_run(run_name="qwen3-7b-lora-v1"):
    # 하이퍼파라미터 로깅
    mlflow.log_params({
        "base_model": "Qwen/Qwen3-7B-Instruct",
        "method": "LoRA",
        "rank": 16,
        "alpha": 32,
        "learning_rate": 2e-4,
        "batch_size": 4,
        "gradient_accumulation": 8,
        "epochs": 3,
        "dataset": "legal_qa_v1.2"
    })

    # 학습 중 메트릭 로깅
    for epoch in range(3):
        mlflow.log_metrics({
            "train_loss": train_loss,
            "val_loss": val_loss,
            "perplexity": perplexity,
            "gpu_memory_gb": gpu_memory
        }, step=epoch)

    # 모델 저장
    mlflow.pyfunc.log_model("model", ...)
```

#### 4.3 모델 레지스트리 및 버전 관리

**기능**:
1. **모델 등록 및 버전 관리**
   - MLflow Model Registry 통합
   - 모델 메타데이터 관리
   - 태그 및 설명 추가

2. **모델 상태 관리**
   - Staging: 검증 중
   - Production: 프로덕션 배포
   - Archived: 사용 중지

3. **모델 비교 도구**
   - A/B 테스트 자동화
   - 성능 메트릭 시각화
   - 모델 간 차이점 분석

#### 4.4 자동화된 학습 파이프라인

**워크플로우 예시**:

```yaml
name: fine-tuning-pipeline
steps:
  - name: data-preparation
    script: scripts/prepare_dataset.py
    inputs:
      - raw_documents
    outputs:
      - processed_dataset

  - name: quality-check
    script: scripts/check_dataset_quality.py
    inputs:
      - processed_dataset
    outputs:
      - quality_report

  - name: training
    script: scripts/run_finetuning.py
    gpu: "0,1"
    inputs:
      - processed_dataset
      - config.yaml
    outputs:
      - trained_model
      - checkpoints

  - name: evaluation
    script: scripts/evaluate_model.py
    inputs:
      - trained_model
      - test_dataset
    outputs:
      - evaluation_results

  - name: deployment
    condition: evaluation_results.accuracy > 0.90
    script: scripts/deploy_model.py
    inputs:
      - trained_model
```

**구현 기술 옵션**:
- **Apache Airflow** (워크플로우 오케스트레이션) 또는
- **Prefect** (경량 대안) 또는
- **Celery** (비동기 작업 큐, 기존 FastAPI와 통합 용이)

#### 4.5 A/B 테스트 프레임워크

**목표**: RFP FUN-006 요구사항 구현 - 모델 A vs 모델 B 성능 비교

**기능**:

1. **실험 설계**
   - 트래픽 분할 비율 설정 (예: 50:50, 80:20)
   - 테스트 기간 설정
   - 평가 메트릭 정의

2. **자동 트래픽 라우팅**
   - 사용자별 일관된 모델 할당 (sticky session)
   - 실시간 메트릭 수집

3. **통계적 유의성 검증**
   - T-test, Mann-Whitney U test
   - Confidence interval 계산

4. **자동 승격/롤백**
   - 승리 모델 자동 감지
   - 성능 저하 시 자동 롤백

### Phase 2: 고급 기능 (선택적)

#### 4.6 분산 학습 지원
- DeepSpeed, FSDP (Fully Sharded Data Parallel)
- Multi-node 학습 (향후 GPU 확장 시)

#### 4.7 자동 하이퍼파라미터 튜닝
- Optuna, Ray Tune 통합
- 베이지안 최적화

#### 4.8 모델 압축 및 최적화
- Quantization (AWQ, GPTQ)
- Pruning, Distillation

---

## 5. 기술 아키텍처

### 5.1 시스템 구성도

```
┌─────────────────────────────────────────────────────────────┐
│                    사용자 (AI 엔지니어)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Admin UI (React)                           │
│  - 데이터셋 관리                                               │
│  - Fine-tuning 작업 생성                                      │
│  - A/B 테스트 관리                                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│               FastAPI Backend (admin-api)                    │
│  /api/v1/admin/training/*                                    │
│  /api/v1/admin/finetuning/*                                  │
│  /api/v1/admin/models/*                                      │
│  /api/v1/admin/ab-tests/*                                    │
└─┬─────────────┬─────────────┬─────────────┬─────────────────┘
  │             │             │             │
  │             │             │             │
  ▼             ▼             ▼             ▼
┌─────────┐ ┌──────────┐ ┌─────────┐ ┌────────────┐
│PostgreSQL│ │  MLflow  │ │ Celery  │ │   Qdrant   │
│  (Meta)  │ │(Tracking)│ │(Workers)│ │ (Vectors)  │
└─────────┘ └──────────┘ └─────────┘ └────────────┘
                 │
                 ▼
         ┌──────────────┐
         │Model Registry│
         │   (MLflow)   │
         └──────────────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │   Fine-tuning Workers      │
    │ (Axolotl / HF Trainer)     │
    │   GPU: H100 × 2 (0,1)      │
    └────────────────────────────┘
                 │
                 ▼
         ┌──────────────┐
         │Model Storage │
         │ /data/models │
         └──────────────┘
                 │
                 ▼
         ┌──────────────┐
         │ vLLM Servers │
         │  (Inference) │
         └──────────────┘
```

### 5.2 Fine-tuning 워커 구현

**Docker 컨테이너**:

```dockerfile
# Dockerfile.finetuning
FROM nvidia/cuda:12.1.0-devel-ubuntu22.04

# Python 3.11 설치
RUN apt-get update && apt-get install -y python3.11 python3-pip

# Axolotl 설치
RUN pip install axolotl[flash-attn,deepspeed]

# 추가 도구
RUN pip install mlflow boto3 qdrant-client

WORKDIR /workspace

CMD ["python", "finetuning_worker.py"]
```

**워커 스크립트 예시**:

```python
# finetuning_worker.py
import os
import json
import mlflow
from axolotl import train

async def run_finetuning_job(job_config):
    """
    Axolotl을 사용한 Fine-tuning 실행
    """
    # MLflow 실험 시작
    mlflow.set_experiment(job_config["experiment_name"])

    with mlflow.start_run(run_name=job_config["job_name"]):
        # Axolotl config 생성
        axolotl_config = {
            "base_model": job_config["base_model"],
            "model_type": "AutoModelForCausalLM",
            "tokenizer_type": "AutoTokenizer",

            # 데이터셋
            "datasets": [
                {
                    "path": job_config["dataset_path"],
                    "type": "sharegpt",  # instruction format
                }
            ],

            # LoRA 설정
            "adapter": "lora",
            "lora_r": job_config["hyperparameters"]["lora_rank"],
            "lora_alpha": job_config["hyperparameters"]["lora_alpha"],
            "lora_dropout": 0.05,
            "lora_target_modules": [
                "q_proj", "k_proj", "v_proj", "o_proj"
            ],

            # 학습 설정
            "sequence_len": job_config["hyperparameters"]["max_seq_length"],
            "micro_batch_size": job_config["hyperparameters"]["batch_size"],
            "gradient_accumulation_steps":
                job_config["hyperparameters"]["gradient_accumulation_steps"],
            "num_epochs": job_config["hyperparameters"]["num_epochs"],
            "learning_rate": job_config["hyperparameters"]["learning_rate"],
            "warmup_steps": job_config["hyperparameters"]["warmup_steps"],

            # 최적화
            "optimizer": "adamw_torch",
            "lr_scheduler": "cosine",
            "flash_attention": True,
            "bf16": True,

            # 저장
            "output_dir": job_config["output_dir"],
            "save_steps": 500,
            "eval_steps": 500,
            "logging_steps": 10,

            # MLflow 로깅
            "mlflow_tracking_uri": os.getenv("MLFLOW_TRACKING_URI"),
        }

        # Axolotl 학습 실행
        train(config=axolotl_config)

        # 모델 등록
        mlflow.log_artifact(job_config["output_dir"])
```

### 5.3 데이터셋 전처리 파이프라인

```python
# /app/services/dataset_processor.py

class DatasetProcessor:
    """학습 데이터셋 전처리"""

    async def process_documents_to_dataset(
        self,
        document_ids: List[int],
        template: str = "qa"  # qa, chat, summary
    ) -> str:
        """
        문서들을 Fine-tuning용 데이터셋으로 변환

        Args:
            document_ids: 문서 ID 목록
            template: 데이터셋 템플릿 종류

        Returns:
            생성된 데이터셋 파일 경로
        """

        # 1. 문서 로드
        documents = await self.load_documents(document_ids)

        # 2. Q&A 쌍 생성 (LLM 사용)
        qa_pairs = []
        for doc in documents:
            pairs = await self.generate_qa_from_document(doc)
            qa_pairs.extend(pairs)

        # 3. 개인정보 마스킹
        qa_pairs = await self.mask_pii(qa_pairs)

        # 4. 중복 제거
        qa_pairs = self.deduplicate(qa_pairs)

        # 5. 품질 필터링
        qa_pairs = self.filter_by_quality(qa_pairs, min_score=0.7)

        # 6. 템플릿 적용
        dataset = []
        for pair in qa_pairs:
            if template == "qa":
                dataset.append({
                    "messages": [
                        {
                            "role": "system",
                            "content": "당신은 한국도로공사의 AI 어시스턴트입니다."
                        },
                        {"role": "user", "content": pair["question"]},
                        {"role": "assistant", "content": pair["answer"]}
                    ]
                })

        # 7. 저장
        output_path = f"/data/datasets/dataset_{timestamp}.jsonl"
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in dataset:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        return output_path

    async def generate_qa_from_document(
        self,
        document: Document
    ) -> List[Dict]:
        """LLM을 사용해 문서에서 Q&A 쌍 생성"""

        prompt = f"""
다음 문서를 읽고 10개의 질문-답변 쌍을 생성하세요.

[문서]
{document.content[:2000]}

JSON 형식으로 출력하세요:
[
  {{"question": "...", "answer": "..."}},
  ...
]
"""

        # vLLM API 호출
        response = await self.llm_client.generate(
            prompt,
            temperature=0.7
        )
        qa_pairs = json.loads(response)

        return qa_pairs
```

---

## 6. API 설계

### 6.1 학습 데이터 관리 API

```python
# /app/routers/admin/training_data.py

@router.post("/api/v1/admin/training/datasets")
async def create_dataset(
    name: str,
    file: UploadFile,
    description: Optional[str] = None
) -> DatasetResponse:
    """데이터셋 생성 및 업로드"""

@router.get("/api/v1/admin/training/datasets")
async def list_datasets(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
) -> DatasetListResponse:
    """데이터셋 목록 조회"""

@router.get("/api/v1/admin/training/datasets/{dataset_id}/stats")
async def get_dataset_stats(
    dataset_id: int
) -> DatasetStatsResponse:
    """데이터셋 통계 조회"""

@router.post("/api/v1/admin/training/datasets/{dataset_id}/validate")
async def validate_dataset(
    dataset_id: int
) -> ValidationReportResponse:
    """데이터 품질 검증 실행"""

@router.post("/api/v1/admin/training/datasets/{dataset_id}/split")
async def split_dataset(
    dataset_id: int,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1
) -> DatasetSplitResponse:
    """데이터셋 분할 (Train/Val/Test)"""
```

### 6.2 Fine-tuning 작업 API

```python
# /app/routers/admin/finetuning.py

@router.post("/api/v1/admin/finetuning/jobs")
async def create_finetuning_job(
    request: FinetuningJobRequest
) -> FinetuningJobResponse:
    """
    Fine-tuning 작업 생성 및 시작

    Request Body 예시:
    {
      "job_name": "qwen-legal-v1",
      "base_model": "Qwen/Qwen3-7B-Instruct",
      "dataset_id": 123,
      "method": "lora",
      "hyperparameters": {
        "lora_rank": 16,
        "lora_alpha": 32,
        "learning_rate": 2e-4,
        "batch_size": 4,
        "gradient_accumulation_steps": 8,
        "num_epochs": 3,
        "warmup_steps": 100,
        "max_seq_length": 2048
      },
      "gpu_ids": "0,1"
    }
    """

@router.get("/api/v1/admin/finetuning/jobs")
async def list_finetuning_jobs(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
) -> FinetuningJobListResponse:
    """Fine-tuning 작업 목록 조회"""

@router.get("/api/v1/admin/finetuning/jobs/{job_id}")
async def get_finetuning_job(
    job_id: int
) -> FinetuningJobDetailResponse:
    """Fine-tuning 작업 상세 조회 (진행률, 메트릭 포함)"""

@router.post("/api/v1/admin/finetuning/jobs/{job_id}/stop")
async def stop_finetuning_job(
    job_id: int
) -> FinetuningJobResponse:
    """학습 중단"""

@router.post("/api/v1/admin/finetuning/jobs/{job_id}/resume")
async def resume_finetuning_job(
    job_id: int,
    checkpoint_id: int
) -> FinetuningJobResponse:
    """체크포인트에서 학습 재개"""

@router.get("/api/v1/admin/finetuning/jobs/{job_id}/logs")
async def get_training_logs(
    job_id: int,
    lines: int = 100
) -> TrainingLogsResponse:
    """실시간 학습 로그 조회"""

@router.get("/api/v1/admin/finetuning/jobs/{job_id}/metrics")
async def get_training_metrics(
    job_id: int
) -> MetricsResponse:
    """학습 메트릭 조회 (loss, perplexity 그래프 데이터)"""
```

### 6.3 모델 레지스트리 API

```python
# /app/routers/admin/model_registry.py

@router.post("/api/v1/admin/models/register")
async def register_model(
    request: ModelRegisterRequest
) -> ModelResponse:
    """Fine-tuned 모델을 레지스트리에 등록"""

@router.get("/api/v1/admin/models")
async def list_models(
    status: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> ModelListResponse:
    """모델 목록 조회"""

@router.post("/api/v1/admin/models/{model_id}/evaluate")
async def evaluate_model(
    model_id: int,
    test_dataset_id: int
) -> EvaluationResponse:
    """모델 평가 실행"""

@router.post("/api/v1/admin/models/{model_id}/promote")
async def promote_to_production(
    model_id: int
) -> ModelResponse:
    """Staging -> Production 승격"""

@router.post("/api/v1/admin/models/{model_id}/deploy")
async def deploy_model(
    model_id: int,
    deployment_config: DeploymentConfig
) -> DeploymentResponse:
    """vLLM 서버로 모델 배포"""
```

### 6.4 A/B 테스트 API

```python
# /app/routers/admin/ab_testing.py

@router.post("/api/v1/admin/ab-tests")
async def create_ab_test(
    request: ABTestRequest
) -> ABTestResponse:
    """
    A/B 테스트 실험 생성

    Request 예시:
    {
      "experiment_name": "qwen-legal-vs-base",
      "model_a_id": 10,
      "model_b_id": 15,
      "traffic_split": {"a": 0.5, "b": 0.5},
      "target_samples": 200,
      "success_metric": "user_rating"
    }
    """

@router.get("/api/v1/admin/ab-tests")
async def list_ab_tests() -> ABTestListResponse:
    """A/B 테스트 목록"""

@router.get("/api/v1/admin/ab-tests/{experiment_id}/results")
async def get_ab_test_results(
    experiment_id: int
) -> ABTestResultsResponse:
    """A/B 테스트 결과 조회 (통계 포함)"""

@router.post("/api/v1/admin/ab-tests/{experiment_id}/stop")
async def stop_ab_test(
    experiment_id: int
) -> ABTestResponse:
    """A/B 테스트 중단"""

@router.post("/api/v1/admin/ab-tests/{experiment_id}/conclude")
async def conclude_ab_test(
    experiment_id: int,
    winner: str  # 'a' or 'b'
) -> ABTestResponse:
    """A/B 테스트 종료 및 승자 선정"""
```

---

## 7. 데이터베이스 스키마

### 7.1 학습 데이터 관련 테이블

```sql
-- 학습 데이터셋
CREATE TABLE training_datasets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    version VARCHAR(50) NOT NULL,  -- v1.0, v1.1
    description TEXT,
    format VARCHAR(50) DEFAULT 'jsonl',  -- jsonl, json, parquet
    file_path TEXT NOT NULL,  -- /data/datasets/dataset_v1.jsonl
    total_samples INTEGER,
    train_samples INTEGER,
    val_samples INTEGER,
    test_samples INTEGER,
    metadata JSONB,  -- 통계 정보
    quality_score FLOAT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active',  -- active, deprecated, archived
    UNIQUE(name, version)
);

-- 데이터셋 품질 검증 로그
CREATE TABLE dataset_quality_logs (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER REFERENCES training_datasets(id),
    check_type VARCHAR(100),  -- pii_detection, duplicate_check, quality_score
    passed BOOLEAN,
    issues JSONB,  -- 발견된 문제점 목록
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 7.2 Fine-tuning 작업 관련 테이블

```sql
-- Fine-tuning 작업
CREATE TABLE finetuning_jobs (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(255) UNIQUE NOT NULL,
    base_model VARCHAR(255) NOT NULL,  -- Qwen/Qwen3-7B-Instruct
    dataset_id INTEGER REFERENCES training_datasets(id),
    method VARCHAR(50) NOT NULL,  -- full, lora, qlora
    hyperparameters JSONB NOT NULL,  -- 모든 학습 설정
    mlflow_run_id VARCHAR(255),  -- MLflow 연동
    status VARCHAR(50) DEFAULT 'pending',
        -- pending, running, completed, failed
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    output_dir TEXT,  -- /data/models/finetuned/job_123
    checkpoint_dir TEXT,  -- 체크포인트 저장 경로
    logs_path TEXT,  -- 로그 파일 경로
    gpu_ids VARCHAR(50),  -- 0,1,2,3
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 체크포인트 (중간 저장)
CREATE TABLE training_checkpoints (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES finetuning_jobs(id),
    checkpoint_name VARCHAR(255),  -- checkpoint-1000, checkpoint-2000
    step INTEGER,
    epoch FLOAT,
    metrics JSONB,  -- {train_loss: 0.5, val_loss: 0.6}
    file_path TEXT,
    file_size_gb FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 평가 결과
CREATE TABLE model_evaluations (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES finetuning_jobs(id),
    checkpoint_id INTEGER REFERENCES training_checkpoints(id),
    eval_dataset_id INTEGER REFERENCES training_datasets(id),
    metrics JSONB NOT NULL,
        -- {accuracy: 0.92, f1: 0.89, perplexity: 5.2}
    test_cases JSONB,  -- 개별 테스트 케이스 결과
    evaluated_at TIMESTAMP DEFAULT NOW(),
    evaluator INTEGER REFERENCES users(id)
);
```

### 7.3 모델 레지스트리 테이블

```sql
-- 모델 레지스트리
CREATE TABLE model_registry (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    base_model VARCHAR(255),  -- 원본 모델
    finetuning_job_id INTEGER REFERENCES finetuning_jobs(id),
    model_path TEXT NOT NULL,  -- /data/models/registered/model_v1
    model_format VARCHAR(50) DEFAULT 'huggingface',
        -- huggingface, gguf, awq
    model_size_gb FLOAT,
    status VARCHAR(50) DEFAULT 'staging',
        -- staging, production, archived
    deployment_config JSONB,  -- vLLM 설정
    mlflow_model_uri TEXT,
    description TEXT,
    tags TEXT[],  -- {legal, korean, 7b}
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(model_name, version)
);

-- 모델 성능 벤치마크
CREATE TABLE model_benchmarks (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES model_registry(id),
    benchmark_name VARCHAR(255),
        -- mmlu_kr, kobest, internal_test
    score FLOAT,
    details JSONB,
    benchmark_date TIMESTAMP DEFAULT NOW()
);
```

### 7.4 A/B 테스트 테이블

```sql
-- A/B 테스트 실험
CREATE TABLE ab_experiments (
    id SERIAL PRIMARY KEY,
    experiment_name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    model_a_id INTEGER REFERENCES model_registry(id),
    model_b_id INTEGER REFERENCES model_registry(id),
    traffic_split JSONB DEFAULT '{"a": 0.5, "b": 0.5}',
    status VARCHAR(50) DEFAULT 'running',
        -- running, completed, stopped
    start_date TIMESTAMP DEFAULT NOW(),
    end_date TIMESTAMP,
    target_samples INTEGER DEFAULT 200,  -- 최소 샘플 수
    success_metric VARCHAR(100) DEFAULT 'user_rating',
    created_by INTEGER REFERENCES users(id)
);

-- A/B 테스트 로그
CREATE TABLE ab_test_logs (
    id SERIAL PRIMARY KEY,
    experiment_id INTEGER REFERENCES ab_experiments(id),
    user_id INTEGER,
    session_id VARCHAR(255),
    variant VARCHAR(10),  -- 'a' or 'b'
    model_id INTEGER REFERENCES model_registry(id),
    query TEXT,
    response TEXT,
    response_time_ms INTEGER,
    user_rating INTEGER,  -- 1-5
    user_feedback TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- A/B 테스트 결과
CREATE TABLE ab_test_results (
    id SERIAL PRIMARY KEY,
    experiment_id INTEGER REFERENCES ab_experiments(id),
    variant VARCHAR(10),
    total_samples INTEGER,
    avg_rating FLOAT,
    avg_response_time_ms FLOAT,
    confidence_interval JSONB,  -- {lower: 4.1, upper: 4.5}
    statistical_significance BOOLEAN,
    winner BOOLEAN,
    calculated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 8. 프론트엔드 UI 설계

### 8.1 주요 화면

1. **데이터셋 관리 페이지** (`/admin/training/datasets`)
   - 데이터셋 업로드 폼
   - 데이터셋 목록 (테이블)
   - 통계 대시보드 (차트)
   - 품질 검증 결과

2. **Fine-tuning 작업 페이지** (`/admin/training/jobs`)
   - 작업 생성 위저드
   - 작업 목록 (상태별 필터)
   - 진행률 표시 (프로그레스 바)
   - 실시간 로그 뷰어

3. **실험 비교 페이지** (`/admin/training/experiments`)
   - MLflow UI 임베드
   - 메트릭 그래프 (loss, perplexity)
   - 하이퍼파라미터 비교 테이블

4. **모델 레지스트리 페이지** (`/admin/models`)
   - 모델 카드 (카드 뷰)
   - 모델 상세 정보
   - 평가 결과 시각화
   - 배포 버튼

5. **A/B 테스트 페이지** (`/admin/ab-tests`)
   - 실험 생성 폼
   - 실험 목록
   - 실시간 결과 대시보드 (승률, 통계)
   - 승자 선택 UI

### 8.2 UI 컴포넌트 예시 (React)

```jsx
// TrainingJobList.jsx
import React, { useState, useEffect } from 'react';
import { Table, Tag, Progress, Button } from 'antd';

function TrainingJobList() {
  const [jobs, setJobs] = useState([]);

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000); // 5초마다 갱신
    return () => clearInterval(interval);
  }, []);

  const fetchJobs = async () => {
    const response = await fetch('/api/v1/admin/finetuning/jobs');
    const data = await response.json();
    setJobs(data.items);
  };

  const columns = [
    {
      title: 'Job Name',
      dataIndex: 'job_name',
      key: 'job_name',
    },
    {
      title: 'Base Model',
      dataIndex: 'base_model',
      key: 'base_model',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const colorMap = {
          pending: 'blue',
          running: 'green',
          completed: 'success',
          failed: 'error'
        };
        return <Tag color={colorMap[status]}>
          {status.toUpperCase()}
        </Tag>;
      }
    },
    {
      title: 'Progress',
      key: 'progress',
      render: (_, record) => {
        if (record.status === 'running') {
          return <Progress percent={record.progress || 0} />;
        }
        return '-';
      }
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Button.Group>
          <Button onClick={() => viewLogs(record.id)}>
            Logs
          </Button>
          <Button onClick={() => viewMetrics(record.id)}>
            Metrics
          </Button>
          {record.status === 'running' && (
            <Button danger onClick={() => stopJob(record.id)}>
              Stop
            </Button>
          )}
        </Button.Group>
      )
    }
  ];

  return (
    <div>
      <h2>Fine-tuning Jobs</h2>
      <Table
        dataSource={jobs}
        columns={columns}
        rowKey="id"
      />
    </div>
  );
}

export default TrainingJobList;
```

---

## 9. 성능 요구사항

### 9.1 학습 성능
- **7B 모델 LoRA Fine-tuning**: H100 2장으로 1 epoch당 2-4시간 (10K samples 기준)
- **체크포인트 저장**: 500 step마다 자동 저장
- **조기 종료**: Validation loss 기반

### 9.2 시스템 성능
- **데이터셋 업로드**: 200MB 파일 30초 이내 처리
- **작업 생성**: 5초 이내 응답
- **실시간 로그**: 1초 지연 이내

### 9.3 확장성
- **동시 학습 작업**: 최대 2개 (GPU 2장 기준, 1작업당 1장)
- **데이터셋 크기**: 최대 1M samples
- **모델 레지스트리**: 최대 100개 모델 버전

---

## 10. 보안 요구사항

### 10.1 데이터 보안
- **개인정보 자동 탐지**: 정규식 + NER 모델
- **학습 데이터 암호화**: 저장 시 AES-256
- **접근 제어**: Cerbos 기반 역할별 권한

### 10.2 모델 보안
- **모델 워터마킹**: Fine-tuned 모델에 워터마크 삽입
- **사용 추적**: 모델 다운로드/배포 로그 기록

### 10.3 API 보안
- **인증**: JWT 기반
- **Rate limiting**: IP당 100 req/min
- **감사 로그**: 모든 Fine-tuning 작업 기록

---

## 11. 테스트 요구사항

### 11.1 단위 테스트

```python
# tests/test_dataset_processor.py
import pytest
from app.services.dataset_processor import DatasetProcessor

@pytest.mark.asyncio
async def test_pii_masking():
    processor = DatasetProcessor()

    text = "홍길동의 주민등록번호는 123456-1234567입니다."
    masked = await processor.mask_pii(text)

    assert "홍길동" not in masked
    assert "123456-1234567" not in masked
    assert "[이름]" in masked
    assert "[주민등록번호]" in masked
```

### 11.2 통합 테스트

```python
# tests/test_finetuning_pipeline.py
@pytest.mark.asyncio
async def test_end_to_end_finetuning():
    """데이터셋 생성 -> 학습 -> 평가 -> 등록 전체 플로우 테스트"""

    # 1. 데이터셋 생성
    dataset_id = await create_test_dataset()

    # 2. Fine-tuning 작업 생성
    job_id = await create_finetuning_job(dataset_id)

    # 3. 작업 완료 대기 (최대 30분)
    await wait_for_job_completion(job_id, timeout=1800)

    # 4. 모델 평가
    eval_result = await evaluate_model(job_id)
    assert eval_result["accuracy"] > 0.8

    # 5. 모델 등록
    model_id = await register_model(job_id)
    assert model_id is not None
```

### 11.3 성능 벤치마크
- **학습 속도**: tokens/sec 측정
- **메모리 사용량**: GPU 메모리 프로파일링
- **추론 속도**: 배포 후 latency 측정

---

## 12. 산출물

### 12.1 코드

```
/home/aigen/admin-api/
├── app/
│   ├── routers/admin/
│   │   ├── training_data.py      # 데이터셋 관리 API
│   │   ├── finetuning.py         # Fine-tuning 작업 API
│   │   ├── model_registry.py     # 모델 레지스트리 API
│   │   └── ab_testing.py         # A/B 테스트 API
│   ├── services/
│   │   ├── dataset_processor.py  # 데이터셋 전처리
│   │   ├── finetuning_service.py # 학습 관리
│   │   ├── model_evaluator.py    # 모델 평가
│   │   └── ab_test_service.py    # A/B 테스트 로직
│   ├── models/
│   │   ├── training.py           # 학습 관련 DB 모델
│   │   └── ab_test.py            # A/B 테스트 DB 모델
│   ├── schemas/
│   │   ├── training.py           # Pydantic 스키마
│   │   └── ab_test.py
│   └── workers/
│       └── finetuning_worker.py  # Celery 워커
├── frontend/
│   └── src/
│       └── pages/
│           ├── TrainingDataPage.jsx
│           ├── FinetuningJobsPage.jsx
│           ├── ModelRegistryPage.jsx
│           └── ABTestingPage.jsx
├── scripts/
│   ├── prepare_dataset.py
│   ├── run_finetuning.py
│   └── evaluate_model.py
└── docker/
    ├── Dockerfile.finetuning
    └── docker-compose-training.yaml
```

### 12.2 문서

1. **시스템 아키텍처 문서**
   - 전체 구성도
   - 데이터 플로우
   - 컴포넌트 설명

2. **사용자 매뉴얼**
   - 데이터셋 준비 가이드
   - Fine-tuning 작업 생성 가이드
   - A/B 테스트 실행 가이드
   - 트러블슈팅

3. **API 문서**
   - OpenAPI (Swagger) 문서
   - API 사용 예시

4. **개발자 가이드**
   - 새로운 Fine-tuning 메소드 추가 방법
   - 커스텀 평가 메트릭 정의
   - 워크플로우 확장

5. **운영 가이드**
   - GPU 리소스 모니터링
   - 문제 발생 시 대응
   - 백업 및 복구

### 12.3 데이터베이스 마이그레이션

```sql
-- migrations/versions/xxxx_add_finetuning_tables.py
-- 위에서 정의한 모든 테이블 생성 스크립트
```

### 12.4 테스트 케이스

```
tests/
├── unit/
│   ├── test_dataset_processor.py
│   ├── test_pii_detector.py
│   └── test_model_evaluator.py
├── integration/
│   ├── test_finetuning_pipeline.py
│   ├── test_api_endpoints.py
│   └── test_ab_testing.py
└── performance/
    ├── benchmark_training_speed.py
    └── benchmark_inference_speed.py
```

---

## 13. 일정

### Week 1-2: 기반 인프라
- [ ] 데이터베이스 스키마 설계 및 마이그레이션
- [ ] Celery 워커 환경 구축
- [ ] MLflow 연동 강화
- [ ] Docker 컨테이너 (Fine-tuning 워커)

### Week 3-4: 데이터 파이프라인
- [ ] 데이터셋 업로드 API
- [ ] 데이터 품질 검증 (PII 탐지, 중복 제거)
- [ ] 데이터셋 전처리 서비스
- [ ] 데이터셋 통계 및 시각화

### Week 5-6: Fine-tuning 파이프라인
- [ ] Fine-tuning 작업 생성 API
- [ ] Axolotl/HF Trainer 통합
- [ ] 학습 모니터링 (실시간 로그, 메트릭)
- [ ] 체크포인트 관리

### Week 7: 모델 레지스트리 & A/B 테스트
- [ ] 모델 등록/배포 API
- [ ] A/B 테스트 프레임워크
- [ ] 통계적 유의성 검증

### Week 8: 통합 & 테스트
- [ ] 프론트엔드 UI 개발
- [ ] 통합 테스트
- [ ] 성능 벤치마크
- [ ] 문서화

---

## 14. 기술 스택 요약

```yaml
백엔드:
  - Python 3.11
  - FastAPI
  - SQLAlchemy (async)
  - Celery (비동기 작업)
  - PostgreSQL
  - MLflow

Fine-tuning:
  - Axolotl (통합 학습 프레임워크)
  - Hugging Face Transformers
  - PEFT (LoRA, QLoRA)
  - DeepSpeed (선택적)

모델 서빙:
  - vLLM v0.8.5.post1

프론트엔드:
  - React
  - Ant Design
  - Recharts (메트릭 시각화)

인프라:
  - Docker / Docker Compose
  - NVIDIA CUDA 12.1
  - H100 GPU × 2
```

---

## 15. 참고 자료

**기존 코드**:
- `/home/aigen/admin-api/app/routers/admin/deployment.py` - 배포 관리 (MLflow 연동)
- `/home/aigen/ex-gpt/docker-compose-model-server.yaml` - vLLM 배포 설정
- `/home/aigen/admin-api/docs/DATABASE_SCHEMA.md` - DB 스키마

**외부 문서**:
- Axolotl: https://github.com/OpenAccess-AI-Collective/axolotl
- MLflow: https://mlflow.org/docs/latest/index.html
- PEFT (LoRA): https://huggingface.co/docs/peft/
- vLLM: https://docs.vllm.ai/

---

## 16. 핵심 과제 및 해결 방안

### 과제 1: GPU 리소스 관리
**문제**: H100 2장으로 여러 작업 동시 실행 시 충돌

**해결**:
- Job Queue (Celery) + GPU 잠금 메커니즘
- 작업별 GPU 할당 명시 (`CUDA_VISIBLE_DEVICES`)

### 과제 2: 학습 중 서버 재시작 시 복구
**문제**: 서버 장애 시 학습 진행 손실

**해결**:
- 500 step마다 체크포인트 자동 저장
- 재시작 시 마지막 체크포인트에서 재개

### 과제 3: 한국어 품질 평가
**문제**: MMLU 등 영어 벤치마크는 한국어에 부적합

**해결**:
- KoBEST, KLUE 벤치마크 활용
- 자체 테스트 케이스 200개 구축 (RFP 요구사항)
- 전문가 정성 평가

### 과제 4: 데이터셋 자동 생성
**문제**: 수작업으로 Q&A 쌍 만들기 힘듦

**해결**:
- LLM 활용 자동 Q&A 생성
- 검증 파이프라인 (품질 필터링)

---

## 17. 성공 기준

### ✅ 필수 (Must-have)

1. 데이터셋 업로드 및 품질 검증 (PII 탐지 포함)
2. LoRA Fine-tuning 작업 생성 및 모니터링
3. MLflow 연동 (실험 추적)
4. 모델 레지스트리 (등록, 버전 관리)
5. A/B 테스트 프레임워크 (RFP FUN-006)

### ⭐ 우선 (Should-have)

1. 자동 데이터셋 생성 (LLM 기반 Q&A 생성)
2. 체크포인트 관리 및 재개
3. 프론트엔드 UI (관리 페이지)
4. 자동 평가 파이프라인

### 🌟 선택 (Nice-to-have)

1. QLoRA 지원
2. 분산 학습 (Multi-node)
3. 하이퍼파라미터 자동 튜닝
4. 모델 압축 (Quantization)

---

## 18. 질문 사항

개발 시작 전 확인 필요:

1. **GPU 할당**: 현재 H100 2장 중 Fine-tuning 전용으로 몇 장 할당 가능한가요?
2. **MLflow 서버**: 이미 실행 중인가요? 접속 정보를 공유해주세요.
3. **학습 데이터**: 초기 Fine-tuning용 샘플 데이터셋이 있나요?
4. **테스트 케이스**: RFP의 90% 정확도 기준이 되는 200개 테스트 케이스를 제공받을 수 있나요?
5. **우선순위**: Phase 1에서 어떤 기능을 가장 먼저 개발해야 하나요?
   - a) 데이터 파이프라인
   - b) Fine-tuning 실행
   - c) A/B 테스트

---

## 🤝 AI 협업 안내

**이 문서는 Claude Code와 Gemini가 협업하기 위한 프롬프트입니다.**

### Gemini에게 요청사항

1. **설계 검토**: 위 아키텍처와 기술 스택이 적절한지 검토
2. **개선 제안**: 누락된 부분이나 더 나은 대안 제시
3. **구현 우선순위**: Phase 1에서 무엇을 먼저 개발할지 제안
4. **기술적 질문**: 명확히 해야 할 사항 질문

### 응답 형식

다음 구조로 답변해주세요:

- ✅ **동의/승인**: 잘 설계된 부분들
- ⚠️ **개선 필요**: 문제점 및 개선 방안
- 💡 **추가 제안**: Claude가 놓친 부분이나 더 나은 대안
- ❓ **질문**: 명확히 할 사항
- 📝 **다음 단계**: Claude가 다음에 할 작업 제안

---

**이 프롬프트를 받은 개발자(Gemini)는 위 요구사항을 바탕으로 자율적으로 설계, 개발, 테스트를 수행하고, 최종 산출물을 제출하세요.**
