package com.datastreams.gpt.login.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

/**
 * 실제 SSOToken 라이브러리를 사용한 SSO 테스트 컨트롤러
 * dummy-ssotoken-1.0.0.jar 라이브러리를 사용하여 실제 SSO 토큰을 생성하고 분석
 * 
 * @author DataStreams
 * @since 2025-10-15
 */
@RestController
@RequestMapping("/api/auth/sso/real")
@CrossOrigin(origins = "*")
@Tag(name = "실제 SSO 테스트 API", description = "dummy-ssotoken 라이브러리를 사용한 실제 SSO 토큰 테스트")
public class RealSSOTestController {

    private static final Logger log = LoggerFactory.getLogger(RealSSOTestController.class);

    @Value("${spring.profiles.active:dev}")
    private String activeProfile;

    /**
     * 실제 SSO 토큰 생성 및 분석 API
     * dummy-ssotoken 라이브러리를 사용하여 실제 SSO 토큰을 생성하고 구조를 분석
     * 
     * @param userData 사용자 데이터 (empCode, name, deptCode)
     * @param session HTTP 세션
     * @return 실제 SSO 토큰 생성 및 분석 결과
     */
    @PostMapping("/createRealToken")
    @Operation(
        summary = "실제 SSO 토큰 생성", 
        description = "dummy-ssotoken 라이브러리를 사용하여 실제 SSO 토큰을 생성하고 구조를 분석합니다."
    )
    public ResponseEntity<Map<String, Object>> createRealToken(
            @Parameter(description = "사용자 정보 (empCode, name, deptCode)")
            @RequestBody Map<String, String> userData,
            HttpSession session,
            HttpServletRequest request) {
        
        Map<String, Object> responseData = new HashMap<>();
        
        try {
            // 운영 환경에서는 차단
            if ("prd".equals(activeProfile) || "prod".equals(activeProfile)) {
                responseData.put("result", "error");
                responseData.put("message", "운영 환경에서는 실제 SSO 토큰 테스트를 사용할 수 없습니다.");
                responseData.put("data", null);
                
                log.error("[실제 SSO] 운영 환경에서 실제 SSO 토큰 테스트 시도 차단!");
                return ResponseEntity.status(403).body(responseData);
            }
            
            // 사용자 데이터 추출
            String empCode = userData.getOrDefault("empCode", "21311729");
            String name = userData.getOrDefault("name", "테스트유저");
            String deptCode = userData.getOrDefault("deptCode", "D001");
            
            // 실제 SSO 토큰 생성 시도
            Map<String, Object> tokenAnalysis = new HashMap<>();
            
            try {
                // SSOToken 클래스 로드 시도
                Class<?> ssoTokenClass = Class.forName("com.dreamsecurity.sso.agent.token.SSOToken");
                log.info("[실제 SSO] SSOToken 클래스 로드 성공: {}", ssoTokenClass.getName());
                
                // SSOToken 인스턴스 생성
                Object ssoToken = ssoTokenClass.getDeclaredConstructor().newInstance();
                
                // 토큰에 사용자 정보 설정 시도
                // 실제 SSOToken의 메서드들을 리플렉션으로 호출
                java.lang.reflect.Method setPropertyMethod = ssoTokenClass.getMethod("setProperty", 
                    String.class, String.class, String.class);
                
                // 사용자 정보 설정
                setPropertyMethod.invoke(ssoToken, "USER", "ID", empCode);
                setPropertyMethod.invoke(ssoToken, "USER", "EMPNO", empCode);
                setPropertyMethod.invoke(ssoToken, "USER", "NAME", name);
                setPropertyMethod.invoke(ssoToken, "USER", "DEPT_CODE", deptCode);
                setPropertyMethod.invoke(ssoToken, "USER", "DEPT_NAME", "테스트부서");
                
                // 타임스탬프 설정
                long currentTime = System.currentTimeMillis();
                setPropertyMethod.invoke(ssoToken, "USER", "TIMESTAMP", String.valueOf(currentTime));
                setPropertyMethod.invoke(ssoToken, "USER", "NOT_AFTER", String.valueOf(currentTime + 3600000)); // 1시간 후
                
                // 토큰 값 생성
                java.lang.reflect.Method getTokenValueMethod = ssoTokenClass.getMethod("getTokenValue");
                StringBuilder tokenValue = (StringBuilder) getTokenValueMethod.invoke(ssoToken);
                
                // 세션에 토큰 저장
                session.setAttribute("SSO_ID", empCode);
                session.setAttribute("_TOKEN", tokenValue.toString());
                
                // 토큰 분석 정보
                tokenAnalysis.put("tokenCreated", true);
                tokenAnalysis.put("tokenValue", tokenValue.toString());
                tokenAnalysis.put("tokenLength", tokenValue.length());
                tokenAnalysis.put("empCode", empCode);
                tokenAnalysis.put("name", name);
                tokenAnalysis.put("deptCode", deptCode);
                tokenAnalysis.put("timestamp", currentTime);
                tokenAnalysis.put("sessionId", session.getId());
                
                // 토큰 구조 분석
                java.lang.reflect.Method getPropertyNamesMethod = ssoTokenClass.getMethod("getPropertyNames");
                java.util.List propertyNames = (java.util.List) getPropertyNamesMethod.invoke(ssoToken);
                tokenAnalysis.put("propertyNames", propertyNames);
                
                java.lang.reflect.Method getGroupNamesMethod = ssoTokenClass.getMethod("getGroupNames");
                String[] groupNames = (String[]) getGroupNamesMethod.invoke(ssoToken);
                tokenAnalysis.put("groupNames", groupNames);
                
                responseData.put("result", "success");
                responseData.put("message", "실제 SSO 토큰이 생성되었습니다.");
                responseData.put("data", tokenAnalysis);
                
                log.info("[실제 SSO] 토큰 생성 성공 - 사번: {}, 토큰 길이: {}", empCode, tokenValue.length());
                
            } catch (ClassNotFoundException e) {
                log.error("[실제 SSO] SSOToken 클래스를 찾을 수 없습니다: {}", e.getMessage());
                tokenAnalysis.put("error", "SSOToken 클래스를 찾을 수 없습니다. 라이브러리가 올바르게 로드되었는지 확인하세요.");
                tokenAnalysis.put("classpath", System.getProperty("java.class.path"));
                
                responseData.put("result", "error");
                responseData.put("message", "SSOToken 라이브러리를 찾을 수 없습니다.");
                responseData.put("data", tokenAnalysis);
                
            } catch (Exception e) {
                log.error("[실제 SSO] 토큰 생성 실패: {}", e.getMessage(), e);
                tokenAnalysis.put("error", e.getMessage());
                tokenAnalysis.put("errorType", e.getClass().getSimpleName());
                
                responseData.put("result", "error");
                responseData.put("message", "SSO 토큰 생성 실패: " + e.getMessage());
                responseData.put("data", tokenAnalysis);
            }
            
            return ResponseEntity.ok(responseData);
            
        } catch (Exception e) {
            responseData.put("result", "error");
            responseData.put("message", "실제 SSO 토큰 생성 실패: " + e.getMessage());
            responseData.put("data", null);
            
            log.error("[실제 SSO] 전체 프로세스 실패: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(responseData);
        }
    }

    /**
     * 실제 SSO 토큰 파싱 테스트 API
     * 생성된 토큰을 다시 파싱하여 정보를 추출
     * 
     * @param session HTTP 세션
     * @return 토큰 파싱 결과
     */
    @GetMapping("/parseToken")
    @Operation(summary = "실제 SSO 토큰 파싱", description = "세션에 저장된 실제 SSO 토큰을 파싱하여 정보를 추출합니다.")
    public ResponseEntity<Map<String, Object>> parseToken(HttpSession session) {
        
        Map<String, Object> responseData = new HashMap<>();
        
        try {
            Object tokenValue = session.getAttribute("_TOKEN");
            Object ssoId = session.getAttribute("SSO_ID");
            
            if (tokenValue == null) {
                responseData.put("result", "error");
                responseData.put("message", "세션에 토큰이 없습니다. 먼저 /api/auth/sso/real/createRealToken을 호출하세요.");
                responseData.put("data", null);
                return ResponseEntity.ok(responseData);
            }
            
            Map<String, Object> parseResult = new HashMap<>();
            
            try {
                // SSOToken 클래스로 토큰 파싱
                Class<?> ssoTokenClass = Class.forName("com.dreamsecurity.sso.agent.token.SSOToken");
                
                // 토큰 문자열로 SSOToken 객체 생성
                Object ssoToken = ssoTokenClass.getDeclaredConstructor(String.class).newInstance(tokenValue.toString());
                
                // 토큰 정보 추출
                java.lang.reflect.Method getPropertyMethod = ssoTokenClass.getMethod("getProperty", String.class);
                java.lang.reflect.Method getPropertyWithDefaultMethod = ssoTokenClass.getMethod("getProperty", String.class, String.class);
                
                parseResult.put("empCode", getPropertyMethod.invoke(ssoToken, "ID"));
                parseResult.put("name", getPropertyMethod.invoke(ssoToken, "NAME"));
                parseResult.put("deptCode", getPropertyMethod.invoke(ssoToken, "DEPT_CODE"));
                parseResult.put("deptName", getPropertyMethod.invoke(ssoToken, "DEPT_NAME"));
                parseResult.put("timestamp", getPropertyMethod.invoke(ssoToken, "TIMESTAMP"));
                parseResult.put("notAfter", getPropertyMethod.invoke(ssoToken, "NOT_AFTER"));
                
                // 그룹 정보
                java.lang.reflect.Method getGroupNamesMethod = ssoTokenClass.getMethod("getGroupNames");
                String[] groupNames = (String[]) getGroupNamesMethod.invoke(ssoToken);
                parseResult.put("groupNames", groupNames);
                
                // 속성 목록
                java.lang.reflect.Method getPropertyNamesMethod = ssoTokenClass.getMethod("getPropertyNames");
                java.util.List propertyNames = (java.util.List) getPropertyNamesMethod.invoke(ssoToken);
                parseResult.put("propertyNames", propertyNames);
                
                parseResult.put("parseSuccess", true);
                parseResult.put("tokenValue", tokenValue.toString());
                parseResult.put("tokenLength", tokenValue.toString().length());
                
                responseData.put("result", "success");
                responseData.put("message", "토큰 파싱 성공");
                responseData.put("data", parseResult);
                
                log.info("[실제 SSO] 토큰 파싱 성공 - 사번: {}", parseResult.get("empCode"));
                
            } catch (Exception e) {
                log.error("[실제 SSO] 토큰 파싱 실패: {}", e.getMessage(), e);
                parseResult.put("parseSuccess", false);
                parseResult.put("error", e.getMessage());
                parseResult.put("tokenValue", tokenValue.toString());
                
                responseData.put("result", "error");
                responseData.put("message", "토큰 파싱 실패: " + e.getMessage());
                responseData.put("data", parseResult);
            }
            
            return ResponseEntity.ok(responseData);
            
        } catch (Exception e) {
            responseData.put("result", "error");
            responseData.put("message", "토큰 파싱 프로세스 실패: " + e.getMessage());
            responseData.put("data", null);
            
            log.error("[실제 SSO] 토큰 파싱 프로세스 실패: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(responseData);
        }
    }

    /**
     * 실제 SSO 로그인 테스트 API
     * 실제 SSO 토큰을 사용하여 로그인 시뮬레이션
     * 
     * @param session HTTP 세션
     * @param request HTTP 요청
     * @return 실제 SSO 로그인 결과
     */
    @PostMapping("/realLogin")
    @Operation(summary = "실제 SSO 로그인", description = "실제 SSO 토큰을 사용하여 로그인을 시뮬레이션합니다.")
    public ResponseEntity<Map<String, Object>> realLogin(
            HttpSession session,
            HttpServletRequest request) {
        
        Map<String, Object> responseData = new HashMap<>();
        
        try {
            Object tokenValue = session.getAttribute("_TOKEN");
            Object ssoId = session.getAttribute("SSO_ID");
            
            if (tokenValue == null || ssoId == null) {
                responseData.put("result", "error");
                responseData.put("message", "SSO 토큰이 없습니다. 먼저 /api/auth/sso/real/createRealToken을 호출하세요.");
                responseData.put("data", null);
                return ResponseEntity.ok(responseData);
            }
            
            // 실제 SSO 토큰 파싱하여 로그인 처리
            Map<String, Object> loginResult = new HashMap<>();
            
            try {
                Class<?> ssoTokenClass = Class.forName("com.dreamsecurity.sso.agent.token.SSOToken");
                Object ssoToken = ssoTokenClass.getDeclaredConstructor(String.class).newInstance(tokenValue.toString());
                
                // 사용자 정보 추출
                java.lang.reflect.Method getPropertyMethod = ssoTokenClass.getMethod("getProperty", String.class);
                String empCode = (String) getPropertyMethod.invoke(ssoToken, "ID");
                String name = (String) getPropertyMethod.invoke(ssoToken, "NAME");
                String deptCode = (String) getPropertyMethod.invoke(ssoToken, "DEPT_CODE");
                
                // IP 주소 추출
                String ipAddr = getClientIp(request);
                String sessionId = session.getId();
                
                // 세션에 로그인 정보 저장
                session.setAttribute("user", empCode);
                session.setAttribute("authenticated", true);
                session.setAttribute("userId", empCode);
                session.setAttribute("ipAddr", ipAddr);
                session.setAttribute("ssoAuthenticated", true);
                session.setAttribute("realSSOMode", true);
                
                loginResult.put("userId", empCode);
                loginResult.put("empCode", empCode);
                loginResult.put("name", name);
                loginResult.put("deptCode", deptCode);
                loginResult.put("sessionId", sessionId);
                loginResult.put("ipAddr", ipAddr);
                loginResult.put("authType", "REAL_SSO");
                loginResult.put("tokenValue", tokenValue.toString());
                loginResult.put("note", "실제 SSO 토큰을 사용한 로그인 완료");
                
                responseData.put("result", "success");
                responseData.put("message", "실제 SSO 로그인 성공");
                responseData.put("data", loginResult);
                
                log.info("[실제 SSO 로그인] 성공 - 사번: {}, 이름: {}, IP: {}", empCode, name, ipAddr);
                
            } catch (Exception e) {
                log.error("[실제 SSO 로그인] 토큰 파싱 실패: {}", e.getMessage(), e);
                loginResult.put("error", e.getMessage());
                loginResult.put("tokenValue", tokenValue.toString());
                
                responseData.put("result", "error");
                responseData.put("message", "SSO 토큰 파싱 실패: " + e.getMessage());
                responseData.put("data", loginResult);
            }
            
            return ResponseEntity.ok(responseData);
            
        } catch (Exception e) {
            responseData.put("result", "error");
            responseData.put("message", "실제 SSO 로그인 실패: " + e.getMessage());
            responseData.put("data", null);
            
            log.error("[실제 SSO 로그인] 전체 프로세스 실패: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(responseData);
        }
    }
    
    /**
     * 클라이언트 IP 주소 추출
     * @param request HTTP 요청
     * @return IP 주소
     */
    private String getClientIp(HttpServletRequest request) {
        String ip = request.getHeader("X-Forwarded-For");
        
        if (ip == null || ip.isEmpty() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getHeader("Proxy-Client-IP");
        }
        if (ip == null || ip.isEmpty() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getHeader("WL-Proxy-Client-IP");
        }
        if (ip == null || ip.isEmpty() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getHeader("HTTP_CLIENT_IP");
        }
        if (ip == null || ip.isEmpty() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getHeader("HTTP_X_FORWARDED_FOR");
        }
        if (ip == null || ip.isEmpty() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getRemoteAddr();
        }
        
        if (ip != null && ip.contains(",")) {
            ip = ip.split(",")[0].trim();
        }
        
        return ip;
    }
}
