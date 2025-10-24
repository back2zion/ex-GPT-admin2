package com.datastreams.gpt.login.service;

import com.datastreams.gpt.login.dto.UserInfoDto;
import com.datastreams.gpt.login.mapper.UserMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/**
 * 사용자 정보 관리 서비스
 * L-005: 사용자 조회 기능
 */
@Service
public class UserService {
    
    private static final Logger log = LoggerFactory.getLogger(UserService.class);
    
    @Autowired
    private UserMapper userMapper;
    
    /**
     * 사용자 정보 조회 (L-005)
     * @param userId 사용자 ID
     * @return 사용자 상세 정보
     */
    public UserInfoDto getUserInfo(String userId) {
        try {
            UserInfoDto userInfo = userMapper.getUserInfo(userId);
            
            if (userInfo != null) {
                log.info("[L-005] 사용자 정보 조회 성공 - 사용자: {}, 이름: {}, 부서: {}", 
                    userId, userInfo.getUsrNm(), userInfo.getDeptNm());
            } else {
                log.warn("[L-005] 사용자 정보 없음 - 사용자: {}", userId);
            }
            
            return userInfo;
        } catch (Exception e) {
            log.error("[L-005] 사용자 정보 조회 실패 - 사용자: {}, 에러: {}", userId, e.getMessage());
            throw new RuntimeException("사용자 정보 조회 실패", e);
        }
    }
}
