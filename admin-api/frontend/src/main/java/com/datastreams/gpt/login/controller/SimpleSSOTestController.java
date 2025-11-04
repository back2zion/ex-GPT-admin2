package com.datastreams.gpt.login.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

import com.datastreams.gpt.login.dto.UserInfoDto;

/**
 * 간단한 SSO 테스트 컨트롤러
 * 데이터베이스 연결 없이 SSO 토큰 테스트만 수행
 * 
 * @author DataStreams
 * @since 2025-10-15
 */
@RestController
@RequestMapping("/api/sso")
@CrossOrigin(origins = "*")
@Tag(name = "간단한 SSO 테스트 API", description = "데이터베이스 연결 없이 SSO 토큰 테스트")
public class SimpleSSOTestController {

    private static final Logger log = LoggerFactory.getLogger(SimpleSSOTestController.class);

    /**
     * 간단한 SSO 토큰 생성 API
     * 
     * @param userData 사용자 데이터
     * @param session HTTP 세션
     * @return SSO 토큰 생성 결과
     */
    @PostMapping("/createToken")
    @Operation(summary = "SSO 토큰 생성", description = "간단한 SSO 토큰을 생성합니다.")
    public ResponseEntity<Map<String, Object>> createToken(
            @Parameter(description = "사용자 정보")
            @RequestBody Map<String, String> userData,
            HttpSession session) {
        
        Map<String, Object> responseData = new HashMap<>();
        
        try {
            String empCode = userData.getOrDefault("empCode", "21311729");
            String name = userData.getOrDefault("name", "테스트유저");
            String deptCode = userData.getOrDefault("deptCode", "D001");
            
            // 간단한 토큰 생성
            String tokenValue = String.format(
                "EMPCODE=%s;NAME=%s;DEPT_CODE=%s;ID=%s;TIMESTAMP=%d",
                empCode, name, deptCode, empCode, System.currentTimeMillis()
            );
            
            // 세션에 저장
            session.setAttribute("SSO_ID", empCode);
            session.setAttribute("_TOKEN", tokenValue);
            
            Map<String, Object> tokenData = new HashMap<>();
            tokenData.put("empCode", empCode);
            tokenData.put("name", name);
            tokenData.put("deptCode", deptCode);
            tokenData.put("tokenValue", tokenValue);
            tokenData.put("sessionId", session.getId());
            tokenData.put("timestamp", System.currentTimeMillis());
            
            responseData.put("result", "success");
            responseData.put("message", "SSO 토큰이 생성되었습니다.");
            responseData.put("data", tokenData);
            
            log.info("[SSO] 토큰 생성 - 사번: {}, 이름: {}", empCode, name);
            
            return ResponseEntity.ok(responseData);
            
        } catch (Exception e) {
            responseData.put("result", "error");
            responseData.put("message", "토큰 생성 실패: " + e.getMessage());
            responseData.put("data", null);
            
            log.error("[SSO] 토큰 생성 실패: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(responseData);
        }
    }

    /**
     * SSO 토큰 확인 API
     * 
     * @param session HTTP 세션
     * @return SSO 토큰 정보
     */
    @GetMapping("/checkToken")
    @Operation(summary = "SSO 토큰 확인", description = "현재 세션의 SSO 토큰을 확인합니다.")
    public ResponseEntity<Map<String, Object>> checkToken(HttpSession session) {
        
        Map<String, Object> responseData = new HashMap<>();
        
        try {
            Object ssoId = session.getAttribute("SSO_ID");
            Object token = session.getAttribute("_TOKEN");
            
            Map<String, Object> sessionData = new HashMap<>();
            sessionData.put("hasSSO_ID", ssoId != null);
            sessionData.put("has_TOKEN", token != null);
            sessionData.put("SSO_ID", ssoId);
            sessionData.put("_TOKEN", token);
            sessionData.put("sessionId", session.getId());
            
            responseData.put("result", "success");
            responseData.put("message", "SSO 토큰 확인 완료");
            responseData.put("data", sessionData);
            
            log.info("[SSO] 토큰 확인 - SSO_ID: {}, 토큰 존재: {}", ssoId, token != null);
            
            return ResponseEntity.ok(responseData);
            
        } catch (Exception e) {
            responseData.put("result", "error");
            responseData.put("message", "토큰 확인 실패: " + e.getMessage());
            responseData.put("data", null);
            
            log.error("[SSO] 토큰 확인 실패: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(responseData);
        }
    }

    /**
     * SSO 로그인 API
     * 
     * @param session HTTP 세션
     * @param request HTTP 요청
     * @return SSO 로그인 결과
     */
    @PostMapping("/login")
    @Operation(summary = "SSO 로그인", description = "SSO 토큰을 사용하여 로그인합니다.")
    public ResponseEntity<Map<String, Object>> login(
            HttpSession session,
            HttpServletRequest request) {
        
        Map<String, Object> responseData = new HashMap<>();
        
        try {
            Object tokenValue = session.getAttribute("_TOKEN");
            Object ssoId = session.getAttribute("SSO_ID");
            
            if (tokenValue == null || ssoId == null) {
                responseData.put("result", "error");
                responseData.put("message", "SSO 토큰이 없습니다. 먼저 /api/sso/createToken을 호출하세요.");
                responseData.put("data", null);
                return ResponseEntity.ok(responseData);
            }
            
            // 토큰에서 사용자 정보 추출
            String tokenStr = tokenValue.toString();
            String empCode = extractValue(tokenStr, "EMPCODE");
            String name = extractValue(tokenStr, "NAME");
            String deptCode = extractValue(tokenStr, "DEPT_CODE");
            
            // IP 주소 추출
            String ipAddr = getClientIp(request);
            
            // UserInfoDto 객체 생성 및 세션에 저장
            UserInfoDto userInfo = new UserInfoDto();
            userInfo.setUsrId(empCode);
            userInfo.setUsrNm(name);
            userInfo.setDeptCd(deptCode);
            userInfo.setDeptNm("테스트부서");
            userInfo.setEmail(empCode + "@test.com");
            userInfo.setTelNo("010-1234-5678");
            userInfo.setUseYn("Y");
            userInfo.setSysAccsYn("Y");
            userInfo.setMgrAuthYn("N");
            userInfo.setVceMdlUseYn("Y");
            userInfo.setImgMdlUseYn("Y");
            userInfo.setFntSizeCd("M");
            userInfo.setUiThmCd("LIGHT");
            
            // 세션에 로그인 정보 저장
            session.setAttribute("user", empCode);
            session.setAttribute("authenticated", true);
            session.setAttribute("userId", empCode);
            session.setAttribute("ipAddr", ipAddr);
            session.setAttribute("ssoAuthenticated", true);
            session.setAttribute("userInfo", userInfo);  // Chat API에서 필요한 userInfo 객체 저장
            
            Map<String, Object> userData = new HashMap<>();
            userData.put("userId", empCode);
            userData.put("empCode", empCode);
            userData.put("name", name);
            userData.put("deptCode", deptCode);
            userData.put("sessionId", session.getId());
            userData.put("ipAddr", ipAddr);
            userData.put("authType", "SSO");
            userData.put("tokenValue", tokenValue);
            
            responseData.put("result", "success");
            responseData.put("message", "SSO 로그인 성공");
            responseData.put("data", userData);
            
            log.info("[SSO 로그인] 성공 - 사번: {}, 이름: {}, IP: {}", empCode, name, ipAddr);
            
            return ResponseEntity.ok(responseData);
            
        } catch (Exception e) {
            responseData.put("result", "error");
            responseData.put("message", "SSO 로그인 실패: " + e.getMessage());
            responseData.put("data", null);
            
            log.error("[SSO 로그인] 실패: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(responseData);
        }
    }

    /**
     * SSO 세션 초기화 API
     * 
     * @param session HTTP 세션
     * @return 초기화 결과
     */
    @PostMapping("/logout")
    @Operation(summary = "SSO 로그아웃", description = "SSO 세션을 초기화합니다.")
    public ResponseEntity<Map<String, Object>> logout(HttpSession session) {
        
        Map<String, Object> responseData = new HashMap<>();
        
        try {
            session.removeAttribute("SSO_ID");
            session.removeAttribute("_TOKEN");
            session.removeAttribute("user");
            session.removeAttribute("authenticated");
            session.removeAttribute("userId");
            session.removeAttribute("ssoAuthenticated");
            session.removeAttribute("userInfo");  // userInfo 객체도 제거
            
            responseData.put("result", "success");
            responseData.put("message", "SSO 로그아웃 완료");
            responseData.put("data", Map.of("sessionId", session.getId()));
            
            log.info("[SSO] 로그아웃 완료");
            
            return ResponseEntity.ok(responseData);
            
        } catch (Exception e) {
            responseData.put("result", "error");
            responseData.put("message", "로그아웃 실패: " + e.getMessage());
            responseData.put("data", null);
            
            log.error("[SSO] 로그아웃 실패: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(responseData);
        }
    }
    
    /**
     * 토큰에서 값 추출
     */
    private String extractValue(String token, String key) {
        try {
            String[] pairs = token.split(";");
            for (String pair : pairs) {
                if (pair.trim().startsWith(key + "=")) {
                    return pair.trim().substring(key.length() + 1);
                }
            }
        } catch (Exception e) {
            log.warn("토큰에서 {} 값 추출 실패: {}", key, e.getMessage());
        }
        return "";
    }
    
    /**
     * 클라이언트 IP 주소 추출
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
