# 체크박스 및 이벤트 처리 실수 문서

## 날짜: 2025-10-24

## 문제 상황
사용자가 "체크박스/카드를 두 번 클릭해야 선택된다"는 문제를 보고했으나, 10번 이상의 수정 시도에도 해결하지 못함.

---

## 실수 1: MUI Checkbox의 onChange vs onClick 혼동

### ❌ 잘못된 시도들
```jsx
// 시도 1: stopPropagation 추가 (문제 악화)
<Checkbox
  checked={...}
  onClick={(e) => e.stopPropagation()}
  onChange={(e) => handleSelectOne(doc.id, e)}
/>

// 시도 2: onClick만 사용 (MUI 내부 동작 무시)
<Checkbox
  checked={...}
  onClick={() => handleSelectOne(doc.id)}
/>

// 시도 3: readOnly 사용 (완전히 작동 안함)
<Checkbox checked={...} readOnly />
```

### ✅ 올바른 해결책
```jsx
// 네이티브 HTML checkbox 사용
<input
  type="checkbox"
  id={`checkbox-${doc.id}`}
  checked={selectedItems.includes(doc.id)}
  onChange={() => handleSelectOne(doc.id)}
  style={{ width: '18px', height: '18px', cursor: 'pointer' }}
  aria-label={`Select row ${index + 1}`}
/>
```

### 교훈
1. **MUI Checkbox는 controlled component로 복잡한 내부 동작이 있음**
2. **onChange만 사용해야 하며, onClick이나 stopPropagation을 추가하면 안됨**
3. **문제가 계속되면 네이티브 HTML로 교체하는 것이 더 빠름**

---

## 실수 2: TableRow의 `selected` prop 간섭

### ❌ 잘못된 코드
```jsx
<TableRow
  key={doc.id}
  selected={selectedItems.includes(doc.id)}  // ← 클릭 이벤트 가로챔!
>
```

### ✅ 올바른 해결책
```jsx
<TableRow
  key={doc.id}
  sx={{
    bgcolor: isSelected ? 'rgba(0, 166, 81, 0.08)' : 'inherit'  // CSS로만 표시
  }}
>
```

### 교훈
**MUI TableRow의 `selected` prop은 자체 이벤트 핸들링을 추가하여 자식 요소의 클릭과 충돌함**

---

## 실수 3: useEffect 의존성 배열 누락

### ❌ 잘못된 코드
```jsx
useEffect(() => {
  loadDocuments();
}, [page, rowsPerPage]);  // categoryFilter, searchText 누락!

// 그래서 수동으로 호출 시도 (나쁜 패턴)
onClick={() => {
  setCategoryFilter(value);
  setTimeout(() => loadDocuments(), 0);  // ❌ 안티패턴
}}
```

### ✅ 올바른 해결책
```jsx
useEffect(() => {
  loadDocuments();
}, [page, rowsPerPage, categoryFilter, searchText]);  // 모든 의존성 추가

// onClick은 상태만 변경
onClick={() => {
  setCategoryFilter(value);
  setPage(1);
  // useEffect가 자동으로 loadDocuments 호출
}}
```

### 교훈
1. **useEffect 의존성 배열에 모든 관련 상태를 포함해야 함**
2. **setTimeout으로 수동 호출하는 것은 안티패턴**
3. **React는 선언적 프로그래밍 - 상태 변경하면 자동으로 처리되어야 함**

---

## 실수 4: Card와 CardContent 이벤트 충돌

### ❌ 잘못된 코드
```jsx
<Card onClick={() => setCategoryFilter(doctype)}>
  <CardContent>
    <Typography>...</Typography>  // ← 이것도 클릭 받음
  </CardContent>
</Card>
```

### ✅ 올바른 해결책
```jsx
<Card onClick={(e) => {
  e.stopPropagation();
  setCategoryFilter(doctype);
}}>
  <CardContent sx={{ pointerEvents: 'none' }}>  // ← 자식 클릭 차단
    <Typography>...</Typography>
  </CardContent>
</Card>
```

### 교훈
**MUI Card 내부의 CardContent, Typography 등이 클릭 이벤트를 받으므로 `pointerEvents: 'none'` 필요**

---

## 실수 5: 브라우저 캐시 문제로 오인

### 문제
사용자가 "안된다"고 했을 때, 브라우저 캐시 문제라고 계속 주장함.

### 실제 원인
코드 자체에 근본적인 문제가 있었음 (위의 1~4번 실수들).

### 교훈
1. **"브라우저 캐시 문제"라고 변명하기 전에 코드를 철저히 검증**
2. **버전 번호를 제목에 표시하여 실제로 새 버전이 로드되었는지 확인**
3. **console.log로 실제 이벤트가 발생하는지 먼저 확인**

---

## 실수 6: 과도한 이벤트 제어 (stopPropagation 남용)

### ❌ 잘못된 패턴
```jsx
<TableCell onClick={(e) => handleSelectOne(doc.id, e)}>
  <Checkbox
    onClick={(e) => e.stopPropagation()}  // ❌ 과도한 제어
    onChange={(e) => handleSelectOne(doc.id, e)}
  />
</TableCell>
```

### ✅ 올바른 패턴
```jsx
<TableCell padding="checkbox">
  <input
    type="checkbox"
    checked={...}
    onChange={() => handleSelectOne(doc.id)}  // 단순하게
  />
</TableCell>
```

### 교훈
**이벤트 처리를 복잡하게 만들수록 버그 발생 확률이 높아짐. 단순하게 유지할 것.**

---

## 반복하지 말아야 할 실수 체크리스트

### 체크박스 문제가 발생하면:
- [ ] MUI Checkbox 대신 네이티브 `<input type="checkbox">` 사용
- [ ] onChange만 사용, onClick/stopPropagation 사용 금지
- [ ] TableRow의 `selected` prop 제거, CSS로 시각 표시
- [ ] 부모 요소(TableCell)에 onClick 추가 금지

### 상태 변경 시 데이터 로딩이 안되면:
- [ ] useEffect 의존성 배열에 해당 상태 추가
- [ ] setTimeout으로 수동 호출하지 말 것
- [ ] onClick에서는 상태만 변경, useEffect가 자동 처리하도록

### 카드/버튼 클릭이 두 번 필요하면:
- [ ] 자식 요소에 `pointerEvents: 'none'` 추가
- [ ] onClick에 `e.stopPropagation()` 추가
- [ ] console.log로 이벤트가 몇 번 발생하는지 확인

### 사용자가 "안된다"고 하면:
- [ ] 브라우저 캐시 탓하지 말고 코드 재검증
- [ ] console.log 추가하여 실제 동작 확인
- [ ] 버전 번호를 UI에 표시하여 배포 확인
- [ ] 사용자에게 F12 개발자도구 콘솔 확인 요청

---

## 핵심 원칙

### 1. 단순성 (Simplicity)
복잡한 이벤트 처리는 버그의 온상. 가능한 단순하게.

### 2. React 표준 패턴 준수
- Controlled component는 value + onChange
- 상태 변경 → useEffect 자동 실행
- 수동 호출(setTimeout, 직접 함수 호출)은 안티패턴

### 3. MUI 컴포넌트 이해
- MUI 컴포넌트는 복잡한 내부 동작이 있음
- 문제가 계속되면 네이티브 HTML로 교체 고려
- MUI 공식 문서의 예제 패턴 따를 것

### 4. 디버깅 우선
- console.log로 실제 동작 확인
- 추측하지 말고 검증
- 사용자의 피드백을 진지하게 받아들일 것

---

## 이 문서의 목적

**같은 실수를 반복하지 않기 위해, 문제 발생 시 이 문서를 먼저 참고할 것.**
