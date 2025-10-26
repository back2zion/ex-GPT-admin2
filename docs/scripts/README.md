# Apache 설정 스크립트 모음

**작성일**: 2025-10-25
**목적**: Apache ProxyPass 및 경로 설정 작업 중 생성된 스크립트

---

## ⚠️ 주의사항

이 스크립트들은 `/exGenBotDS/ai` 경로 설정 시도 과정에서 생성되었습니다.
**대부분 실패한 시도**이며, 참고용으로만 보관됩니다.

---

## 📁 스크립트 목록

### ❌ 실패한 시도

| 스크립트 | 목적 | 결과 |
|---------|------|------|
| `fix_ssl_path.sh` | SSL 인증서 경로 수정 | ❌ ssl.conf도 수정 필요했음 |
| `fix_all_ssl.sh` | 모든 SSL 설정 수정 | ⚠️ 부분 성공 |
| `fix_ssl_conf_proxypass.sh` | ssl.conf ProxyPass 수정 | ❌ /testOld 작동 중단 (치명적) |
| `exclude_ai_from_proxy.sh` | /ai 경로 ProxyPass 제외 | ❌ 효과 없음 |
| `add_exclude_to_ssl.sh` | ssl.conf에 제외 규칙 추가 | ❌ 여전히 프록시됨 |
| `setup_safe_ai_route.sh` | 안전한 /ai 경로 설정 (v1) | ❌ VirtualHost 충돌 |
| `setup_safe_ai_route_v2.sh` | 안전한 /ai 경로 설정 (v2) | ❌ 여전히 404 |
| `add_localhost_alias.sh` | localhost ServerAlias 추가 | ⚠️ 의미 없음 |

### ✅ 참고용 스크립트

| 스크립트 | 목적 | 비고 |
|---------|------|------|
| `fix_front_server.sh` | 프론트 서버 설정 (종합) | 미사용 (SSH 접근 불가) |
| `fix_port_20443.sh` | port-20443.conf 수정 | 초기 시도 |
| `fix_ssl_only.sh` | SSL 설정만 수정 | 부분 성공 |

---

## 🎓 교훈

### 실패 원인

```apache
# 이 광범위한 규칙이 문제였음
ProxyPass /exGenBotDS/ http://localhost:18180/exGenBotDS/
```

- `/exGenBotDS/` 하위 **모든 경로**를 Spring Boot로 프록시
- `/exGenBotDS/ai`만 제외하려 했으나, `/testOld`의 정적 리소스도 영향받음
- ProxyPass 제외 규칙 (`ProxyPass /exGenBotDS/ai !`)은 정확한 경로만 제외

### 성공 사례

**새 경로 추가**는 안전:

```apache
# 기존 설정 건드리지 않고 새 경로만 추가
ProxyPass /api/chat/ http://localhost:8010/api/chat/
ProxyPassReverse /api/chat/ http://localhost:8010/api/chat/
```

→ 성공! (SUCCESS_CHAT_API.md 참조)

---

## 🚫 사용 금지

**이 스크립트들을 실행하지 마세요!**

- 대부분 실패한 시도의 기록
- /testOld를 망가뜨릴 위험
- 참고 및 학습용으로만 사용

---

## 📚 관련 문서

- **[SUCCESS_CHAT_API.md](../SUCCESS_CHAT_API.md)** - 성공 사례
- **[FAILURE_LOG.md](../FAILURE_LOG.md)** - 실패 사례 정리
- **[AI_PATH_DEBUG.md](../AI_PATH_DEBUG.md)** - 디버깅 로그

---

**보관 이유**: 같은 실수 반복하지 않기 위해
