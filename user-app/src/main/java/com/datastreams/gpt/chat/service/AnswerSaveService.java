package com.datastreams.gpt.chat.service;

import com.datastreams.gpt.chat.dto.AnswerSaveRequestDto;
import com.datastreams.gpt.chat.dto.AnswerSaveResponseDto;
import com.datastreams.gpt.chat.mapper.AnswerSaveMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@Transactional
public class AnswerSaveService {

    private static final Logger logger = LoggerFactory.getLogger(AnswerSaveService.class);

    @Autowired
    private AnswerSaveMapper answerSaveMapper;

    /**
     * L-034: 답변 저장
     * @param requestDto 답변 저장 요청 DTO
     * @return 답변 저장 응답 DTO 리스트
     * @throws Exception 처리 중 오류 발생 시
     */
    public List<AnswerSaveResponseDto> saveAnswer(AnswerSaveRequestDto requestDto) throws Exception {
        logger.info("답변 저장 시작 - 대화 식별 ID: {}, 대화 ID: {}", 
                   requestDto.getCnvsIdtId(), requestDto.getCnvsId());

        try {
            // 입력 파라미터 검증
            validateAnswerSaveRequest(requestDto);

            // 답변 저장 실행
            List<AnswerSaveResponseDto> responseList = answerSaveMapper.insertAnswerSave(requestDto);

            logger.info("답변 저장 완료 - 처리된 트랜잭션 수: {}", responseList.size());

            return responseList;

        } catch (IllegalArgumentException e) {
            logger.warn("답변 저장 요청 데이터 오류: {}", e.getMessage());
            throw e;
        } catch (Exception e) {
            logger.error("답변 저장 중 오류 발생", e);
            throw new Exception("답변 저장 중 오류가 발생했습니다: " + e.getMessage());
        }
    }

    /**
     * 답변 저장 요청 데이터 검증
     * @param requestDto 답변 저장 요청 DTO
     * @throws IllegalArgumentException 검증 실패 시
     */
    private void validateAnswerSaveRequest(AnswerSaveRequestDto requestDto) {
        if (requestDto == null) {
            throw new IllegalArgumentException("요청 데이터가 null입니다.");
        }
        if (requestDto.getCnvsIdtId() == null || requestDto.getCnvsIdtId().trim().isEmpty()) {
            throw new IllegalArgumentException("대화 식별 아이디는 필수입니다.");
        }
        if (requestDto.getCnvsId() == null) {
            throw new IllegalArgumentException("대화 아이디는 필수입니다.");
        }
        if (requestDto.getInfrTxt() == null || requestDto.getInfrTxt().trim().isEmpty()) {
            throw new IllegalArgumentException("추론 텍스트는 필수입니다.");
        }
        if (requestDto.getAnsTxt() == null || requestDto.getAnsTxt().trim().isEmpty()) {
            throw new IllegalArgumentException("답변 텍스트는 필수입니다.");
        }
        if (requestDto.getQroutTypCd() == null || requestDto.getQroutTypCd().trim().isEmpty()) {
            throw new IllegalArgumentException("쿼리라우팅 유형 코드는 필수입니다.");
        }
        if (requestDto.getDocCatSysCd() == null || requestDto.getDocCatSysCd().trim().isEmpty()) {
            throw new IllegalArgumentException("문서 분류 체계 코드는 필수입니다.");
        }
        if (requestDto.getSrchTimMs() == null) {
            throw new IllegalArgumentException("검색 시간은 필수입니다.");
        }
        if (requestDto.getRspTimMs() == null) {
            throw new IllegalArgumentException("응답 시간은 필수입니다.");
        }
        if (requestDto.getTknUseCnt() == null) {
            throw new IllegalArgumentException("토큰 사용 개수는 필수입니다.");
        }
        if (requestDto.getUsrId() == null || requestDto.getUsrId().trim().isEmpty()) {
            throw new IllegalArgumentException("사용자 아이디는 필수입니다.");
        }
        if (requestDto.getAnsAbrtYn() == null || requestDto.getAnsAbrtYn().trim().isEmpty()) {
            throw new IllegalArgumentException("답변 중지 여부는 필수입니다.");
        }
        if (!"Y".equals(requestDto.getAnsAbrtYn()) && !"N".equals(requestDto.getAnsAbrtYn())) {
            throw new IllegalArgumentException("답변 중지 여부는 Y 또는 N이어야 합니다.");
        }
        if (requestDto.getRefDocList() == null || requestDto.getRefDocList().isEmpty()) {
            throw new IllegalArgumentException("참조 문서 목록은 필수입니다.");
        }
        if (requestDto.getAddQuesList() == null || requestDto.getAddQuesList().isEmpty()) {
            throw new IllegalArgumentException("추가 질의 목록은 필수입니다.");
        }
    }
}
