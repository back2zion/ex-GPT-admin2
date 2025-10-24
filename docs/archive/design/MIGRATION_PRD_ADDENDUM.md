# MIGRATION_PRD 추가 섹션 (실제 코드 분석 기반)

## 🔐 인증 시스템 통합 (실제 구현 기반)

### 현재 상태 (AS-IS)

**Spring Boot 인증:**
```java
// SecurityConfig.java:30-36
.sessionManagement(session -> session
    .sessionCreationPolicy(SessionCreationPolicy.ALWAYS)
    .maximumSessions(1)
    .maxSessionsPreventsLogin(false)
)

// application.yml:97
ds.ssoUse: false  # SSO는 아직 미구현
```

**주요 특징:**
- HTTP 세션 기반 인증 (Spring Session)
- DreamSecurity SSO 미구현 (주석에 "담에 SSO 할 때" 표시)
- 세션 만료 시 `/api/auth/login` 리다이렉트
- **사용자 답변**: 백엔드에서만 가능, 기존 사용자는 로그인 없이 마이그레이션 불가

### FastAPI 마이그레이션 전략 (TO-BE)

#### 방안 1: HTTP 세션 유지 (단기 - 빠른 마이그레이션)

**장점:**
- 기존 사용자 영향 최소화 (세션 공유 가능)
- 로그인 시스템 변경 불필요
- 빠른 배포 가능 (1-2주)

**단점:**
- Stateful 서버 (수평 확장 제한)
- Redis 세션 스토어 필요
- 세션 동기화 복잡도

**구현 예시:**
```python
# app/core/session.py
from fastapi import Cookie, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
import redis.asyncio as redis
import json

# Redis 세션 스토어
redis_client = redis.from_url("redis://localhost:6379")

async def get_current_user_from_session(
    session_id: str = Cookie(None, alias="JSESSIONID"),
    db: AsyncSession = Depends(get_db)
):
    """HTTP 세션에서 사용자 정보 조회"""
    if not session_id:
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다")

    # Redis에서 세션 조회
    user_data = await redis_client.get(f"session:{session_id}")
    if not user_data:
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다")

    user_info = json.loads(user_data)
    return user_info

# app/routers/chat/chat.py
@router.post("/api/v1/chat/send")
async def send_chat_message(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user_from_session)
):
    """HTTP 세션 기반 인증"""
    user_id = current_user["usr_id"]
    department = current_user["dept_cd"]
    # ... 처리
```

#### 방안 2: JWT 토큰 (중기 - 권장)

**장점:**
- Stateless 서버 (수평 확장 가능)
- 마이크로서비스 친화적
- Redis 불필요

**단점:**
- 기존 사용자 재로그인 필요
- 로그인 시스템 수정 필요

**구현 예시:**
```python
# app/core/security.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = "your-secret-key-change-this"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8시간

security = HTTPBearer()

def create_access_token(user_info: dict) -> str:
    """JWT 토큰 생성"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": user_info["usr_id"],
        "dept": user_info["dept_cd"],
        "name": user_info["usr_nm"],
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """JWT 토큰 검증"""
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰")

        return {
            "user_id": user_id,
            "department": payload.get("dept"),
            "name": payload.get("name")
        }

    except JWTError:
        raise HTTPException(status_code=401, detail="토큰 검증 실패")

# app/routers/auth/login.py
@router.post("/api/v1/auth/login")
async def login(
    username: str,
    password: str,
    db: AsyncSession = Depends(get_db)
):
    """로그인 (JWT 발급)"""
    # 사용자 인증 (DB 조회)
    user = await authenticate_user(db, username, password)

    if not user:
        raise HTTPException(status_code=401, detail="인증 실패")

    # JWT 토큰 생성
    access_token = create_access_token({
        "usr_id": user.usr_id,
        "dept_cd": user.dept_cd,
        "usr_nm": user.usr_nm
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": {
            "user_id": user.usr_id,
            "name": user.usr_nm,
            "department": user.dept_cd
        }
    }
```

**프론트엔드 변경 (React):**
```javascript
// src/api/auth.js
export const login = async (username, password) => {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });

  const data = await response.json();

  // 토큰 저장 (localStorage)
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('user_info', JSON.stringify(data.user_info));

  return data;
};

// src/api/chat.js
const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };
};

export const sendChatMessage = async (message, roomId) => {
  const response = await fetch('/api/v1/chat/send', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      cnvs_idt_id: roomId,
      message: message
    })
  });

  return response;
};
```

#### 권장: 단계별 마이그레이션

**Week 1-2: HTTP 세션 유지**
- 빠른 배포 및 검증
- Redis 세션 스토어 구성

**Week 3-4: JWT 전환 준비**
- 로그인 API 개발 (`/api/v1/auth/login`)
- 프론트엔드 토큰 관리 코드 추가
- 병렬 운영 (세션 + JWT 모두 지원)

**Week 5: 완전 전환**
- HTTP 세션 제거
- JWT만 사용

---

## 🤖 AI 서비스 연동 (vLLM + RAG)

### 실제 환경 분석

**ex-gpt AI 서버 (사용자 답변):**
```yaml
# ex-gpt/template.env
CHAT_MODEL_ENDPOINT=http://vllm:8000/v1
EMBEDDING_MODEL_ENDPOINT=http://vllm-embeddings:8000/v1
RERANK_MODEL_ENDPOINT=http://vllm-rerank:8000/v1

# 모델 선택
DEFAULT_MODEL=Qwen/Qwen2.5-32B-Instruct  # 외부망
# 내부망: Qwen/Qwen3-235B-A22B-AWQ
```

**Spring Boot AI 호출 방식:**
```java
// ChatController.java:109
String targetUrl = aiServerUrl + "/v1/chat/";  // http://localhost:8083/v1/chat/

// POST 요청 (SSE 스트리밍)
HttpPost post = new HttpPost(targetUrl);
post.setHeader("Content-Type", "application/json");
post.setHeader("X-API-Key", apiKey);

// 요청 본문
{
  "user_id": "user123",
  "department": "D001",
  "authorization": "Bearer <api-key>",
  "stream": true,
  "message": "질문 내용",
  "history": [],
  "search_documents": true,
  "max_context_tokens": 4000,
  "temperature": 0.7
}
```

**기존 admin-api AI 호출 방식 (chat_proxy.py 참고):**
```python
# app/routers/chat_proxy.py:141
async with client.stream(
    "POST",
    f"{LLM_API_URL}/v1/chat/completions",  # vLLM OpenAI-compatible API
    json=llm_payload,
    headers={"Content-Type": "application/json"}
) as response:
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            data_str = line[6:].strip()
            if data_str == "[DONE]":
                break

            data = json.loads(data_str)
            token = data["choices"][0]["delta"]["content"]
            yield f"data: {json.dumps({'content': token})}\n\n"
```

### FastAPI 구현 (TO-BE)

#### AI 서비스 클래스 (완전한 구현)

```python
# app/services/ai_service.py
import httpx
import json
from typing import AsyncGenerator, List, Dict, Any, Optional
from app.core.config import settings

class AIService:
    """vLLM OpenAI-compatible API 연동"""

    def __init__(self):
        self.llm_url = settings.LLM_API_URL  # http://localhost:8000/v1
        self.model = settings.LLM_MODEL  # Qwen/Qwen2.5-32B-Instruct
        self.embedding_url = settings.EMBEDDING_MODEL_ENDPOINT

    async def stream_chat(
        self,
        message: str,
        history: List[Dict[str, str]] = None,
        search_documents: bool = False,
        department: Optional[str] = None,
        search_scope: Optional[List[str]] = None,
        max_context_tokens: int = 4000,
        temperature: float = 0.7,
        think_mode: bool = False
    ) -> AsyncGenerator[str, None]:
        """AI 채팅 스트리밍 (vLLM OpenAI-compatible)"""

        # RAG: 문서 검색 (Qdrant)
        search_results = []
        if search_documents:
            search_results = await self._search_documents(
                message,
                department=department,
                search_scope=search_scope,
                max_results=5
            )

        # 컨텍스트 생성
        messages = self._build_messages(message, history, search_results)

        # vLLM 요청 페이로드
        llm_payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "max_tokens": 2000,
            "temperature": temperature
        }

        # Think Mode 활성화
        if think_mode:
            llm_payload["extra_body"] = {
                "enable_thinking": True,
                "thinking_budget": 2000
            }

        # 스트리밍 호출
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.llm_url}/chat/completions",
                json=llm_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status_code != 200:
                    error_msg = f"AI 서버 오류: {response.status_code}"
                    yield json.dumps({"error": error_msg})
                    return

                # SSE 파싱 및 전달
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                token = delta.get("content", "")

                                if token:
                                    yield token
                        except json.JSONDecodeError:
                            pass

    async def _search_documents(
        self,
        query: str,
        department: Optional[str] = None,
        search_scope: Optional[List[str]] = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Qdrant 벡터 검색 (RAG)"""
        from qdrant_client import QdrantClient
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        # Qdrant 클라이언트
        client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            api_key=settings.QDRANT_API_KEY
        )

        # 쿼리 임베딩 생성
        query_vector = await self._get_embedding(query)

        # 필터 구성
        query_filter = None
        if department or search_scope:
            conditions = []

            if department:
                conditions.append(
                    FieldCondition(key="department", match=MatchValue(value=department))
                )

            if search_scope:
                conditions.append(
                    FieldCondition(key="category", match=MatchValue(any=search_scope))
                )

            if conditions:
                query_filter = Filter(must=conditions)

        # 벡터 검색
        search_results = client.search(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=max_results
        )

        # 결과 변환
        results = []
        for hit in search_results:
            results.append({
                "document_id": hit.payload.get("document_id"),
                "chunk_text": hit.payload.get("chunk_text"),
                "score": hit.score,
                "metadata": {
                    "title": hit.payload.get("title"),
                    "category": hit.payload.get("category"),
                    "department": hit.payload.get("department")
                }
            })

        return results

    async def _get_embedding(self, text: str) -> List[float]:
        """텍스트 임베딩 생성 (vLLM embeddings API)"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.embedding_url}/embeddings",
                json={
                    "model": "default-embeddings",
                    "input": text
                }
            )

            data = response.json()
            return data["data"][0]["embedding"]

    def _build_messages(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]],
        search_results: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """LLM 프롬프트 생성 (RAG 컨텍스트 포함)"""
        messages = []

        # 시스템 프롬프트
        system_prompt = "당신은 AI Streams의 전문적인 AI 어시스턴트입니다."

        # RAG 컨텍스트 추가
        if search_results:
            context = "\n\n참조 문서:\n"
            for idx, doc in enumerate(search_results, 1):
                context += f"\n[문서 {idx}] {doc['metadata']['title']}\n{doc['chunk_text'][:500]}...\n"

            system_prompt += f"\n\n{context}\n\n위 참조 문서를 바탕으로 답변해주세요."

        messages.append({"role": "system", "content": system_prompt})

        # 대화 이력
        if history:
            messages.extend(history)

        # 현재 질문
        messages.append({"role": "user", "content": message})

        return messages


# Singleton
ai_service = AIService()
```

#### 환경 변수 설정

```python
# app/core/config.py
class Settings(BaseSettings):
    # AI Service (vLLM)
    LLM_API_URL: str = "http://localhost:8000/v1"
    LLM_MODEL: str = "Qwen/Qwen2.5-32B-Instruct"
    EMBEDDING_MODEL_ENDPOINT: str = "http://localhost:8001/v1"
    RERANK_MODEL_ENDPOINT: str = "http://localhost:8002/v1"

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6335
    QDRANT_COLLECTION: str = "130825-512-v3"
    QDRANT_API_KEY: str = "QFy9YlRTm0Y1yo6D"
```

```.env
# .env
LLM_API_URL=http://host.docker.internal:8000/v1
LLM_MODEL=Qwen/Qwen2.5-32B-Instruct
EMBEDDING_MODEL_ENDPOINT=http://host.docker.internal:8001/v1
QDRANT_HOST=localhost
QDRANT_PORT=6335
QDRANT_COLLECTION=130825-512-v3
QDRANT_API_KEY=QFy9YlRTm0Y1yo6D
```

---

## 📁 MinIO 파일 업로드 (실제 구현 기반)

### 기존 구현 분석

**admin-api/app/services/minio_service.py (이미 구현됨):**
```python
class MinIOService:
    """MinIO 파일 업로드 서비스"""

    def upload_file(
        self,
        file_obj: BinaryIO,
        filename: str,
        content_type: str = "application/octet-stream"
    ) -> Tuple[str, int]:
        """
        파일 업로드
        - Path Traversal 방지
        - 파일 크기 제한 (100MB)
        - UUID 기반 고유 경로 생성
        """
        safe_filename = self._sanitize_filename(filename)
        file_extension = os.path.splitext(safe_filename)[1]
        unique_id = str(uuid.uuid4())
        object_name = f"documents/{unique_id}{file_extension}"

        # Upload to MinIO
        self.client.put_object(
            self.bucket,
            object_name,
            file_obj,
            length=file_size,
            content_type=content_type
        )

        return object_name, file_size
```

### FastAPI 채팅 파일 업로드 구현

```python
# app/routers/chat/files.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from app.services.minio_service import minio_service
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/api/v1/files/upload")
async def upload_chat_file(
    file: UploadFile = File(...),
    room_id: str = Form(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    채팅 파일 업로드 (MinIO + DB)

    Security:
    - 파일 타입 검증 (허용: PDF, DOCX, XLSX, TXT, PNG, JPG)
    - 파일 크기 제한 (100MB)
    - Path Traversal 방지
    - 바이러스 스캔 (TODO)
    """
    # 1. 권한 검증: room_id가 사용자 소유인지 확인
    is_valid = await validate_room_id(room_id, current_user["user_id"], db)
    if not is_valid:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    # 2. 파일 타입 검증
    ALLOWED_EXTENSIONS = {
        '.pdf', '.docx', '.xlsx', '.txt',
        '.png', '.jpg', '.jpeg'
    }
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"허용되지 않은 파일 형식입니다: {file_ext}"
        )

    # 3. 파일 크기 확인
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > 100 * 1024 * 1024:  # 100MB
        raise HTTPException(
            status_code=400,
            detail="파일 크기가 100MB를 초과합니다."
        )

    # 4. MinIO 업로드
    try:
        object_name, uploaded_size = minio_service.upload_file(
            file.file,
            file.filename,
            file.content_type
        )
    except Exception as e:
        logger.error(f"MinIO upload error: {e}")
        raise HTTPException(
            status_code=500,
            detail="파일 업로드 실패"
        )

    # 5. DB에 메타데이터 저장 (USR_UPLD_DOC_MNG)
    file_uid = object_name  # "documents/uuid.pdf"
    file_download_url = minio_service.get_file_url(object_name)

    await db.execute(
        """
        INSERT INTO USR_UPLD_DOC_MNG (
            CNVS_IDT_ID, FILE_NM, FILE_UID, FILE_DOWN_URL,
            FILE_SIZE, FILE_TYP_CD, USR_ID, REG_DT
        ) VALUES (
            :room_id, :filename, :file_uid, :file_url,
            :file_size, :file_type, :user_id, CURRENT_TIMESTAMP
        )
        """,
        {
            "room_id": room_id,
            "filename": file.filename,
            "file_uid": file_uid,
            "file_url": file_download_url,
            "file_size": uploaded_size,
            "file_type": file_ext[1:],  # ".pdf" -> "pdf"
            "user_id": current_user["user_id"]
        }
    )
    await db.commit()

    # 6. 벡터화 트리거 (백그라운드 작업)
    from app.tasks.vectorization import trigger_vectorization
    await trigger_vectorization(file_uid, room_id)

    return {
        "success": True,
        "file_uid": file_uid,
        "filename": file.filename,
        "size": uploaded_size,
        "download_url": file_download_url
    }
```

**벡터화 트리거 (백그라운드 작업):**
```python
# app/tasks/vectorization.py
import asyncio
import httpx
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

async def trigger_vectorization(file_uid: str, room_id: str):
    """
    문서 벡터화 트리거 (비동기)

    1. MinIO에서 파일 다운로드
    2. 텍스트 추출 (PDF, DOCX 등)
    3. 청킹 (512 tokens per chunk)
    4. 임베딩 생성 (vLLM embeddings API)
    5. Qdrant 업로드
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.ADMIN_API_URL}/api/v1/admin/documents/upload",
                json={
                    "file_uid": file_uid,
                    "room_id": room_id
                },
                timeout=300.0
            )

            if response.status_code == 200:
                logger.info(f"Vectorization triggered: {file_uid}")
            else:
                logger.error(f"Vectorization failed: {response.text}")

    except Exception as e:
        logger.error(f"Vectorization trigger error: {e}")
```

---

## 📊 모니터링 및 로깅 전략

### 현재 상태 (AS-IS)

**Spring Boot 로깅:**
```yaml
# application.yml:66-75
logging:
  level:
    root: DEBUG
    com.datastreams.gpt: DEBUG
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n"
  file:
    name: logs/dsgpt.log
```

**admin-api 로깅:**
- 기본 로깅만 있음 (구조화된 로깅 없음)
- Prometheus metrics 없음

### FastAPI 모니터링 구현 (TO-BE)

#### 1. 구조화된 로깅 (JSON 포맷)

```python
# app/core/logging_config.py
import logging
import sys
from pythonjsonlogger import jsonlogger
from datetime import datetime
from app.core.config import settings

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """구조화된 JSON 로깅"""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        # 타임스탬프
        log_record['timestamp'] = datetime.utcnow().isoformat()

        # 로그 레벨
        log_record['level'] = record.levelname

        # 서비스 정보
        log_record['service'] = 'admin-api'
        log_record['environment'] = settings.ENVIRONMENT

        # 요청 정보 (컨텍스트에서 가져오기)
        from contextvars import ContextVar
        request_context: ContextVar = ContextVar('request_context', default={})
        context = request_context.get()

        if context:
            log_record['user_id'] = context.get('user_id')
            log_record['request_id'] = context.get('request_id')
            log_record['endpoint'] = context.get('endpoint')

def setup_logging():
    """로깅 설정"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # JSON 포맷 핸들러
    handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
```

#### 2. Request ID 미들웨어

```python
# app/middleware/logging.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import logging
from contextvars import ContextVar

request_context = ContextVar('request_context', default={})
logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """요청 로깅 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        # Request ID 생성
        request_id = str(uuid.uuid4())

        # 컨텍스트 설정
        context = {
            'request_id': request_id,
            'endpoint': f"{request.method} {request.url.path}",
            'user_id': None
        }
        request_context.set(context)

        # 요청 로깅
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host
            }
        )

        # 요청 처리
        response = await call_next(request)

        # 응답 로깅
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code
            }
        )

        # Response Header에 Request ID 추가
        response.headers["X-Request-ID"] = request_id

        return response
```

#### 3. Health Check API

```python
# app/routers/health.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.minio_service import minio_service
from app.core.config import settings
from qdrant_client import QdrantClient
import httpx

router = APIRouter()

@router.get("/health")
async def health_check():
    """기본 헬스 체크"""
    return {
        "status": "healthy",
        "service": "admin-api",
        "version": "0.1.0"
    }

@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """상세 헬스 체크 (DB, MinIO, Qdrant, vLLM)"""
    health = {
        "status": "healthy",
        "checks": {}
    }

    # 1. PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
        health["checks"]["database"] = {"status": "up"}
    except Exception as e:
        health["status"] = "degraded"
        health["checks"]["database"] = {"status": "down", "error": str(e)}

    # 2. MinIO
    try:
        minio_service.client.bucket_exists(minio_service.bucket)
        health["checks"]["minio"] = {"status": "up"}
    except Exception as e:
        health["status"] = "degraded"
        health["checks"]["minio"] = {"status": "down", "error": str(e)}

    # 3. Qdrant
    try:
        client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        client.get_collection(settings.QDRANT_COLLECTION)
        health["checks"]["qdrant"] = {"status": "up"}
    except Exception as e:
        health["status"] = "degraded"
        health["checks"]["qdrant"] = {"status": "down", "error": str(e)}

    # 4. vLLM
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.LLM_API_URL}/models", timeout=5)
            if response.status_code == 200:
                health["checks"]["vllm"] = {"status": "up"}
            else:
                raise Exception(f"Status {response.status_code}")
    except Exception as e:
        health["status"] = "degraded"
        health["checks"]["vllm"] = {"status": "down", "error": str(e)}

    return health
```

#### 4. 환경 변수 설정

```python
# app/core/config.py
class Settings(BaseSettings):
    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    ENVIRONMENT: str = "production"  # dev, staging, production
```

```.env
LOG_LEVEL=INFO
ENVIRONMENT=production
```

---

## 🔄 배포 전략 (사용자 답변 기반)

### 사용자 답변 정리

- **layout.html 유지 불필요**: 새 버전에서 모든 기능이 작동하면 됨
- **롤백 계획 없음**: 실패 시 그냥 실패 (재배포)
- **데이터 마이그레이션 없음**: 실패 시 그냥 실패

### 단일 배포 전략

**목표:**
- 새 버전에서 모든 기능 작동
- 기존 시스템 제거
- 빠른 배포 (롤백 없이)

#### Docker Compose 구성

```yaml
# docker-compose.yml
version: '3.8'

services:
  admin-api:
    build: .
    container_name: admin-api
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/admin_db
      - LLM_API_URL=http://vllm:8000/v1
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
      - MINIO_ENDPOINT=minio:9000
    depends_on:
      - postgres
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: admin_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

#### 배포 스크립트

```bash
#!/bin/bash
# deploy.sh

set -e

echo "🚀 Deploying admin-api (New Version)"

# 1. 코드 최신화
echo "📥 Pulling latest code..."
git pull origin main

# 2. 의존성 설치
echo "📦 Installing dependencies..."
poetry install --no-dev

# 3. 데이터베이스 마이그레이션
echo "🗄️ Running database migrations..."
alembic upgrade head

# 4. 프론트엔드 빌드
echo "🔨 Building frontend..."
cd frontend
npm install
npm run build
cd ..

# 5. Docker 이미지 빌드
echo "🐳 Building Docker image..."
docker compose build

# 6. 기존 컨테이너 중지
echo "⏸️ Stopping old containers..."
docker compose down

# 7. 새 컨테이너 시작
echo "▶️ Starting new containers..."
docker compose up -d

# 8. 헬스 체크
echo "🏥 Running health check..."
sleep 10
curl -f http://localhost:8001/health || exit 1

echo "✅ Deployment successful!"
```

---

**마지막 업데이트**: 2025-10-22 (실제 코드 분석 + 사용자 답변 기반 상세 구현 가이드)
