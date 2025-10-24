# 마이그레이션 일일 To-Do List (21일)

## 📅 Week 1: 환경 설정 및 기반 구축 (Day 1-7)

### Day 1 (월) - 프로젝트 구조 설정
**목표**: FastAPI 프로젝트 기본 구조 완성

#### 오전 (4시간)
- [ ] FastAPI 프로젝트 디렉토리 생성
  ```bash
  cd /home/aigen/admin-api
  mkdir -p app/routers/chat
  mkdir -p app/services
  mkdir -p app/schemas
  mkdir -p app/utils
  mkdir -p tests/chat
  ```
- [ ] `pyproject.toml` 의존성 추가
  ```toml
  python-jose = "^3.3.0"
  qdrant-client = "^1.7.0"
  python-multipart = "^0.0.6"
  slowapi = "^0.1.9"
  ```
- [ ] `poetry install` 실행
- [ ] Git 브랜치 생성: `git checkout -b feature/chat-migration`

#### 오후 (4시간)
- [ ] 파일 구조 생성:
  ```
  app/routers/chat/
    ├── __init__.py
    ├── chat.py          # 채팅 메시지
    ├── rooms.py         # 대화방 관리
    ├── history.py       # 히스토리
    └── files.py         # 파일 업로드

  app/schemas/
    └── chat_schemas.py  # Pydantic 모델

  app/services/
    ├── chat_service.py  # 비즈니스 로직
    └── ai_service.py    # AI 연동

  app/utils/
    ├── room_id_generator.py
    └── auth.py
  ```
- [ ] 각 파일에 기본 템플릿 작성
- [ ] Git commit: "chore: 프로젝트 구조 설정"

#### 완료 기준
- ✅ 디렉토리 구조 생성 완료
- ✅ 의존성 설치 완료
- ✅ Git 커밋 완료

---

### Day 2 (화) - 데이터베이스 설정
**목표**: PostgreSQL 테이블 생성 및 SQLAlchemy 모델 작성

#### 오전 (4시간)
- [ ] Alembic 마이그레이션 스크립트 작성
  ```bash
  alembic revision -m "create_chat_tables"
  ```
- [ ] 실제 테이블 구조 구현 (USR_CNVS_SMRY, USR_CNVS 등)
  ```python
  # migrations/versions/xxx_create_chat_tables.py
  def upgrade():
      # USR_CNVS_SMRY
      op.create_table(
          'USR_CNVS_SMRY',
          sa.Column('CNVS_IDT_ID', sa.String(255), primary_key=True),
          sa.Column('CNVS_SMRY_TXT', sa.Text),
          sa.Column('REP_CNVS_NM', sa.String(500)),
          sa.Column('USR_ID', sa.String(50), nullable=False),
          # ... 나머지 컬럼
      )
      # USR_CNVS, USR_CNVS_REF_DOC_LST 등
  ```
- [ ] 마이그레이션 실행: `alembic upgrade head`
- [ ] DB 연결 테스트

#### 오후 (4시간)
- [ ] SQLAlchemy 모델 작성 (`app/models/chat.py`)
  ```python
  class UsrCnvsSmry(Base):
      __tablename__ = 'USR_CNVS_SMRY'
      cnvs_idt_id = Column(String(255), primary_key=True)
      # ...
  ```
- [ ] Pydantic 스키마 작성 (`app/schemas/chat_schemas.py`)
  ```python
  class ChatRequest(BaseModel):
      cnvs_idt_id: str = ""
      message: str
      stream: bool = True
      # ...
  ```
- [ ] DB 쿼리 테스트 스크립트 작성
- [ ] Git commit: "feat: 데이터베이스 스키마 설정"

#### 완료 기준
- ✅ 6개 테이블 생성 완료
- ✅ SQLAlchemy 모델 작성 완료
- ✅ DB 연결 테스트 성공

---

### Day 3 (수) - 인증 시스템 구현
**목표**: HTTP 세션 기반 인증 구현 (JWT는 추후)

#### 오전 (4시간)
- [ ] Redis 설치 및 설정
  ```bash
  docker run -d --name redis -p 6379:6379 redis:7
  ```
- [ ] Redis 클라이언트 설정 (`app/core/redis.py`)
  ```python
  from redis import asyncio as aioredis
  redis_client = aioredis.from_url("redis://localhost:6379")
  ```
- [ ] 세션 기반 인증 함수 구현 (`app/utils/auth.py`)
  ```python
  async def get_current_user_from_session(
      session_id: str = Cookie(None, alias="JSESSIONID"),
      db: AsyncSession = Depends(get_db)
  ):
      # Redis에서 세션 조회
      # 사용자 정보 반환
  ```

#### 오후 (4시간)
- [ ] 인증 테스트 작성 (`tests/test_auth.py`)
  ```python
  async def test_session_validation():
      # 유효한 세션
      # 만료된 세션
      # 없는 세션
  ```
- [ ] 테스트 실행: `pytest tests/test_auth.py -v`
- [ ] 인증 미들웨어 추가 (`app/middleware/auth.py`)
- [ ] Git commit: "feat: HTTP 세션 인증 구현"

#### 완료 기준
- ✅ Redis 연동 완료
- ✅ 세션 인증 함수 작성 완료
- ✅ 테스트 통과 (3개 이상)

---

### Day 4 (목) - Room ID 생성 및 검증
**목표**: CNVS_IDT_ID 생성 로직 구현

#### 오전 (4시간)
- [ ] Room ID 생성 함수 구현 (`app/utils/room_id_generator.py`)
  ```python
  def generate_room_id(user_id: str) -> str:
      """
      형식: {user_id}_{timestamp}{microseconds}
      예: user123_20251022104412345678
      """
      now = datetime.now()
      timestamp = now.strftime('%Y%m%d%H%M%S')
      microseconds = f"{now.microsecond % 1000000:06d}"
      return f"{user_id}_{timestamp}{microseconds}"
  ```
- [ ] Room ID 파싱 함수 구현
  ```python
  def parse_room_id(room_id: str) -> dict:
      # user_id, timestamp, microseconds 추출
  ```
- [ ] Unit Test 작성 (`tests/test_room_id.py`)
  - 생성 형식 검증
  - 고유성 검증 (100회 생성)
  - 파싱 검증

#### 오후 (4시간)
- [ ] Room ID 검증 함수 구현 (`app/services/chat_service.py`)
  ```python
  async def validate_room_id(
      room_id: str,
      user_id: str,
      db: AsyncSession
  ) -> bool:
      """DB에서 room_id 소유권 확인 (Stateless)"""
      result = await db.execute(
          "SELECT COUNT(*) FROM USR_CNVS_SMRY "
          "WHERE CNVS_IDT_ID = :room_id AND USR_ID = :user_id",
          {"room_id": room_id, "user_id": user_id}
      )
      return result.scalar() > 0
  ```
- [ ] 검증 테스트 작성 (유효/무효/권한 없음)
- [ ] 테스트 실행: `pytest tests/test_room_id.py -v`
- [ ] Git commit: "feat: Room ID 생성 및 검증 구현"

#### 완료 기준
- ✅ Room ID 생성 함수 작동
- ✅ 검증 함수 작동
- ✅ 테스트 5개 이상 통과

---

### Day 5 (금) - AI 서비스 연동 (vLLM)
**목표**: vLLM API 호출 및 스트리밍 구현

#### 오전 (4시간)
- [ ] AI 서비스 클래스 기본 구조 (`app/services/ai_service.py`)
  ```python
  class AIService:
      def __init__(self):
          self.llm_url = settings.LLM_API_URL
          self.model = settings.LLM_MODEL

      async def stream_chat(
          self,
          message: str,
          history: List[Dict[str, str]] = None,
          **kwargs
      ) -> AsyncGenerator[str, None]:
          """vLLM OpenAI-compatible API 호출"""
  ```
- [ ] 환경 변수 설정 (`.env`)
  ```
  LLM_API_URL=http://localhost:8000/v1
  LLM_MODEL=Qwen/Qwen2.5-32B-Instruct
  ```
- [ ] vLLM 서버 연결 테스트
  ```bash
  curl http://localhost:8000/v1/models
  ```

#### 오후 (4시간)
- [ ] SSE 스트리밍 구현
  ```python
  async with httpx.AsyncClient(timeout=120.0) as client:
      async with client.stream(
          "POST",
          f"{self.llm_url}/chat/completions",
          json=llm_payload
      ) as response:
          async for line in response.aiter_lines():
              if line.startswith("data: "):
                  # 토큰 파싱 및 yield
  ```
- [ ] 테스트 작성 (`tests/test_ai_service.py`)
  - 기본 채팅 테스트
  - 스트리밍 테스트
- [ ] 실제 vLLM 서버로 테스트
- [ ] Git commit: "feat: vLLM AI 서비스 연동"

#### 완료 기준
- ✅ vLLM 서버 연결 성공
- ✅ 스트리밍 응답 수신 성공
- ✅ 테스트 2개 이상 통과

---

### Day 6 (토) - RAG 구현 (Qdrant 검색)
**목표**: 벡터 검색 및 컨텍스트 생성

#### 오전 (4시간)
- [ ] Qdrant 클라이언트 설정
  ```python
  from qdrant_client import QdrantClient

  client = QdrantClient(
      host=settings.QDRANT_HOST,
      port=settings.QDRANT_PORT,
      api_key=settings.QDRANT_API_KEY
  )
  ```
- [ ] 임베딩 생성 함수 구현
  ```python
  async def _get_embedding(self, text: str) -> List[float]:
      """vLLM embeddings API 호출"""
      async with httpx.AsyncClient() as client:
          response = await client.post(
              f"{self.embedding_url}/embeddings",
              json={"model": "default-embeddings", "input": text}
          )
          return response.json()["data"][0]["embedding"]
  ```
- [ ] Qdrant 연결 테스트

#### 오후 (4시간)
- [ ] 문서 검색 함수 구현
  ```python
  async def _search_documents(
      self,
      query: str,
      department: Optional[str] = None,
      max_results: int = 5
  ) -> List[Dict]:
      """Qdrant 벡터 검색"""
      query_vector = await self._get_embedding(query)
      search_results = client.search(
          collection_name=settings.QDRANT_COLLECTION,
          query_vector=query_vector,
          limit=max_results
      )
      return search_results
  ```
- [ ] 컨텍스트 생성 함수 구현 (`_build_messages`)
- [ ] RAG 테스트 작성
- [ ] Git commit: "feat: RAG 구현 (Qdrant)"

#### 완료 기준
- ✅ Qdrant 연결 성공
- ✅ 벡터 검색 작동
- ✅ RAG 컨텍스트 생성 성공

---

### Day 7 (일) - 채팅 API 구현 (SSE)
**목표**: POST /api/v1/chat/send 구현

#### 오전 (4시간)
- [ ] 채팅 API 라우터 구현 (`app/routers/chat/chat.py`)
  ```python
  @router.post("/api/v1/chat/send")
  async def send_chat_message(
      request: ChatRequest,
      current_user: dict = Depends(get_current_user_from_session),
      db: AsyncSession = Depends(get_db)
  ):
      """채팅 메시지 전송 (SSE)"""
      return StreamingResponse(
          generate_chat_stream(request, current_user["user_id"], db),
          media_type="text/event-stream"
      )
  ```
- [ ] 스트리밍 생성 함수 구현 (`generate_chat_stream`)
  - Room ID 생성/검증
  - AI 서비스 호출
  - DB 저장

#### 오후 (4시간)
- [ ] API 라우터 등록 (`app/main.py`)
  ```python
  from app.routers.chat import chat
  app.include_router(chat.router)
  ```
- [ ] Postman/curl 테스트
  ```bash
  curl -X POST http://localhost:8001/api/v1/chat/send \
    -H "Content-Type: application/json" \
    -H "Cookie: JSESSIONID=test-session" \
    -d '{"cnvs_idt_id": "", "message": "안녕하세요"}'
  ```
- [ ] 통합 테스트 작성
- [ ] Git commit: "feat: 채팅 API 구현"

#### 완료 기준
- ✅ API 호출 성공
- ✅ SSE 스트리밍 작동
- ✅ DB에 메시지 저장 확인

---

## 📅 Week 2: 핵심 기능 구현 (Day 8-14)

### Day 8 (월) - 질문 저장 로직
**목표**: USR_CNVS INSERT 구현

#### 오전 (4시간)
- [ ] 질문 저장 함수 구현 (`app/services/chat_service.py`)
  ```python
  async def save_question(
      db: AsyncSession,
      room_id: str,
      user_id: str,
      question: str,
      session_id: str
  ) -> int:
      """USR_CNVS에 질문 저장"""
      result = await db.execute(
          """
          INSERT INTO USR_CNVS (CNVS_IDT_ID, QUES_TXT, SESN_ID, USR_ID)
          VALUES (:room_id, :question, :session_id, :user_id)
          RETURNING CNVS_ID
          """,
          {
              "room_id": room_id,
              "question": question,
              "session_id": session_id,
              "user_id": user_id
          }
      )
      return result.scalar()
  ```
- [ ] 새 대화 시 USR_CNVS_SMRY INSERT
  ```python
  async def create_room(
      db: AsyncSession,
      room_id: str,
      user_id: str,
      first_question: str
  ):
      """USR_CNVS_SMRY 생성 (첫 질문으로 요약)"""
  ```

#### 오후 (4시간)
- [ ] 테스트 작성 (`tests/test_chat_service.py`)
  - 새 대화 생성 테스트
  - 기존 대화 질문 추가 테스트
- [ ] 채팅 API에 저장 로직 통합
- [ ] DB 데이터 확인
  ```sql
  SELECT * FROM USR_CNVS_SMRY;
  SELECT * FROM USR_CNVS;
  ```
- [ ] Git commit: "feat: 질문 저장 로직 구현"

#### 완료 기준
- ✅ 질문 저장 함수 작동
- ✅ Room 생성 함수 작동
- ✅ DB에 데이터 저장 확인

---

### Day 9 (화) - 답변 저장 로직
**목표**: USR_CNVS UPDATE 및 참조 문서 저장

#### 오전 (4시간)
- [ ] 답변 저장 함수 구현
  ```python
  async def save_answer(
      db: AsyncSession,
      cnvs_id: int,
      answer: str,
      token_count: int,
      response_time_ms: int
  ):
      """USR_CNVS 업데이트 (답변 추가)"""
      await db.execute(
          """
          UPDATE USR_CNVS
          SET ANS_TXT = :answer,
              TKN_USE_CNT = :tokens,
              RSP_TIM_MS = :response_time,
              MOD_DT = CURRENT_TIMESTAMP
          WHERE CNVS_ID = :cnvs_id
          """,
          {
              "answer": answer,
              "tokens": token_count,
              "response_time": response_time_ms,
              "cnvs_id": cnvs_id
          }
      )
  ```
- [ ] 토큰 카운트 함수 구현
  ```python
  def count_tokens(text: str) -> int:
      return len(text.split())  # 간단한 구현
  ```

#### 오후 (4시간)
- [ ] 참조 문서 저장 함수 구현
  ```python
  async def save_reference_documents(
      db: AsyncSession,
      cnvs_id: int,
      search_results: List[Dict]
  ):
      """USR_CNVS_REF_DOC_LST INSERT"""
      for idx, doc in enumerate(search_results):
          await db.execute(
              """
              INSERT INTO USR_CNVS_REF_DOC_LST (
                  CNVS_ID, REF_SEQ, ATT_DOC_NM,
                  DOC_CHNK_TXT, SMLT_RTE
              ) VALUES (:cnvs_id, :ref_seq, :doc_name, :chunk_text, :score)
              """,
              {
                  "cnvs_id": cnvs_id,
                  "ref_seq": idx,
                  "doc_name": doc["metadata"]["title"],
                  "chunk_text": doc["chunk_text"],
                  "score": doc["score"]
              }
          )
  ```
- [ ] 채팅 API에 답변 저장 통합
- [ ] 테스트 작성 및 실행
- [ ] Git commit: "feat: 답변 및 참조 문서 저장"

#### 완료 기준
- ✅ 답변 저장 작동
- ✅ 참조 문서 저장 작동
- ✅ DB 데이터 확인

---

### Day 10 (수) - 대화 목록 API
**목표**: POST /api/v1/chat/history/list 구현

#### 오전 (4시간)
- [ ] 히스토리 API 라우터 생성 (`app/routers/chat/history.py`)
  ```python
  @router.post("/api/v1/chat/history/list")
  async def get_conversation_list(
      user_id: str,
      current_user: dict = Depends(get_current_user_from_session),
      db: AsyncSession = Depends(get_db)
  ):
      """대화 목록 조회"""
  ```
- [ ] 대화 목록 조회 함수 구현
  ```python
  async def get_user_conversations(
      db: AsyncSession,
      user_id: str
  ) -> List[Dict]:
      """USR_CNVS_SMRY 조회"""
      result = await db.execute(
          """
          SELECT CNVS_IDT_ID, CNVS_SMRY_TXT, REG_DT
          FROM USR_CNVS_SMRY
          WHERE USR_ID = :user_id AND USE_YN = 'Y'
          ORDER BY REG_DT DESC
          """,
          {"user_id": user_id}
      )
      return result.fetchall()
  ```

#### 오후 (4시간)
- [ ] 권한 검증 추가 (본인 데이터만 조회)
  ```python
  if user_id != current_user["user_id"]:
      raise HTTPException(status_code=403)
  ```
- [ ] 응답 포맷 정의 (Pydantic)
  ```python
  class ConversationListResponse(BaseModel):
      conversations: List[ConversationSummary]
      total: int
  ```
- [ ] API 테스트 (curl/Postman)
- [ ] Git commit: "feat: 대화 목록 API 구현"

#### 완료 기준
- ✅ API 호출 성공
- ✅ 대화 목록 반환 확인
- ✅ 권한 검증 작동

---

### Day 11 (목) - 메시지 조회 API
**목표**: GET /api/v1/chat/history/{room_id} 구현

#### 오전 (4시간)
- [ ] 메시지 조회 API 구현
  ```python
  @router.get("/api/v1/chat/history/{room_id}")
  async def get_conversation_detail(
      room_id: str,
      current_user: dict = Depends(get_current_user_from_session),
      db: AsyncSession = Depends(get_db)
  ):
      """특정 대화의 메시지 상세 조회"""
  ```
- [ ] 메시지 조회 함수 구현
  ```python
  async def get_conversation_messages(
      db: AsyncSession,
      room_id: str
  ) -> List[Dict]:
      """USR_CNVS 조회 (질문 + 답변)"""
      result = await db.execute(
          """
          SELECT CNVS_ID, QUES_TXT, ANS_TXT, REG_DT
          FROM USR_CNVS
          WHERE CNVS_IDT_ID = :room_id AND USE_YN = 'Y'
          ORDER BY REG_DT, CNVS_ID
          """,
          {"room_id": room_id}
      )
      return result.fetchall()
  ```

#### 오후 (4시간)
- [ ] 참조 문서 조회 추가
  ```python
  # 각 메시지의 참조 문서 조회
  for msg in messages:
      refs = await db.execute(
          "SELECT * FROM USR_CNVS_REF_DOC_LST WHERE CNVS_ID = :cnvs_id",
          {"cnvs_id": msg.cnvs_id}
      )
      msg.references = refs.fetchall()
  ```
- [ ] 추천 질문 조회 추가 (USR_CNVS_ADD_QUES_LST)
- [ ] 응답 포맷 정의
- [ ] API 테스트
- [ ] Git commit: "feat: 메시지 조회 API 구현"

#### 완료 기준
- ✅ API 호출 성공
- ✅ 메시지 리스트 반환
- ✅ 참조 문서 포함 확인

---

### Day 12 (금) - 대화명 변경 및 삭제 API
**목표**: PATCH /rooms/{room_id}/name, DELETE /rooms/{room_id}

#### 오전 (4시간)
- [ ] 대화명 변경 API (`app/routers/chat/rooms.py`)
  ```python
  @router.patch("/api/v1/chat/rooms/{room_id}/name")
  async def update_room_name(
      room_id: str,
      name: str,
      current_user: dict = Depends(get_current_user_from_session),
      db: AsyncSession = Depends(get_db)
  ):
      """대화명 변경"""
      await db.execute(
          """
          UPDATE USR_CNVS_SMRY
          SET REP_CNVS_NM = :name, MOD_DT = CURRENT_TIMESTAMP
          WHERE CNVS_IDT_ID = :room_id
          """,
          {"name": name, "room_id": room_id}
      )
  ```
- [ ] 권한 검증 추가
- [ ] API 테스트

#### 오후 (4시간)
- [ ] 대화 삭제 API (소프트 삭제)
  ```python
  @router.delete("/api/v1/chat/rooms/{room_id}")
  async def delete_room(
      room_id: str,
      current_user: dict = Depends(get_current_user_from_session),
      db: AsyncSession = Depends(get_db)
  ):
      """대화 삭제 (USE_YN = 'N')"""
      await db.execute(
          """
          UPDATE USR_CNVS_SMRY
          SET USE_YN = 'N', MOD_DT = CURRENT_TIMESTAMP
          WHERE CNVS_IDT_ID = :room_id
          """,
          {"room_id": room_id}
      )
      # 하위 메시지도 소프트 삭제
      await db.execute(
          """
          UPDATE USR_CNVS
          SET USE_YN = 'N'
          WHERE CNVS_IDT_ID = :room_id
          """,
          {"room_id": room_id}
      )
  ```
- [ ] API 테스트
- [ ] Git commit: "feat: 대화명 변경 및 삭제 API"

#### 완료 기준
- ✅ 대화명 변경 작동
- ✅ 소프트 삭제 작동
- ✅ DB 데이터 확인

---

### Day 13 (토) - 파일 업로드 API
**목표**: POST /api/v1/files/upload 구현

#### 오전 (4시간)
- [ ] 파일 업로드 API (`app/routers/chat/files.py`)
  ```python
  @router.post("/api/v1/files/upload")
  async def upload_chat_file(
      file: UploadFile = File(...),
      room_id: str = Form(...),
      current_user: dict = Depends(get_current_user_from_session),
      db: AsyncSession = Depends(get_db)
  ):
      """채팅 파일 업로드"""
  ```
- [ ] 파일 타입 검증 (PDF, DOCX, XLSX, TXT, PNG, JPG)
- [ ] 파일 크기 검증 (100MB)
- [ ] MinIO 업로드 연동 (기존 minio_service 활용)

#### 오후 (4시간)
- [ ] DB 메타데이터 저장 (USR_UPLD_DOC_MNG)
  ```python
  await db.execute(
      """
      INSERT INTO USR_UPLD_DOC_MNG (
          CNVS_IDT_ID, FILE_NM, FILE_UID,
          FILE_SIZE, USR_ID
      ) VALUES (:room_id, :filename, :file_uid, :size, :user_id)
      """,
      {...}
  )
  ```
- [ ] 파일 다운로드 URL 생성
- [ ] API 테스트 (실제 파일 업로드)
- [ ] Git commit: "feat: 파일 업로드 API 구현"

#### 완료 기준
- ✅ 파일 업로드 성공
- ✅ MinIO 저장 확인
- ✅ DB 메타데이터 저장 확인

---

### Day 14 (일) - 통합 테스트
**목표**: E2E 시나리오 테스트

#### 오전 (4시간)
- [ ] E2E 테스트 시나리오 작성 (`tests/test_e2e_chat.py`)
  ```python
  async def test_full_chat_flow():
      # 1. 새 대화 시작 (cnvs_idt_id = "")
      # 2. room_id 받기
      # 3. 추가 메시지 전송 (room_id 전달)
      # 4. 대화 목록 조회
      # 5. 메시지 조회
      # 6. 대화명 변경
      # 7. 대화 삭제
  ```
- [ ] Stateless 아키텍처 테스트
  - 세션 없이 room_id만으로 대화 이어가기
- [ ] 권한 검증 테스트
  - 다른 사용자의 room_id 접근 차단

#### 오후 (4시간)
- [ ] 부하 테스트 (선택사항)
  ```bash
  # 동시 요청 10개
  for i in {1..10}; do
    curl -X POST http://localhost:8001/api/v1/chat/send ... &
  done
  ```
- [ ] 버그 수정
- [ ] 코드 리뷰 및 리팩토링
- [ ] Git commit: "test: E2E 통합 테스트 추가"

#### 완료 기준
- ✅ E2E 시나리오 통과
- ✅ Stateless 검증 완료
- ✅ 권한 검증 통과

---

## 📅 Week 3: 프론트엔드 통합 및 배포 (Day 15-21)

### Day 15 (월) - React API 클라이언트 수정
**목표**: 프론트엔드 API 연동 수정

#### 오전 (4시간)
- [ ] API 클라이언트 수정 (`src/api/chat.js`)
  ```javascript
  // AS-IS: POST /api/chat/conversation
  // TO-BE: POST /api/v1/chat/send
  export const sendChatMessage = async (message, roomId) => {
    const response = await fetch('/api/v1/chat/send', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        cnvs_idt_id: roomId,
        message: message,
        stream: true
      })
    });
    return response;
  };
  ```
- [ ] 히스토리 API 수정 (`src/api/history.js`)
  ```javascript
  // POST /api/chat/history/list → POST /api/v1/chat/history/list
  export const getConversationList = async (userId) => {
    const response = await fetch('/api/v1/chat/history/list', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ user_id: userId })
    });
    return response.json();
  };
  ```

#### 오후 (4시간)
- [ ] SSE 응답 파싱 수정
  ```javascript
  // room_created 이벤트 처리
  if (data.type === 'room_created') {
    const newRoomId = data.room_id;
    roomIdStore.setCurrentRoomId(newRoomId);
  }
  ```
- [ ] 에러 핸들링 개선
- [ ] 로컬 테스트 (프론트+백엔드 동시 실행)
  ```bash
  # Backend
  cd /home/aigen/admin-api
  uvicorn app.main:app --reload --port 8001

  # Frontend
  cd /home/aigen/new-exgpt-feature-chat/frontend
  npm run dev
  ```
- [ ] Git commit: "feat: React API 클라이언트 수정"

#### 완료 기준
- ✅ API 경로 변경 완료
- ✅ 로컬 테스트 성공
- ✅ SSE 스트리밍 작동 확인

---

### Day 16 (화) - Zustand Store 검증
**목표**: 상태 관리 동작 확인

#### 오전 (4시간)
- [ ] roomIdStore 동작 확인
  ```javascript
  // 새 대화 시작 시 roomId 초기화 확인
  // room_created 이벤트로 roomId 설정 확인
  // 기존 대화 클릭 시 roomId 변경 확인
  ```
- [ ] messageStore 확인
  - 메시지 추가/삭제
  - 히스토리 로드
- [ ] 브라우저 DevTools로 상태 확인
  ```javascript
  // Redux DevTools 또는 Console 로그
  console.log(useRoomId.getState());
  console.log(useMessageStore.getState());
  ```

#### 오후 (4시간)
- [ ] ChatHistory.jsx 통합 테스트
  - 대화 목록 표시
  - 클릭 시 roomId 변경
  - 새 대화 버튼 동작
- [ ] 버그 수정
- [ ] Git commit: "test: Zustand store 검증 완료"

#### 완료 기준
- ✅ roomId 상태 관리 정상
- ✅ 메시지 상태 관리 정상
- ✅ UI 동작 확인

---

### Day 17 (수) - UI 컴포넌트 E2E 테스트
**목표**: 실제 사용자 시나리오 테스트

#### 오전 (4시간)
- [ ] ChatPage.jsx E2E 테스트
  1. 페이지 로드
  2. "안녕하세요" 입력
  3. 전송 버튼 클릭
  4. 스트리밍 응답 확인
  5. roomId 확인
  6. 추가 메시지 전송
  7. 히스토리 확인
- [ ] 브라우저 콘솔 에러 확인
- [ ] 네트워크 탭 확인 (API 요청/응답)

#### 오후 (4시간)
- [ ] 파일 업로드 UI 테스트
  - 파일 선택
  - 업로드 진행 표시
  - 업로드 완료 확인
- [ ] 대화명 변경 UI 테스트
- [ ] 대화 삭제 UI 테스트
- [ ] 버그 수정
- [ ] Git commit: "test: UI 컴포넌트 E2E 테스트"

#### 완료 기준
- ✅ 전체 사용자 시나리오 정상 작동
- ✅ 콘솔 에러 없음
- ✅ 네트워크 요청 정상

---

### Day 18 (목) - 보안 테스트
**목표**: OWASP Top 10 검증

#### 오전 (4시간)
- [ ] SQL Injection 테스트
  ```python
  # tests/test_security.py
  async def test_sql_injection_prevention():
      malicious_room_id = "'; DROP TABLE USR_CNVS_SMRY; --"
      response = await client.post(
          "/api/v1/chat/send",
          json={"cnvs_idt_id": malicious_room_id, "message": "test"}
      )
      assert response.status_code in [400, 403]
  ```
- [ ] XSS 테스트
  ```python
  async def test_xss_prevention():
      xss_message = "<script>alert('XSS')</script>"
      response = await client.post(
          "/api/v1/chat/send",
          json={"cnvs_idt_id": "", "message": xss_message}
      )
      # 응답에 <script> 태그가 이스케이프되었는지 확인
  ```
- [ ] Path Traversal 테스트

#### 오후 (4시간)
- [ ] 인증/권한 테스트
  - 세션 없이 API 호출 → 401
  - 다른 사용자 room_id 접근 → 403
- [ ] Rate Limiting 테스트 (선택사항)
- [ ] Bandit 정적 분석
  ```bash
  pip install bandit
  bandit -r app/
  ```
- [ ] 보안 이슈 수정
- [ ] Git commit: "test: 보안 테스트 및 취약점 수정"

#### 완료 기준
- ✅ OWASP Top 10 테스트 통과
- ✅ Bandit 경고 0개
- ✅ 인증/권한 검증 정상

---

### Day 19 (금) - 성능 테스트 및 최적화
**목표**: 응답 시간 및 동시성 테스트

#### 오전 (4시간)
- [ ] 응답 시간 측정
  ```python
  import time
  start = time.time()
  response = await client.post("/api/v1/chat/send", ...)
  end = time.time()
  print(f"Response time: {end - start:.2f}s")
  ```
- [ ] DB 쿼리 최적화
  - 인덱스 확인
  - N+1 쿼리 문제 해결
- [ ] 로깅 레벨 조정 (DEBUG → INFO)

#### 오후 (4시간)
- [ ] 동시성 테스트 (locust 또는 ab)
  ```bash
  ab -n 100 -c 10 http://localhost:8001/api/v1/chat/send
  ```
- [ ] 메모리 사용량 확인
  ```bash
  docker stats admin-api
  ```
- [ ] 병목 지점 파악 및 개선
- [ ] Git commit: "perf: 성능 최적화"

#### 완료 기준
- ✅ 평균 응답 시간 < 2초
- ✅ 동시 요청 10개 처리 가능
- ✅ 메모리 사용량 안정적

---

### Day 20 (토) - Docker 이미지 빌드 및 배포 준비
**목표**: 운영 환경 설정

#### 오전 (4시간)
- [ ] Dockerfile 최적화
  ```dockerfile
  FROM python:3.11-slim

  WORKDIR /app

  COPY pyproject.toml poetry.lock ./
  RUN pip install poetry && poetry install --no-dev

  COPY app ./app
  COPY alembic ./alembic
  COPY alembic.ini ./

  CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
  ```
- [ ] docker-compose.yml 작성
- [ ] 이미지 빌드
  ```bash
  docker compose build
  ```
- [ ] 로컬 Docker 테스트
  ```bash
  docker compose up -d
  docker logs admin-api -f
  ```

#### 오후 (4시간)
- [ ] 환경 변수 설정 (`.env.production`)
  ```
  DATABASE_URL=postgresql+asyncpg://...
  LLM_API_URL=http://vllm:8000/v1
  QDRANT_HOST=qdrant
  LOG_LEVEL=INFO
  ENVIRONMENT=production
  ```
- [ ] Nginx 설정 업데이트
  ```nginx
  location /api/v1/ {
      proxy_pass http://localhost:8001;
      # SSE 지원 설정
  }
  ```
- [ ] SSL 인증서 확인
- [ ] Git commit: "chore: Docker 배포 설정"

#### 완료 기준
- ✅ Docker 이미지 빌드 성공
- ✅ 로컬 Docker 테스트 성공
- ✅ Nginx 설정 완료

---

### Day 21 (일) - 운영 배포 및 문서화
**목표**: 프로덕션 배포 및 마무리

#### 오전 (4시간)
- [ ] 운영 서버 배포
  ```bash
  ssh user@ui.datastreams.co.kr
  cd /home/aigen/admin-api
  git pull origin main
  ./deploy.sh
  ```
- [ ] 헬스 체크
  ```bash
  curl https://ui.datastreams.co.kr:20443/health
  curl https://ui.datastreams.co.kr:20443/health/detailed
  ```
- [ ] 실제 사용자 시나리오 테스트
  - 로그인
  - 채팅 전송
  - 히스토리 조회
- [ ] 로그 모니터링
  ```bash
  docker logs admin-api -f --tail 100
  ```

#### 오후 (4시간)
- [ ] API 문서 생성 (Swagger)
  - `https://ui.datastreams.co.kr:20443/docs` 접속 확인
  - API 엔드포인트 설명 추가
- [ ] 배포 가이드 작성 (`DEPLOYMENT.md`)
  ```markdown
  # 배포 가이드
  ## 사전 준비
  ## 배포 절차
  ## 롤백 방법 (N/A)
  ## 트러블슈팅
  ```
- [ ] README.md 업데이트
- [ ] 팀에 배포 완료 공지
- [ ] Git commit: "docs: 배포 가이드 작성"
- [ ] Git merge: `git merge feature/chat-migration` → `main`

#### 완료 기준
- ✅ 프로덕션 배포 완료
- ✅ 모든 기능 정상 작동
- ✅ 문서화 완료

---

## 📊 진행률 체크리스트

### Week 1 (Day 1-7)
- [ ] 프로젝트 구조 설정
- [ ] 데이터베이스 설정
- [ ] 인증 시스템
- [ ] Room ID 생성/검증
- [ ] AI 서비스 연동
- [ ] RAG 구현
- [ ] 채팅 API 기본 구현

### Week 2 (Day 8-14)
- [ ] 질문 저장
- [ ] 답변 저장
- [ ] 대화 목록 API
- [ ] 메시지 조회 API
- [ ] 대화명 변경/삭제
- [ ] 파일 업로드
- [ ] 통합 테스트

### Week 3 (Day 15-21)
- [ ] React API 연동
- [ ] Zustand Store 검증
- [ ] UI E2E 테스트
- [ ] 보안 테스트
- [ ] 성능 최적화
- [ ] Docker 배포
- [ ] 운영 배포 및 문서화

---

## 🎯 주요 마일스톤

| 날짜 | 마일스톤 | 산출물 |
|------|---------|--------|
| Day 3 | 인증 시스템 완료 | HTTP 세션 인증 작동 |
| Day 7 | 채팅 API 완료 | SSE 스트리밍 작동 |
| Day 12 | CRUD API 완료 | 모든 API 엔드포인트 작동 |
| Day 14 | 백엔드 완료 | E2E 테스트 통과 |
| Day 17 | 프론트엔드 통합 완료 | UI 정상 작동 |
| Day 21 | 프로덕션 배포 완료 | 운영 환경 배포 |

---

## 💡 팁

1. **매일 Git Commit**: 작업 내용을 매일 커밋하여 진행 상황 추적
2. **테스트 먼저**: 기능 구현 전에 테스트 케이스 작성 (TDD)
3. **코드 리뷰**: Day 7, 14, 21에 팀원과 코드 리뷰
4. **문제 발생 시**: MIGRATION_PRD.md의 구현 예시 참고
5. **시간 부족 시**: 우선순위 조정 (파일 업로드 → 추후, 보안 테스트 → 필수)

---

**작성일**: 2025-10-22
**예상 소요 시간**: 21일 (주 5일 근무 기준)
**실제 작업 시간**: 약 168시간 (8시간/일 × 21일)
