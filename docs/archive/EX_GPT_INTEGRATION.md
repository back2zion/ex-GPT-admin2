# ex-GPT API와 관리도구 연동 가이드

## 개요
ex-gpt API가 사용 이력을 admin-api로 전송하여 실시간 통계를 수집합니다.

## 사용 이력 로깅 API

### 엔드포인트
```
POST http://admin-api:8001/api/v1/usage/log
```

### 요청 형식
```json
{
  "user_id": "user123",
  "session_id": "session_abc",
  "question": "한국도로공사의 안전관리 규정은?",
  "answer": "안전관리 규정은...",
  "response_time": 1523.5,
  "model_name": "Qwen3-32B",
  "referenced_documents": [
    {
      "doc_id": "doc_001",
      "title": "안전관리 규정",
      "relevance": 0.95
    }
  ],
  "usage_metadata": {
    "tokens_input": 45,
    "tokens_output": 320,
    "temperature": 0.7
  }
}
```

### 응답 형식
```json
{
  "id": 12345,
  "message": "사용 이력이 기록되었습니다",
  "created_at": "2025-10-20T12:34:56Z"
}
```

## Docker 네트워크 연결

ex-gpt와 admin-api가 같은 네트워크에 있어야 합니다:

```yaml
# ex-gpt/docker-compose-api-server.yaml
services:
  api:
    image: registry.cloud.neoali.com/datastreams/ex-gpt/ai-api:0.5.14-prod
    environment:
      - ADMIN_API_URL=http://admin-api:8001  # 추가
    networks:
      - default
      - admin_network  # admin-api 네트워크 추가

networks:
  admin_network:
    external: true
    name: admin-api_default
```

## Python 코드 예시 (ex-gpt API에 추가)

```python
import httpx
from datetime import datetime

async def log_usage_to_admin(
    user_id: str,
    question: str,
    answer: str,
    response_time: float,
    model_name: str,
    referenced_docs: list = None
):
    """관리도구에 사용 이력 전송"""
    admin_api_url = os.getenv("ADMIN_API_URL", "http://admin-api:8001")

    payload = {
        "user_id": user_id,
        "question": question,
        "answer": answer,
        "response_time": response_time,
        "model_name": model_name,
        "referenced_documents": referenced_docs,
        "usage_metadata": {
            "timestamp": datetime.utcnow().isoformat()
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{admin_api_url}/api/v1/usage/log",
                json=payload,
                timeout=5.0
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        # 로깅 실패해도 사용자 요청은 성공 처리
        print(f"Failed to log usage: {e}")
        return None
```

## 통합 체크리스트

- [ ] ex-gpt API에 ADMIN_API_URL 환경변수 추가
- [ ] Docker 네트워크 연결 (admin-api_default)
- [ ] ex-gpt API 코드에 log_usage_to_admin() 함수 추가
- [ ] 각 질문/답변 후 log_usage_to_admin() 호출
- [ ] 테스트: http://localhost:8010/admin/stats/exgpt 에서 실시간 데이터 확인

## 모델명 매핑

실제 사용하는 모델명:
- **Qwen3-32B**: 메인 Chat 모델 (/models/Qwen3-32B)
- **Qwen3-Embedding-0.6B**: Embedding 모델
- **bge-reranker-v2-m3**: Rerank 모델

## 문의

- 관리도구 API 문서: http://localhost:8010/docs
- 통계 대시보드: http://localhost:8010/admin/stats/exgpt
