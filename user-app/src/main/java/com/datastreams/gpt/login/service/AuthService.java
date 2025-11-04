package com.datastreams.gpt.login.service;

import org.springframework.stereotype.Service;

/**
 * 인증 관련 서비스
 * 향후 확장을 위한 서비스 레이어
 */
@Service
public class AuthService {
    
    /**
     * 사용자 인증 처리
     * @param username 사용자명
     * @param password 비밀번호
     * @return 인증 성공 여부
     */
    public boolean authenticate(String username, String password) {
        // admin/admin 조건 확인
        return "admin".equals(username) && "admin".equals(password);
    }
    
    /**
     * 세션 정보 생성
     * @param username 사용자명
     * @return 세션 정보
     */
    public java.util.Map<String, Object> createSessionInfo(String username) {
        java.util.Map<String, Object> sessionInfo = new java.util.HashMap<>();
        sessionInfo.put("user", username);
        sessionInfo.put("loginTime", System.currentTimeMillis());
        sessionInfo.put("role", "ADMIN");
        return sessionInfo;
    }
}


