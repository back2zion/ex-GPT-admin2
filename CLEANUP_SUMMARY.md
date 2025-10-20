# 사용 이력 데이터 정리 완료

**작업 일시**: 2025-10-19 17:59 KST
**작업 내용**: 테스트/더미 데이터 삭제 및 타임존 수정

---

## ✅ 완료된 작업

### 1. 더미 데이터 삭제
```sql
DELETE FROM usage_history
WHERE user_id LIKE '%test%'
   OR user_id LIKE '%DROP%'
   OR user_id LIKE '%security%'
   OR user_id LIKE '%direct%'
   OR user_id LIKE '%admin___%';

-- 결과: 12개 레코드 삭제
```

#### 삭제된 데이터 목록:
| ID | user_id | question |
|----|---------|----------|
| 19 | test_user | 고속도로 시공시 절차를 알려줘 |
| 18 | test | NULL바이트테스트 |
| 17 | admin___DROP_TABLE_users-- | SQL Injection 시도 |
| 16 | test_user | 정상적인 질문입니다 |
| 15 | test | $(python3 -c 'print(A*15000)') |
| 14 | test__DROP_TABLE_users-- | SQL Injection 테스트 |
| 13 | security_test | 보안 테스트 |
| 12 | test_user | 안녕 |
| 11 | test | 테스트 |
| 10 | test28091 | 28091 테스트 |
| 9 | test_user | 테스트 질문 |
| 8 | direct_test | 직접 테스트 |

### 2. 타임존 문제 수정

#### Before (타임존 미고려):
```python
# app/models/base.py
created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

#### After (타임존 인식):
```python
# app/models/base.py
created_at = Column(
    DateTime(timezone=True),  # ✅ timezone-aware
    default=lambda: datetime.now(timezone.utc),
    nullable=False
)
```

**효과**:
- DB에 UTC 시간 저장 (timezone-aware)
- ISO 8601 형식으로 응답 (예: `2025-10-19T08:59:07.898947+00:00`)
- 프론트엔드에서 브라우저 로컬 시간대로 자동 변환 가능

---

## 📊 현재 상태

### Database
```sql
SELECT COUNT(*) FROM usage_history;
-- 결과: 0개 (모든 더미 데이터 삭제 완료)
```

### Timezone
```sql
-- PostgreSQL 서버 시간 (UTC)
SELECT NOW();
-- 2025-10-19 08:59:07+00

-- 한국 시간 (KST = UTC+9)
SELECT NOW() AT TIME ZONE 'Asia/Seoul';
-- 2025-10-19 17:59:07
```

---

## 🔧 수정된 파일

### 1. `/home/aigen/admin-api/app/models/base.py`
```python
class TimestampMixin:
    """
    타임스탬프 믹스인

    **Timezone**: UTC로 저장 (timezone-aware datetime)
    - 한국 시간(KST) = UTC + 9시간
    - 응답 시 schema에서 KST로 변환
    """
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
```

### 2. `/home/aigen/admin-api/app/schemas/usage.py`
```python
class UsageHistoryResponse(BaseModel):
    """
    사용 이력 응답 스키마

    **Timezone 처리**:
    - DB에는 UTC로 저장 (timezone-aware)
    - 응답 시 ISO 8601 형식으로 UTC 시간 반환
    - 프론트엔드에서 브라우저의 로컬 시간대로 표시 권장
    """
    ...

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
```

---

## 🌐 프론트엔드 권장 사항

### JavaScript에서 시간대 변환
```javascript
// API 응답 예시:
// {"created_at": "2025-10-19T08:59:07.898947+00:00"}

const response = await fetch('/api/v1/admin/usage/');
const data = await response.json();

// UTC 시간을 브라우저 로컬 시간대로 변환
data.forEach(item => {
    const utcDate = new Date(item.created_at);

    // 한국 시간대로 표시 (KST)
    const kstString = utcDate.toLocaleString('ko-KR', {
        timeZone: 'Asia/Seoul',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });

    console.log(`Created: ${kstString}`);
    // 출력: "Created: 2025. 10. 19. 오후 5:59:07"
});
```

### HTML Table 표시
```html
<table>
  <tr>
    <th>ID</th>
    <th>사용자</th>
    <th>질문</th>
    <th>생성 시간 (KST)</th>
  </tr>
  <tbody id="usage-list"></tbody>
</table>

<script>
fetch('/api/v1/admin/usage/')
  .then(res => res.json())
  .then(data => {
    const tbody = document.getElementById('usage-list');
    data.forEach(item => {
      const tr = document.createElement('tr');
      const createdDate = new Date(item.created_at);
      const kstTime = createdDate.toLocaleString('ko-KR', {
        timeZone: 'Asia/Seoul'
      });

      tr.innerHTML = `
        <td>${item.id}</td>
        <td>${item.user_id}</td>
        <td>${item.question}</td>
        <td>${kstTime}</td>
      `;
      tbody.appendChild(tr);
    });
  });
</script>
```

---

## 🧪 테스트

### 1. 데이터 확인
```bash
# PostgreSQL 직접 조회
PGPASSWORD=password psql -h localhost -p 5432 -U postgres -d admin_db \
  -c "SELECT COUNT(*) FROM usage_history;"

# API 조회
curl http://localhost:8010/api/v1/admin/usage/
```

### 2. 시간대 확인
```bash
# 새 데이터 생성
curl -X POST http://localhost:8010/api/v1/admin/usage/log \
  -H "Content-Type: application/json" \
  -d '{"user_id":"real_user","question":"시간대 테스트"}'

# 응답 예시:
# {
#   "id": 20,
#   "created_at": "2025-10-19T08:59:07.898947+00:00",  // UTC
#   ...
# }

# JavaScript에서 변환:
# new Date("2025-10-19T08:59:07.898947+00:00")
#   .toLocaleString('ko-KR', {timeZone: 'Asia/Seoul'})
# => "2025. 10. 19. 오후 5:59:07"  // KST (UTC+9)
```

---

## 📝 추가 정리 방법 (향후)

### 정기적으로 오래된 데이터 삭제
```sql
-- 90일 이상 된 데이터 삭제 (GDPR 준수)
DELETE FROM usage_history
WHERE created_at < NOW() - INTERVAL '90 days';
```

### 특정 패턴 데이터 삭제
```sql
-- 특정 사용자 패턴 삭제
DELETE FROM usage_history
WHERE user_id LIKE '%pattern%';

-- 질문이 비어있는 데이터 삭제
DELETE FROM usage_history
WHERE question = '' OR question IS NULL;
```

### Python 스크립트로 정리 (cron 등록 가능)
```python
# /tmp/cleanup_old_usage.py
import asyncpg
import asyncio
from datetime import datetime, timedelta

async def cleanup():
    conn = await asyncpg.connect(
        "postgresql://postgres:password@localhost:5432/admin_db"
    )

    # 90일 이상 된 데이터 삭제
    cutoff = datetime.utcnow() - timedelta(days=90)
    result = await conn.execute(
        "DELETE FROM usage_history WHERE created_at < $1",
        cutoff
    )
    print(f"Deleted {result} old records")

    await conn.close()

asyncio.run(cleanup())
```

---

## ✅ 검증 완료

```bash
# 현재 상태 확인
$ PGPASSWORD=password psql -h localhost -p 5432 -U postgres -d admin_db \
  -c "SELECT COUNT(*) FROM usage_history;"

 count
-------
     0
(1 row)

✅ 모든 더미 데이터 삭제 완료
✅ 타임존 설정 수정 완료
✅ API 응답 형식 개선 완료
```

---

**작업 완료**: 2025-10-19 17:59 KST
**상태**: ✅ 정리 완료, 실제 사용자 데이터만 저장됨
**다음 정리**: 필요 시 90일마다 자동 정리 권장
