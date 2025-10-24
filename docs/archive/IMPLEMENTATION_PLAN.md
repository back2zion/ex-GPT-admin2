# 구현 계획 - FastAPI 방식 (수정됨)

**시작 시각**: 2025-10-18 14:30
**목표**: 오늘 내 MVP 완성 (순수 FastAPI)
**변경 사유**: Flask가 기존 스택에 없음 → 순수 FastAPI로 변경

---

## 🎯 오늘의 목표 (5.5시간)

### ✅ 완성 기준
- [ ] 공지사항 CRUD API 동작
- [ ] 사용 이력 조회 API (읽기 전용)
- [ ] 만족도 조사 조회 API
- [ ] **Cerbos 권한 미들웨어 적용**
- [ ] 엑셀 내보내기 동작
- [ ] http://localhost:8010/docs (Swagger) 접속 가능

---

## 📋 단계별 체크리스트

### Step 1: 의존성 추가 (10분)

**1.1 pyproject.toml 수정**
```bash
cd /home/aigen/admin-api
poetry add pandas openpyxl apscheduler cerbos-sdk-python
```

**필요한 패키지**:
- `pandas`: 엑셀 내보내기
- `openpyxl`: 엑셀 엔진
- `apscheduler`: 스케줄러 (Phase 2용, 미리 설치)
- `cerbos-sdk-python`: Cerbos 공식 Python SDK

---

### Step 2: DB 모델 완성 (50분)

**2.1 app/models/notice.py**
```python
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from app.database import Base

class Notice(Base):
    __tablename__ = "notices"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    priority = Column(Enum('high', 'normal', 'low', name='priority_enum'), default='normal')
    is_active = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**2.2 app/models/usage.py**
```python
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base

class UsageHistory(Base):
    __tablename__ = "usage_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    response_time = Column(Float)  # milliseconds
    model_name = Column(String(100))
    metadata = Column(JSON)  # 추가 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**2.3 app/models/satisfaction.py**
```python
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.sql import func
from app.database import Base

class SatisfactionSurvey(Base):
    __tablename__ = "satisfaction_surveys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-5
    feedback = Column(Text)
    category = Column(Enum('ui', 'speed', 'accuracy', 'other', name='category_enum'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**2.4 app/models/__init__.py**
```python
from app.models.notice import Notice
from app.models.usage import UsageHistory
from app.models.satisfaction import SatisfactionSurvey

__all__ = ["Notice", "UsageHistory", "SatisfactionSurvey"]
```

**2.5 Alembic migration 생성**
```bash
alembic revision --autogenerate -m "Add notice, usage, satisfaction models"
alembic upgrade head
```

---

### Step 3: Pydantic 스키마 생성 (30분)

**3.1 app/schemas/notice.py**
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class NoticeBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str
    priority: str = Field(default='normal', pattern='^(high|normal|low)$')
    is_active: bool = True

class NoticeCreate(NoticeBase):
    pass

class NoticeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    priority: Optional[str] = Field(None, pattern='^(high|normal|low)$')
    is_active: Optional[bool] = None

class NoticeResponse(NoticeBase):
    id: int
    view_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
```

**3.2 app/schemas/usage.py**
```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any

class UsageHistoryResponse(BaseModel):
    id: int
    user_id: str
    question: str
    answer: Optional[str]
    response_time: Optional[float]
    model_name: Optional[str]
    metadata: Optional[Any]
    created_at: datetime

    class Config:
        from_attributes = True
```

**3.3 app/schemas/satisfaction.py**
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class SatisfactionResponse(BaseModel):
    id: int
    user_id: str
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str]
    category: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
```

---

### Step 4: CRUD 엔드포인트 구현 (90분)

**4.1 app/routers/admin/notices.py** (공지사항 CRUD)
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.models import Notice
from app.schemas.notice import NoticeCreate, NoticeUpdate, NoticeResponse
from app.database import get_db
from app.dependencies import check_permission

router = APIRouter(prefix="/api/v1/admin/notices", tags=["admin-notices"])

@router.get("/", response_model=List[NoticeResponse])
async def list_notices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    search: str | None = None,
    priority: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db)
):
    """공지사항 목록 조회"""
    query = select(Notice)

    if search:
        query = query.filter(
            (Notice.title.contains(search)) | (Notice.content.contains(search))
        )
    if priority:
        query = query.filter(Notice.priority == priority)
    if is_active is not None:
        query = query.filter(Notice.is_active == is_active)

    query = query.order_by(Notice.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=NoticeResponse, status_code=201)
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
async def get_notice(notice_id: int, db: AsyncSession = Depends(get_db)):
    """공지사항 상세 조회"""
    result = await db.execute(select(Notice).filter(Notice.id == notice_id))
    notice = result.scalar_one_or_none()
    if not notice:
        raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다")

    # 조회수 증가
    notice.view_count += 1
    await db.commit()
    return notice

@router.put("/{notice_id}", response_model=NoticeResponse)
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
async def delete_notice(notice_id: int, db: AsyncSession = Depends(get_db)):
    """공지사항 삭제"""
    result = await db.execute(select(Notice).filter(Notice.id == notice_id))
    db_notice = result.scalar_one_or_none()
    if not db_notice:
        raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다")

    await db.delete(db_notice)
    await db.commit()
```

**4.2 app/routers/admin/usage.py** (사용 이력 조회)
```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.models import UsageHistory
from app.schemas.usage import UsageHistoryResponse
from app.database import get_db

router = APIRouter(prefix="/api/v1/admin/usage", tags=["admin-usage"])

@router.get("/", response_model=List[UsageHistoryResponse])
async def list_usage_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    user_id: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """사용 이력 조회 (읽기 전용)"""
    query = select(UsageHistory)

    if user_id:
        query = query.filter(UsageHistory.user_id == user_id)
    if search:
        query = query.filter(
            (UsageHistory.question.contains(search)) |
            (UsageHistory.answer.contains(search))
        )

    query = query.order_by(UsageHistory.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
```

**4.3 app/routers/admin/satisfaction.py** (만족도 조회)
```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict

from app.models import SatisfactionSurvey
from app.schemas.satisfaction import SatisfactionResponse
from app.database import get_db

router = APIRouter(prefix="/api/v1/admin/satisfaction", tags=["admin-satisfaction"])

@router.get("/", response_model=List[SatisfactionResponse])
async def list_satisfaction(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    rating: int | None = Query(None, ge=1, le=5),
    category: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """만족도 조사 조회"""
    query = select(SatisfactionSurvey)

    if rating:
        query = query.filter(SatisfactionSurvey.rating == rating)
    if category:
        query = query.filter(SatisfactionSurvey.category == category)

    query = query.order_by(SatisfactionSurvey.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/stats")
async def get_satisfaction_stats(db: AsyncSession = Depends(get_db)):
    """만족도 통계"""
    result = await db.execute(
        select(
            func.avg(SatisfactionSurvey.rating).label('average'),
            func.count(SatisfactionSurvey.id).label('total')
        )
    )
    stats = result.one()
    return {
        "average_rating": round(stats.average, 2) if stats.average else 0,
        "total_surveys": stats.total
    }
```

---

### Step 5: Cerbos 권한 미들웨어 (90분) - 공식 SDK + Depends 패턴

**5.1 app/dependencies.py**
```python
from fastapi import Depends, HTTPException, Request
from cerbos.sdk.client import AsyncCerbosClient
from cerbos.sdk.model import Principal, Resource, ResourceAction
from app.config import settings
from typing import Callable

# Cerbos 클라이언트 싱글톤
_cerbos_client = None

async def get_cerbos_client() -> AsyncCerbosClient:
    """Cerbos 클라이언트 의존성 (싱글톤)"""
    global _cerbos_client
    if _cerbos_client is None:
        _cerbos_client = AsyncCerbosClient(
            host=f"http://{settings.CERBOS_HOST}:{settings.CERBOS_PORT}"
        )
    return _cerbos_client

async def get_principal(request: Request) -> Principal:
    """현재 사용자 Principal 추출"""
    # TODO: JWT 토큰 검증 로직 (Phase 1에서 구현)
    # 임시: 하드코딩된 admin 사용자
    return Principal(
        id="admin",
        roles={"admin"},
        attr={"department": "engineering"}
    )

# 권한 체크 헬퍼 함수
async def check_resource_permission(
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

# 각 리소스별 권한 체크 Depends 팩토리
def require_permission(resource_kind: str, action: str):
    """권한 체크 Depends 생성 팩토리"""
    async def permission_checker(
        principal: Principal = Depends(get_principal),
        cerbos: AsyncCerbosClient = Depends(get_cerbos_client)
    ) -> Principal:
        resource = Resource(id="any", kind=resource_kind)
        await check_resource_permission(principal, resource, action, cerbos)
        return principal

    return permission_checker

# 리소스 ID가 있는 경우 권한 체크
def require_resource_permission(resource_kind: str, action: str, id_param: str = "id"):
    """특정 리소스 ID에 대한 권한 체크"""
    async def permission_checker(
        resource_id: int,
        principal: Principal = Depends(get_principal),
        cerbos: AsyncCerbosClient = Depends(get_cerbos_client)
    ) -> Principal:
        resource = Resource(id=str(resource_id), kind=resource_kind)
        await check_resource_permission(principal, resource, action, cerbos)
        return principal

    return permission_checker
```

**5.2 라우터에 권한 체크 적용 (Depends 패턴)**
```python
# app/routers/admin/notices.py 수정
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.models import Notice
from app.schemas.notice import NoticeCreate, NoticeUpdate, NoticeResponse
from app.database import get_db
from app.dependencies import require_permission, get_principal
from cerbos.sdk.model import Principal

router = APIRouter(prefix="/api/v1/admin/notices", tags=["admin-notices"])

# 읽기는 모든 사용자 가능
@router.get("/", response_model=List[NoticeResponse])
async def list_notices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    search: str | None = None,
    priority: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_principal)  # 인증만 체크
):
    """공지사항 목록 조회"""
    query = select(Notice)
    # ... (기존 코드)
    result = await db.execute(query)
    return result.scalars().all()

# 생성은 admin/manager만 가능
@router.post("/", response_model=NoticeResponse, status_code=201)
async def create_notice(
    notice: NoticeCreate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("notice", "create"))
):
    """공지사항 생성 (admin/manager만)"""
    db_notice = Notice(**notice.model_dump())
    db.add(db_notice)
    await db.commit()
    await db.refresh(db_notice)
    return db_notice

# 수정은 admin/manager만 가능
@router.put("/{notice_id}", response_model=NoticeResponse)
async def update_notice(
    notice_id: int,
    notice_update: NoticeUpdate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("notice", "update"))
):
    """공지사항 수정 (admin/manager만)"""
    result = await db.execute(select(Notice).filter(Notice.id == notice_id))
    db_notice = result.scalar_one_or_none()
    if not db_notice:
        raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다")

    for field, value in notice_update.model_dump(exclude_unset=True).items():
        setattr(db_notice, field, value)

    await db.commit()
    await db.refresh(db_notice)
    return db_notice

# 삭제는 admin만 가능
@router.delete("/{notice_id}", status_code=204)
async def delete_notice(
    notice_id: int,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("notice", "delete"))
):
    """공지사항 삭제 (admin만)"""
    result = await db.execute(select(Notice).filter(Notice.id == notice_id))
    db_notice = result.scalar_one_or_none()
    if not db_notice:
        raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다")

    await db.delete(db_notice)
    await db.commit()
```

**5.3 장점**
- ✅ FastAPI 네이티브 패턴 (Depends)
- ✅ 타입 안전성 (Principal 객체)
- ✅ 재사용성 (팩토리 패턴)
- ✅ 테스트 용이성 (Depends 오버라이드 가능)
- ✅ Swagger 문서 자동 생성

---

### Step 6: 엑셀 내보내기 (30분)

**6.1 app/routers/admin/export.py**
```python
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import pandas as pd
from io import BytesIO

from app.models import Notice, UsageHistory, SatisfactionSurvey
from app.database import get_db
from app.dependencies import require_permission
from cerbos.sdk.model import Principal

router = APIRouter(prefix="/api/v1/admin/export", tags=["admin-export"])

@router.get("/notices")
async def export_notices(
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("notice", "read"))
):
    """공지사항 엑셀 내보내기"""
    result = await db.execute(select(Notice))
    notices = result.scalars().all()

    df = pd.DataFrame([{
        "ID": n.id,
        "제목": n.title,
        "내용": n.content,
        "우선순위": n.priority,
        "활성화": n.is_active,
        "조회수": n.view_count,
        "생성일": n.created_at.strftime("%Y-%m-%d %H:%M:%S") if n.created_at else ""
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
async def export_usage(
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("usage_history", "read"))
):
    """사용 이력 엑셀 내보내기"""
    result = await db.execute(select(UsageHistory).limit(10000))
    history = result.scalars().all()

    df = pd.DataFrame([{
        "ID": h.id,
        "사용자": h.user_id,
        "질문": h.question,
        "답변": h.answer[:100] if h.answer else "",
        "응답시간(ms)": h.response_time,
        "모델": h.model_name,
        "생성일": h.created_at.strftime("%Y-%m-%d %H:%M:%S")
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

@router.get("/satisfaction")
async def export_satisfaction(
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_permission("satisfaction", "read"))
):
    """만족도 조사 엑셀 내보내기"""
    result = await db.execute(select(SatisfactionSurvey))
    surveys = result.scalars().all()

    df = pd.DataFrame([{
        "ID": s.id,
        "사용자": s.user_id,
        "평점": s.rating,
        "피드백": s.feedback,
        "카테고리": s.category,
        "생성일": s.created_at.strftime("%Y-%m-%d %H:%M:%S")
    } for s in surveys])

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='만족도조사')

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=satisfaction.xlsx"}
    )
```

---

### Step 7: 라우터 등록 (10분)

**7.1 app/main.py 수정**
```python
from fastapi import FastAPI
from app.routers.admin import notices, usage, satisfaction, export

app = FastAPI(title="AI Streams Admin API", version="1.0.0")

# Admin 라우터 등록
app.include_router(notices.router)
app.include_router(usage.router)
app.include_router(satisfaction.router)
app.include_router(export.router)

@app.get("/")
async def root():
    return {"message": "AI Streams Admin API", "docs": "/docs"}
```

---

### Step 8: 테스트 (30분)

**8.1 Docker 재빌드 및 실행**
```bash
cd /home/aigen/admin-api
docker-compose down
docker-compose build
docker-compose up -d
docker-compose logs -f admin-api
```

**8.2 Swagger 문서 확인**
```bash
curl http://localhost:8010/docs
```
브라우저로 http://localhost:8010/docs 접속하여 API 문서 확인

**8.3 API 테스트**
```bash
# 공지사항 목록 조회
curl http://localhost:8010/api/v1/admin/notices/

# 공지사항 생성
curl -X POST http://localhost:8010/api/v1/admin/notices/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "테스트 공지",
    "content": "테스트 내용입니다",
    "priority": "high"
  }'

# 엑셀 다운로드
curl -O http://localhost:8010/api/v1/admin/export/notices
```

**8.4 Cerbos 권한 테스트**
```bash
# Cerbos 로그 확인
docker-compose logs cerbos | grep "check"

# 수동 권한 체크
curl -X POST http://localhost:3592/api/check \
  -H "Content-Type: application/json" \
  -d '{
    "principal": {"id": "admin", "roles": ["admin"]},
    "resource": {"kind": "notice", "id": "any"},
    "actions": ["create"]
  }'
```

---

## 📊 진행 상황 추적

| 단계 | 예상 시간 | 실제 시간 | 상태 |
|------|-----------|-----------|------|
| Step 1: 의존성 추가 | 10분 | | ⏳ 대기 |
| Step 2: DB 모델 | 50분 | | ⏳ 대기 |
| Step 3: Pydantic 스키마 | 30분 | | ⏳ 대기 |
| Step 4: CRUD 엔드포인트 | 90분 | | ⏳ 대기 |
| Step 5: Cerbos 미들웨어 | 90분 | | ⏳ 대기 |
| Step 6: 엑셀 내보내기 | 30분 | | ⏳ 대기 |
| Step 7: 라우터 등록 | 10분 | | ⏳ 대기 |
| Step 8: 테스트 | 30분 | | ⏳ 대기 |
| **총계** | **5.5시간** | | |

---

## 🚨 문제 발생 시

### DB 연결 오류
```bash
# PostgreSQL 상태 확인
docker-compose ps postgres
docker-compose logs postgres

# 테이블 확인
docker-compose exec postgres psql -U postgres -d admin_db -c "\dt"
```

### Cerbos 연결 오류
```bash
# Cerbos 서비스 확인
docker-compose ps cerbos
docker-compose logs cerbos

# 정책 파일 확인
ls -la policies/
```

### 모델 임포트 오류
```python
# app/database.py 확인
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base

Base = declarative_base()
```

---

## ✅ 완성 후 확인 사항

**MVP 체크리스트**:
- [ ] ✅ http://localhost:8010/docs 접속 가능
- [ ] ✅ 공지사항 CRUD API 동작
- [ ] ✅ 사용 이력 조회 API 동작
- [ ] ✅ 만족도 조사 조회 API 동작
- [ ] ✅ 엑셀 내보내기 (3개) 동작
- [ ] ✅ Cerbos 권한 체크 동작
- [ ] ✅ 검색/필터링 동작

**다음 단계 (Phase 1)**:
1. 페이지네이션 메타데이터 추가
2. 부서/역할 CRUD 구현
3. Cerbos 부서별 권한 정책
4. 프론트엔드 API 연동

---

**시작 준비 완료!** 🚀

지금 바로 구현을 시작하시겠습니까?
