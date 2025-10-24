package com.datastreams.gpt.user.service;

import com.datastreams.gpt.user.dto.UserSettingsDto;
import com.datastreams.gpt.user.mapper.UserSettingsMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/**
 * 사용자 설정 관리 서비스
 */
@Service
public class UserSettingsService {

    private static final Logger log = LoggerFactory.getLogger(UserSettingsService.class);
    
    @Autowired
    private UserSettingsMapper userSettingsMapper;

    /**
     * 사용자 설정 저장 (Upsert)
     * L-010 기능정의서 오리지널 쿼리 기준
     * 
     * @param userId 사용자 ID
     * @param settings 사용자 설정 정보
     * @return 저장 성공 여부
     */
    public boolean saveUserSettings(String userId, UserSettingsDto settings) {
        try {
            log.info("[L-010 사용자 설정 저장] 사용자: {}, 테마: {}, 폰트: {}", 
                    userId, settings.getUiThmCd(), settings.getFntSizeCd());
            
            // L-010 기능정의서 오리지널 Upsert 쿼리 실행
            int result = userSettingsMapper.saveOrUpdateUserSettings(
                userId,
                settings.getUiThmCd(),
                settings.getFntSizeCd(),
                settings.getSystemAccessYn(),
                settings.getManagerAuthYn(),
                settings.getVoiceModelUseYn(),
                settings.getImageModelUseYn()
            );
            
            boolean success = result > 0;
            log.info("[L-010 사용자 설정 저장] 결과: {}, 처리된 행 수: {}", success ? "성공" : "실패", result);
            
            return success;
            
        } catch (Exception e) {
            log.error("[L-010 사용자 설정 저장] 오류 발생: {}", e.getMessage(), e);
            return false;
        }
    }

    /**
     * 사용자 설정 조회
     * 
     * @param userId 사용자 ID
     * @return 사용자 설정 정보
     */
    public UserSettingsDto getUserSettings(String userId) {
        try {
            log.info("[사용자 설정 조회] 사용자: {}", userId);
            return userSettingsMapper.getUserSettings(userId);
        } catch (Exception e) {
            log.error("[사용자 설정 조회] 오류 발생: {}", e.getMessage(), e);
            return null;
        }
    }
}
