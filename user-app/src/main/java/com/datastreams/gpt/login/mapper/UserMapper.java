package com.datastreams.gpt.login.mapper;

import com.datastreams.gpt.login.dto.UserInfoDto;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * 사용자 정보 조회 Mapper
 * L-005: 사용자 조회 기능
 */
@Mapper
public interface UserMapper {
    
    /**
     * 사용자 정보 조회 (L-005)
     * @param userId 사용자 ID
     * @return 사용자 상세 정보
     */
    UserInfoDto getUserInfo(@Param("userId") String userId);
}
