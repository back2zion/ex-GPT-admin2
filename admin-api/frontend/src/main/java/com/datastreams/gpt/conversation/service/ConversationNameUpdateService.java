package com.datastreams.gpt.conversation.service;

import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.datastreams.gpt.conversation.dto.ConversationNameUpdateRequestDto;
import com.datastreams.gpt.conversation.dto.ConversationNameUpdateResponseDto;
import com.datastreams.gpt.conversation.mapper.ConversationNameUpdateMapper;

/**
 * L-025: 대화 대표 명 변경 Service
 * 대화 대표 명 및 사용 여부를 업데이트하는 비즈니스 로직 처리
 */
@Service
public class ConversationNameUpdateService {
    
    private static final Logger logger = LoggerFactory.getLogger(ConversationNameUpdateService.class);
    
    @Autowired
    private ConversationNameUpdateMapper conversationNameUpdateMapper;
    
    /**
     * 대화 대표 명 및 사용 여부 업데이트
     * @param requestDto 요청 데이터
     * @return 업데이트 결과 응답
     */
    @Transactional
    public ConversationNameUpdateResponseDto updateConversationName(ConversationNameUpdateRequestDto requestDto) {
        long startTime = System.currentTimeMillis();
        
        try {
            // 입력 검증
            validateRequest(requestDto);
            
            // 데이터베이스에서 대화 대표 명 및 사용 여부 업데이트
            List<Map<String, Object>> resultList = conversationNameUpdateMapper.updateConversationName(requestDto);
            
            // 업데이트된 대화 정보 조회
            Map<String, Object> updatedInfo = conversationNameUpdateMapper.selectUpdatedConversationInfo(requestDto.getCnvsIdtId());
            
            // 결과 분석
            String txnNm = "UPD_USR_CNVS_SMRY";
            Integer totalCnt = 0;
            
            for (Map<String, Object> result : resultList) {
                String resultTxnNm = (String) result.get("TXN_NM");
                Integer resultCnt = ((Number) result.get("CNT")).intValue();
                totalCnt += resultCnt;
                
                logger.info("L-025: 업데이트 결과 - 트랜잭션: {}, 건수: {}", resultTxnNm, resultCnt);
            }
            
            // 응답 DTO 생성
            ConversationNameUpdateResponseDto responseDto = new ConversationNameUpdateResponseDto();
            responseDto.setCnvsIdtId(requestDto.getCnvsIdtId());
            responseDto.setTxnNm(txnNm);
            responseDto.setCnt(totalCnt);
            responseDto.setStatus("success");
            responseDto.setProcessingTime(System.currentTimeMillis() - startTime);
            
            // 업데이트된 정보 설정
            if (updatedInfo != null) {
                responseDto.setUpdatedRepCnvsNm((String) updatedInfo.get("REP_CNVS_NM"));
                responseDto.setUpdatedUseYn((String) updatedInfo.get("USE_YN"));
            }
            
            logger.info("L-025: 대화 대표 명 변경 완료 - 대화ID: {}, 업데이트건수: {}", 
                       requestDto.getCnvsIdtId(), totalCnt);
            
            return responseDto;
            
        } catch (Exception e) {
            logger.error("L-025: 대화 대표 명 변경 실패 - 대화ID: {}", 
                        requestDto.getCnvsIdtId(), e);
            
            ConversationNameUpdateResponseDto errorResponse = new ConversationNameUpdateResponseDto();
            errorResponse.setCnvsIdtId(requestDto.getCnvsIdtId());
            errorResponse.setTxnNm("UPD_USR_CNVS_SMRY");
            errorResponse.setCnt(0);
            errorResponse.setStatus("error");
            errorResponse.setProcessingTime(System.currentTimeMillis() - startTime);
            
            return errorResponse;
        }
    }
    
    /**
     * 요청 데이터 검증
     * @param requestDto 요청 데이터
     */
    private void validateRequest(ConversationNameUpdateRequestDto requestDto) {
        if (requestDto == null) {
            throw new IllegalArgumentException("요청 데이터가 null입니다.");
        }
        
        if (requestDto.getCnvsIdtId() == null || requestDto.getCnvsIdtId().trim().isEmpty()) {
            throw new IllegalArgumentException("대화 식별 ID는 필수입니다.");
        }
        
        // 대화 대표 명과 사용 여부 중 하나는 필수
        if ((requestDto.getRepCnvsNm() == null || requestDto.getRepCnvsNm().trim().isEmpty()) &&
            (requestDto.getUseYn() == null || requestDto.getUseYn().trim().isEmpty())) {
            throw new IllegalArgumentException("대화 대표 명 또는 사용 여부 중 하나는 필수입니다.");
        }
        
        // 사용 여부 값 검증
        if (requestDto.getUseYn() != null && !requestDto.getUseYn().trim().isEmpty()) {
            String useYn = requestDto.getUseYn().trim().toUpperCase();
            if (!"Y".equals(useYn) && !"N".equals(useYn)) {
                throw new IllegalArgumentException("사용 여부는 'Y' 또는 'N'만 가능합니다.");
            }
        }
    }
}
