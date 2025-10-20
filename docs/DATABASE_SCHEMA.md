# 데이터베이스 스키마 문서

## 개요

AI Streams 관리 시스템의 데이터베이스 스키마입니다. PostgreSQL을 사용하며, SQLAlchemy ORM을 통해 관리됩니다.

## 테이블 목록

### 1. 사용자 관리

#### users
사용자 정보를 저장하는 테이블

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | Integer | 기본키 |
| username | String(50) | 사용자명 (고유) |
| email | String(255) | 이메일 (고유) |
| hashed_password | String(255) | 해시된 비밀번호 |
| full_name | String(100) | 전체 이름 |
| is_active | Boolean | 활성화 상태 |
| is_superuser | Boolean | 슈퍼유저 여부 |
| department_id | Integer | 부서 ID (FK) |
| created_at | DateTime | 생성 시각 |
| updated_at | DateTime | 수정 시각 |

#### roles
역할 정보

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | Integer | 기본키 |
| name | String(50) | 역할명 (고유) |
| description | String(255) | 설명 |
| is_active | Boolean | 활성화 상태 |
| created_at | DateTime | 생성 시각 |
| updated_at | DateTime | 수정 시각 |

#### permissions
권한 정보

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | Integer | 기본키 |
| resource | String(100) | 리소스명 |
| action | String(50) | 액션명 |
| description | String(255) | 설명 |
| created_at | DateTime | 생성 시각 |
| updated_at | DateTime | 수정 시각 |

#### departments
부서 정보

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | Integer | 기본키 |
| name | String(100) | 부서명 (고유) |
| code | String(50) | 부서 코드 (고유) |
| description | String(255) | 설명 |
| parent_id | Integer | 상위 부서 ID (FK, 자기참조) |
| created_at | DateTime | 생성 시각 |
| updated_at | DateTime | 수정 시각 |

### 2. 문서 관리

#### documents
문서 정보

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | Integer | 기본키 |
| document_id | String(100) | 문서 ID (고유) |
| title | String(500) | 제목 |
| document_type | Enum | 문서 타입 (law/regulation/standard/manual/other) |
| status | Enum | 상태 (active/pending/archived/deleted) |
| legacy_id | String(100) | 레거시 시스템 ID |
| legacy_updated_at | String(50) | 레거시 시스템 업데이트 시각 |
| content | Text | 내용 |
| summary | Text | 요약 |
| metadata | JSON | 메타데이터 |
| current_version | String(20) | 현재 버전 |
| created_at | DateTime | 생성 시각 |
| updated_at | DateTime | 수정 시각 |

#### document_versions
문서 버전 이력

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | Integer | 기본키 |
| document_id | Integer | 문서 ID (FK) |
| version | String(20) | 버전 |
| content | Text | 내용 |
| change_summary | Text | 변경 요약 |
| changed_by | String(100) | 변경자 |
| created_at | DateTime | 생성 시각 |
| updated_at | DateTime | 수정 시각 |

#### document_changes
문서 변경 이력

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | Integer | 기본키 |
| document_id | Integer | 문서 ID (FK) |
| change_type | String(50) | 변경 타입 |
| old_content | Text | 이전 내용 |
| new_content | Text | 새 내용 |
| diff | Text | 차이점 |
| approved | Boolean | 승인 여부 |
| approved_by | String(100) | 승인자 |
| approved_at | String(50) | 승인 시각 |
| created_at | DateTime | 생성 시각 |
| updated_at | DateTime | 수정 시각 |

### 3. 사용 이력

#### usage_history
사용 이력

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | Integer | 기본키 |
| user_id | Integer | 사용자 ID (FK) |
| session_id | String(100) | 세션 ID |
| question | Text | 질문 |
| answer | Text | 답변 |
| response_time | Float | 응답 시간 (초) |
| referenced_documents | JSON | 참조 문서 목록 |
| model_name | String(100) | 모델명 |
| metadata | JSON | 메타데이터 |
| ip_address | String(45) | IP 주소 |
| created_at | DateTime | 생성 시각 |
| updated_at | DateTime | 수정 시각 |

### 4. 권한 관리

#### approval_lines
결재라인

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | Integer | 기본키 |
| name | String(100) | 결재라인명 |
| description | String(255) | 설명 |
| departments | JSON | 부서 ID 목록 |
| approvers | JSON | 승인자 정보 |
| created_at | DateTime | 생성 시각 |
| updated_at | DateTime | 수정 시각 |

#### document_permissions
문서 접근 권한

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | Integer | 기본키 |
| document_id | Integer | 문서 ID (FK) |
| department_id | Integer | 부서 ID (FK, nullable) |
| approval_line_id | Integer | 결재라인 ID (FK, nullable) |
| can_read | Boolean | 읽기 권한 |
| can_write | Boolean | 쓰기 권한 |
| can_delete | Boolean | 삭제 권한 |
| created_at | DateTime | 생성 시각 |
| updated_at | DateTime | 수정 시각 |

### 5. 공지사항

#### notices
공지사항

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | Integer | 기본키 |
| title | String(255) | 제목 |
| content | Text | 내용 |
| priority | Enum | 우선순위 (low/normal/high/urgent) |
| is_active | Boolean | 활성화 상태 |
| target_users | JSON | 대상 사용자 목록 |
| target_departments | JSON | 대상 부서 목록 |
| start_date | String(50) | 시작일 |
| end_date | String(50) | 종료일 |
| created_by | String(100) | 작성자 |
| view_count | Integer | 조회수 |
| created_at | DateTime | 생성 시각 |
| updated_at | DateTime | 수정 시각 |

### 6. 만족도 조사

#### satisfaction_surveys
만족도 조사

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | Integer | 기본키 |
| user_id | Integer | 사용자 ID (FK, nullable) |
| rating | Integer | 평점 (1-5) |
| feedback | Text | 피드백 |
| category | String(50) | 카테고리 |
| related_question_id | Integer | 관련 질문 ID (FK, nullable) |
| metadata | JSON | 메타데이터 |
| ip_address | String(45) | IP 주소 |
| created_at | DateTime | 생성 시각 |
| updated_at | DateTime | 수정 시각 |

## 관계도

```
users ──┬── usage_history
        ├── satisfaction_surveys
        └── departments

documents ──┬── document_versions
            ├── document_changes
            └── document_permissions ──┬── departments
                                       └── approval_lines

roles ──┬── user_roles (M:N) ── users
        └── role_permissions (M:N) ── permissions
```

## 인덱스

- users: username, email, department_id
- documents: document_id, legacy_id
- usage_history: user_id, session_id
- document_permissions: document_id, department_id, approval_line_id

## 마이그레이션

Alembic을 사용하여 데이터베이스 마이그레이션을 관리합니다.

```bash
# 마이그레이션 생성
poetry run alembic revision --autogenerate -m "description"

# 마이그레이션 적용
poetry run alembic upgrade head

# 마이그레이션 롤백
poetry run alembic downgrade -1
```
