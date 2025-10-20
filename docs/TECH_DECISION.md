# 기술 스택 결정 문서 (ADR - Architecture Decision Record)

**날짜**: 2025-10-18
**상태**: 제안됨 (Proposed)
**결정자**: 개발팀

---

## 컨텍스트 및 문제 진술

과업지시서의 관리도구 요구사항을 **6일 내에** 구현해야 합니다.

**핵심 도전 과제**:
1. ⏰ **시간 압박**: 오늘 MVP 완성 목표 (5.5시간)
2. 🔄 **반복적인 CRUD**: 공지사항, 이력 조회, 권한 관리 등
3. 📊 **데이터 내보내기**: 엑셀, CSV 필수
4. 🔒 **복잡한 권한**: Cerbos를 활용한 세밀한 권한 제어
5. 🔗 **레거시 연동**: 비동기 처리 필수
6. 🏗️ **기존 인프라 통합**: ds-api와 동일한 FastAPI 스택 사용

**현재 상황**:
- FastAPI 기반 프로젝트 시작 (/home/aigen/admin-api/)
- 기존 인프라: ds-api (FastAPI + Poetry), ex-gpt (Docker 서비스)
- **Flask 없음** - 순수 FastAPI 환경
- HTML 어드민 프론트엔드 이미 존재 (/home/aigen/html/admin/)
- PostgreSQL, Redis, Cerbos 이미 docker-compose 구성됨

---

## 고려한 대안

### 옵션 1: Flask-Admin + FastAPI 하이브리드

**장점**:
- ✅ 자동 CRUD UI 생성
- ✅ 엑셀 내보내기 기본 제공
- ✅ 빠른 프로토타이핑

**단점**:
- ❌ **기존 인프라와 불일치**: Flask가 현재 스택에 없음
- ❌ 두 개의 웹 프레임워크 관리 (복잡도 증가)
- ❌ 의존성 추가 (flask, flask-admin, flask-sqlalchemy)
- ❌ 동기 처리 제약 (Flask-Admin은 비동기 지원 제한적)

**결론**: ❌ **배제** - 기존 순수 FastAPI 환경과 맞지 않음

---

### 옵션 2: 순수 FastAPI ⭐ **채택**

**아키텍처**:
```
┌─────────────────────────────────────────────┐
│  FastAPI (포트 8010)                         │
│                                              │
│  ┌────────────────────────────────────┐    │
│  │  Admin CRUD API (/api/v1/admin/)   │    │
│  │  - 공지사항 CRUD                    │    │
│  │  - 사용 이력 조회                   │    │
│  │  - 만족도 조사 조회                 │    │
│  │  - 엑셀 내보내기 엔드포인트         │    │
│  │  - Cerbos 권한 미들웨어             │    │
│  └────────────────────────────────────┘    │
│                                              │
│  ┌────────────────────────────────────┐    │
│  │  User API (/api/v1/)               │    │
│  │  - layout.html 연동 API             │    │
│  │  - 문서 검색                        │    │
│  └────────────────────────────────────┘    │
│                                              │
│  ┌────────────────────────────────────┐    │
│  │  Background Tasks                  │    │
│  │  - 레거시 DB 동기화 (비동기)        │    │
│  │  - 스케줄러 (APScheduler)           │    │
│  └────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
                    ↓
              PostgreSQL + Redis + Cerbos
                    ↑
┌─────────────────────────────────────────────┐
│  정적 파일 서빙                              │
│  - /admin → /home/aigen/html/admin/         │
│  - HTML/JS 프론트엔드 (이미 존재)           │
└─────────────────────────────────────────────┘
```

**장점**:
- ✅ **기존 인프라와 완벽히 통합** (ds-api와 동일한 스택)
- ✅ 단일 웹 프레임워크 (관리 단순)
- ✅ 비동기 처리 (레거시 DB 동기화에 필수)
- ✅ 자동 API 문서 (Swagger/ReDoc)
- ✅ Pydantic 타입 검증
- ✅ 기존 HTML 프론트엔드 재활용 가능
- ✅ Cerbos 미들웨어 통합 용이
- ✅ 의존성 최소화 (새로운 프레임워크 불필요)

**단점**:
- ⚠️ CRUD 엔드포인트 직접 구현 필요 (하지만 FastAPI는 간결함)
- ⚠️ 엑셀 내보내기 직접 구현 (openpyxl/pandas 사용)
- ⚠️ 프론트엔드 일부 수정 필요 (API 연동)

**예상 개발 시간**: **45.5시간** (6일)
- MVP (오늘): 5.5시간
- Phase 1: 10시간
- Phase 2: 30시간

**구현 패턴** (FastAPI는 매우 간결):
```python
# 공지사항 CRUD 엔드포인트 예시
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, check_permission

router = APIRouter(prefix="/api/v1/admin/notices", tags=["admin"])

@router.get("/")
@check_permission(resource="notice", action="read")
async def list_notices(
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Notice)
    if search:
        query = query.filter(Notice.title.contains(search))
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

@router.post("/")
@check_permission(resource="notice", action="create")
async def create_notice(
    notice: NoticeCreate,
    db: AsyncSession = Depends(get_db)
):
    db_notice = Notice(**notice.dict())
    db.add(db_notice)
    await db.commit()
    return db_notice

# 엑셀 내보내기
@router.get("/export")
@check_permission(resource="notice", action="read")
async def export_notices(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Notice))
    notices = result.scalars().all()

    # pandas로 엑셀 생성
    df = pd.DataFrame([n.dict() for n in notices])

    buffer = BytesIO()
    df.to_excel(buffer, index=False)

    return StreamingResponse(
        BytesIO(buffer.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=notices.xlsx"}
    )
```

**Cerbos 통합** (공식 SDK + Depends 패턴):
```python
# app/dependencies.py
from fastapi import Depends, HTTPException, Request
from cerbos.sdk.client import AsyncCerbosClient
from cerbos.sdk.model import Principal, Resource, ResourceAction
from app.config import settings

# Cerbos 클라이언트 싱글톤
_cerbos_client = None

async def get_cerbos_client() -> AsyncCerbosClient:
    """Cerbos 클라이언트 의존성"""
    global _cerbos_client
    if _cerbos_client is None:
        _cerbos_client = AsyncCerbosClient(
            host=f"http://{settings.CERBOS_HOST}:{settings.CERBOS_PORT}"
        )
    return _cerbos_client

async def get_principal(request: Request) -> Principal:
    """현재 사용자 Principal 추출 (JWT에서)"""
    # TODO: JWT 토큰 검증 로직
    # 임시: 하드코딩
    return Principal(
        id="admin",
        roles={"admin"},
        attr={"department": "engineering"}
    )

async def check_resource_action(
    principal: Principal,
    resource: Resource,
    action: str,
    cerbos: AsyncCerbosClient
) -> bool:
    """Cerbos CheckResources API 호출"""
    result = await cerbos.check_resources(
        principal=principal,
        resources=[
            ResourceAction(resource=resource, actions=[action])
        ]
    )

    resource_result = result.results[0]
    if not resource_result.is_allowed(action):
        raise HTTPException(
            status_code=403,
            detail=f"{action} 권한이 없습니다"
        )
    return True

# 각 리소스별 권한 체크 헬퍼
async def check_notice_permission(
    action: str,
    notice_id: str = "any",
    principal: Principal = Depends(get_principal),
    cerbos: AsyncCerbosClient = Depends(get_cerbos_client)
):
    """공지사항 권한 체크"""
    resource = Resource(id=notice_id, kind="notice")
    await check_resource_action(principal, resource, action, cerbos)
    return principal
```

---

### 옵션 3: Django Admin

**단점**:
- ❌ 무거운 프레임워크 (불필요한 기능 과다)
- ❌ 기존 FastAPI 코드와 통합 불가
- ❌ 학습 곡선 높음
- ❌ 비동기 지원 제한적

**결론**: ❌ **배제** - FastAPI 환경과 호환성 없음

---

## 결정: 순수 FastAPI ⭐

### 이유

1. **기존 인프라와 완벽한 통합**
   - ds-api와 동일한 FastAPI + Poetry 스택
   - Flask 의존성 없음 (단일 웹 프레임워크)
   - 기존 패턴과 일관성 유지

2. **비동기 처리 우선**
   - 레거시 DB 동기화 필수 (blocking 불가)
   - FastAPI의 native async/await 지원
   - 고성능 concurrent 처리

3. **유연성과 확장성**
   - API 우선 설계 (프론트엔드 독립적)
   - 기존 HTML 프론트엔드 재활용 가능
   - 향후 React/Vue 전환 용이

4. **Cerbos 통합 용이**
   - 미들웨어/데코레이터 패턴으로 깔끔한 구현
   - 모든 엔드포인트에 일관된 권한 체크

5. **의존성 최소화**
   - 새로운 웹 프레임워크 불필요
   - 관리 복잡도 감소
   - 배포 및 모니터링 단순화

### 구현 계획

#### Phase 0: MVP (오늘 5.5시간)

**Step 1: DB 모델 및 스키마 완성** (1시간)
```bash
# 모델 정의 완성
app/models/notice.py
app/models/usage.py
app/models/satisfaction.py

# Alembic migration 생성
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

**Step 2: CRUD 엔드포인트 구현** (2.5시간)
```python
# app/routers/admin/notices.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import Notice
from app.schemas import NoticeCreate, NoticeUpdate, NoticeResponse
from app.dependencies import get_db, check_permission

router = APIRouter(prefix="/api/v1/admin/notices", tags=["admin-notices"])

@router.get("/", response_model=list[NoticeResponse])
@check_permission(resource="notice", action="read")
async def list_notices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    search: str | None = None,
    priority: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db)
):
    """공지사항 목록 조회 (검색/필터링)"""
    query = select(Notice)

    # 검색
    if search:
        query = query.filter(
            (Notice.title.contains(search)) | (Notice.content.contains(search))
        )

    # 필터
    if priority:
        query = query.filter(Notice.priority == priority)
    if is_active is not None:
        query = query.filter(Notice.is_active == is_active)

    # 정렬 및 페이징
    query = query.order_by(Notice.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=NoticeResponse, status_code=201)
@check_permission(resource="notice", action="create")
async def create_notice(
    notice: NoticeCreate,
    db: AsyncSession = Depends(get_db)
):
    """공지사항 생성"""
    db_notice = Notice(**notice.model_dump())
    db.add(db_notice)
    await db.commit()
    await db.refresh(db_notice)
    return db_notice

@router.get("/{notice_id}", response_model=NoticeResponse)
@check_permission(resource="notice", action="read")
async def get_notice(notice_id: int, db: AsyncSession = Depends(get_db)):
    """공지사항 상세 조회"""
    result = await db.execute(select(Notice).filter(Notice.id == notice_id))
    notice = result.scalar_one_or_none()
    if not notice:
        raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다")
    return notice

@router.put("/{notice_id}", response_model=NoticeResponse)
@check_permission(resource="notice", action="update")
async def update_notice(
    notice_id: int,
    notice_update: NoticeUpdate,
    db: AsyncSession = Depends(get_db)
):
    """공지사항 수정"""
    result = await db.execute(select(Notice).filter(Notice.id == notice_id))
    db_notice = result.scalar_one_or_none()
    if not db_notice:
        raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다")

    for field, value in notice_update.model_dump(exclude_unset=True).items():
        setattr(db_notice, field, value)

    await db.commit()
    await db.refresh(db_notice)
    return db_notice

@router.delete("/{notice_id}", status_code=204)
@check_permission(resource="notice", action="delete")
async def delete_notice(notice_id: int, db: AsyncSession = Depends(get_db)):
    """공지사항 삭제"""
    result = await db.execute(select(Notice).filter(Notice.id == notice_id))
    db_notice = result.scalar_one_or_none()
    if not db_notice:
        raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다")

    await db.delete(db_notice)
    await db.commit()
```

**Step 3: Cerbos 권한 미들웨어** (1.5시간)
```python
# app/dependencies.py
from functools import wraps
from fastapi import HTTPException, Request, Depends
import httpx
from app.config import settings

async def get_current_user(request: Request):
    """JWT 토큰에서 사용자 정보 추출 (임시: 하드코딩)"""
    # TODO: JWT 검증 로직
    return {
        "id": "admin",
        "roles": ["admin"],
        "department": None
    }

def check_permission(resource: str, action: str):
    """Cerbos 권한 체크 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 요청에서 current_user 추출
            request = kwargs.get('request')
            if not request:
                # Depends로 주입된 경우
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            # 사용자 정보 가져오기
            current_user = await get_current_user(request)

            # Cerbos API 호출
            async with httpx.AsyncClient() as client:
                try:
                    resp = await client.post(
                        f"http://{settings.CERBOS_HOST}:{settings.CERBOS_PORT}/api/check",
                        json={
                            "principal": {
                                "id": current_user["id"],
                                "roles": current_user["roles"],
                                "attr": {"department": current_user.get("department")}
                            },
                            "resource": {
                                "kind": resource,
                                "id": "any"
                            },
                            "actions": [action]
                        },
                        timeout=2.0
                    )
                    result = resp.json()

                    if result["results"][0]["effect"] != "EFFECT_ALLOW":
                        raise HTTPException(
                            status_code=403,
                            detail=f"{action} 권한이 없습니다"
                        )
                except httpx.HTTPError as e:
                    # Cerbos 연결 실패 시 거부
                    raise HTTPException(
                        status_code=503,
                        detail="권한 서버 연결 실패"
                    )

            # 원래 함수 실행 (current_user 추가)
            kwargs['current_user'] = current_user
            return await func(*args, **kwargs)

        return wrapper
    return decorator
```

**Step 4: 엑셀 내보내기** (0.5시간)
```python
# app/routers/admin/export.py
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import pandas as pd
from io import BytesIO
from app.models import Notice, UsageHistory, SatisfactionSurvey
from app.dependencies import get_db, check_permission

router = APIRouter(prefix="/api/v1/admin/export", tags=["admin-export"])

@router.get("/notices")
@check_permission(resource="notice", action="read")
async def export_notices(db: AsyncSession = Depends(get_db)):
    """공지사항 엑셀 내보내기"""
    result = await db.execute(select(Notice))
    notices = result.scalars().all()

    df = pd.DataFrame([{
        "ID": n.id,
        "제목": n.title,
        "내용": n.content,
        "우선순위": n.priority,
        "활성화": n.is_active,
        "생성일": n.created_at
    } for n in notices])

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='공지사항')

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=notices.xlsx"}
    )

@router.get("/usage")
@check_permission(resource="usage_history", action="read")
async def export_usage(db: AsyncSession = Depends(get_db)):
    """사용 이력 엑셀 내보내기"""
    result = await db.execute(select(UsageHistory).limit(10000))  # 최대 1만건
    history = result.scalars().all()

    df = pd.DataFrame([{
        "ID": h.id,
        "사용자": h.user_id,
        "질문": h.question,
        "답변": h.answer[:100],  # 답변 100자 제한
        "응답시간(ms)": h.response_time,
        "모델": h.model_name,
        "생성일": h.created_at
    } for h in history])

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='사용이력')

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=usage_history.xlsx"}
    )
```

#### Phase 1: 핵심 기능 고도화 (1-2일, 10시간)

- 검색/필터링 고도화 (full-text search)
- 페이지네이션 메타데이터 (total count 등)
- 부서/역할 CRUD 구현
- Cerbos 부서별 권한 정책
- 프론트엔드 API 연동

#### Phase 2: 레거시 연동 (3-5일, 30시간)

- 레거시 DB 연결 풀 설정
- 문서 변경 감지 스케줄러 (APScheduler)
- Diff 생성 및 승인 워크플로우
- WebSocket 실시간 알림

---

## 타임라인

### 🚀 Phase 0: MVP (오늘 5.5시간)
| 작업 | 시간 | 상태 |
|------|------|------|
| DB 모델 및 스키마 완성 | 1시간 | ⏳ |
| 공지사항 CRUD 엔드포인트 | 1시간 | ⏳ |
| 사용 이력 조회 엔드포인트 | 0.5시간 | ⏳ |
| 만족도 조사 조회 엔드포인트 | 0.5시간 | ⏳ |
| **Cerbos 권한 미들웨어** | 1.5시간 | ⏳ |
| 엑셀 내보내기 구현 | 1시간 | ⏳ |
| **MVP 완성** ✅ | **5.5시간** | **오늘** |

### 📅 Phase 1: 핵심 기능 고도화 (1-2일, 10시간)
| 작업 | 시간 |
|------|------|
| 검색/필터링 고도화 (full-text) | 2시간 |
| 페이지네이션 메타데이터 | 1시간 |
| **Cerbos 부서별 권한 정책** | 4시간 |
| 부서/역할 CRUD | 2시간 |
| 프론트엔드 API 연동 | 1시간 |
| **총계** | **10시간 (1-2일)** |

### 🔗 Phase 2: 레거시 연동 (3-5일, 30시간)
| 작업 | 시간 |
|------|------|
| 레거시 DB 연결 풀 설정 | 4시간 |
| 문서 변경 감지 스케줄러 | 8시간 |
| Diff 생성 및 비교 | 6시간 |
| 승인 워크플로우 구현 | 10시간 |
| WebSocket 실시간 알림 | 2시간 |
| **총계** | **30시간 (3-5일)** |

**전체 타임라인**:
- **오늘**: MVP 완성 (5.5시간)
- **Day 1-2**: 핵심 기능 완성 (15.5시간 누적)
- **Day 3-6**: 레거시 연동 포함 전체 완성 (45.5시간)

**총 예상 시간**: 45.5시간 = **약 6일** (1인 기준)

---

## 성공 지표

### MVP (오늘)
- [ ] ✅ 공지사항 CRUD API 동작
- [ ] ✅ 사용 이력 조회 API 동작
- [ ] ✅ 만족도 조사 조회 API 동작
- [ ] ✅ Cerbos 권한 체크 동작
- [ ] ✅ 엑셀 내보내기 동작
- [ ] ✅ Swagger 문서 확인 가능

### Phase 1 (Day 1-2)
- [ ] 검색/필터링 고도화
- [ ] 페이지네이션 메타데이터
- [ ] 부서별 권한 정책 적용
- [ ] 프론트엔드 연동 완료

### Phase 2 (Day 3-6)
- [ ] 레거시 DB 동기화 스케줄러
- [ ] 문서 승인 워크플로우
- [ ] 실시간 알림 시스템
- [ ] 전체 통합 테스트 통과

---

## 리스크 및 완화

| 리스크 | 확률 | 영향 | 완화 전략 |
|--------|------|------|-----------|
| CRUD 구현 시간 초과 | 중간 | 중간 | FastAPI 코드 생성 자동화, 패턴 재사용 |
| Cerbos 통합 복잡도 | 낮음 | 중간 | 데코레이터 패턴으로 단순화, 기존 정책 활용 |
| 엑셀 내보내기 성능 | 낮음 | 낮음 | 페이징 처리, 최대 건수 제한 (1만건) |
| 레거시 DB 동기화 오류 | 중간 | 높음 | 에러 핸들링, 재시도 로직, 로깅 강화 |

---

## 의존성 추가

**pyproject.toml에 추가 필요**:
```toml
[tool.poetry.dependencies]
pandas = "^2.0.0"           # 엑셀 내보내기
openpyxl = "^3.1.0"         # 엑셀 엔진
apscheduler = "^3.10.0"     # 스케줄러 (레거시 연동)
```

---

## 결론

**순수 FastAPI 방식 채택** ⭐

**핵심 근거**:
1. 🏗️ **기존 인프라 통합**: ds-api와 동일한 스택, Flask 불필요
2. ⚡ **비동기 우선**: 레거시 DB 동기화 필수
3. 🎯 **단순성**: 단일 웹 프레임워크, 관리 복잡도 최소화
4. 🔒 **Cerbos 통합**: 데코레이터 패턴으로 깔끔한 권한 체크
5. 📊 **유연성**: API 우선 설계, 프론트엔드 독립적

**다음 단계 (지금 바로 시작)** ⚡:
1. ✅ 기술 스택 결정 완료
2. [ ] **[1시간]** DB 모델 및 스키마 완성
3. [ ] **[2.5시간]** CRUD 엔드포인트 구현
4. [ ] **[1.5시간]** Cerbos 권한 미들웨어
5. [ ] **[0.5시간]** 엑셀 내보내기
6. [ ] **[오늘 완성]** MVP 데모 가능 (http://localhost:8010/docs)

**목표**: 오늘 5.5시간 내 MVP 완성! 🚀

---

**작성자**: 개발팀
**날짜**: 2025-10-18
**상태**: ✅ **순수 FastAPI 방식 확정**, 즉시 구현 시작
