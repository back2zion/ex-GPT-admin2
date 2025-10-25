# Vector Documents API Migration: Qdrant → EDB

## 개요

벡터 문서 관리 API를 Qdrant에서 EDB (EnterpriseDB)로 마이그레이션했습니다.

## 변경 사항

### 1. 데이터 소스 변경
- **이전**: Qdrant Vector Database (385개 문서)
- **이후**: EDB `wisenut.doc_bas_lst` 테이블 (1,985개 문서)

### 2. API 엔드포인트 (변경 없음)
- `GET /api/v1/admin/vector-documents/stats` - 통계 조회
- `GET /api/v1/admin/vector-documents` - 문서 목록 조회
- `GET /api/v1/admin/vector-documents/{document_id}` - 문서 상세 조회

### 3. 컬럼 매핑

| EDB 컬럼 | API 응답 필드 | 설명 |
|----------|--------------|------|
| `doc_id` | `id` | 문서 ID |
| `doc_rep_title_nm` / `doc_title_nm` | `title` | 문서 제목 |
| `doc_cat_cd` | `doctype` | 문서 카테고리 |
| `doc_det_level_n1_cd`, `n2_cd`, `n3_cd` | `file_path` | 문서 경로 (배열) |
| `use_yn` | `is_active` | 활성 여부 |
| `reg_dt` | `created_at` | 생성일 |
| `LENGTH(doc_txt)` | `token_count` | 문서 길이 |
| `doc_txt` | `content` | 문서 내용 (상세 조회 시) |

### 4. 통계 집계 변경
- **이전**: `doctype` 필드 기준 (D, 기타 등)
- **이후**: `doc_cat_cd` 필드 기준 (실제 카테고리 코드)

## 설정 요구사항

### EDB pg_hba.conf 설정

Docker 컨테이너에서 EDB에 접속하려면 `pg_hba.conf`에 Docker 네트워크를 추가해야 합니다:

```bash
# /var/lib/edb/as14/data/pg_hba.conf에 추가
host    all             all             172.31.0.0/16           md5
```

설정 적용:
```bash
sudo systemctl reload edb-as-14
```

### 환경 변수

`/home/aigen/admin-api/app/routers/admin/vector_documents.py`:
```python
EDB_HOST = "host.docker.internal"  # Docker 내부에서 호스트 접근
EDB_PORT = 5444
EDB_DATABASE = "AGENAI"
EDB_USER = "wisenut_dev"
EDB_PASSWORD = "express!12"
```

## 테스트 방법

### 1. 통계 조회
```bash
curl -s http://localhost:8010/api/v1/admin/vector-documents/stats | jq
```

예상 결과:
```json
{
  "total": 1985,
  "by_doctype": {
    "CAT001": 500,
    "CAT002": 300,
    ...
  }
}
```

### 2. 문서 목록 조회
```bash
curl -s "http://localhost:8010/api/v1/admin/vector-documents?skip=0&limit=10" | jq
```

### 3. 문서 검색
```bash
curl -s "http://localhost:8010/api/v1/admin/vector-documents?search=test" | jq
```

### 4. 문서 상세 조회
```bash
curl -s http://localhost:8010/api/v1/admin/vector-documents/1 | jq
```

## 프론트엔드 영향

프론트엔드는 **변경 없음**. API 응답 구조가 동일하게 유지됩니다.

- URL: https://ui.datastreams.co.kr:20443/admin/#/vector-data/documents
- 기존 React 컴포넌트 그대로 작동
- 통계 카드는 EDB의 실제 카테고리를 동적으로 표시

## 장점

1. **일관된 데이터 소스**: MinIO/Qdrant 대신 EDB 단일 소스 사용
2. **더 많은 문서**: 385개 → 1,985개
3. **내부망 지원**: 인터넷 없는 환경에서도 작동
4. **메타데이터 풍부**: 카테고리, 레벨, 상태 등 추가 정보
5. **SQL 쿼리 지원**: 복잡한 필터링과 검색 가능

## 주의사항

1. **pg_hba.conf 설정 필수**: Docker 네트워크 허용 필요
2. **포트 5444 사용**: 외부 포트 25444가 아닌 로컬 포트 5444
3. **use_yn = 'Y' 필터**: 활성 문서만 조회
4. **토큰 카운트**: 실제 토큰이 아닌 문자 길이 (LENGTH)

## 롤백 방법

Qdrant로 되돌리려면:

1. `vector_documents.py` 파일을 Git에서 복원
2. 서비스 재시작: `docker-compose restart admin-api`

```bash
cd /home/aigen/admin-api
git checkout HEAD -- app/routers/admin/vector_documents.py
docker-compose restart admin-api
```

## 작성일

2025-10-24

## 작성자

Claude Code (AI Assistant)
