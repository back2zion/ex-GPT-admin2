# RFP 요구사항 준수 현황 체크리스트

**검토일**: 2025-10-22
**검토자**: Claude Code
**검토 대상**: http://localhost:8010/admin#/ 및 하위 메뉴들

---

## FUN-002: 생성형AI 활용 관리도구 기능개선 ⭐ 핵심 요구사항

### 1. 레거시 시스템과 DB 연계를 통한 제·개정 문서 확인 기능 개발

#### 요구사항
- 법령, 사규, 업무기준 등 변동 시 관리자 확인 기능 추가
- 제·개정된 문서는 변동된 부분만 전처리에 자동 반영

#### 현재 구현 상태
❌ **미구현**

#### 필요한 구현
**백엔드**:
```
- [ ] 레거시 DB 연결 설정 (PostgreSQL/Oracle)
- [ ] 스케줄러: 1시간 간격으로 변경 감지
- [ ] 문서 변경 감지 로직
- [ ] 변경 전/후 diff 비교
- [ ] 관리자 승인 워크플로우 API
- [ ] 승인 시 벡터 DB 자동 업데이트
```

**프론트엔드**:
```
- [ ] 변경 문서 목록 페이지
- [ ] 변경 내역 비교 뷰 (diff view)
- [ ] 승인/반려 버튼
- [ ] 승인 이력 조회
```

**API 엔드포인트 (필요)**:
```
GET  /api/v1/admin/legacy-sync/detect-changes
GET  /api/v1/admin/legacy-sync/pending-approvals
GET  /api/v1/admin/legacy-sync/{id}/diff
POST /api/v1/admin/legacy-sync/{id}/approve
POST /api/v1/admin/legacy-sync/{id}/reject
GET  /api/v1/admin/legacy-sync/history
```

---

### 2. 서비스 평가 및 개선을 위한 사용 이력 관리

#### 요구사항
- 질문/답변/시각 등 사용 이력 관리

#### 현재 구현 상태
✅ **구현 완료**

**구현된 기능**:
- [x] 대화내역 조회 페이지 (`/conversations`)
- [x] 날짜 범위 필터링
- [x] 대분류/소분류 필터
- [x] 상세보기 (질문/답변/thinking/참조문서)
- [x] 엑셀 다운로드
- [x] 페이지네이션

**개선 필요 사항**:
⚠️ **날짜 필터에 캘린더 UI 없음**
- 현재: `<TextField type="date">` 사용 (브라우저 기본 캘린더)
- 개선: Material-UI DatePicker 또는 react-datepicker 적용 권장

---

### 3. 접근 가능 문서 권한 관리

#### 요구사항
- 부서별, 결재라인별 등 접근 가능 문서 권한 관리

#### 현재 구현 상태
🟡 **부분 구현**

**구현된 기능**:
- [x] 부서 관리 (삭제됨 - 사용자 관리로 통합)
- [x] 사용자 관리 (`/users`)
- [x] 문서 권한 관리 (`/document-permissions`)
- [x] 결재라인 관리 (`/approval-lines`)

**백엔드 API**:
- [x] `/api/v1/admin/departments/` (기능 있음)
- [x] `/api/v1/admin/users/` (기능 있음)
- [x] `/api/v1/admin/document-permissions/` (기능 있음)
- [x] `/api/v1/admin/approval-lines/` (기능 있음)

**미구현/개선 필요**:
```
- [ ] 부서별 학습데이터 참조 범위 지정 기능
      예: 국가계약법 → 전부서 참조, 야생동물보호법 → 품질환경처만 참조
- [ ] 실제 문서 접근 권한 검증 로직
- [ ] 권한 적용 테스트
```

---

### 4. 이용만족도 조사 기능

#### 현재 구현 상태
✅ **구현 완료**

**구현된 기능**:
- [x] 만족도 조사 페이지 (`/satisfaction`)
- [x] 만족도 목록 조회
- [x] 필터링 (rating, category, user_id)
- [x] 페이지네이션

**백엔드 API**:
- [x] `GET /api/v1/admin/satisfaction/`
- [x] `GET /api/v1/admin/satisfaction/{id}`

---

### 5. 공지메시지 표출 기능

#### 현재 구현 상태
✅ **구현 완료**

**구현된 기능**:
- [x] 공지사항 관리 페이지 (`/notices`)
- [x] 공지사항 목록 조회
- [x] 공지사항 생성/수정/삭제
- [x] 우선순위 관리
- [x] 활성화/비활성화

**백엔드 API**:
- [x] `GET /api/v1/admin/notices`
- [x] `GET /api/v1/admin/notices/{id}`
- [x] `POST /api/v1/admin/notices`
- [x] `PUT /api/v1/admin/notices/{id}`
- [x] `DELETE /api/v1/admin/notices/{id}`

---

## FUN-003: 학습데이터 갱신 및 추가

### 1. 학습데이터 관리 기능

#### 요구사항
- 법령, 사규, 규정, 매뉴얼, 지침, 각종 보고서 등 학습데이터 관리

#### 현재 구현 상태
✅ **프론트엔드 구현 완료** / ❌ **백엔드 일부 미구현**

**프론트엔드 구현**:
- [x] 대상 문서관리 페이지 (`/vector-data/documents`)
- [x] 수집대상 필터 (법령, 업무가이드, 업무기준, 지침, 사규, 노동조합, 일반사항, 참고자료)
- [x] 카테고리별 통계 (9개 카테고리, 건수 표시)
- [x] 문서 등록 모달 (카테고리 선택, 경로 선택, 파일 업로드)
- [x] 카테고리 생성 모달 (패시징 패턴 설정)
- [x] 문서 목록 테이블 (번호, 대분류, 파일명, 상태, 벡터화, 청크수, 삭제, 등록일)
- [x] 엑셀 다운로드
- [x] 페이지네이션

**백엔드 API (필요)**:
```
❌ 미구현:
- [ ] POST /api/v1/admin/vector-data/documents (문서 업로드)
- [ ] POST /api/v1/admin/vector-data/categories (카테고리 생성)
- [ ] GET  /api/v1/admin/vector-data/documents (문서 목록)
- [ ] GET  /api/v1/admin/vector-data/statistics (카테고리별 통계)
- [ ] DELETE /api/v1/admin/vector-data/documents/{id} (문서 삭제)
- [ ] POST /api/v1/admin/vector-data/folders (폴더 생성)
```

---

### 2. 사전 관리 기능

#### 요구사항
- 동의어사전, 사용자사전 관리

#### 현재 구현 상태
✅ **프론트엔드 구현 완료** / ❌ **백엔드 미구현**

**프론트엔드 구현**:
- [x] 사전관리 페이지 (`/vector-data/dictionaries`)
- [x] 사전 목록 조회
- [x] 사전 종류 필터 (동의어사전, 사용자사전)
- [x] 검색 (전체, 사전명, 사전 설명)
- [x] 사전 추가/수정/삭제
- [x] 동기화 기능
- [x] 페이지네이션

**백엔드 API (필요)**:
```
❌ 미구현:
- [ ] GET  /api/v1/admin/dictionaries (사전 목록)
- [ ] POST /api/v1/admin/dictionaries (사전 추가)
- [ ] PUT  /api/v1/admin/dictionaries/{id} (사전 수정)
- [ ] DELETE /api/v1/admin/dictionaries/{id} (사전 삭제)
- [ ] POST /api/v1/admin/dictionaries/sync (동기화)
```

---

### 3. 전처리 데이터 개인정보 유무 검출

#### 요구사항
- 개인정보 의심 데이터가 포함된 원본 문서 목록
- 검출된 데이터의 관리자 확인

#### 현재 구현 상태
🟡 **백엔드 부분 구현** / ❌ **프론트엔드 미구현**

**백엔드 구현**:
- [x] PII 검출기 (`app/services/pii_detector.py`)
- [x] 테스트 코드 (`tests/test_pii_detection.py`)
- [x] 주민등록번호, 전화번호, 이메일, 주소, 신용카드 패턴 감지
- [x] 마스킹 기능

**프론트엔드 (필요)**:
```
❌ 미구현:
- [ ] PII 검출 결과 목록 페이지
- [ ] 검출된 개인정보 상세 뷰
- [ ] 관리자 승인/마스킹 처리
```

**백엔드 API (필요)**:
```
❌ 미구현:
- [ ] GET  /api/v1/admin/pii-detections (PII 검출 목록)
- [ ] GET  /api/v1/admin/pii-detections/{id} (상세 조회)
- [ ] POST /api/v1/admin/pii-detections/{id}/approve (승인)
- [ ] POST /api/v1/admin/pii-detections/{id}/mask (마스킹)
```

---

## 부가서비스 관리

### 1. 버전관리

#### 현재 구현 상태
✅ **프론트엔드 구현 완료** / ❌ **백엔드 미구현**

**프론트엔드**:
- [x] 버전관리 페이지 (`/services/version`)
- [x] 버전 입력 (현재 1.5)
- [x] 버전수정 버튼

**백엔드 API (필요)**:
```
❌ 미구현:
- [ ] GET  /api/v1/admin/version (현재 버전 조회)
- [ ] PUT  /api/v1/admin/version (버전 수정)
- [ ] GET  /api/v1/admin/version/history (버전 이력)
```

---

### 2. 오류신고관리

#### 현재 구현 상태
✅ **프론트엔드 구현 완료** / ❌ **백엔드 미구현**

**프론트엔드**:
- [x] 오류신고관리 페이지 (`/services/error-reports`)
- [x] 기간 선택 (시작일/종료일)
- [x] 검색 타입 (전체, 작성자, 신고내용)
- [x] 검색창
- [x] 테이블 (번호, 메뉴명, 신고내용, 이름, 일자)
- [x] 엑셀 다운로드
- [x] 페이지네이션

⚠️ **날짜 선택: 브라우저 기본 캘린더 사용 중**
- 개선 권장: Material-UI DatePicker

**백엔드 API (필요)**:
```
❌ 미구현:
- [ ] GET  /api/v1/admin/error-reports (오류신고 목록)
- [ ] GET  /api/v1/admin/error-reports/{id} (상세 조회)
- [ ] POST /api/v1/admin/error-reports (오류신고 등록)
- [ ] DELETE /api/v1/admin/error-reports/{id} (삭제)
```

---

### 3. 추천질문관리

#### 현재 구현 상태
✅ **프론트엔드 구현 완료** / ❌ **백엔드 미구현**

**프론트엔드**:
- [x] 추천질문관리 페이지 (`/services/recommended-questions`)
- [x] 등록 모달 (질문 입력, 노출 여부 체크박스)
- [x] 테이블 (체크박스, 번호, 제목, 사용, 일자)
- [x] 삭제 버튼
- [x] 엑셀 다운로드
- [x] 페이지네이션

**백엔드 API (필요)**:
```
❌ 미구현:
- [ ] GET  /api/v1/admin/recommended-questions (목록 조회)
- [ ] POST /api/v1/admin/recommended-questions (등록)
- [ ] PUT  /api/v1/admin/recommended-questions/{id} (수정)
- [ ] DELETE /api/v1/admin/recommended-questions (일괄 삭제)
```

---

## STT 음성 전사 시스템

#### 현재 구현 상태
✅ **구현 완료**

**프론트엔드**:
- [x] STT 음성 전사 페이지 (`/stt-batches`)

**백엔드**:
- [x] `GET /api/v1/admin/stt-batches`
- [x] `POST /api/v1/admin/stt-batches`
- [x] 배치 생성 시 자동으로 오디오 파일 개수 카운트
- [x] Windows 폴더 업로드 API

---

## 통계 및 대시보드

#### 현재 구현 상태
✅ **구현 완료** (인증 헤더 수정 완료)

**프론트엔드**:
- [x] 메인 대시보드 (`/`)
- [x] 통계 대시보드 (`/dashboard`)
- [x] ex-GPT 통계 (`/stats/exgpt`)
- [x] 서버 통계 (`/stats/server`)

**백엔드**:
- [x] `GET /api/v1/admin/stats/dashboard`
- [x] `GET /api/v1/admin/stats/daily-trend`
- [x] `GET /api/v1/admin/stats/weekly-trend`
- [x] `GET /api/v1/admin/stats/monthly-trend`
- [x] `GET /api/v1/admin/stats/hourly-pattern`
- [x] `GET /api/v1/admin/stats/system`

---

## 📅 날짜 관련 UI 개선 필요 (캘린더 기능)

### 현재 상태
모든 날짜 입력 필드에서 `<TextField type="date">` 사용 중
- 브라우저 기본 캘린더 제공
- UI/UX가 일관성 없음

### 개선 권장 페이지

#### 1. 대화내역 페이지 (`/conversations`)
```
현재: <TextField type="date" />
개선: <DatePicker /> (Material-UI 또는 react-datepicker)
```

#### 2. 오류신고관리 (`/services/error-reports`)
```
현재: <TextField type="date" label="시작일" />
      <TextField type="date" label="종료일" />
개선: <DateRangePicker /> 사용 권장
```

#### 3. 접근승인관리 (`/users` 탭2)
```
현재: <TextField type="date" label="시작일" />
      <TextField type="date" label="종료일" />
개선: <DateRangePicker />
```

### 구현 방법

**Option 1: Material-UI DatePicker (권장)**
```bash
npm install @mui/x-date-pickers
npm install dayjs
```

```javascript
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';

<LocalizationProvider dateAdapter={AdapterDayjs}>
  <DatePicker
    label="시작일"
    value={startDate}
    onChange={(newValue) => setStartDate(newValue)}
  />
</LocalizationProvider>
```

**Option 2: react-datepicker**
```bash
npm install react-datepicker
```

---

## 🔴 미구현 백엔드 API 전체 목록

### 레거시 시스템 연계 (최우선 - RFP 핵심)
```python
# /api/v1/admin/legacy-sync/
GET  /detect-changes              # 변경 문서 감지
GET  /pending-approvals           # 승인 대기 목록
GET  /{id}/diff                   # 변경 전후 비교
POST /{id}/approve                # 승인
POST /{id}/reject                 # 반려
GET  /history                     # 이력 조회
```

### 학습데이터 관리
```python
# /api/v1/admin/vector-data/
POST /documents                   # 문서 업로드
POST /categories                  # 카테고리 생성
GET  /documents                   # 문서 목록
GET  /statistics                  # 통계
DELETE /documents/{id}            # 문서 삭제
POST /folders                     # 폴더 생성
```

### 사전 관리
```python
# /api/v1/admin/dictionaries/
GET    /                          # 목록 조회
POST   /                          # 추가
PUT    /{id}                      # 수정
DELETE /{id}                      # 삭제
POST   /sync                      # 동기화
```

### PII 검출 관리
```python
# /api/v1/admin/pii-detections/
GET  /                            # 목록 조회
GET  /{id}                        # 상세 조회
POST /{id}/approve                # 승인
POST /{id}/mask                   # 마스킹
```

### 버전 관리
```python
# /api/v1/admin/version/
GET  /                            # 현재 버전
PUT  /                            # 버전 수정
GET  /history                     # 버전 이력
```

### 오류신고 관리
```python
# /api/v1/admin/error-reports/
GET    /                          # 목록 조회
GET    /{id}                      # 상세 조회
POST   /                          # 등록
DELETE /{id}                      # 삭제
```

### 추천질문 관리
```python
# /api/v1/admin/recommended-questions/
GET    /                          # 목록 조회
POST   /                          # 등록
PUT    /{id}                      # 수정
DELETE /                          # 일괄 삭제 (body: ids[])
```

---

## ✅ 구현 완료된 기능

### 권한 관리
- [x] 사용자 관리 (`/users`)
- [x] 문서 권한 관리 (`/document-permissions`)
- [x] 결재라인 관리 (`/approval-lines`)

### 서비스 관리
- [x] 대화내역 조회 (`/conversations`)
- [x] 공지사항 (`/notices`)
- [x] 만족도 조사 (`/satisfaction`)

### 통계
- [x] 대시보드 (`/`)
- [x] 통계 대시보드 (`/dashboard`)
- [x] ex-GPT 통계 (`/stats/exgpt`)
- [x] 서버 통계 (`/stats/server`)

### STT
- [x] STT 음성 전사 (`/stt-batches`)
- [x] 파일 업로드 API
- [x] 자동 파일 개수 카운트

---

## 📊 RFP 준수율

### FUN-002 (관리도구 기능개선)
- **레거시 시스템 연계**: ❌ 0% (최우선 구현 필요)
- **사용 이력 관리**: ✅ 100% (완료)
- **문서 권한 관리**: 🟡 70% (부서별 학습데이터 범위 지정 미구현)
- **만족도 조사**: ✅ 100% (완료)
- **공지메시지**: ✅ 100% (완료)

**FUN-002 전체**: 🟡 **약 68%**

### FUN-003 (학습데이터 갱신)
- **학습데이터 관리 UI**: ✅ 100% (프론트엔드 완료)
- **학습데이터 관리 API**: ❌ 0% (백엔드 미구현)
- **사전 관리 UI**: ✅ 100% (프론트엔드 완료)
- **사전 관리 API**: ❌ 0% (백엔드 미구현)
- **PII 검출 로직**: ✅ 100% (백엔드 완료)
- **PII 검출 UI**: ❌ 0% (프론트엔드 미구현)

**FUN-003 전체**: 🟡 **약 33%**

---

## 🎯 우선순위별 구현 계획

### P0 (최우선 - RFP 핵심)
1. **레거시 시스템 연계** (FUN-002 핵심)
   - 백엔드 API 6개 엔드포인트
   - 프론트엔드 페이지 1개
   - 예상 소요: 3-5일

### P1 (높음)
2. **학습데이터 관리 백엔드** (FUN-003)
   - 문서 업로드/관리 API
   - 카테고리 관리 API
   - 예상 소요: 2-3일

3. **사전 관리 백엔드** (FUN-003)
   - 사전 CRUD API
   - 동기화 API
   - 예상 소요: 1-2일

### P2 (중간)
4. **PII 검출 관리 UI** (FUN-003)
   - 프론트엔드 페이지
   - 승인 워크플로우
   - 예상 소요: 1-2일

5. **부가서비스 백엔드**
   - 버전 관리 API
   - 오류신고 API
   - 추천질문 API
   - 예상 소요: 2-3일

### P3 (낮음)
6. **날짜 UI 개선**
   - DatePicker 라이브러리 적용
   - 모든 날짜 입력 필드 개선
   - 예상 소요: 1일

---

**총 예상 소요**: 10-16일
**RFP 핵심 요구사항 완료까지**: 3-5일 (레거시 시스템 연계)
