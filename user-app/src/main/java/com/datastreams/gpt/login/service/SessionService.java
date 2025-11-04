package com.datastreams.gpt.login.service;

import com.datastreams.gpt.login.mapper.SessionMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/**
 * 세션 관리 서비스
 * DB를 통한 세션 저장 및 유효성 검증
 */
@Service
public class SessionService {
    
    private static final Logger log = LoggerFactory.getLogger(SessionService.class);
    
    @Autowired
    private SessionMapper sessionMapper;
    
    /**
     * 로그인 시 세션 기록 저장 (L-006)
     * @param userId 사용자 ID
     * @param ipAddr IP 주소
     * @param sessionId 세션 ID
     */
    public void saveSessionRecord(String userId, String ipAddr, String sessionId) {
        try {
            sessionMapper.saveSessionRecord(userId, ipAddr, sessionId);
            log.info("[L-006] 세션 기록 저장 완료 - 사용자: {}, IP: {}, 세션ID: {}", userId, ipAddr, sessionId);
        } catch (Exception e) {
            log.error("[L-006] 세션 기록 저장 실패 - 사용자: {}, 에러: {}", userId, e.getMessage());
            throw new RuntimeException("세션 기록 저장 실패", e);
        }
    }
    
    /**
     * 세션 유효성 체크 (L-004)
     * @param userId 사용자 ID
     * @param sessionId 세션 ID
     * @return true: 유효함, false: 만료됨
     */
    public boolean isSessionValid(String userId, String sessionId) {
        try {
            String result = sessionMapper.checkSessionValid(userId, sessionId);
            // 'N' = 유효함, 'Y' = 만료됨
            boolean isValid = "N".equals(result);
            
            if (isValid) {
                log.info("[L-004] 세션 유효 - 사용자: {}, 세션ID: {}", userId, sessionId);
            } else {
                log.warn("[L-004] 세션 만료 - 사용자: {}, 세션ID: {}", userId, sessionId);
            }
            
            return isValid;
        } catch (Exception e) {
            log.error("[L-004] 세션 유효성 체크 실패 - 사용자: {}, 에러: {}", userId, e.getMessage());
            // 에러 발생 시 안전하게 false 반환
            return false;
        }
    }
}


