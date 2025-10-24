package com.datastreams.gpt.error.service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.datastreams.gpt.error.dto.ErrorChoiceDto;
import com.datastreams.gpt.error.dto.ErrorChoiceListRequestDto;
import com.datastreams.gpt.error.dto.ErrorChoiceListResponseDto;
import com.datastreams.gpt.error.mapper.ErrorChoiceListMapper;

/**
 * L-022: 오류 선택지 목록 조회 Service
 * 공통코드 레벨2 조회 비즈니스 로직 처리
 */
@Service
public class ErrorChoiceListService {
    
    private static final Logger logger = LoggerFactory.getLogger(ErrorChoiceListService.class);
    
    @Autowired
    private ErrorChoiceListMapper errorChoiceListMapper;
    
    /**
     * 오류 선택지 목록 조회
     * @param requestDto 요청 데이터
     * @return 오류 선택지 목록 응답
     */
    public ErrorChoiceListResponseDto getErrorChoiceList(ErrorChoiceListRequestDto requestDto) {
        long startTime = System.currentTimeMillis();
        
        try {
            // 입력 검증
            validateRequest(requestDto);
            
            // 데이터베이스에서 오류 선택지 목록 조회
            List<Map<String, Object>> resultList = errorChoiceListMapper.selectErrorChoiceList(requestDto);
            
            // 결과를 DTO로 변환
            List<ErrorChoiceDto> errorChoices = convertToErrorChoiceList(resultList);
            
            // 총 개수 조회
            Integer totalCount = errorChoiceListMapper.selectErrorChoiceCount(requestDto.getLevelN1Cd());
            
            // 응답 DTO 생성
            ErrorChoiceListResponseDto responseDto = new ErrorChoiceListResponseDto();
            responseDto.setLevelN1Cd(requestDto.getLevelN1Cd());
            responseDto.setErrorChoices(errorChoices);
            responseDto.setTotalCount(totalCount);
            responseDto.setStatus("success");
            responseDto.setProcessingTime(System.currentTimeMillis() - startTime);
            
            logger.info("L-022: 오류 선택지 목록 조회 완료 - 레벨1코드: {}, 조회건수: {}", 
                       requestDto.getLevelN1Cd(), errorChoices.size());
            
            return responseDto;
            
        } catch (Exception e) {
            logger.error("L-022: 오류 선택지 목록 조회 실패 - 레벨1코드: {}", requestDto.getLevelN1Cd(), e);
            
            ErrorChoiceListResponseDto errorResponse = new ErrorChoiceListResponseDto();
            errorResponse.setLevelN1Cd(requestDto.getLevelN1Cd());
            errorResponse.setErrorChoices(new ArrayList<>());
            errorResponse.setTotalCount(0);
            errorResponse.setStatus("error");
            errorResponse.setProcessingTime(System.currentTimeMillis() - startTime);
            
            return errorResponse;
        }
    }
    
    /**
     * 요청 데이터 검증
     * @param requestDto 요청 데이터
     */
    private void validateRequest(ErrorChoiceListRequestDto requestDto) {
        if (requestDto == null) {
            throw new IllegalArgumentException("요청 데이터가 null입니다.");
        }
        
        if (requestDto.getLevelN1Cd() == null || requestDto.getLevelN1Cd().trim().isEmpty()) {
            throw new IllegalArgumentException("레벨1 코드는 필수입니다.");
        }
    }
    
    /**
     * 데이터베이스 결과를 DTO 리스트로 변환
     * @param resultList 데이터베이스 조회 결과
     * @return ErrorChoiceDto 리스트
     */
    private List<ErrorChoiceDto> convertToErrorChoiceList(List<Map<String, Object>> resultList) {
        List<ErrorChoiceDto> errorChoices = new ArrayList<>();
        
        for (Map<String, Object> row : resultList) {
            ErrorChoiceDto errorChoice = new ErrorChoiceDto();
            
            // 데이터 타입 변환 및 설정
            if (row.get("LEVEL_N2_SEQ") != null) {
                errorChoice.setLevelN2Seq(((Number) row.get("LEVEL_N2_SEQ")).longValue());
            }
            errorChoice.setLevelN1Cd((String) row.get("LEVEL_N1_CD"));
            errorChoice.setLevelN2Cd((String) row.get("LEVEL_N2_CD"));
            errorChoice.setLevelN2Nm((String) row.get("LEVEL_N2_NM"));
            errorChoice.setUseYn((String) row.get("USE_YN"));
            
            if (row.get("CD_SEQ") != null) {
                errorChoice.setCdSeq(((Number) row.get("CD_SEQ")).longValue());
            }
            if (row.get("CD_SORT_SEQ") != null) {
                errorChoice.setCdSortSeq(((Number) row.get("CD_SORT_SEQ")).longValue());
            }
            if (row.get("TOT_CD_CNT") != null) {
                errorChoice.setTotCdCnt(((Number) row.get("TOT_CD_CNT")).longValue());
            }
            
            errorChoices.add(errorChoice);
        }
        
        return errorChoices;
    }
}
