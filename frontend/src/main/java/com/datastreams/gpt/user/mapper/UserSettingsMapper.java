package com.datastreams.gpt.user.mapper;

import com.datastreams.gpt.user.dto.UserSettingsDto;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * 사용자 설정 MyBatis 매퍼 인터페이스
 */
@Mapper
public interface UserSettingsMapper {

    /**
     * 사용자 설정 조회
     * 
     * @param userId 사용자 ID
     * @return 사용자 설정 정보
     */
    UserSettingsDto getUserSettings(@Param("userId") String userId);

    /**
     * 사용자 설정 저장 또는 업데이트 (Upsert)
     * L-010 기능정의서 오리지널 쿼리 기준
     * 
     * @param userId 사용자 ID
     * @param uiThmCd UI 테마 코드
     * @param fntSizeCd 폰트 크기 코드
     * @param sysAccsYn 시스템 접근 여부
     * @param mgrAuthYn 관리자 권한 여부
     * @param vceMdlUseYn 음성 모델 사용 여부
     * @param imgMdlUseYn 이미지 모델 사용 여부
     * @return 처리된 행 수
     */
    int saveOrUpdateUserSettings(@Param("userId") String userId, 
                                @Param("uiThmCd") String uiThmCd,
                                @Param("fntSizeCd") String fntSizeCd,
                                @Param("sysAccsYn") String sysAccsYn,
                                @Param("mgrAuthYn") String mgrAuthYn,
                                @Param("vceMdlUseYn") String vceMdlUseYn,
                                @Param("imgMdlUseYn") String imgMdlUseYn);
}
