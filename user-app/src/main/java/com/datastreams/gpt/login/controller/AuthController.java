package com.datastreams.gpt.login.controller;

import com.datastreams.gpt.login.service.AuthService;
import com.datastreams.gpt.login.service.SessionService;
import com.datastreams.gpt.login.service.UserService;
import com.datastreams.gpt.login.service.SSOService;
import com.datastreams.gpt.login.dto.UserInfoDto;
import com.datastreams.gpt.login.dto.SSOUserDto;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;
import java.util.HashMap;
import java.util.Map;

/**
 * 인증 관련 API 컨트롤러
 * Swagger 문서화 포함
 */
@RestController
@RequestMapping("/api/auth")
@CrossOrigin(origins = "*")
@Tag(name = "인증 API", description = "로그인/로그아웃 관련 API")
public class AuthController {

    private static final Logger log = LoggerFactory.getLogger(AuthController.class);

    @Autowired
    private AuthService authService;
    
    @Autowired
    private SessionService sessionService;
    
    @Autowired
    private UserService userService;
    
    @Autowired
    private SSOService ssoService;

    /**
     * 로그인 API
     * @param requestBody 로그인 요청 데이터 (username, password)
     * @param session HTTP 세션
     * @param request HTTP 요청 (IP 주소 추출용)
     * @return 로그인 결과 (result, message, data)
     */
    @PostMapping("/login")
    @Operation(summary = "로그인", description = "사용자 로그인 처리 API")
    public ResponseEntity<Map<String, Object>> login(
            @Parameter(description = "로그인 요청 데이터") @RequestBody Map<String, String> requestBody,
            HttpSession session,
            HttpServletRequest request,
            HttpServletResponse response) {
        
        Map<String, Object> responseData = new HashMap<>();
        
        try {
            String username = requestBody.get("username");
            String password = requestBody.get("password");
            
            // L-002: 로그인 체크 - L-005 사용자 정보 조회를 통한 사용자 존재 여부 확인
            if (username != null && password != null && username.equals(password)) {
                // L-005: 사용자 정보 조회 - DB에서 실제 사용자 존재 여부 확인
                UserInfoDto userInfo = userService.getUserInfo(username);
                
                // stgubun이 'N1' 또는 'N2'인 경우 활성 사용자로 판단
                if (userInfo != null && (userInfo.getUseYn() != null && 
                    (userInfo.getUseYn().equals("N1") || userInfo.getUseYn().equals("N2")))) {
                    // IP 주소 추출
                    String ipAddr = getClientIp(request);
                    String sessionId = session.getId();
        
                    // L-003: 세션 처리 - 세션에 사용자 정보 저장
                    session.setAttribute("user", username);
                    session.setAttribute("authenticated", true);
                    session.setAttribute("userId", username);
                    session.setAttribute("ipAddr", ipAddr);
                    session.setAttribute("userInfo", userInfo);  // Chat API에서 필요한 userInfo 객체 저장
                    
                    // 세션 ID를 쿠키로 설정 (프론트엔드 전달용)
                    Cookie sessionCookie = new Cookie("JSESSIONID", sessionId);
                    sessionCookie.setHttpOnly(true);  // XSS 공격 방지
                    sessionCookie.setSecure(false);    // HTTP 환경에서도 사용 가능
                    sessionCookie.setPath("/");        // 전체 경로에서 사용 가능
                    sessionCookie.setMaxAge(3600);     // 1시간 유효
                    response.addCookie(sessionCookie);
                    
                    // L-006: 사용자 접속/세션 기록 - DB에 세션 기록 저장
                    try {
                        sessionService.saveSessionRecord(username, ipAddr, sessionId);
                    } catch (Exception e) {
                        log.warn("세션 기록 저장 실패 (로그인은 계속 진행): {}", e.getMessage());
                    }
                    
                    responseData.put("result", "success");
                    responseData.put("message", "로그인 성공");
                    responseData.put("data", Map.of(
                        "user", username, 
                        "sessionId", sessionId,
                        "ipAddr", ipAddr
                    ));
                    
                    log.info("로그인 성공 - 사용자: {}, IP: {}, 세션ID: {}", username, ipAddr, sessionId);
                    
                    return ResponseEntity.ok(responseData);
                } else {
                    responseData.put("result", "fail");
                    responseData.put("message", "존재하지 않는 사용자이거나 비활성 계정입니다.");
                    responseData.put("data", null);
                    
                    log.warn("로그인 실패 - 사용자 존재하지 않음: {}", username);
                    
                    return ResponseEntity.ok(responseData);
                }
            } else {
                responseData.put("result", "fail");
                responseData.put("message", "아이디와 비밀번호가 일치하지 않습니다.");
                responseData.put("data", null);
                
                log.warn("로그인 실패 - 아이디/비밀번호 불일치: {}", username);
                
                return ResponseEntity.ok(responseData);
            }
        } catch (Exception e) {
            responseData.put("result", "error");
            responseData.put("message", "로그인 처리 중 오류가 발생했습니다: " + e.getMessage());
            responseData.put("data", null);
            
            log.error("로그인 오류: {}", e.getMessage());
            
            return ResponseEntity.ok(responseData);
        }
    }

    /**
     * SSO 로그인 API
     * SSO 토큰에서 사용자 정보를 추출하여 로그인 처리
     * 
     * @param session HTTP 세션
     * @param request HTTP 요청
     * @param response HTTP 응답
     * @return 로그인 결과 (result, message, data)
     */
    @PostMapping("/sso/login")
    @Operation(summary = "SSO 로그인", description = "SSO 토큰 기반 로그인 처리 API")
    public ResponseEntity<Map<String, Object>> ssoLogin(
            HttpSession session,
            HttpServletRequest request,
            HttpServletResponse response) {
        
        Map<String, Object> responseData = new HashMap<>();
        
        try {
            // SSO가 비활성화되어 있으면
            if (!ssoService.isSSOEnabled()) {
                responseData.put("result", "fail");
                responseData.put("message", "SSO가 비활성화되어 있습니다.");
                responseData.put("data", null);
                
                log.warn("[SSO 로그인] SSO 비활성화 상태");
                return ResponseEntity.ok(responseData);
            }
            
            // SSO 사용자 정보 추출
            SSOUserDto ssoUser = ssoService.getSSOUserInfo(request);
            
            if (ssoUser == null || !ssoUser.isAuthenticated()) {
                responseData.put("result", "fail");
                responseData.put("message", "SSO 인증 실패 - 유효한 SSO 토큰이 없습니다.");
                responseData.put("data", null);
                
                log.warn("[SSO 로그인] SSO 토큰 없음 또는 인증 실패");
                return ResponseEntity.ok(responseData);
            }
            
            // L-005: 사용자 정보 조회 - DB에서 실제 사용자 존재 여부 확인
            UserInfoDto userInfo = userService.getUserInfo(ssoUser.getEmpCode());
            
            // 사용자가 활성 상태인지 확인
            if (userInfo != null && (userInfo.getUseYn() != null && 
                (userInfo.getUseYn().equals("N1") || userInfo.getUseYn().equals("N2")))) {
                
                // IP 주소 추출
                String ipAddr = getClientIp(request);
                String sessionId = session.getId();
                
                // L-003: 세션 처리 - 세션에 사용자 정보 저장
                session.setAttribute("user", ssoUser.getEmpCode());
                session.setAttribute("authenticated", true);
                session.setAttribute("userId", ssoUser.getEmpCode());
                session.setAttribute("ipAddr", ipAddr);
                session.setAttribute("ssoAuthenticated", true);
                session.setAttribute("ssoUser", ssoUser);
                
                // 세션 ID를 쿠키로 설정 (프론트엔드 전달용)
                Cookie sessionCookie = new Cookie("JSESSIONID", sessionId);
                sessionCookie.setHttpOnly(true);  // XSS 공격 방지
                sessionCookie.setSecure(false);    // HTTP 환경에서도 사용 가능
                sessionCookie.setPath("/");        // 전체 경로에서 사용 가능
                sessionCookie.setMaxAge(3600);     // 1시간 유효
                response.addCookie(sessionCookie);
                
                // L-006: 사용자 접속/세션 기록 - DB에 세션 기록 저장
                try {
                    sessionService.saveSessionRecord(ssoUser.getEmpCode(), ipAddr, sessionId);
                } catch (Exception e) {
                    log.warn("[SSO 로그인] 세션 기록 저장 실패 (로그인은 계속 진행): {}", e.getMessage());
                }
                
                Map<String, Object> userData = new HashMap<>();
                userData.put("userId", ssoUser.getEmpCode());
                userData.put("empCode", ssoUser.getEmpCode());
                userData.put("name", ssoUser.getName());
                userData.put("deptCode", ssoUser.getDeptCode());
                userData.put("sessionId", sessionId);
                userData.put("ipAddr", ipAddr);
                userData.put("authType", "SSO");
                
                responseData.put("result", "success");
                responseData.put("message", "SSO 로그인 성공");
                responseData.put("data", userData);
                
                log.info("[SSO 로그인] 성공 - 사번: {}, 이름: {}, IP: {}", 
                         ssoUser.getEmpCode(), ssoUser.getName(), ipAddr);
                
                return ResponseEntity.ok(responseData);
                
            } else {
                responseData.put("result", "fail");
                responseData.put("message", "존재하지 않는 사용자이거나 비활성 계정입니다.");
                responseData.put("data", null);
                
                log.warn("[SSO 로그인] 사용자 없음 또는 비활성 - 사번: {}", ssoUser.getEmpCode());
                return ResponseEntity.ok(responseData);
            }
            
        } catch (Exception e) {
            responseData.put("result", "error");
            responseData.put("message", "SSO 로그인 처리 중 오류가 발생했습니다: " + e.getMessage());
            responseData.put("data", null);
            
            log.error("[SSO 로그인] 오류: {}", e.getMessage(), e);
            return ResponseEntity.ok(responseData);
        }
    }

    /**
     * 로그아웃 API
     * @param session HTTP 세션
     * @return 로그아웃 결과 (result, message, data)
     */
    @PostMapping("/logout")
    @Operation(summary = "로그아웃", description = "사용자 로그아웃 처리 API")
    public ResponseEntity<Map<String, Object>> logout(HttpSession session) {
        Map<String, Object> response = new HashMap<>();
        
        try {
            String sessionId = session.getId();
            // 세션 무효화
            session.invalidate();
            
            response.put("result", "success");
            response.put("message", "로그아웃 성공");
            response.put("data", Map.of("sessionId", sessionId));
                        
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            response.put("result", "error");
            response.put("message", "로그아웃 처리 중 오류가 발생했습니다: " + e.getMessage());
            response.put("data", null);
                        
            return ResponseEntity.ok(response);
        }
    }

    /**
     * 로그인 상태 확인 API
     * @param session HTTP 세션
     * @return 로그인 상태 (result, message, data)
     */
    @GetMapping("/status")
    @Operation(summary = "로그인 상태 확인", description = "현재 로그인 상태를 확인하는 API")
    public ResponseEntity<Map<String, Object>> checkStatus(HttpSession session) {
        Map<String, Object> response = new HashMap<>();
        
        try {
            Boolean authenticated = (Boolean) session.getAttribute("authenticated");
            if (authenticated != null && authenticated) {
                String user = (String) session.getAttribute("user");
                Boolean ssoAuthenticated = (Boolean) session.getAttribute("ssoAuthenticated");
                
                Map<String, Object> statusData = new HashMap<>();
                statusData.put("user", user);
                statusData.put("authenticated", true);
                statusData.put("sessionId", session.getId());
                statusData.put("authType", ssoAuthenticated != null && ssoAuthenticated ? "SSO" : "NORMAL");
                
                response.put("result", "success");
                response.put("message", "로그인 상태");
                response.put("data", statusData);        
          
                return ResponseEntity.ok(response);
            } else {
                response.put("result", "fail");
                response.put("message", "로그인되지 않음");
                response.put("data", Map.of("authenticated", false));                
                
                return ResponseEntity.ok(response);
            }
        } catch (Exception e) {
            response.put("result", "error");
            response.put("message", "상태 확인 중 오류가 발생했습니다: " + e.getMessage());
            response.put("data", null);
            
            return ResponseEntity.ok(response);
        }
    }
    
    /**
     * SSO 상태 확인 API
     * SSO 인증 여부 및 사용자 정보 확인
     * 
     * @param request HTTP 요청
     * @param session HTTP 세션
     * @return SSO 인증 상태
     */
    @GetMapping("/sso/status")
    @Operation(summary = "SSO 상태 확인", description = "SSO 인증 여부 및 사용자 정보를 확인하는 API")
    public ResponseEntity<Map<String, Object>> checkSSOStatus(
            HttpServletRequest request,
            HttpSession session) {
        
        Map<String, Object> responseData = new HashMap<>();
        
        try {
            // SSO가 비활성화되어 있으면
            if (!ssoService.isSSOEnabled()) {
                responseData.put("result", "success");
                responseData.put("message", "SSO가 비활성화되어 있습니다.");
                responseData.put("data", Map.of(
                    "ssoEnabled", false,
                    "authenticated", false
                ));
                
                return ResponseEntity.ok(responseData);
            }
            
            // SSO 인증 여부 확인
            boolean authenticated = ssoService.isSSOAuthenticated(request);
            
            if (authenticated) {
                SSOUserDto ssoUser = ssoService.getSSOUserInfo(request);
                
                Map<String, Object> ssoData = new HashMap<>();
                ssoData.put("ssoEnabled", true);
                ssoData.put("authenticated", true);
                ssoData.put("empCode", ssoUser.getEmpCode());
                ssoData.put("name", ssoUser.getName());
                ssoData.put("deptCode", ssoUser.getDeptCode());
                
                responseData.put("result", "success");
                responseData.put("message", "SSO 인증 완료");
                responseData.put("data", ssoData);
                
                log.info("[SSO 상태] 인증됨 - 사번: {}", ssoUser.getEmpCode());
                
            } else {
                responseData.put("result", "success");
                responseData.put("message", "SSO 인증되지 않음");
                responseData.put("data", Map.of(
                    "ssoEnabled", true,
                    "authenticated", false
                ));
                
                log.debug("[SSO 상태] 인증되지 않음");
            }
            
            return ResponseEntity.ok(responseData);
            
        } catch (Exception e) {
            responseData.put("result", "error");
            responseData.put("message", "SSO 상태 확인 중 오류가 발생했습니다: " + e.getMessage());
            responseData.put("data", null);
            
            log.error("[SSO 상태] 오류: {}", e.getMessage(), e);
            return ResponseEntity.ok(responseData);
        }
    }
    
    /**
     * 세션 유효성 체크 API (L-004)
     * @param session HTTP 세션
     * @return 세션 유효성 결과
     */
    @GetMapping("/session/validate")
    @Operation(summary = "세션 유효성 체크", description = "현재 세션이 유효한지 확인하는 API")
    public ResponseEntity<Map<String, Object>> validateSession(HttpSession session, HttpServletRequest request) {
        Map<String, Object> responseData = new HashMap<>();
        
        try {
            String userId = (String) session.getAttribute("userId");
            String sessionId = getSessionIdFromCookie(request);
            Boolean authenticated = (Boolean) session.getAttribute("authenticated");
            
            // 세션에 사용자 정보가 없으면
            if (userId == null || authenticated == null || !authenticated) {
                responseData.put("result", "fail");
                responseData.put("message", "로그인되지 않음");
                responseData.put("data", Map.of("valid", false, "reason", "not_logged_in"));
                
                log.warn("세션 검증 실패 - 로그인되지 않음");
                return ResponseEntity.ok(responseData);
            }
            
            // DB에서 세션 유효성 체크
            boolean isValid = sessionService.isSessionValid(userId, sessionId);
            
            if (isValid) {
                responseData.put("result", "success");
                responseData.put("message", "세션 유효");
                responseData.put("data", Map.of(
                    "valid", true,
                    "userId", userId,
                    "sessionId", sessionId
                ));
                
                log.info("세션 유효 - 사용자: {}", userId);
            } else {
                responseData.put("result", "fail");
                responseData.put("message", "세션 만료");
                responseData.put("data", Map.of("valid", false, "reason", "expired"));
                
                // 세션 무효화
                session.invalidate();
                
                log.warn("세션 만료 - 사용자: {}", userId);
            }
            
            return ResponseEntity.ok(responseData);
        } catch (Exception e) {
            responseData.put("result", "error");
            responseData.put("message", "세션 검증 중 오류 발생: " + e.getMessage());
            responseData.put("data", Map.of("valid", false, "reason", "error"));
            
            log.error("세션 검증 오류: {}", e.getMessage());
            return ResponseEntity.ok(responseData);
        }
    }
    
    /**
     * 쿠키에서 세션 ID 추출
     * @param request HTTP 요청
     * @return 세션 ID (없으면 null)
     */
    private String getSessionIdFromCookie(HttpServletRequest request) {
        Cookie[] cookies = request.getCookies();
        if (cookies != null) {
            for (Cookie cookie : cookies) {
                if ("JSESSIONID".equals(cookie.getName())) {
                    return cookie.getValue();
                }
            }
        }
        return null;
    }
    
    /**
     * 사용자 정보 조회 API (L-005)
     * @param userId 사용자 ID
     * @return 사용자 상세 정보
     */
    @GetMapping("/user/{userId}")
    @Operation(summary = "사용자 정보 조회", description = "사용자 ID로 상세 정보를 조회하는 API")
    public ResponseEntity<Map<String, Object>> getUserInfo(
            @Parameter(description = "사용자 ID") @PathVariable String userId) {
        
        Map<String, Object> responseData = new HashMap<>();
        
        try {
            UserInfoDto userInfo = userService.getUserInfo(userId);
            
            if (userInfo != null) {
                responseData.put("result", "success");
                responseData.put("message", "사용자 정보 조회 성공");
                responseData.put("data", userInfo);
                
                log.info("사용자 정보 조회 성공 - 사용자: {}", userId);
            } else {
                responseData.put("result", "fail");
                responseData.put("message", "사용자 정보를 찾을 수 없습니다");
                responseData.put("data", null);
                
                log.warn("사용자 정보 없음 - 사용자: {}", userId);
            }
            
            return ResponseEntity.ok(responseData);
        } catch (Exception e) {
            responseData.put("result", "error");
            responseData.put("message", "사용자 정보 조회 중 오류 발생: " + e.getMessage());
            responseData.put("data", null);
            
            log.error("사용자 정보 조회 오류 - 사용자: {}, 에러: {}", userId, e.getMessage());
            return ResponseEntity.ok(responseData);
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
        
        // X-Forwarded-For에 여러 IP가 있을 경우 첫 번째 IP 사용
        if (ip != null && ip.contains(",")) {
            ip = ip.split(",")[0].trim();
        }
        
        return ip;
    }
}


