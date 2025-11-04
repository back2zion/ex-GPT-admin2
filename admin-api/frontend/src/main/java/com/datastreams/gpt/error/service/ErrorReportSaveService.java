package com.datastreams.gpt.error.service;

import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.datastreams.gpt.error.dto.ErrorReportSaveRequestDto;
import com.datastreams.gpt.error.dto.ErrorReportSaveResponseDto;
import com.datastreams.gpt.error.mapper.ErrorReportSaveMapper;

/**
 * L-023: 오류 보고/오류 선택지 목록 저장 Service
 * 오류 보고 및 선택된 오류 코드들을 저장하는 비즈니스 로직 처리
 */
@Service
public class ErrorReportSaveService {
    
    private static final Logger logger = LoggerFactory.getLogger(ErrorReportSaveService.class);
    
    @Autowired
    private ErrorReportSaveMapper errorReportSaveMapper;
    
    /**
     * 오류 보고 및 선택지 목록 저장
     * @param requestDto 요청 데이터
     * @return 저장 결과 응답
     */
    @Transactional
    public ErrorReportSaveResponseDto saveErrorReport(ErrorReportSaveRequestDto requestDto) {
        long startTime = System.currentTimeMillis();
        
        try {
            // 입력 검증
            validateRequest(requestDto);
            
            // 데이터베이스에 오류 보고 및 선택지 목록 저장
            List<Map<String, Object>> resultList = errorReportSaveMapper.saveErrorReport(requestDto);
            
            // 저장된 오류 보고 코드 목록 조회
            List<String> savedErrRptCdList = errorReportSaveMapper.selectSavedErrorReportCodes(
                requestDto.getCnvsId(), requestDto.getUsrId());
            
            // 결과 분석
            String txnNm = "SAVE_ERROR_REPORT";
            Integer totalCnt = 0;
            
            for (Map<String, Object> result : resultList) {
                String resultTxnNm = (String) result.get("TXN_NM");
                Integer resultCnt = ((Number) result.get("CNT")).intValue();
                totalCnt += resultCnt;
                
                logger.info("L-023: 저장 결과 - 트랜잭션: {}, 건수: {}", resultTxnNm, resultCnt);
            }
            
            // 응답 DTO 생성
            ErrorReportSaveResponseDto responseDto = new ErrorReportSaveResponseDto();
            responseDto.setCnvsId(requestDto.getCnvsId());
            responseDto.setUsrId(requestDto.getUsrId());
            responseDto.setTxnNm(txnNm);
            responseDto.setCnt(totalCnt);
            responseDto.setStatus("success");
            responseDto.setProcessingTime(System.currentTimeMillis() - startTime);
            responseDto.setSavedErrRptCdList(savedErrRptCdList);
            
            logger.info("L-023: 오류 보고 저장 완료 - 대화ID: {}, 사용자ID: {}, 총건수: {}", 
                       requestDto.getCnvsId(), requestDto.getUsrId(), totalCnt);
            
            return responseDto;
            
        } catch (Exception e) {
            logger.error("L-023: 오류 보고 저장 실패 - 대화ID: {}, 사용자ID: {}", 
                        requestDto.getCnvsId(), requestDto.getUsrId(), e);
            
            ErrorReportSaveResponseDto errorResponse = new ErrorReportSaveResponseDto();
            errorResponse.setCnvsId(requestDto.getCnvsId());
            errorResponse.setUsrId(requestDto.getUsrId());
            errorResponse.setTxnNm("SAVE_ERROR_REPORT");
            errorResponse.setCnt(0);
            errorResponse.setStatus("error");
            errorResponse.setProcessingTime(System.currentTimeMillis() - startTime);
            errorResponse.setSavedErrRptCdList(List.of());
            
            return errorResponse;
        }
    }
    
    /**
     * 요청 데이터 검증
     * @param requestDto 요청 데이터
     */
    private void validateRequest(ErrorReportSaveRequestDto requestDto) {
        if (requestDto == null) {
            throw new IllegalArgumentException("요청 데이터가 null입니다.");
        }
        
        if (requestDto.getCnvsId() == null || requestDto.getCnvsId().trim().isEmpty()) {
            throw new IllegalArgumentException("대화 ID는 필수입니다.");
        }
        
        if (requestDto.getUsrId() == null || requestDto.getUsrId().trim().isEmpty()) {
            throw new IllegalArgumentException("사용자 ID는 필수입니다.");
        }
        
        if (requestDto.getErrRptTxt() == null || requestDto.getErrRptTxt().trim().isEmpty()) {
            throw new IllegalArgumentException("오류 보고 텍스트는 필수입니다.");
        }
        
        if (requestDto.getErrRptCdList() == null || requestDto.getErrRptCdList().isEmpty()) {
            throw new IllegalArgumentException("오류 보고 코드 목록은 필수입니다.");
        }
        
        // 오류 보고 코드 목록 검증
        for (String errRptCd : requestDto.getErrRptCdList()) {
            if (errRptCd == null || errRptCd.trim().isEmpty()) {
                throw new IllegalArgumentException("오류 보고 코드는 빈 값일 수 없습니다.");
            }
        }
    }
}
