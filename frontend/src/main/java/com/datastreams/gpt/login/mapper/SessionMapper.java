package com.datastreams.gpt.login.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * 세션 관리 Mapper
 * MyBatis를 통한 DB 접근
 */
@Mapper
public interface SessionMapper {
    
    /**
     * 세션 기록 저장 (L-006)
     * @param userId 사용자 ID
     * @param ipAddr IP 주소
     * @param sessionId 세션 ID
     */
    void saveSessionRecord(@Param("userId") String userId, 
                          @Param("ipAddr") String ipAddr, 
                          @Param("sessionId") String sessionId);
    
    /**
     * 세션 유효 체크 (L-004)
     * @param userId 사용자 ID
     * @param sessionId 세션 ID
     * @return 세션 만료 여부 ('Y': 만료됨, 'N': 유효함)
     */
    String checkSessionValid(@Param("userId") String userId, 
                            @Param("sessionId") String sessionId);
}


