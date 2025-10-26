# /exGenBotDS/ai 경로 디버깅 로그

**날짜**: 2025-10-25
**서버**: 1.215.235.250 (프론트 서버)

---

## 알아낸 정보

### 네트워크 구조
```
브라우저
  ↓ (ui.datastreams.co.kr:20443 입력)
  ↓ (실제로는 443 포트로 연결됨)
1.215.235.250:443 (프론트 서버) ← 현재 작업 중
  ↓
172.25.101.91 (백엔드 서버)
```

### 발견 사항
1. ✅ 브라우저는 **443 포트**로 연결 (ssl.conf 사용)
2. ✅ ssl_access_log에 로그 찍힘: `183.98.123.194 - - [25/Oct/2025:17:19:01 +0900] "GET /exGenBotDS/ai HTTP/1.1" 404 275`
3. ✅ access_log (20443)에는 로그 안 찍힌
4. ✅ 파일 존재: `/var/www/html/exGenBotDS/index.html`
5. ❌ 현재 상태: Spring Boot로 프록시됨 (`Content-Type: application/json`)

### 현재 ssl.conf 설정 (69-71번 줄)
```apache
ProxyPass /exGenBotDS/ai !
ProxyPass /exGenBotDS/ http://localhost:18180/exGenBotDS/
```

순서는 맞음. 제외 규칙이 먼저, 프록시 규칙이 나중.

### 현재 ssl.conf 설정 (47번 줄)
```apache
Alias /exGenBotDS /var/www/html/exGenBotDS
```

Alias도 있음.

---

## 의문점

### 왜 ProxyPass 제외 규칙이 작동하지 않는가?

**가능성 1**: trailing slash 문제
- `/exGenBotDS/ai` (제외 규칙)
- `/exGenBotDS/ai/` (실제 요청?)

**가능성 2**: ProxyPass보다 먼저 적용되는 다른 규칙
- RewriteRule?
- 다른 ProxyPass?

**가능성 3**: 설정이 실제로 적용되지 않음
- Apache 재시작 안 됨?
- 설정 파일 문법 오류?

**가능성 4**: VirtualHost 매칭 문제
- 다른 VirtualHost로 매칭?

---

## 다음 진단 단계

### 1단계: 로그 레벨 높여서 디버깅
```bash
# LogLevel 변경
sudo sed -i 's/^LogLevel .*/LogLevel proxy:trace5/' /etc/httpd/conf/httpd.conf
sudo systemctl restart httpd

# 요청 후 로그 확인
curl https://localhost:443/exGenBotDS/ai -k
sudo grep -i "proxy" /var/log/httpd/error_log | tail -20
```

### 2단계: 실제 매칭되는 규칙 확인
```bash
# Apache가 실제로 어떤 설정을 읽고 있는지 확인
sudo httpd -t -D DUMP_RUN_CFG | grep -i proxy | grep -i exgenbot
```

### 3단계: ProxyPass 제외 규칙 테스트
```bash
# 간단한 테스트 경로로 확인
echo "test" | sudo tee /var/www/html/test.html
curl https://localhost:443/test.html -k  # 200이어야 함
```

---

## 최종 상태 (2025-10-25)
- ❌ /exGenBotDS/ai 경로 구현 실패 (보류)
- ✅ /testOld 정상 작동 유지
- ✅ /api/chat/ 경로 추가 성공 (layout.html ↔ admin 연결)

## 실패 원인
```apache
ProxyPass /exGenBotDS/ http://localhost:18180/exGenBotDS/
```
이 광범위한 프록시 규칙이:
- /exGenBotDS/ai → Spring Boot로 프록시 (원하지 않음)
- /exGenBotDS/testOld → Spring Boot로 프록시 (필요함)
- /exGenBotDS/assets/* → Spring Boot로 프록시 (문제!)

**ProxyPass 제외 규칙 시도**:
```apache
ProxyPass /exGenBotDS/ai !
```
→ `/ai`는 Apache가 서빙하지만, `/testOld`의 정적 리소스(로고)도 Apache로 가서 깨짐

## 결론
- `/exGenBotDS/` 전체 구조 변경 없이는 `/ai` 경로만 분리 불가
- Spring Boot 애플리케이션이 `/exGenBotDS/` 하위의 정적 리소스도 서빙하는 구조
- 변경 시 `/testOld` 영향 불가피

## 대안 (미시도)
1. 완전히 다른 경로 사용: `/ai-chat/` (기존 경로 건드리지 않음)
2. 별도 도메인/포트 사용
3. Spring Boot 애플리케이션 수정 (백엔드 변경 필요)
