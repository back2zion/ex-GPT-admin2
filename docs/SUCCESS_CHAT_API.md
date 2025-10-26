# ✅ 성공 사례: layout.html ↔ admin 연결

**날짜**: 2025-10-25
**서버**: 1.215.235.250 (프론트 서버)
**작업 시간**: 약 1시간

---

## 🎯 목표
`https://ui.datastreams.co.kr:20443/layout.html`에서 대화 목록을 `https://ui.datastreams.co.kr:20443/admin/#/conversations`와 공유

---

## 🔍 문제 진단

### 초기 증상
```javascript
// 브라우저 콘솔
GET https://ui.datastreams.co.kr:20443/api/chat/sessions?user_id=test_user 404 (Not Found)
PATCH https://ui.datastreams.co.kr:20443/api/chat/sessions/.../title 405 (Method Not Allowed)
```

### 원인 분석
1. ✅ API 엔드포인트는 존재: `http://localhost:8010/api/chat/sessions`
2. ❌ Apache ProxyPass 규칙이 없음
3. ❌ 브라우저에서 접근 불가

### 진단 과정
```bash
# 1. 직접 API 호출 테스트
curl -s http://localhost:8010/api/chat/sessions?user_id=test_user
# → 200 OK, JSON 응답 받음

# 2. 기존 ProxyPass 규칙 확인
grep "ProxyPass /api" /etc/httpd/conf.d/ssl.conf
# → /api/chat/ 경로 없음 발견

# 3. 브라우저가 443 포트로 연결 확인
tail -f /var/log/httpd/ssl_access_log
# → 183.98.123.194 로그 확인 (ssl.conf 사용)
```

---

## ✅ 해결 방법

### 1단계: 백업
```bash
sudo cp /etc/httpd/conf.d/ssl.conf \
  /etc/httpd/conf.d/ssl.conf.backup_chat_api_$(date +%Y%m%d_%H%M%S)
```

### 2단계: ProxyPass 규칙 추가
```bash
# /api/chat_stream 규칙 다음에 추가
sudo sed -i '/ProxyPass \/api\/chat_stream/a\
  ProxyPass /api/chat/ http://localhost:8010/api/chat/\
  ProxyPassReverse /api/chat/ http://localhost:8010/api/chat/' \
  /etc/httpd/conf.d/ssl.conf
```

**추가된 설정** (ssl.conf 79-81번 줄):
```apache
ProxyPass /api/chat_stream http://localhost:8010/api/chat_stream
ProxyPass /api/chat/ http://localhost:8010/api/chat/
ProxyPassReverse /api/chat/ http://localhost:8010/api/chat/
```

### 3단계: Apache 재시작
```bash
sudo httpd -t  # Syntax OK 확인
sudo systemctl restart httpd
```

### 4단계: 검증
```bash
# 서버 내부 테스트
curl -s "https://localhost:443/api/chat/sessions?user_id=test_user" -k | head -5
# → 200 OK, JSON 응답

# 브라우저 테스트
# https://ui.datastreams.co.kr:20443/layout.html
# → 404 에러 사라짐
# → 좌측 사이드바에 대화 목록 표시됨 ✅
```

---

## 📊 결과

### 성공 확인
- ✅ `/api/chat/sessions` → 200 OK
- ✅ layout.html 좌측 사이드바에 대화 목록 표시
- ✅ admin/#/conversations와 동일한 데이터 공유
- ✅ 기존 `/testOld` 기능 정상 작동 (영향 없음)

### 최종 ProxyPass 규칙 (ssl.conf)
```apache
# Admin API proxy
ProxyPass /api/v1/admin/ http://localhost:8010/api/v1/admin/
ProxyPassReverse /api/v1/admin/ http://localhost:8010/api/v1/admin/

# Satisfaction API proxy
ProxyPass /api/v1/satisfaction/ http://localhost:8010/api/v1/satisfaction/
ProxyPassReverse /api/v1/satisfaction/ http://localhost:8010/api/v1/satisfaction/

# Chat Stream API proxy
ProxyPass /api/chat_stream http://localhost:8010/api/chat_stream
ProxyPass /api/chat/ http://localhost:8010/api/chat/           # ← 추가됨
ProxyPassReverse /api/chat/ http://localhost:8010/api/chat/    # ← 추가됨
```

---

## 💡 핵심 교훈

### 진단 순서
1. **API 엔드포인트 확인** (서버 내부에서 curl)
2. **Apache 로그 확인** (어느 포트로 들어오는지)
3. **ProxyPass 규칙 확인** (누락된 경로 찾기)

### 안전한 작업 방법
1. ✅ **항상 백업** (롤백 가능하도록)
2. ✅ **최소 변경** (필요한 것만 추가)
3. ✅ **단계별 검증** (httpd -t, 재시작, 테스트)
4. ✅ **기존 기능 확인** (/testOld 정상 작동 확인)

### 문제 해결 패턴
```
API 404 에러
  ↓
서버 내부에서 curl 테스트
  ↓
정상 작동 확인
  ↓
ProxyPass 규칙 누락 발견
  ↓
규칙 추가
  ↓
✅ 해결
```

---

## 🔧 관련 파일

### 수정된 파일
- `/etc/httpd/conf.d/ssl.conf` (ProxyPass 규칙 추가)

### 백업 파일
- `/etc/httpd/conf.d/ssl.conf.backup_chat_api_20251025_*`

### 영향받는 페이지
- `https://ui.datastreams.co.kr:20443/layout.html` (사용자 UI)
- `https://ui.datastreams.co.kr:20443/admin/#/conversations` (관리자 UI)

---

## 📝 재현 방법

다른 서버나 환경에서 동일한 설정을 적용하려면:

```bash
# 1. ssl.conf 편집
sudo vim /etc/httpd/conf.d/ssl.conf

# 2. ProxyPass /api/chat_stream 다음에 추가
ProxyPass /api/chat/ http://localhost:8010/api/chat/
ProxyPassReverse /api/chat/ http://localhost:8010/api/chat/

# 3. 재시작
sudo httpd -t
sudo systemctl restart httpd

# 4. 테스트
curl -s "https://localhost:443/api/chat/sessions?user_id=test_user" -k
```

---

## ⚠️ 주의사항

### 롤백 방법
```bash
# 문제 발생 시
sudo cp /etc/httpd/conf.d/ssl.conf.backup_chat_api_* \
  /etc/httpd/conf.d/ssl.conf
sudo systemctl restart httpd
```

### ProxyPass 순서 중요
- ✅ **구체적 경로 먼저**: `/api/chat/sessions`
- ✅ **광범위 경로 나중**: `/api/chat/`
- ❌ **순서 바뀌면**: 광범위 규칙이 모든 요청 가로챔

---

## 🎉 성공 요인

1. **체계적 진단**: API 작동 여부부터 확인
2. **최소 변경**: 꼭 필요한 ProxyPass만 추가
3. **단계별 검증**: 각 단계마다 테스트
4. **안전 장치**: 백업 후 작업, httpd -t로 검증

---

**작성자**: Claude Code
**최종 업데이트**: 2025-10-25
