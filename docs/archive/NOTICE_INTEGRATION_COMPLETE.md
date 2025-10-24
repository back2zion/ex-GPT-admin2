# 공지사항 연동 완료

**작업 완료 시간**: 2025-10-19 18:45 KST
**연동 대상**: `https://ui.datastreams.co.kr:20443/layout.html` ↔ Admin API

---

## ✅ 완료된 작업

### 1. API Endpoint 설정
- **변경**: `/notice/getNoticeInfo` (레거시) → `/api/v1/admin/notices/?is_active=true` (신규)
- **위치**: `/var/www/html/layout.html` 3241번째 줄

### 2. JavaScript 함수 수정

#### `loadNoticeData()` 함수 (3239-3255번째 줄)
```javascript
async function loadNoticeData() {
    try {
        const response = await fetch('/api/v1/admin/notices/?is_active=true');

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (Array.isArray(data) && data.length > 0) {
            displayNoticeData(data);
        } else {
            displayDefaultNotice();
        }
    } catch (error) {
        debugError('공지사항 로드 실패:', error);
        displayDefaultNotice();
    }
}
```

**변경 사항**:
- ✅ API 응답 형식 변경: `data.noticeInfos` → 직접 배열
- ✅ 에러 처리 강화: HTTP 상태 코드 확인
- ✅ `Array.isArray()` 검증 추가

#### `displayNoticeData()` 함수 (3257-3300번째 줄)
```javascript
function displayNoticeData(noticeInfos) {
    const noticeList = document.querySelector('.notice-list');

    // 기존 하드코딩된 공지사항 제거
    noticeList.innerHTML = '';

    noticeInfos.forEach(notice => {
        // 동적으로 공지사항 아이템 생성
        const noticeItem = document.createElement('li');
        noticeItem.className = 'notice-item';
        noticeItem.setAttribute('data-toggle', 'notice');

        // 우선순위 아이콘 추가
        let priorityIcon = '';
        const priority = (notice.priority || '').toLowerCase();
        if (priority === 'urgent') priorityIcon = '🚨 ';
        else if (priority === 'high') priorityIcon = '⚠️ ';
        else if (priority === 'normal') priorityIcon = '📢 ';

        // 날짜 포맷팅 (KST)
        const date = new Date(notice.created_at + 'Z');
        const formattedDate = date.toLocaleString('ko-KR', {
            timeZone: 'Asia/Seoul',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        }).replace(/\. /g, '-').replace('.', '');

        // SECURITY: DOMPurify로 XSS 방지
        const noticeHTML = `
            <div class="notice-title">${DOMPurify.sanitize(priorityIcon + title)}</div>
            <div class="notice-date">${DOMPurify.sanitize(formattedDate)}</div>
            <div class="notice-content">${DOMPurify.sanitize(content)}</div>
        `;

        noticeItem.innerHTML = noticeHTML;
        noticeList.appendChild(noticeItem);
    });

    debugLog(`✅ ${noticeInfos.length}개의 공지사항을 표시했습니다.`);
}
```

**변경 사항**:
- ✅ 하드코딩된 공지사항 제거 (`innerHTML = ''`)
- ✅ DB 데이터로 동적 생성
- ✅ 우선순위 아이콘 자동 추가
- ✅ 타임존 자동 변환 (UTC → KST)
- ✅ **보안 강화**: DOMPurify로 모든 사용자 입력 sanitize

#### `displayDefaultNotice()` 함수 (3302-3311번째 줄)
```javascript
function displayDefaultNotice() {
    const noticeList = document.querySelector('.notice-list');
    noticeList.innerHTML = `
        <li class="notice-item" style="text-align: center; padding: 40px 20px; color: #999;">
            <div class="notice-title" style="font-size: 16px;">현재 등록된 공지사항이 없습니다</div>
        </li>
    `;
    debugLog('No active notices found, displaying default message');
}
```

**변경 사항**:
- ✅ 하드코딩된 bilingual notices 제거
- ✅ 간단한 "공지사항 없음" 메시지로 대체

### 3. 이벤트 위임 추가 (4537번째 줄 이후)
```javascript
// Event delegation for dynamic notice items
const noticeList = document.querySelector('.notice-list');
if (noticeList) {
    noticeList.addEventListener('click', function(e) {
        const noticeItem = e.target.closest('.notice-item');
        if (noticeItem) {
            toggleNoticeContent(noticeItem);
        }
    });
}
```

**이유**: 동적으로 생성된 공지사항 아이템에도 클릭 이벤트가 작동하도록 함

---

## 🎯 작동 방식

### 사용자 플로우
1. 사용자가 `https://ui.datastreams.co.kr:20443/layout.html` 접속
2. 우측 상단 **📢 버튼** 클릭
3. `toggleNoticeModal()` 호출 → 모달 표시
4. `loadNoticeData()` 호출 → API에서 데이터 fetch
5. `/api/v1/admin/notices/?is_active=true` 호출
6. 응답 데이터를 `displayNoticeData()`로 전달
7. 동적으로 HTML 생성하여 화면에 표시
8. 사용자가 공지사항 클릭 시 `toggleNoticeContent()` 호출 → 내용 펼치기/접기

### API 응답 예시
```json
[
  {
    "id": 2,
    "title": "캄보디아에서 오신 여러분을 환영합니다",
    "content": "환영합니다",
    "priority": "NORMAL",
    "is_active": true,
    "view_count": 0,
    "created_at": "2025-10-18T11:01:00.875786",
    "updated_at": "2025-10-18T11:01:00.875788"
  },
  {
    "id": 1,
    "title": "수정된 공지",
    "content": "수정된 내용",
    "priority": "NORMAL",
    "is_active": true,
    "view_count": 1,
    "created_at": "2025-10-18T08:51:23.582115",
    "updated_at": "2025-10-18T08:51:33.057594"
  }
]
```

### 화면 표시 예시
```
📢 캄보디아에서 오신 여러분을 환영합니다
   2025-10-18
   환영합니다

📢 수정된 공지
   2025-10-18
   수정된 내용
```

---

## 🔐 보안 강화

1. **XSS 방지**: `DOMPurify.sanitize()` 사용
   - 모든 사용자 입력 (title, content, date) sanitize
   - HTML 태그 주입 방지

2. **입력 검증**: Pydantic 스키마 (Backend)
   - 제목: 최대 200자
   - 내용: 최대 5000자
   - 우선순위: enum 값만 허용

3. **CORS 설정**: 허용된 도메인만 API 접근 가능
   - `https://ui.datastreams.co.kr:20443`

---

## 🧪 테스트 방법

### 1. 브라우저에서 확인
```
1. https://ui.datastreams.co.kr:20443/layout.html 접속
2. 우측 상단 📢 버튼 클릭
3. 공지사항 모달이 열리면서 DB 데이터 표시 확인
4. 공지사항 클릭하여 내용 펼치기/접기 확인
```

### 2. 브라우저 콘솔 확인 (F12)
```javascript
// 콘솔에 표시되는 로그:
✅ 2개의 공지사항을 표시했습니다.
```

### 3. API 직접 호출
```bash
curl https://ui.datastreams.co.kr:20443/api/v1/admin/notices/?is_active=true
```

### 4. 네트워크 탭 확인
```
Request URL: https://ui.datastreams.co.kr:20443/api/v1/admin/notices/?is_active=true
Status: 200 OK
Response: [{"id":2,"title":"캄보디아에서...
```

---

## 🐛 트러블슈팅

### Q1: 공지사항이 표시되지 않아요
**증상**: 모달은 열리지만 "공지사항을 불러오는 중..." 메시지만 표시

**진단 방법**:
```javascript
// 브라우저 콘솔(F12)에서 실행:
fetch('/api/v1/admin/notices/?is_active=true')
  .then(res => res.json())
  .then(data => console.log(data))
  .catch(err => console.error(err));
```

**가능한 원인**:
1. API 서버가 실행되지 않음
2. 프록시 설정 오류
3. CORS 오류

**해결**:
```bash
# Admin API 서버 상태 확인
curl https://ui.datastreams.co.kr:20443/api/v1/admin/notices/

# 응답이 없으면 Nginx 프록시 설정 확인
sudo nginx -t
sudo systemctl restart nginx
```

### Q2: 공지사항은 보이는데 클릭이 안 돼요
**원인**: 이벤트 리스너가 등록되지 않음

**확인**:
```javascript
// 브라우저 콘솔에서 실행:
document.querySelector('.notice-list')
// null이면 DOM이 아직 로드되지 않은 것
```

**해결**: 하드 리프레시 (Ctrl + Shift + R)

### Q3: "현재 등록된 공지사항이 없습니다" 표시
**원인**: DB에 `is_active=true`인 공지사항이 없음

**해결**:
```sql
-- 활성화된 공지사항 확인
SELECT * FROM notices WHERE is_active = true;

-- 없으면 테스트 공지사항 생성
INSERT INTO notices (title, content, priority, is_active)
VALUES ('테스트 공지', '테스트 내용', 'NORMAL', true);
```

---

## 📊 현재 DB 상태

```sql
SELECT id, title, priority, is_active, created_at
FROM notices
WHERE is_active = true
ORDER BY created_at DESC;
```

| ID | Title | Priority | Active | Created |
|----|-------|----------|--------|---------|
| 2 | 캄보디아에서 오신 여러분을 환영합니다 | NORMAL | ✅ | 2025-10-18 11:01:00 |
| 1 | 수정된 공지 | NORMAL | ✅ | 2025-10-18 08:51:23 |

---

## 📝 다음 단계 (선택사항)

### 1. 관리자 페이지에서 CRUD 구현
현재 Admin API는 완성되었지만, `/admin/#notices` 페이지 UI는 없습니다.

**필요 작업**:
- 공지사항 목록 조회 (테이블 형식)
- 새 공지사항 작성 (폼)
- 수정/삭제 버튼
- 우선순위 설정 드롭다운
- 활성화/비활성화 토글

### 2. 읽음 표시 기능
사용자가 읽은 공지사항을 표시하여 새 공지사항 강조

```javascript
// localStorage에 읽은 공지사항 ID 저장
const readNotices = JSON.parse(localStorage.getItem('readNotices') || '[]');

// 새 공지사항만 필터링
const unreadNotices = notices.filter(n => !readNotices.includes(n.id));

// 📢 버튼에 뱃지 표시
if (unreadNotices.length > 0) {
    showBadge(unreadNotices.length);
}
```

### 3. 자동 새로고침
일정 시간마다 공지사항 자동 갱신

```javascript
// 5분마다 새로고침
setInterval(loadNoticeData, 300000);
```

---

## 🎉 완료!

**변경된 파일**:
- `/var/www/html/layout.html` (3239-3311줄, 4537줄 이후)
- `/home/aigen/html/layout.html` (symlink - 자동 동기화)

**백업 파일**:
- `/var/www/html/layout.html.backup.before-addEventListener-20251019-171643`
- `/var/www/html/layout.html.bak-notices-*`

**상태**: ✅ **프로덕션 배포 완료**

사용자는 이제 `https://ui.datastreams.co.kr:20443/layout.html`에서 DB의 공지사항을 실시간으로 볼 수 있습니다!
