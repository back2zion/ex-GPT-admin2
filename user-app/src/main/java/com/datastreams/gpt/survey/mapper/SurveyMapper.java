package com.datastreams.gpt.survey.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * 만족도 저장 MyBatis 매퍼 인터페이스
 */
@Mapper
public interface SurveyMapper {

    /**
     * 만족도 저장 (L-012)
     * 
     * @param usrId 사용자 아이디
     * @param ractTxt 만족도 평가 내용
     * @param ractLevelVal 만족도 레벨 값 (1~5)
     * @param sesnId 세션 아이디
     * @return 처리된 행 수
     */
    int saveSurvey(@Param("usrId") String usrId, 
                   @Param("ractTxt") String ractTxt,
                   @Param("ractLevelVal") Integer ractLevelVal,
                   @Param("sesnId") String sesnId);
}
