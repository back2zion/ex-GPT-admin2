package com.datastreams.gpt.chat.service;

import com.datastreams.gpt.chat.dto.QuerySaveRequestDto;
import com.datastreams.gpt.chat.dto.QuerySaveResponseDto;
import com.datastreams.gpt.chat.mapper.QuerySaveMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class QuerySaveService {

    private static final Logger logger = LoggerFactory.getLogger(QuerySaveService.class);

    @Autowired
    private QuerySaveMapper querySaveMapper;

    /**
     * L-033: 질의 저장
     * @param requestDto 질의 저장 요청 DTO
     * @return 질의 저장 응답 DTO
     * @throws Exception 처리 중 오류 발생 시
     */
    public QuerySaveResponseDto saveQuery(QuerySaveRequestDto requestDto) throws Exception {
        logger.info("질의 저장 시작 - 사용자: {}, 질의: {}", requestDto.getUsrId(), 
                   requestDto.getQuesTxt() != null ? requestDto.getQuesTxt().substring(0, Math.min(50, requestDto.getQuesTxt().length())) : "null");

        try {
            // 입력 파라미터 검증
            validateQuerySaveRequest(requestDto);

            // 질의 저장 실행
            QuerySaveResponseDto response = querySaveMapper.insertQuerySave(requestDto);

            logger.info("질의 저장 완료 - 대화 식별 ID: {}, 대화 ID: {}", 
                       response.getCnvsIdtId(), response.getCnvsId());

            return response;

        } catch (IllegalArgumentException e) {
            logger.warn("질의 저장 요청 데이터 오류: {}", e.getMessage());
            throw e;
        } catch (Exception e) {
            logger.error("질의 저장 중 오류 발생", e);
            throw new Exception("질의 저장 중 오류가 발생했습니다: " + e.getMessage());
        }
    }

    /**
     * 질의 저장 요청 데이터 검증
     * @param requestDto 질의 저장 요청 DTO
     * @throws IllegalArgumentException 검증 실패 시
     */
    private void validateQuerySaveRequest(QuerySaveRequestDto requestDto) {
        if (requestDto == null) {
            throw new IllegalArgumentException("요청 데이터가 null입니다.");
        }
        if (requestDto.getQuesTxt() == null || requestDto.getQuesTxt().trim().isEmpty()) {
            throw new IllegalArgumentException("질의 텍스트는 필수입니다.");
        }
        if (requestDto.getSesnId() == null || requestDto.getSesnId().trim().isEmpty()) {
            throw new IllegalArgumentException("세션 아이디는 필수입니다.");
        }
        if (requestDto.getUsrId() == null || requestDto.getUsrId().trim().isEmpty()) {
            throw new IllegalArgumentException("사용자 ID는 필수입니다.");
        }
        if (requestDto.getMenuIdtId() == null || requestDto.getMenuIdtId().trim().isEmpty()) {
            throw new IllegalArgumentException("메뉴 식별 아이디는 필수입니다.");
        }
        if (requestDto.getRcmQuesYn() == null || requestDto.getRcmQuesYn().trim().isEmpty()) {
            throw new IllegalArgumentException("추천 질의 여부는 필수입니다.");
        }
        if (!"Y".equals(requestDto.getRcmQuesYn()) && !"N".equals(requestDto.getRcmQuesYn())) {
            throw new IllegalArgumentException("추천 질의 여부는 Y 또는 N이어야 합니다.");
        }
    }
}
