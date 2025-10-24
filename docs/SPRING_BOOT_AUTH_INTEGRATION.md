# Spring Boot 인증 통합 가이드

FastAPI Admin Tool과 기존 Spring Boot 애플리케이션 간의 세션 기반 인증 통합 방법을 설명합니다.

## 개요

FastAPI Admin Tool은 기존 Spring Boot 애플리케이션의 JSESSIONID 쿠키를 사용하여 사용자 인증을 수행합니다. 이를 위해 Spring Boot에 세션 검증 API 엔드포인트를 추가해야 합니다.

## 아키텍처

```
┌──────────────┐       JSESSIONID       ┌──────────────────┐
│  Frontend    │─────────────────────>│  FastAPI Admin   │
│  (React)     │                       │  (Port 8010)     │
└──────────────┘                       └──────────────────┘
                                               │
                                               │ Validate Session
                                               ▼
                                       ┌──────────────────┐
                                       │  Spring Boot     │
                                       │  (Port 18180)    │
                                       │  /exGenBotDS     │
                                       └──────────────────┘
```

## Spring Boot 설정 정보

- **URL**: `http://localhost:18180/exGenBotDS`
- **서버**: Apache Tomcat 10.1.43
- **데이터베이스**: EDB PostgreSQL (Port 5444)
- **SSO 모드**: `ssoUse: false` (테스트 모드)

## 필요한 Spring Boot 코드 추가

### 1. AuthValidationController 생성

Spring Boot 프로젝트에 다음 컨트롤러를 추가하세요:

```java
package com.example.exgenbotds.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpStatus;

import javax.servlet.http.HttpSession;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/auth")
public class AuthValidationController {

    /**
     * 세션 검증 API
     *
     * FastAPI Admin Tool에서 호출하여 현재 사용자의 세션 유효성을 확인합니다.
     *
     * @param session HttpSession 객체 (자동 주입)
     * @return 사용자 정보 (user_id, roles, email, department 등)
     */
    @GetMapping("/validate")
    public ResponseEntity<Map<String, Object>> validateSession(HttpSession session) {
        // Spring Security Context에서 인증 정보 가져오기
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

        // 인증되지 않은 경우 또는 익명 사용자인 경우
        if (authentication == null || !authentication.isAuthenticated()
            || "anonymousUser".equals(authentication.getPrincipal())) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }

        // 세션 유효성 확인
        if (session == null || session.isNew()) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }

        // 사용자 정보 추출
        Map<String, Object> userInfo = new HashMap<>();

        // 사용자 ID (username)
        String userId = authentication.getName();
        userInfo.put("user_id", userId);
        userInfo.put("username", userId);

        // 권한(역할) 목록
        List<String> roles = authentication.getAuthorities().stream()
            .map(GrantedAuthority::getAuthority)
            .map(role -> role.replace("ROLE_", ""))  // "ROLE_ADMIN" -> "ADMIN"
            .collect(Collectors.toList());
        userInfo.put("roles", roles);

        // 세션에서 추가 정보 가져오기 (있는 경우)
        // 실제 구현에 맞게 수정 필요
        Object email = session.getAttribute("user_email");
        Object department = session.getAttribute("user_department");
        Object fullName = session.getAttribute("user_full_name");

        if (email != null) {
            userInfo.put("email", email);
        }
        if (department != null) {
            userInfo.put("department", department);
        }
        if (fullName != null) {
            userInfo.put("full_name", fullName);
        }

        // 세션 정보
        userInfo.put("session_id", session.getId());
        userInfo.put("session_created", session.getCreationTime());
        userInfo.put("session_last_accessed", session.getLastAccessedTime());

        return ResponseEntity.ok(userInfo);
    }

    /**
     * 현재 사용자 정보 조회 (선택 사항)
     */
    @GetMapping("/current-user")
    public ResponseEntity<Map<String, Object>> getCurrentUser() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

        if (authentication == null || !authentication.isAuthenticated()) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }

        Map<String, Object> userInfo = new HashMap<>();
        userInfo.put("user_id", authentication.getName());
        userInfo.put("roles", authentication.getAuthorities().stream()
            .map(GrantedAuthority::getAuthority)
            .collect(Collectors.toList()));

        return ResponseEntity.ok(userInfo);
    }
}
```

### 2. Spring Security 설정 업데이트

`SecurityConfig.java` (또는 해당 설정 파일)에 API 엔드포인트 접근 권한 추가:

```java
@Override
protected void configure(HttpSecurity http) throws Exception {
    http
        .authorizeRequests()
            // 세션 검증 API는 인증된 사용자만 접근 가능
            .antMatchers("/api/auth/validate").authenticated()
            .antMatchers("/api/auth/current-user").authenticated()
            // ... 기타 설정
        .and()
        .sessionManagement()
            .sessionCreationPolicy(SessionCreationPolicy.IF_REQUIRED)
            .maximumSessions(1)  // 동시 세션 제한 (필요시)
            .maxSessionsPreventsLogin(false);
}
```

### 3. CORS 설정 (필요시)

FastAPI가 다른 포트(8010)에서 실행되므로 CORS 설정 필요:

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins("http://localhost:8010", "https://ui.datastreams.co.kr")
            .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
            .allowedHeaders("*")
            .allowCredentials(true)  // 쿠키 허용
            .maxAge(3600);
    }
}
```

## API 응답 형식

### 성공 (200 OK)

```json
{
  "user_id": "admin",
  "username": "admin",
  "roles": ["ADMIN", "USER"],
  "email": "admin@example.com",
  "department": "engineering",
  "full_name": "관리자",
  "session_id": "A1B2C3D4E5F6...",
  "session_created": 1234567890000,
  "session_last_accessed": 1234567890000
}
```

### 인증 실패 (401 Unauthorized)

```
(빈 응답)
```

## FastAPI 측 설정

FastAPI는 이미 Spring Boot 세션 인증을 지원하도록 구현되어 있습니다:

### 파일 위치

- **미들웨어**: `/home/aigen/admin-api/app/middleware/spring_session_auth.py`
- **의존성**: `/home/aigen/admin-api/app/dependencies.py`

### 동작 방식

1. **요청 수신**: 사용자가 FastAPI API를 호출
2. **JSESSIONID 추출**: 쿠키에서 JSESSIONID 추출
3. **Spring Boot 검증**: `http://localhost:18180/exGenBotDS/api/auth/validate` 호출
4. **사용자 정보 변환**: Spring Boot 응답을 Cerbos Principal 객체로 변환
5. **권한 검증**: Cerbos를 통해 리소스별 권한 확인
6. **응답 반환**: API 요청 처리 및 응답

### 테스트 모드

개발 중에는 `X-Test-Auth` 헤더를 사용하여 인증 우회 가능:

```bash
# 테스트 사용자로 API 호출
curl -H "X-Test-Auth: admin" http://localhost:8010/api/v1/admin/dictionaries
```

## 통합 테스트

### 1. Spring Boot 엔드포인트 테스트

```bash
# 세션 없이 호출 (401 예상)
curl -v http://localhost:18180/exGenBotDS/api/auth/validate

# 유효한 JSESSIONID로 호출 (200 예상)
curl -v --cookie "JSESSIONID=YOUR_SESSION_ID" \
  http://localhost:18180/exGenBotDS/api/auth/validate
```

### 2. FastAPI 통합 테스트

```bash
# 1. Spring Boot 로그인하여 JSESSIONID 얻기
# (브라우저나 Postman 사용)

# 2. FastAPI API 호출
curl -v --cookie "JSESSIONID=YOUR_SESSION_ID" \
  http://localhost:8010/api/v1/admin/dictionaries
```

### 3. 프론트엔드 통합

React 프론트엔드는 자동으로 JSESSIONID 쿠키를 포함하여 요청:

```javascript
// axios 설정
axios.defaults.withCredentials = true;

// API 호출
const response = await axios.get('/api/v1/admin/dictionaries');
```

## 트러블슈팅

### 401 Unauthorized 오류

1. **Spring Boot 로그인 상태 확인**: 먼저 Spring Boot 애플리케이션에 로그인되어 있는지 확인
2. **JSESSIONID 쿠키 확인**: 브라우저 개발자 도구에서 쿠키 확인
3. **CORS 설정 확인**: Spring Boot의 CORS 설정에 FastAPI 도메인이 포함되어 있는지 확인
4. **세션 타임아웃**: 세션이 만료되었을 수 있음 (재로그인 필요)

### 500 Internal Server Error

1. **Spring Boot 로그 확인**: Tomcat 로그에서 예외 확인
2. **네트워크 연결**: FastAPI와 Spring Boot 간 네트워크 연결 확인
3. **포트 확인**: Spring Boot가 18180 포트에서 실행 중인지 확인

### CORS 오류

```
Access to XMLHttpRequest at 'http://localhost:8010/api/...' from origin 'http://localhost:18180'
has been blocked by CORS policy
```

**해결책**: Spring Boot의 CORS 설정에 FastAPI 도메인 추가

## 보안 고려사항

1. **HTTPS 사용**: 프로덕션에서는 반드시 HTTPS 사용
2. **Secure 쿠키**: JSESSIONID 쿠키에 `Secure`, `HttpOnly`, `SameSite` 플래그 설정
3. **세션 타임아웃**: 적절한 세션 타임아웃 설정 (30분 권장)
4. **CSRF 보호**: Spring Security CSRF 토큰 검증 활성화
5. **세션 고정 공격 방지**: 로그인 시 세션 ID 재생성

## 향후 개선사항

1. **Redis 세션 스토어**: 확장성을 위해 Redis 기반 세션 공유 고려
2. **JWT 토큰**: 무상태(stateless) 인증을 위한 JWT 도입 검토
3. **SSO 통합**: 엔터프라이즈 SSO(예: SAML, OAuth2) 통합
4. **세션 클러스터링**: 다중 서버 환경에서 세션 공유

## 참고 자료

- [Spring Security Reference](https://docs.spring.io/spring-security/reference/)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Cerbos Authorization](https://docs.cerbos.dev/)
