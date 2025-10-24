# 문서 등록/삭제 실제 동작 확인 가이드

## 문제점
Dummy data 때문에 UI에서 문서 등록/삭제가 실제로 작동하는지 확인하기 어려움

## 해결책
3개 저장소(EDB, MinIO, Qdrant)를 직접 확인하는 검증 스크립트 사용

---

## 테스트 절차

### 1단계: 문서 업로드 전 상태 확인

UI에서 문서를 업로드하기 **전에**, 사용할 문서 ID를 예측하여 확인:

```bash
cd /home/aigen/admin-api

# 마지막 문서 ID 확인
docker exec admin-api-admin-api-1 bash -c "
python3 -c \"
import asyncpg, asyncio
async def get_max_id():
    conn = await asyncpg.connect(
        host='host.docker.internal', port=5444,
        database='AGENAI', user='wisenut_dev', password='express!12'
    )
    result = await conn.fetchval('SET search_path TO wisenut; SELECT COALESCE(MAX(doc_id), 0) FROM doc_bas_lst')
    print(f'현재 마지막 문서 ID: {result}')
    print(f'다음 문서 ID 예상: {result + 1}')
    await conn.close()
asyncio.run(get_max_id())
\"
"
```

출력 예시:
```
현재 마지막 문서 ID: 2005
다음 문서 ID 예상: 2006
```

### 2단계: UI에서 문서 업로드

1. 브라우저에서 https://ui.datastreams.co.kr:20443/admin/#/vector-data/documents 접속
2. "문서등록" 버튼 클릭
3. 카테고리 선택 (예: 99 - 테스트)
4. 테스트 파일 업로드 (예: test_document.pdf)
5. "저장" 버튼 클릭
6. 성공 메시지 확인

### 3단계: 업로드 직후 검증

```bash
./test_document_lifecycle.sh 2006 99
```

**예상 결과 (성공적인 업로드):**
```
📊 [1/3] EDB 확인 (메타데이터)
-----------------------------------
✅ EDB에 문서 존재
   - ID: 2006
   - 제목: test_document.pdf
   - 카테고리: 99
   - 상태: Y
   - 등록일: 2025-10-24 ...

📦 [2/3] MinIO 확인 (문서 파일)
-----------------------------------
✅ MinIO에 1개 파일 존재 (카테고리 99):
   - 99/기타/00/00/test_document.pdf (245.67 KB)

🔍 [3/3] Qdrant 확인 (벡터 임베딩)
-----------------------------------
✅ Qdrant에 벡터 존재
{
  "file_id": "2006",
  "filename": "test_document.pdf",
  "status": "indexed"
}
```

**실패한 경우 (문제 있음):**
- EDB만 ✅, 나머지 ❌ → MinIO 업로드 실패 또는 벡터 생성 실패
- EDB, MinIO만 ✅, Qdrant ❌ → ex-gpt API 연동 실패 (RAG 검색 불가)
- 모두 ❌ → 업로드 자체 실패

### 4단계: UI에서 문서 삭제

1. 문서 목록에서 방금 업로드한 문서 체크박스 선택
2. "삭제" 버튼 클릭
3. 첫 번째 확인 대화상자에서 "확인" 클릭
4. 두 번째 확인 대화상자에서 "확인" 클릭 (되돌릴 수 없음 경고)
5. 성공 메시지 확인

### 5단계: 삭제 직후 검증

```bash
./test_document_lifecycle.sh 2006 99
```

**예상 결과 (성공적인 삭제):**
```
📊 [1/3] EDB 확인 (메타데이터)
-----------------------------------
❌ EDB에 문서 없음 (삭제되었거나 등록 안됨)

📦 [2/3] MinIO 확인 (문서 파일)
-----------------------------------
❌ MinIO에 파일 없음 (카테고리 99)

🔍 [3/3] Qdrant 확인 (벡터 임베딩)
-----------------------------------
❌ Qdrant에 벡터 없음 (삭제되었거나 생성 안됨)

🎯 종합 판정
==========================================
📌 문서 삭제(hard delete) 후 예상 결과:
   EDB: ❌ | MinIO: ❌ | Qdrant: ❌
```

**실패한 경우 (문제 있음):**
- EDB만 ❌, 나머지 ✅ → EDB만 삭제됨 (MinIO, Qdrant에 쓰레기 데이터 남음)
- 일부만 ❌ → 부분 삭제 실패 (완전한 삭제가 아님)

---

## 빠른 검증 명령어

### 현재 등록된 문서 수 확인
```bash
docker exec admin-api-admin-api-1 bash -c "
python3 -c \"
import asyncpg, asyncio
async def count_docs():
    conn = await asyncpg.connect(
        host='host.docker.internal', port=5444,
        database='AGENAI', user='wisenut_dev', password='express!12'
    )
    active = await conn.fetchval('SET search_path TO wisenut; SELECT COUNT(*) FROM doc_bas_lst WHERE use_yn = \\\"Y\\\"')
    deleted = await conn.fetchval('SET search_path TO wisenut; SELECT COUNT(*) FROM doc_bas_lst WHERE use_yn = \\\"N\\\"')
    total = await conn.fetchval('SET search_path TO wisenut; SELECT COUNT(*) FROM doc_bas_lst')
    print(f'활성 문서: {active}')
    print(f'삭제 문서 (soft): {deleted}')
    print(f'전체: {total}')
    await conn.close()
asyncio.run(count_docs())
\"
"
```

### MinIO에 저장된 파일 수 확인
```bash
docker exec admin-api-admin-api-1 bash -c "
python3 -c \"
from minio import Minio
client = Minio('host.docker.internal:10002', access_key='admin', secret_key='admin123', secure=False)
objects = list(client.list_objects('documents', recursive=True))
print(f'MinIO 파일 수: {len(objects)}')
for obj in objects[:5]:
    print(f'  - {obj.object_name}')
if len(objects) > 5:
    print(f'  ... 외 {len(objects) - 5}개')
\"
"
```

### Qdrant 벡터 수 확인
```bash
curl -s -H "x-api-key: z3JE1M8huXmNux6y" \
  "http://localhost:8083/v1/stats" | python3 -m json.tool
```

---

## 문제 해결

### 문제 1: EDB에는 있는데 Qdrant에 없음
**증상:** RAG 검색이 안됨
**원인:** 벡터 임베딩 생성 실패
**해결:**
```bash
# 백엔드 로그 확인
docker logs admin-api-admin-api-1 --tail=100 | grep -i "vector\|embedding\|ex-gpt"
```

### 문제 2: MinIO에만 파일이 남아있음
**증상:** 삭제했는데 MinIO에 파일 존재
**원인:** hard_delete 파라미터가 전달 안됨
**해결:**
```bash
# 수동 삭제
./test_document_lifecycle.sh <doc_id> <category>
# MinIO 파일 수동 정리
docker exec admin-api-admin-api-1 bash -c "
python3 -c \"
from minio import Minio
client = Minio('host.docker.internal:10002', access_key='admin', secret_key='admin123', secure=False)
objects = client.list_objects('documents', prefix='<category>/', recursive=True)
for obj in objects:
    client.remove_object('documents', obj.object_name)
    print(f'Deleted: {obj.object_name}')
\"
"
```

### 문제 3: 업로드는 되는데 목록에 안 나타남
**증상:** 업로드 성공했는데 UI에 안 보임
**원인:** use_yn='N' 또는 카테고리 필터 문제
**해결:**
```bash
# 최근 등록 문서 확인 (use_yn 무관)
docker exec admin-api-admin-api-1 bash -c "
python3 -c \"
import asyncpg, asyncio
async def recent_docs():
    conn = await asyncpg.connect(
        host='host.docker.internal', port=5444,
        database='AGENAI', user='wisenut_dev', password='express!12'
    )
    rows = await conn.fetch('SET search_path TO wisenut; SELECT doc_id, doc_title_nm, doc_cat_cd, use_yn FROM doc_bas_lst ORDER BY reg_dt DESC LIMIT 5')
    for r in rows:
        print(f'{r[\\\"doc_id\\\"]}: {r[\\\"doc_title_nm\\\"]} (카테고리: {r[\\\"doc_cat_cd\\\"]}, 상태: {r[\\\"use_yn\\\"]})')
    await conn.close()
asyncio.run(recent_docs())
\"
"
```

---

## 체크리스트

### ✅ 업로드 성공 기준
- [ ] EDB에 메타데이터 존재 (use_yn='Y')
- [ ] MinIO에 실제 파일 존재
- [ ] Qdrant에 벡터 임베딩 존재
- [ ] UI 목록에 문서 표시됨

### ✅ 삭제 성공 기준
- [ ] EDB에서 완전히 제거됨 (NOT soft delete)
- [ ] MinIO에서 파일 완전히 제거됨
- [ ] Qdrant에서 벡터 완전히 제거됨
- [ ] UI 목록에서 사라짐

---

## 주의사항

1. **카테고리 코드 확인**: 테스트 시 올바른 카테고리 코드 사용 (99=테스트, 10=기관정보 등)
2. **문서 ID 범위**: 실제 운영 문서를 삭제하지 않도록 테스트 문서 ID 사용
3. **동시 작업 방지**: 테스트 중에는 다른 사용자가 문서 등록/삭제하지 않도록 조율
4. **백엔드 로그**: 문제 발생 시 반드시 백엔드 로그 확인

```bash
# 실시간 로그 모니터링
docker logs -f admin-api-admin-api-1
```
