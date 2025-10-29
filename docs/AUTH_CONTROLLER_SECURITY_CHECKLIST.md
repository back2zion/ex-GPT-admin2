# AuthController 보안 체크리스트

**작성일**: 2025-10-28
**작성자**: Claude
**대상**: Spring Boot AuthController

---

## 현재 구현 상태

### ✅ 구현됨
1. **세션 검증**: HttpSession을 통한 기본 세션 확인
2. **사용자 정보 반환**: user_id, roles, department, email
3. **디버깅 엔드포인트**: /api/auth/session-info

### ❌ 미구현 (보안 강화 필요)

#### 1. XSS (Cross-Site Scripting) 방지
**위험도**: HIGH
**현재 상태**: 세션 속성 값을 그대로 반환 (sanitization 없음)

```java
// 현재 코드
response.put("user_id", userIdObj.toString());  // ❌ XSS 가능

// 개선 필요
response.put("user_id", StringEscapeUtils.escapeHtml4(userIdObj.toString()));
```

**조치 필요**:
- Apache Commons Text 의존성 추가
- 모든 사용자 입력값에 HTML escape 적용

#### 2. Rate Limiting
**위험도**: MEDIUM
**현재 상태**: 무제한 요청 허용

**조치 필요**:
- Spring Boot Bucket4j 또는 Resilience4j 도입
- IP당 1분에 60회 제한 권장

#### 3. CSRF 토큰 검증
**위험도**: MEDIUM  
**현재 상태**: GET 엔드포인트라서 CSRF 위험 낮음

**조치 필요**:
- POST 엔드포인트 추가 시 CSRF 토큰 검증 필수

#### 4. 로깅
**위험도**: LOW (보안보다는 모니터링)
**현재 상태**: DEBUG 레벨 로그만 있음

**조치 필요**:
```java
logger.info("Session validation: userId={}, sessionId={}", userId, session.getId());
logger.warn("Invalid session attempt: sessionId={}", session.getId());
```

#### 5. 에러 정보 노출
**위험도**: LOW
**현재 상태**: "No active session" 같은 명확한 에러 메시지 반환

**조치 필요**:
- 프로덕션에서는 일반적인 에러 메시지 사용
- 상세 정보는 로그에만 기록

---

## 테스트 필요 항목

### 1. 단위 테스트 (JUnit)
```java
@Test
public void testValidateSession_NoSession() {
    // Given: 세션 없음
    // When: validateSession 호출
    // Then: authenticated=false
}

@Test
public void testValidateSession_ValidSession() {
    // Given: 유효한 세션
    // When: validateSession 호출
    // Then: authenticated=true, user_id 반환
}

@Test
public void testValidateSession_XSSAttack() {
    // Given: XSS 코드가 포함된 세션 속성
    // When: validateSession 호출
    // Then: HTML escape된 값 반환
}
```

### 2. 통합 테스트
- FastAPI → Spring Boot 인증 플로우
- 세션 만료 시나리오
- 동시 요청 처리

---

## 유지보수 가이드

### 패치 배포 프로세스

1. **컴파일**:
```bash
cd /tmp/spring-auth-controller
javac -cp "/home/aigen/apache-tomcat-10.1.43/webapps/exGenBotDS/WEB-INF/lib/*" \
  -d . co/kr/wisenut/auth/controller/AuthController.java
```

2. **배포**:
```bash
cp -r /tmp/spring-auth-controller/co/kr/wisenut/auth \
  /home/aigen/apache-tomcat-10.1.43/webapps/exGenBotDS/WEB-INF/classes/co/kr/wisenut/
```

3. **Tomcat 재시작**:
```bash
/home/aigen/apache-tomcat-10.1.43/bin/shutdown.sh
sleep 5
/home/aigen/apache-tomcat-10.1.43/bin/startup.sh
```

4. **검증**:
```bash
curl http://localhost:18180/exGenBotDS/api/auth/validate
# 응답 확인
```

### 백업
- 매 배포 전 기존 .class 파일 백업
- 위치: `/home/aigen/patch/YYYYMMDD/auth-controller-backup/`

---

## 모니터링

### 로그 위치
- Tomcat: `/home/aigen/apache-tomcat-10.1.43/logs/catalina.out`
- FastAPI: `docker logs admin-api-admin-api-1`

### 모니터링 지표
- 세션 검증 실패율
- 응답 시간
- 에러 발생률

---

**참고 문서**:
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Spring Security Best Practices](https://spring.io/guides/topicals/spring-security-architecture/)
