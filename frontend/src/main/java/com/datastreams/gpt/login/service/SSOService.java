package com.datastreams.gpt.login.service;

import com.datastreams.gpt.login.dto.SSOUserDto;
import com.dreamsecurity.sso.agent.token.SSOToken;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

/**
 * SSO 인증 서비스
 * DreamSecurity SSO 토큰을 처리하고 사용자 정보를 추출하는 서비스
 * 
 * @author DataStreams
 * @since 2025-10-15
 */
@Service
public class SSOService {

    private static final Logger log = LoggerFactory.getLogger(SSOService.class);

    @Value("${ds.ssoUse}")
    private boolean ssoUse;

    /**
     * SSO 토큰에서 사용자 정보 추출
     * 
     * @param request HttpServletRequest
     * @return SSOUserDto SSO 사용자 정보
     */
    public SSOUserDto getSSOUserInfo(HttpServletRequest request) {
        try {
            // SSO 비활성화 시 null 반환
            if (!ssoUse) {
                log.debug("[SSO] SSO가 비활성화되어 있습니다. (ssoUse=false)");
                return null;
            }

            HttpSession session = request.getSession(false);
            
            // 세션이 없으면 null 반환
            if (session == null) {
                log.warn("[SSO] 세션이 존재하지 않습니다.");
                return null;
            }

            // SSO_ID 확인
            Object ssoIdObj = session.getAttribute("SSO_ID");
            if (ssoIdObj == null || ssoIdObj.toString().isEmpty()) {
                log.warn("[SSO] SSO_ID가 세션에 없습니다.");
                return null;
            }

            // _TOKEN 추출
            String tokenString = (String) session.getAttribute("_TOKEN");
            if (tokenString == null || tokenString.isEmpty()) {
                log.warn("[SSO] _TOKEN이 세션에 없습니다.");
                return null;
            }

            // SSO 토큰 파싱
            SSOToken token = new SSOToken(tokenString);
            
            // 사용자 정보 추출
            String empCode = token.getProperty("EMPCODE"); // 사번
            String name = token.getProperty("NAME");       // 이름
            String deptCode = token.getProperty("DEPT_CODE"); // 부서코드
            
            // DTO 생성
            SSOUserDto ssoUser = new SSOUserDto(empCode, empCode, name, deptCode, tokenString);
            
            log.info("[SSO] 사용자 정보 추출 성공 - 사번: {}, 이름: {}, 부서: {}", empCode, name, deptCode);
            
            return ssoUser;

        } catch (Exception e) {
            log.error("[SSO] SSO 사용자 정보 추출 실패: {}", e.getMessage(), e);
            return null;
        }
    }

    /**
     * SSO 인증 여부 확인
     * 
     * @param request HttpServletRequest
     * @return boolean SSO 인증 여부
     */
    public boolean isSSOAuthenticated(HttpServletRequest request) {
        try {
            // SSO 비활성화 시 false 반환
            if (!ssoUse) {
                return false;
            }

            HttpSession session = request.getSession(false);
            if (session == null) {
                return false;
            }

            Object ssoIdObj = session.getAttribute("SSO_ID");
            Object tokenObj = session.getAttribute("_TOKEN");

            boolean authenticated = ssoIdObj != null && !ssoIdObj.toString().isEmpty() 
                                 && tokenObj != null && !tokenObj.toString().isEmpty();

            log.debug("[SSO] 인증 여부: {}", authenticated);
            
            return authenticated;

        } catch (Exception e) {
            log.error("[SSO] SSO 인증 여부 확인 실패: {}", e.getMessage(), e);
            return false;
        }
    }

    /**
     * SSO 사용자 ID(사번) 추출
     * 
     * @param request HttpServletRequest
     * @return String 사용자 ID (사번)
     */
    public String getSSOUserId(HttpServletRequest request) {
        try {
            SSOUserDto ssoUser = getSSOUserInfo(request);
            if (ssoUser != null && ssoUser.isAuthenticated()) {
                return ssoUser.getEmpCode();
            }
            return null;
        } catch (Exception e) {
            log.error("[SSO] SSO 사용자 ID 추출 실패: {}", e.getMessage(), e);
            return null;
        }
    }

    /**
     * SSO 활성화 여부 확인
     * 
     * @return boolean SSO 활성화 여부
     */
    public boolean isSSOEnabled() {
        return ssoUse;
    }
}

