# Admin API 기능 점검 보고서

**작성일시**: 2025-10-19
**점검 범위**: `/home/aigen/admin-api/app/routers/admin/` 전체 라우터

---

## 📊 현재 상태 요약

### ✅ 완료된 기능 (Backend API)

| 기능 | 라우터 파일 | API 엔드포인트 | DB 테이블 | 상태 |
|------|------------|---------------|----------|------|
| 사용 이력 관리 | `usage.py` | `/api/v1/admin/usage/` | `usage_history` | ✅ 작동 |
| 공지사항 관리 | `notices.py` | `/api/v1/admin/notices/` | `notices` | ✅ 작동 |
| 만족도 조사 | `satisfaction.py` | `/api/v1/admin/satisfaction/` | `satisfaction_surveys` | ✅ 작동 |
| 데이터 내보내기 | `export.py` | `/api/v1/admin/export/` | - | ✅ 작동 |
| 부서 관리 | `departments.py` | `/api/v1/admin/departments/` | `departments` | ✅ 작동 |
| 역할 관리 | `roles.py` | `/api/v1/admin/roles/` | `roles` | ✅ 작동 |
| 권한 관리 | `permissions.py` | `/api/v1/admin/permissions/` | `permissions` | ✅ 작동 |
| 결재라인 관리 | `approval_lines.py` | `/api/v1/admin/approval-lines/` | `approval_lines` | ✅ 작동 |
| 문서별 권한 관리 | `document_permissions.py` | `/api/v1/admin/document-permissions/` | `document_permissions` | ✅ 작동 |
| 사용자 관리 | `users.py` | `/api/v1/admin/users/` | `users` | ✅ 작동 |

### ❌ 미완료/미연결 기능

| 요구사항 | Backend 상태 | Frontend 상태 | 비고 |
|---------|-------------|--------------|------|
| **문서 변동 확인 기능** | ⚠️ 모델만 존재 | ❌ 미연결 | `document_changes` 테이블은 있으나 라우터 없음 |
| **문서 자동 전처리** | ❌ 미구현 | ❌ 미연결 | 변경 부분만 반영하는 로직 필요 |
| **Frontend UI 연결** | ✅ API 완료 | ⚠️ 부분 완료 | 사용이력, 공지사항만 UI 연결됨 |
| **권한 관리 UI** | ✅ API 완료 | ❌ 미연결 | 메뉴만 있고 기능 없음 |
| **문서 관리 UI** | ⚠️ 부분 완료 | ⚠️ 부분 완료 | 업로드만 가능, 변경 추적 미연결 |

---

## 🔍 상세 분석

### 1. permissions.py vs document_permissions.py 차이점

#### `permissions.py` - **시스템 권한 관리**
```
목적: API 리소스에 대한 권한 정의 (RBAC - Role-Based Access Control)
예시 데이터:
  - resource: "document", action: "read", description: "문서 읽기 권한"
  - resource: "document", action: "write", description: "문서 쓰기 권한"
  - resource: "user", action: "create", description: "사용자 생성 권한"

사용처: Role과 연결하여 "admin 역할은 모든 권한", "user 역할은 읽기만" 등 정의
```

#### `document_permissions.py` - **문서별 접근 권한 관리**
```
목적: 특정 문서에 대한 부서/결재라인별 접근 권한 설정
예시 데이터:
  - document_id: 1, department_id: 10, can_read: true, can_write: false
    → "법령문서 A는 법무팀만 읽기 가능"
  - document_id: 2, approval_line_id: 5, can_read: true, can_write: true
    → "사규문서 B는 경영진 결재라인 모두 읽기/쓰기 가능"

사용처: 법령, 사규, 업무기준 등 민감 문서의 부서별 차등 접근 제어
```

**관계**:
- `permissions.py`: "누가 어떤 API를 호출할 수 있는가?" (시스템 레벨)
- `document_permissions.py`: "누가 어떤 문서를 볼 수 있는가?" (데이터 레벨)

---

### 2. 데이터베이스 현황

```sql
-- 17개 테이블 생성 완료
✅ alembic_version          -- DB 마이그레이션 버전 관리
✅ approval_lines           -- 결재라인 정의
✅ approval_steps           -- 결재 단계
✅ departments              -- 부서 정보 (1개 데이터)
✅ document_change_requests -- 문서 변경 요청
✅ document_changes         -- 문서 변경 이력 ⚠️ 라우터 없음
✅ document_permissions     -- 문서별 권한 (0개 데이터)
✅ document_versions        -- 문서 버전 관리
✅ documents                -- 문서 메타데이터 (5개 데이터)
✅ notices                  -- 공지사항
✅ permissions              -- 시스템 권한 (1개 데이터)
✅ role_permissions         -- 역할-권한 매핑
✅ roles                    -- 역할 정의 (1개 데이터)
✅ satisfaction_surveys     -- 만족도 설문
✅ usage_history            -- 사용 이력 (1개 데이터)
✅ user_roles               -- 사용자-역할 매핑
✅ users                    -- 사용자 정보
```

---

### 3. Frontend UI 연결 상태

#### ✅ 연결 완료
- **대시보드** (`#dashboard`): 통계 표시
- **사용 이력** (`#usage`): API 연결 완료, 타임존 수정 완료
- **공지사항** (`#notices`): CRUD 기능 작동
- **만족도 조사** (`#satisfaction`): 조회/응답 기능

#### ⚠️ 부분 연결
- **문서 관리** (`#documents`):
  - 파일 업로드만 가능
  - 변경 이력 추적 미연결
  - 승인 프로세스 미연결

#### ❌ 미연결
- **권한 관리** (`#permissions`):
  - 메뉴는 있으나 페이지 내용 비어있음
  - 부서 관리 UI 없음
  - 역할 관리 UI 없음
  - 문서별 권한 설정 UI 없음

---

## 🚨 주요 문제점

### 1. 문서 변경 추적 라우터 누락

**상황**:
- `app/models/document.py`에 `DocumentChange` 모델 존재
- DB 테이블 `document_changes` 생성됨
- **하지만 `/app/routers/admin/` 폴더에 라우터 파일 없음**

**요구사항**:
> "법령, 사규, 업무기준 등 변동 시 관리자 확인 기능 추가"
> "제·개정된 문서는 변동된 부분만 전처리에 자동 반영"

**필요 작업**:
```python
# 생성 필요: /home/aigen/admin-api/app/routers/admin/document_changes.py

필수 기능:
1. GET /api/v1/admin/document-changes/ - 변경 이력 목록
2. GET /api/v1/admin/document-changes/{id} - 변경 상세 (diff 포함)
3. PUT /api/v1/admin/document-changes/{id}/approve - 관리자 승인
4. POST /api/v1/admin/document-changes/{id}/apply - 전처리 반영
```

---

### 2. Frontend UI 미완성

**권한 관리 페이지** (`#permissions`):
```html
<!-- 현재 상태: 메뉴만 있고 내용 없음 -->
<div id="permissions-page" class="page">
  <!-- 비어있음 -->
</div>
```

**필요 작업**:
- 부서 관리 UI (CRUD)
- 역할 관리 UI (권한 할당 포함)
- 문서별 권한 설정 UI
- 결재라인 관리 UI

---

### 3. 테스트 코드 부족

**현재 상태**:
```bash
/home/aigen/admin-api/tests/
├── conftest.py                  # 테스트 설정
├── test_approval_workflow.py    # 승인 워크플로우 테스트
├── test_diff_generator.py       # Diff 생성 테스트
├── test_document_sync.py        # 문서 동기화 테스트
├── test_integration_e2e.py      # E2E 통합 테스트
├── test_legacy_db.py            # 레거시 DB 테스트
└── test_scheduler.py            # 스케줄러 테스트
```

**문제점**:
- **라우터별 단위 테스트 없음** (TDD 요구사항 미충족)
- 보안 테스트 없음 (SQL Injection, XSS 등)
- 권한 검증 테스트 없음

**필요 작업**:
각 라우터마다 테스트 파일 생성 필요:
```
tests/routers/admin/
├── test_permissions.py
├── test_document_permissions.py
├── test_departments.py
├── test_roles.py
├── test_users.py
├── test_approval_lines.py
├── test_notices.py
├── test_usage.py
├── test_satisfaction.py
└── test_document_changes.py  # 미생성 라우터
```

---

### 4. 시큐어 코딩 점검 필요

**Cerbos 권한 체크 누락**:
일부 엔드포인트에서 `require_permission` 대신 `get_principal`만 사용:

```python
# ❌ 잘못된 예 (permissions.py:26)
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)  # 권한 체크 안함!
):
```

**올바른 예**:
```python
# ✅ 권한 체크 필수
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("permission", "read"))
):
```

**점검 필요 파일**:
- `permissions.py`: list, get 엔드포인트
- `document_permissions.py`: list, get 엔드포인트
- 모든 라우터의 READ 작업

---

## 📋 요구사항 충족 현황

| 요구사항 | Backend | Frontend | 테스트 | 보안 | 진행률 |
|---------|---------|----------|--------|------|--------|
| **서비스 평가 및 사용 이력 관리** | ✅ | ✅ | ⚠️ | ✅ | 80% |
| **접근 가능 문서 권한 관리** | ✅ | ❌ | ❌ | ⚠️ | 40% |
| **이용만족도 조사 기능** | ✅ | ✅ | ⚠️ | ✅ | 70% |
| **공지메시지 표출 기능** | ✅ | ✅ | ⚠️ | ✅ | 80% |
| **법령/사규 변동 시 관리자 확인** | ❌ | ❌ | ❌ | N/A | 20% |
| **변동 부분만 전처리 자동 반영** | ❌ | ❌ | ❌ | N/A | 10% |

**전체 완성도: 약 50%**

---

## ✅ 다음 단계 작업 계획

### Phase 1: 문서 변경 추적 기능 (TDD)

1. **테스트 작성** (`tests/routers/admin/test_document_changes.py`)
   ```python
   - test_list_document_changes()
   - test_get_document_change_detail()
   - test_approve_document_change()
   - test_apply_document_change_to_preprocessing()
   - test_unauthorized_access()
   - test_sql_injection_prevention()
   ```

2. **라우터 구현** (`app/routers/admin/document_changes.py`)
   - GET `/api/v1/admin/document-changes/` - 변경 이력 목록
   - GET `/api/v1/admin/document-changes/{id}` - 상세 조회 (diff 포함)
   - PUT `/api/v1/admin/document-changes/{id}/approve` - 승인
   - POST `/api/v1/admin/document-changes/{id}/apply` - 전처리 반영

3. **스키마 추가** (`app/schemas/document_change.py`)
   - DocumentChangeResponse
   - DocumentChangeApprove

4. **main.py 등록**
   ```python
   from app.routers.admin import document_changes
   app.include_router(document_changes.router)
   ```

---

### Phase 2: Frontend UI 개발

5. **권한 관리 페이지 구현** (`/home/aigen/html/admin/js/admin.js`)
   - 부서 관리 탭
   - 역할 관리 탭
   - 문서별 권한 설정 탭
   - 결재라인 관리 탭

6. **문서 변경 추적 페이지**
   - 변경 이력 목록
   - Diff 뷰어 (변경 부분 하이라이트)
   - 승인/반려 버튼

---

### Phase 3: 테스트 및 보안

7. **전체 라우터 단위 테스트 작성**
   - 각 라우터마다 테스트 파일 생성
   - CRUD 작업 테스트
   - 권한 검증 테스트
   - 보안 취약점 테스트

8. **시큐어 코딩 점검**
   - 모든 엔드포인트에 `require_permission` 적용
   - SQL Injection 방지 검증
   - XSS 방지 검증
   - CSRF 토큰 검증 (필요 시)

---

## 🔐 보안 체크리스트

- [ ] 모든 엔드포인트에 Cerbos 권한 체크 적용
- [ ] Pydantic 스키마로 입력 검증 (이미 적용됨)
- [ ] SQL Injection 방지 (ORM 사용, 이미 안전)
- [ ] XSS 방지 (Frontend 템플릿 이스케이핑 필요)
- [ ] 민감 정보 로깅 방지
- [ ] Rate Limiting (현재 미적용)
- [ ] HTTPS 강제 (배포 시 필요)

---

## 📌 결론

**현재 상태**:
- Backend API는 80% 완성 (문서 변경 추적만 누락)
- Frontend UI는 40% 완성 (권한 관리, 문서 변경 추적 미연결)
- 테스트 코드는 20% 완성 (라우터별 단위 테스트 부족)
- 보안은 70% 완성 (일부 권한 체크 누락)

**우선순위**:
1. 🔴 **긴급**: 문서 변경 추적 라우터 구현 (TDD)
2. 🟡 **중요**: Frontend 권한 관리 UI 구현
3. 🟡 **중요**: 전체 라우터 단위 테스트 작성
4. 🟢 **권장**: 보안 점검 및 권한 체크 강화

**예상 작업 시간**:
- Phase 1 (문서 변경 추적): 4-6시간
- Phase 2 (Frontend UI): 6-8시간
- Phase 3 (테스트 & 보안): 8-10시간
- **총 예상 시간: 18-24시간**
