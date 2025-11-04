package com.datastreams.gpt.error.mapper;

import java.util.List;
import java.util.Map;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import com.datastreams.gpt.error.dto.ErrorReportSaveRequestDto;

/**
 * L-023: 오류 보고/오류 선택지 목록 저장 Mapper
 * 오류 보고 및 선택된 오류 코드들을 저장하기 위한 데이터베이스 접근 인터페이스
 */
@Mapper
public interface ErrorReportSaveMapper {
    
    /**
     * 오류 보고 및 선택지 목록 저장
     * @param requestDto 요청 데이터
     * @return 저장 결과 (트랜잭션명, 건수)
     */
    List<Map<String, Object>> saveErrorReport(ErrorReportSaveRequestDto requestDto);
    
    /**
     * 저장된 오류 보고 코드 목록 조회
     * @param cnvsId 대화 ID
     * @param usrId 사용자 ID
     * @return 저장된 오류 보고 코드 목록
     */
    List<String> selectSavedErrorReportCodes(@Param("cnvsId") String cnvsId, @Param("usrId") String usrId);
}
