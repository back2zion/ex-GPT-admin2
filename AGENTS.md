# AGENTS.md - AI 협업 가이드

> 이 파일은 Claude Code, Gemini, OpenAI 등 여러 AI 도구가 이 프로젝트에서 협업하기 위한 표준 가이드입니다.

## 📌 프로젝트 개요

**프로젝트명**: 한국도로공사 생성형 AI 시스템 (Admin API)
**기술 스택**: FastAPI + PostgreSQL + Qdrant + vLLM + React
**위치**: `/home/aigen/admin-api/`

## 🎯 현재 진행 중인 작업

### Fine-tuning MLOps 환경 구축 (진행 중)

**담당**: Gemini (주 개발자), Claude Code (리뷰어)
**프롬프트**: `/home/aigen/admin-api/docs/FINETUNING_MLOPS_PROMPT.md`

**목표**: LLM 모델의 Fine-tuning 및 실험 관리를 위한 MLOps 파이프라인 구축

**핵심 구현 사항**:
- 학습 데이터 관리 시스템
- Fine-tuning 작업 실행 및 모니터링
- MLflow 기반 실험 추적
- 모델 레지스트리
- A/B 테스트 프레임워크

## 🔧 개발 환경

```yaml
서버:
  - OS: Rocky Linux 8
  - GPU: NVIDIA H100 NVL × 2 (95GB VRAM each)
  - CPU: 2GHz × 56core × 2
  - RAM: 2TB
  - Storage: /data (SSD 30TB+)

실행 중인 서비스:
  - admin-api: http://localhost:8010 (FastAPI)
  - PostgreSQL: localhost:5432
  - MLflow: http://mlflow:5000
  - Qdrant: http://localhost:6335
  - vLLM (LLM): http://localhost:38000
  - vLLM (Embedding): http://localhost:38100
```

## 📁 프로젝트 구조

```
/home/aigen/admin-api/
├── app/
│   ├── routers/admin/     # API 엔드포인트
│   │   ├── deployment.py  # 배포 관리 (MLflow 연동)
│   │   ├── stats.py       # 통계
│   │   └── ...
│   ├── models/            # SQLAlchemy 모델
│   ├── schemas/           # Pydantic 스키마
│   ├── services/          # 비즈니스 로직
│   └── core/              # 설정, DB 연결
├── frontend/              # React 프론트엔드
├── docs/                  # 문서
│   ├── RFP.txt            # 요구사항 정의서
│   ├── DATABASE_SCHEMA.md # DB 스키마
│   └── FINETUNING_MLOPS_PROMPT.md  # Fine-tuning 프롬프트
├── migrations/            # Alembic 마이그레이션
└── tests/                 # 테스트
```

## 📚 중요 문서

### 필독 문서
1. **RFP**: `docs/RFP.txt` - 한국도로공사의 요구사항 정의서
2. **DB 스키마**: `docs/DATABASE_SCHEMA.md` - 데이터베이스 구조
3. **Fine-tuning 프롬프트**: `docs/FINETUNING_MLOPS_PROMPT.md` - MLOps 구축 가이드

### 참고 문서
- **README.md**: 프로젝트 전체 개요
- **CLAUDE.md**: Claude Code 전용 설정 (있다면)

## 🤝 AI 협업 규칙

### 역할 분담

**Claude Code**:
- 기존 시스템 분석 및 이해
- API 설계 및 리뷰
- 데이터베이스 마이그레이션
- 기존 코드와의 통합 검증
- 한국어 문서 작성

**Gemini**:
- 신규 기능 구현 (Fine-tuning 워커, MLOps 파이프라인)
- 프론트엔드 UI 개발
- 테스트 코드 작성
- 성능 최적화
- 기술 스택 선택 및 검증

### 협업 워크플로우

1. **설계 단계**: Claude가 초안 작성 → Gemini가 리뷰 → 반복
2. **개발 단계**: 역할 분담하여 병렬 개발
3. **리뷰 단계**: 교차 검증 (서로 리뷰)

### 커뮤니케이션 형식

```markdown
## [AI 이름] → [수신자]

### 작업 내용
[무엇을 했는지]

### 요청사항
[무엇을 해달라는지]

### 질문
[명확히 할 사항]

### 첨부
[관련 파일 경로나 코드 스니펫]
```

## 🚀 개발 가이드

### 새 API 엔드포인트 추가

1. `app/routers/admin/` 에 라우터 파일 생성
2. `app/models/` 에 DB 모델 추가 (필요시)
3. `app/schemas/` 에 Pydantic 스키마 추가
4. `migrations/` 에 Alembic 마이그레이션 생성
5. 테스트 작성 (`tests/`)

### 데이터베이스 마이그레이션

```bash
# 마이그레이션 생성
cd /home/aigen/admin-api
alembic revision --autogenerate -m "Add finetuning tables"

# 마이그레이션 적용
alembic upgrade head

# 롤백
alembic downgrade -1
```

### 테스트 실행

```bash
# 전체 테스트
pytest

# 특정 파일
pytest tests/test_finetuning.py

# 커버리지
pytest --cov=app tests/
```

### Docker 빌드 및 실행

```bash
# 백엔드 재시작
docker-compose restart admin-api

# 로그 확인
docker-compose logs -f admin-api

# 새 컨테이너 빌드
docker-compose build admin-api
docker-compose up -d admin-api
```

## 🔐 보안 및 규칙

### 필수 준수 사항

1. **개인정보 보호**
   - 모든 개인정보는 자동 마스킹
   - 주민등록번호, 이름, 전화번호 등 탐지

2. **코드 품질**
   - Type hints 필수 (Python)
   - Docstring 작성 (Google Style)
   - ESLint 통과 (React)

3. **커밋 메시지**
   ```
   feat: 새 기능 추가
   fix: 버그 수정
   refactor: 리팩토링
   docs: 문서 수정
   test: 테스트 추가
   ```

4. **API 설계**
   - RESTful 규칙 준수
   - 에러 핸들링 필수
   - Swagger 문서 자동 생성

## 📊 성능 기준

**RFP 요구사항**:
- 첫 응답 시간: 5초 이내
- 동시 처리: 10개 쿼리
- 정확도: 90% 이상

**추가 기준** (Fine-tuning):
- 데이터셋 업로드: 200MB 파일 30초 이내
- 학습 속도: 7B 모델 LoRA, H100 2장으로 1 epoch당 2-4시간
- 체크포인트 저장: 500 step마다

## 🐛 문제 해결

### 일반적인 문제

**1. GPU 메모리 부족**
```bash
# GPU 상태 확인
nvidia-smi

# 특정 GPU만 사용
CUDA_VISIBLE_DEVICES=0 python script.py
```

**2. PostgreSQL 연결 오류**
```bash
# 컨테이너 확인
docker ps | grep postgres

# 연결 테스트
docker exec -it admin-api-postgres-1 psql -U postgres -d admin_db
```

**3. MLflow 연결 오류**
```bash
# MLflow 서버 확인
curl http://localhost:5000/health

# 환경 변수 확인
echo $MLFLOW_TRACKING_URI
```

## 📞 도움 요청

### Claude에게 도움 요청

```markdown
@Claude 다음 내용을 검토해주세요:

[코드 또는 설계]

확인 사항:
1. 기존 시스템과 충돌 없는지
2. DB 스키마가 적절한지
3. 보안 문제 없는지
```

### Gemini에게 도움 요청

```markdown
@Gemini 다음 기능을 구현해주세요:

[요구사항]

참고:
- 프롬프트: docs/FINETUNING_MLOPS_PROMPT.md
- 기존 코드: app/routers/admin/deployment.py
```

## 📈 프로젝트 상태

### 완료된 작업
- [x] 기본 API 인프라 (FastAPI + PostgreSQL + Qdrant)
- [x] 문서 관리 및 벡터화
- [x] 사용자/권한 관리
- [x] 통계 및 모니터링
- [x] MLflow 기본 연동

### 진행 중
- [ ] Fine-tuning MLOps 파이프라인 **(Gemini 담당)**
  - [ ] 데이터셋 관리 시스템
  - [ ] Fine-tuning 작업 실행
  - [ ] 모델 레지스트리
  - [ ] A/B 테스트 프레임워크

### 계획됨
- [ ] 멀티모달 LLM 통합
- [ ] "나만의 AI" 문서 비교 기능
- [ ] 특정 업무 맞춤형 AI (감사, 안전, 재난, 기술심사)

## 🔗 유용한 링크

- **MLflow UI**: http://localhost:5000 (실행 중이면)
- **Qdrant Dashboard**: http://localhost:6335/dashboard
- **Admin API Swagger**: http://localhost:8010/docs
- **프론트엔드**: http://localhost:3000

---

## 💬 마지막 업데이트

**날짜**: 2025-10-30
**작성자**: Claude Code
**상태**: Fine-tuning MLOps 프롬프트 작성 완료, Gemini와 협업 시작 예정

---

**이 문서를 읽은 AI는 위 규칙과 가이드를 따라 협업해주세요!**
