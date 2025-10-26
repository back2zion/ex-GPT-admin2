# /exGenBotDS/ai 구현 실패 사례 정리

**날짜**: 2025-10-25
**소요 시간**: 10시간+
**최종 상태**: 실패 - /testOld 기능 손상시킴

---

## ❌ 실패 사례

### 실패 1: SSL 인증서 경로 문제
**시도**: `/root/server.crt` 경로를 `/etc/pki/tls/certs/server.crt`로 변경
**결과**: port-20443.conf는 수정했으나 ssl.conf도 같은 문제 있었음
**교훈**: **모든 관련 설정 파일을 먼저 확인**해야 함

### 실패 2: ssl.conf ProxyPass 수정 (치명적 실패)
**시도**: ssl.conf의 `ProxyPass /exGenBotDS/` 규칙 수정
**결과**: ❌ **/testOld 작동 중단** - 로고가 안 뜸
**원인**: ssl.conf가 port 443뿐 아니라 **다른 포트에도 영향**을 미침
**교훈**: 
- ⚠️ **기존 작동 중인 설정 파일은 절대 수정하지 말 것**
- ⚠️ **영향 범위를 100% 확신하지 못하면 건드리지 말 것**
- ⚠️ **백업만으로는 부족 - 테스트 환경에서 먼저 검증 필요**

### 실패 3: VirtualHost 매칭 오해
**문제**: 
- `localhost:20443/ai` → 200 OK (React)
- `ui.datastreams.co.kr:20443/ai` → 404 (Spring Boot)

**원인 추정**: ServerName/ServerAlias 매칭 문제
**교훈**: localhost와 실제 도메인으로 **둘 다 테스트** 필요

---

## 🔴 절대 금지 사항

1. ❌ `/etc/httpd/conf.d/ssl.conf` 수정 금지
2. ❌ `/etc/httpd/conf.d/port-20443.conf` 수정 금지
3. ❌ 기존 ProxyPass 규칙 수정/삭제 금지
4. ❌ 작동 중인 설정에 대한 "추측" 금지
5. ❌ 백업 없이 설정 변경 금지

---

## ✅ 안전한 접근 방법 (새로운 시도 시)

### 원칙
1. **기존 파일은 절대 수정하지 않음**
2. **새로운 설정 파일만 추가**
3. **Include 또는 별도 conf 사용**
4. **testOld 먼저 테스트, ai 나중에 테스트**

### 안전한 방법 옵션

#### 옵션 1: 별도 conf 파일 생성
```bash
/etc/httpd/conf.d/exgenbot-ai.conf  (새 파일)
```
- 기존 파일 건드리지 않음
- 우선순위 설정으로 제어
- 실패 시 파일만 삭제하면 원복

#### 옵션 2: .htaccess 사용
```bash
/var/www/html/exGenBotDS/.htaccess
```
- Apache 설정 파일 건드리지 않음
- 디렉토리 레벨에서만 작동

#### 옵션 3: Nginx 프록시 추가
```
브라우저 → Nginx → Apache
```
- Apache 설정 전혀 건드리지 않음
- Nginx에서 라우팅만 처리

---

## 🎯 근본 원인 분석

### 왜 localhost는 되고 도메인은 안 될까?

**추정 원인**:
```apache
# port-20443.conf
<VirtualHost *:20443>
    ServerName ui.datastreams.co.kr:20443
    ServerAlias 172.25.101.91:20443
    # localhost는 여기에 매칭 안 됨!
```

**가능성**:
1. localhost로 접속 → 다른 VirtualHost (default?)가 응답
2. 도메인으로 접속 → port-20443.conf 또는 ssl.conf가 응답
3. 두 VirtualHost의 설정이 다름

**확인 필요**:
- `httpd -S` 출력에서 default VirtualHost 확인
- localhost 접속 시 어느 VirtualHost가 응답하는지 확인

---

## 📝 다음 시도 전 체크리스트

- [ ] /testOld 정상 작동 확인
- [ ] 백업 파일 생성
- [ ] localhost와 도메인 둘 다 테스트
- [ ] 영향 범위 100% 확인
- [ ] 새 파일만 생성 (기존 파일 수정 금지)
- [ ] 실패 시 롤백 계획 수립
- [ ] 사용자에게 "기존 작동 보장" 확인

---

## 🔧 현재 상태

**작동**:
- ✅ /testOld 정상 작동
- ✅ layout.html ↔ admin/#/conversations 연결 성공

**미작동**:
- ❌ /exGenBotDS/ai (보류 - /testOld에 영향 주는 문제로 중단)

**성공 사례**:
- ✅ `/api/chat/` ProxyPass 추가 성공 (`/home/aigen/SUCCESS_CHAT_API.md` 참조)

---

## 🎓 오늘 배운 교훈 (2025-10-25)

### 성공 패턴
1. **문제 진단 순서**:
   - ① 서버 내부에서 API 직접 호출 (`curl localhost:PORT`)
   - ② Apache 로그로 어느 포트로 요청 들어오는지 확인
   - ③ ProxyPass 규칙 확인

2. **안전한 변경**:
   - ✅ 백업 먼저
   - ✅ 최소 변경 (꼭 필요한 것만)
   - ✅ `httpd -t`로 문법 검증
   - ✅ 재시작 후 즉시 테스트

3. **ProxyPass 규칙**:
   - ✅ 구체적 경로가 우선순위 높음
   - ✅ `/api/chat/sessions` → `/api/chat/` 순서
   - ❌ 광범위한 규칙 (`/exGenBotDS/`)은 위험

### 실패 원인 분석: /exGenBotDS/ai
```apache
# 이 규칙이 문제였음
ProxyPass /exGenBotDS/ http://localhost:18180/exGenBotDS/

# 이유:
# - /exGenBotDS/ai (React 정적 파일) → Spring Boot로 프록시됨
# - /exGenBotDS/assets/logo.png (로고) → Spring Boot로 프록시됨
# - /testOld도 영향받음 (로고가 안 뜸)
```

**해결 시도했으나 실패**:
- ProxyPass 제외 규칙 (`ProxyPass /exGenBotDS/ai !`) 추가 시
- `/testOld`의 정적 리소스(로고, CSS)도 Spring Boot로 못 가서 깨짐

**결론**: `/exGenBotDS/` 전체 프록시 구조를 바꾸지 않고는 `/ai` 경로만 분리 불가

---

**교훈**: 작동 중인 시스템은 성역이다. 절대 건드리지 말 것. 하지만 **새로운 경로 추가**는 안전하다.
