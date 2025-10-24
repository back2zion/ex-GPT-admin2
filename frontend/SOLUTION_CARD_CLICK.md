# ✅ 카드 클릭 문제 해결 - 최종 솔루션

## 날짜: 2025-10-24

## 문제 상황
사용자가 카테고리 카드를 클릭하면:
1. **두 번 클릭해야 선택됨**
2. **Select box에 선택이 표시 안됨**

---

## ✅ 최종 해결책

### 1. Card 이벤트 처리 (두 번 클릭 문제 해결)

#### ❌ 이전 코드 (문제)
```jsx
<Card onClick={() => {
  setCategoryFilter(doctype);
  setPage(1);
}}>
  <CardContent>
    <Typography>국회</Typography>
    <Typography>495건</Typography>
  </CardContent>
</Card>
```

**문제 원인:**
- `CardContent`와 그 안의 `Typography` 컴포넌트들이 **자체적으로 클릭 이벤트를 받음**
- Card의 onClick과 CardContent/Typography의 클릭 이벤트가 **충돌**
- 첫 번째 클릭은 Typography/CardContent가 가로채고, 두 번째 클릭에서 Card의 onClick 실행

#### ✅ 해결 코드
```jsx
<Card onClick={(e) => {
  e.stopPropagation();  // 다른 이벤트 차단
  setCategoryFilter(doctype);
  setPage(1);
}}>
  <CardContent sx={{ pointerEvents: 'none' }}>  {/* ← 핵심! 자식 클릭 차단 */}
    <Typography>국회</Typography>
    <Typography>495건</Typography>
  </CardContent>
</Card>
```

**해결 이유:**
1. `pointerEvents: 'none'`을 CardContent에 추가하여 **자식 요소의 모든 클릭 이벤트 차단**
2. 클릭이 CardContent를 통과하여 **Card의 onClick으로만 전달됨**
3. `e.stopPropagation()`으로 다른 부모 요소로의 전파도 차단
4. **결과: 한 번 클릭으로 즉시 작동**

---

### 2. Select Box 표시 문제 (분류명 안 보이는 문제 해결)

#### ❌ 이전 코드 (문제)
```jsx
<Select
  value={categoryFilter}  // value는 "DOC001" 같은 코드
  label="카테고리"
  onChange={(e) => {
    setCategoryFilter(e.target.value);
    setPage(1);
  }}
>
  <MenuItem value="">전체 ({stats.total.toLocaleString()}건)</MenuItem>
  <MenuItem value="DOC001">국회 (495건)</MenuItem>
</Select>
```

**문제 원인:**
- 카드 클릭 시 `categoryFilter`에 **코드 값 (예: "DOC001")** 이 저장됨
- MUI Select는 기본적으로 선택된 `value`에 해당하는 MenuItem의 children을 표시
- 하지만 카드에서 설정한 코드 값과 MenuItem의 value가 정확히 매칭되지 않거나
- MenuItem이 동적으로 생성되는 경우, Select가 올바른 MenuItem을 찾지 못함
- 결과: Select box에 **"DOC001"** 같은 코드가 표시되거나 **빈 값**으로 표시됨
- 사용자가 원하는 것: **"국회 (495건)"** 같은 분류명 표시

#### ✅ 해결 코드
```jsx
<Select
  value={categoryFilter}
  label="카테고리"
  onChange={(e) => {
    setCategoryFilter(e.target.value);
    setPage(1);
  }}
  renderValue={(selected) => {  // ← 핵심! 표시 값 명시적 지정
    if (selected === '') {
      return `전체 (${stats.total.toLocaleString()}건)`;
    }
    const category = categories.find(cat => cat.code === selected);
    const count = stats.by_doctype[selected]?.count || 0;
    return `${category?.name || selected} (${count.toLocaleString()}건)`;
  }}
>
  <MenuItem value="">전체 ({stats.total.toLocaleString()}건)</MenuItem>
  <MenuItem value="DOC001">국회 (495건)</MenuItem>
</Select>
```

**해결 이유:**
1. `renderValue` prop을 사용하여 **Select에 표시될 값을 명시적으로 지정**
2. `selected` 값(categoryFilter)은 코드("DOC001")이지만, **표시는 분류명("국회")으로 변환**
3. `categories.find(cat => cat.code === selected)`로 코드에서 이름 조회
4. `stats.by_doctype[selected]`로 건수 가져와서 함께 표시
5. **결과: 카드 클릭 시 "DOC001"이 아니라 "국회 (495건)"으로 정확히 표시**

---

## 핵심 개념

### 1. `pointerEvents: 'none'`
CSS 속성으로, **요소가 마우스 이벤트를 받지 않게 만듦**.

```jsx
<div onClick={handleClick}>
  <span style={{ pointerEvents: 'none' }}>클릭 안됨</span>
  <span>클릭 됨</span>
</div>
```

- 첫 번째 span 클릭 → 이벤트가 span을 통과하여 div의 onClick 실행
- 두 번째 span 클릭 → span이 이벤트를 받아서 div의 onClick 실행

**자식 요소가 많고 복잡할 때 매우 유용!**

### 2. MUI Select의 `renderValue`
Select에 표시되는 값을 **커스터마이즈**하는 prop.

```jsx
<Select
  value={selectedValue}
  renderValue={(value) => {
    // 여기서 반환한 내용이 Select에 표시됨
    return `커스텀 표시: ${value}`;
  }}
>
  <MenuItem value="a">옵션 A</MenuItem>
  <MenuItem value="b">옵션 B</MenuItem>
</Select>
```

**사용 시나리오:**
- MenuItem의 children이 아니라 다른 형식으로 표시하고 싶을 때
- value가 코드인데 이름으로 표시하고 싶을 때
- 추가 정보(건수, 아이콘 등)를 함께 표시하고 싶을 때

---

## 전체 흐름

### 카드 클릭 → Select 동기화

1. **사용자가 "국회" 카드 클릭**
2. Card의 onClick 실행 (CardContent는 pointerEvents: 'none'으로 무시)
3. `setCategoryFilter('DOC001')` 실행
4. React 상태 업데이트
5. Select의 `value` prop이 'DOC001'로 변경
6. Select의 `renderValue`가 실행되어 "국회 (495건)" 반환
7. **Select에 "국회 (495건)" 표시**
8. useEffect가 `categoryFilter` 변경 감지
9. `loadDocuments()` 자동 실행
10. **하단 테이블에 국회 문서만 필터링되어 표시**

---

## 체크리스트 - 다시 문제가 발생하면

### Card/Button 클릭이 두 번 필요하면:
- [ ] 자식 요소(CardContent, Typography 등)에 `pointerEvents: 'none'` 추가했는지?
- [ ] onClick에 `e.stopPropagation()` 추가했는지?
- [ ] console.log로 onClick이 몇 번 호출되는지 확인했는지?

### Select box에 분류명이 제대로 표시 안되면:
- [ ] `renderValue` prop을 사용해서 명시적으로 표시 값 지정했는지?
- [ ] value(코드)를 name(분류명)으로 변환하는 로직이 있는지?
- [ ] categories 배열에서 find()로 올바르게 찾고 있는지?
- [ ] MenuItem의 value와 Select의 value가 정확히 매칭되는지?

### 상태 변경 시 UI가 업데이트 안되면:
- [ ] useEffect 의존성 배열에 해당 상태가 포함되어 있는지?
- [ ] setState 후에 setTimeout으로 수동 호출하지 않는지? (안티패턴)
- [ ] React DevTools로 상태가 실제로 변경되는지 확인했는지?

---

## 참고: 비슷한 패턴

### MUI Card 클릭 처리 표준 패턴
```jsx
<Card
  onClick={(e) => {
    e.stopPropagation();
    handleCardClick(item.id);
  }}
  sx={{ cursor: 'pointer' }}
>
  <CardContent sx={{ pointerEvents: 'none' }}>
    {/* 모든 자식 컴포넌트 */}
  </CardContent>
</Card>
```

### MUI Select with Custom Display 표준 패턴
```jsx
<Select
  value={selectedId}
  renderValue={(id) => {
    const item = items.find(x => x.id === id);
    return item ? `${item.name} (${item.count})` : '';
  }}
>
  {items.map(item => (
    <MenuItem key={item.id} value={item.id}>
      {item.name} ({item.count})
    </MenuItem>
  ))}
</Select>
```

---

## 결론

**두 번 클릭 문제 (CardContent/Typography 이벤트 충돌):**
- `pointerEvents: 'none'`으로 자식 요소의 클릭 차단
- Card에만 onClick, 자식은 시각적 표현만 담당

**Select 표시 문제 (코드 vs 분류명):**
- `renderValue`로 표시 값을 명시적으로 지정
- value는 코드("DOC001"), 표시는 분류명("국회 (495건)")
- categories 배열에서 코드로 이름 조회하여 변환

**핵심 원칙: 간단하고 명확하게!**

---

## 요약

사용자가 카테고리 카드를 클릭하면:
1. **Card onClick** → `setCategoryFilter("DOC001")` 실행 (코드 저장)
2. **Select의 value** → "DOC001" (코드)
3. **Select의 renderValue** → "DOC001"을 받아서 "국회 (495건)"으로 변환
4. **사용자가 보는 것** → Select box에 "국회 (495건)" 표시 ✅

이렇게 **내부는 코드로 관리, 화면에는 분류명으로 표시**하는 것이 정답!
