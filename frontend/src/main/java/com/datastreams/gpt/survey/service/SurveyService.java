package com.datastreams.gpt.survey.service;

import com.datastreams.gpt.survey.dto.SurveyRequestDto;
import com.datastreams.gpt.survey.mapper.SurveyMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/**
 * 만족도 저장 서비스
 */
@Service
public class SurveyService {

    private static final Logger log = LoggerFactory.getLogger(SurveyService.class);
    
    @Autowired
    private SurveyMapper surveyMapper;

    /**
     * 만족도 저장
     * L-012 기능정의서 기준
     * 
     * @param request 만족도 저장 요청 DTO
     * @return 저장 성공 여부
     */
    public boolean saveSurvey(SurveyRequestDto request) {
        try {
            log.info("[L-012 만족도 저장] 사용자: {}, 만족도: {}, 세션: {}", 
                    request.getUsrId(), request.getRactLevelVal(), request.getSesnId());
            
            // 만족도 레벨 값 유효성 검증 (1~5)
            if (request.getRactLevelVal() == null || 
                request.getRactLevelVal() < 1 || request.getRactLevelVal() > 5) {
                log.error("[L-012 만족도 저장] 잘못된 만족도 레벨 값: {}", request.getRactLevelVal());
                return false;
            }
            
            // L-012 기능정의서 INSERT 쿼리 실행
            int result = surveyMapper.saveSurvey(
                request.getUsrId(),
                request.getRactTxt(),
                request.getRactLevelVal(),
                request.getSesnId()
            );
            
            boolean success = result > 0;
            log.info("[L-012 만족도 저장] 결과: {}, 처리된 행 수: {}", success ? "성공" : "실패", result);
            
            return success;
            
        } catch (Exception e) {
            log.error("[L-012 만족도 저장] 오류 발생: {}", e.getMessage(), e);
            return false;
        }
    }
}
