# 프론트 서버 (1.215.235.250) 설정 가이드

## 문제 상황
현재 백엔드 서버 (172.25.101.91)에는 `/exGenBotDS/ai` 경로 설정이 완료되었으나, 프론트 서버 (1.215.235.250)에는 아직 적용되지 않았습니다.

브라우저가 1.215.235.250에 연결하므로, 이 서버에도 동일한 설정을 적용해야 합니다.

## 네트워크 구조
```
브라우저
    ↓
1.215.235.250:20443 (프론트 서버) ← 여기에 설정 필요!
    ↓ (내부 프록시/라우팅)
172.25.101.91:20443 (백엔드 서버) ← 이미 설정 완료 ✅
```

## 설정 방법

### 1단계: 프론트 서버에 스크립트 복사

**방법 A: SCP 사용 (현재 서버에서)**
```bash
scp -P 20022 /home/aigen/fix_front_server.sh aigen@1.215.235.250:/home/aigen/
```

**방법 B: 직접 복사 (프론트 서버에서)**
1. 프론트 서버에 SSH 접속:
   ```bash
   ssh -p 20022 aigen@1.215.235.250
   ```

2. 스크립트 파일 생성:
   ```bash
   cat > /home/aigen/fix_front_server.sh << 'SCRIPT_END'
   [스크립트 내용 붙여넣기]
   SCRIPT_END
   chmod +x /home/aigen/fix_front_server.sh
   ```

### 2단계: 프론트 서버에서 스크립트 실행

1. 프론트 서버에 접속:
   ```bash
   ssh -p 20022 aigen@1.215.235.250
   ```

2. 스크립트 실행:
   ```bash
   sudo bash /home/aigen/fix_front_server.sh
   ```

### 3단계: 결과 확인

스크립트가 성공적으로 완료되면:
- ✅ `/testOld` 정상 작동 확인
- ✅ `/ai` 경로 설정 완료
- ✅ Apache 설정 테스트 및 reload 완료

브라우저에서 테스트:
```
https://ui.datastreams.co.kr:20443/exGenBotDS/ai
```

## 스크립트 동작 내용

이 스크립트는 다음을 수행합니다:

1. **안전 확인**: `/testOld` 정상 작동 확인
2. **백업**: 기존 설정 파일 백업
3. **설정 추가**:
   - `port-20443.conf`에 `ProxyPass /exGenBotDS/ai !` 추가
   - `ssl.conf`에 `ProxyPass /exGenBotDS/ai !` 추가 (파일 존재 시)
4. **검증**: Apache 설정 테스트
5. **적용**: Apache reload
6. **재확인**: `/testOld` 여전히 작동하는지 확인
7. **롤백**: 문제 발생 시 자동 롤백

## 문제 발생 시 롤백

스크립트가 자동으로 롤백하지 못한 경우:

```bash
# port-20443.conf 롤백
sudo cp /etc/httpd/conf.d/port-20443.conf.backup_ai_* /etc/httpd/conf.d/port-20443.conf

# ssl.conf 롤백 (있는 경우)
sudo cp /etc/httpd/conf.d/ssl.conf.backup_ai_* /etc/httpd/conf.d/ssl.conf

# Apache reload
sudo systemctl reload httpd
```

## 현재 상태 (2025-10-25 업데이트)

- **백엔드 서버 (172.25.101.91)**: N/A (프론트 서버로 작업 이동)

- **프론트 서버 (1.215.235.250)**:
  - ✅ `/api/chat/` ProxyPass 추가 완료
  - ✅ layout.html ↔ admin/#/conversations 연결 성공
  - ❌ `/exGenBotDS/ai` 경로는 보류 (기존 /testOld 영향으로 중단)

## 성공 사례

### /api/chat/ 경로 추가 (성공)
```bash
# ssl.conf에 추가
ProxyPass /api/chat/ http://localhost:8010/api/chat/
ProxyPassReverse /api/chat/ http://localhost:8010/api/chat/
```

**결과**:
- ✅ layout.html에서 대화 목록 로딩 성공
- ✅ admin 페이지와 데이터 공유
- ✅ 기존 기능 영향 없음

상세 내용: `/home/aigen/SUCCESS_CHAT_API.md` 참조

## 참고

- `/testOld` 경로는 **절대** 영향받지 않습니다
- 모든 변경사항은 백업되며 문제 시 자동 롤백됩니다
- 스크립트는 멱등성(idempotent)을 가지므로 여러 번 실행해도 안전합니다
