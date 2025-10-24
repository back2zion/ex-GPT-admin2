#!/bin/bash

# 문서 생애주기 테스트 스크립트
# 용도: UI에서 문서 등록/삭제 후 실제로 3개 저장소(EDB, MinIO, Qdrant)에서 작동하는지 확인

set -e

DOCUMENT_ID=$1
CATEGORY_CODE=${2:-"99"}

if [ -z "$DOCUMENT_ID" ]; then
    echo "사용법: $0 <document_id> [category_code]"
    echo "예시: $0 2006 99"
    exit 1
fi

echo "=========================================="
echo "문서 생애주기 검증 테스트"
echo "문서 ID: $DOCUMENT_ID"
echo "카테고리: $CATEGORY_CODE"
echo "=========================================="
echo ""

# 1. EDB 확인
echo "📊 [1/3] EDB 확인 (메타데이터)"
echo "-----------------------------------"
docker exec admin-api-admin-api-1 bash -c "
python3 << 'PYTHON_EOF'
import asyncpg
import asyncio

async def check_edb():
    try:
        conn = await asyncpg.connect(
            host='host.docker.internal',
            port=5444,
            database='AGENAI',
            user='wisenut_dev',
            password='express!12'
        )

        await conn.execute('SET search_path TO wisenut')

        row = await conn.fetchrow('''
            SELECT doc_id, doc_title_nm, doc_cat_cd, use_yn, reg_dt
            FROM doc_bas_lst
            WHERE doc_id = \$1
        ''', ${DOCUMENT_ID})

        if row:
            print(f'✅ EDB에 문서 존재')
            print(f'   - ID: {row[\"doc_id\"]}')
            print(f'   - 제목: {row[\"doc_title_nm\"]}')
            print(f'   - 카테고리: {row[\"doc_cat_cd\"]}')
            print(f'   - 상태: {row[\"use_yn\"]}')
            print(f'   - 등록일: {row[\"reg_dt\"]}')
        else:
            print('❌ EDB에 문서 없음 (삭제되었거나 등록 안됨)')

        await conn.close()
    except Exception as e:
        print(f'❌ EDB 연결 실패: {e}')

asyncio.run(check_edb())
PYTHON_EOF
" 2>/dev/null
echo ""

# 2. MinIO 확인
echo "📦 [2/3] MinIO 확인 (문서 파일)"
echo "-----------------------------------"
docker exec admin-api-admin-api-1 bash -c "
python3 << 'PYTHON_EOF'
from minio import Minio

try:
    client = Minio(
        'host.docker.internal:10002',
        access_key='admin',
        secret_key='admin123',
        secure=False
    )

    # 카테고리 경로에서 파일 검색
    objects = list(client.list_objects('documents', prefix='${CATEGORY_CODE}/', recursive=True))

    if objects:
        print(f'✅ MinIO에 {len(objects)}개 파일 존재 (카테고리 ${CATEGORY_CODE}):')
        for obj in objects:
            size_kb = obj.size / 1024
            print(f'   - {obj.object_name} ({size_kb:.2f} KB)')
    else:
        print('❌ MinIO에 파일 없음 (카테고리 ${CATEGORY_CODE})')
except Exception as e:
    print(f'❌ MinIO 연결 실패: {e}')
PYTHON_EOF
" 2>/dev/null
echo ""

# 3. Qdrant 확인 (ex-gpt API를 통해)
echo "🔍 [3/3] Qdrant 확인 (벡터 임베딩)"
echo "-----------------------------------"
# ex-gpt API의 query 엔드포인트로 file_id 검색 시도
EXGPT_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "x-api-key: z3JE1M8huXmNux6y" \
    -H "Content-Type: application/json" \
    "http://localhost:8083/v1/query" \
    -d "{\"query\": \"test\", \"file_id\": \"${DOCUMENT_ID}\", \"limit\": 1}")

HTTP_CODE=$(echo "$EXGPT_RESPONSE" | tail -n1)
BODY=$(echo "$EXGPT_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    # 응답에서 results가 있으면 벡터 존재
    RESULT_COUNT=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('results', [])))" 2>/dev/null || echo "0")
    if [ "$RESULT_COUNT" -gt "0" ]; then
        echo "✅ Qdrant에 벡터 존재 (검색 결과: ${RESULT_COUNT}개)"
    else
        echo "❌ Qdrant에 벡터 없음 (file_id: ${DOCUMENT_ID} 검색 결과 없음)"
    fi
elif [ "$HTTP_CODE" = "404" ]; then
    echo "❌ Qdrant에 벡터 없음 (삭제되었거나 생성 안됨)"
else
    echo "⚠️  Qdrant 확인 불가 (ex-gpt API 응답: HTTP $HTTP_CODE)"
    echo "   참고: 벡터 존재 여부를 직접 확인할 수 없습니다"
fi
echo ""

# 4. 종합 판정
echo "=========================================="
echo "🎯 종합 판정"
echo "=========================================="
echo ""
echo "✅ = 데이터 존재 (정상)"
echo "❌ = 데이터 없음"
echo ""
echo "📌 문서 등록 후 예상 결과:"
echo "   EDB: ✅ | MinIO: ✅ | Qdrant: ✅"
echo ""
echo "📌 문서 삭제(hard delete) 후 예상 결과:"
echo "   EDB: ❌ | MinIO: ❌ | Qdrant: ❌"
echo ""
