package com.datastreams.gpt.chat.service;

import com.datastreams.gpt.chat.dto.*;
import com.datastreams.gpt.chat.mapper.ConversationHistoryMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@Transactional(readOnly = true)
public class ConversationHistoryService {

    private static final Logger logger = LoggerFactory.getLogger(ConversationHistoryService.class);

    @Autowired
    private ConversationHistoryMapper conversationHistoryMapper;

    /**
     * L-041: 이전 대화 이력 조회
     * @param requestDto 이전 대화 이력 조회 요청 DTO
     * @return 이전 대화 이력 조회 응답 DTO 리스트
     * @throws Exception 처리 중 오류 발생 시
     */
    public List<ConversationHistoryResponseDto> getConversationHistory(ConversationHistoryRequestDto requestDto) throws Exception {
        logger.info("이전 대화 이력 조회 시작 - 대화 식별 ID: {}, 대화 ID: {}", 
                   requestDto.getCnvsIdtId(), requestDto.getCnvsId());

        try {
            // 입력 파라미터 검증
            validateConversationHistoryRequest(requestDto);

            // 이전 대화 이력 조회
            List<ConversationHistoryResponseDto> historyList = conversationHistoryMapper.selectConversationHistory(requestDto);

            logger.info("이전 대화 이력 조회 완료 - 조회된 이력 수: {}", historyList.size());

            return historyList;

        } catch (IllegalArgumentException e) {
            logger.warn("이전 대화 이력 조회 요청 데이터 오류: {}", e.getMessage());
            throw e;
        } catch (Exception e) {
            logger.error("이전 대화 이력 조회 중 오류 발생", e);
            throw new Exception("이전 대화 이력 조회 중 오류가 발생했습니다: " + e.getMessage());
        }
    }

    /**
     * 이전 대화 이력 조회 요청 데이터 검증
     * @param requestDto 이전 대화 이력 조회 요청 DTO
     * @throws IllegalArgumentException 검증 실패 시
     */
    private void validateConversationHistoryRequest(ConversationHistoryRequestDto requestDto) {
        if (requestDto == null) {
            throw new IllegalArgumentException("요청 데이터가 null입니다.");
        }
        if (requestDto.getCnvsIdtId() == null || requestDto.getCnvsIdtId().trim().isEmpty()) {
            throw new IllegalArgumentException("대화 식별 아이디는 필수입니다.");
        }
        if (requestDto.getCnvsId() == null) {
            throw new IllegalArgumentException("대화 아이디는 필수입니다.");
        }
    }
    /**
     * L-027: 대화 목록 조회
     */
    public List<ConversationListResponseDto> getConversationList(ConversationListRequestDto requestDto) throws Exception {
        logger.info("대화 목록 조회 시작");
        try {
            return conversationHistoryMapper.selectConversationList(requestDto);
        } catch (Exception e) {
            logger.error("대화 목록 조회 중 오류 발생", e);
            throw new Exception("대화 목록 조회 중 오류가 발생했습니다: " + e.getMessage());
        }
    }

    /**
     * L-028: 사용자 대화 조회
     */
    public List<UserConversationResponseDto> getUserConversation(ConversationListRequestDto requestDto) throws Exception {
        logger.info("사용자 대화 조회 시작");
        try {
            return conversationHistoryMapper.selectUserConversation(requestDto);
        } catch (Exception e) {
            logger.error("사용자 대화 조회 중 오류 발생", e);
            throw new Exception("사용자 대화 조회 중 오류가 발생했습니다: " + e.getMessage());
        }
    }

    /**
     * L-029: 참조 문서 조회
     */
    public List<ConversationListResponseDto> getReferenceDocuments(ConversationListRequestDto requestDto) throws Exception {
        logger.info("참조 문서 조회 시작");
        try {
            return conversationHistoryMapper.selectReferenceDocuments(requestDto);
        } catch (Exception e) {
            logger.error("참조 문서 조회 중 오류 발생", e);
            throw new Exception("참조 문서 조회 중 오류가 발생했습니다: " + e.getMessage());
        }
    }

    /**
     * L-030: 추가 질의 조회
     */
    public List<ConversationListResponseDto> getAdditionalQuestions(ConversationListRequestDto requestDto) throws Exception {
        logger.info("추가 질의 조회 시작");
        try {
            return conversationHistoryMapper.selectAdditionalQuestions(requestDto);
        } catch (Exception e) {
            logger.error("추가 질의 조회 중 오류 발생", e);
            throw new Exception("추가 질의 조회 중 오류가 발생했습니다: " + e.getMessage());
        }
    }

    /**
     * L-031: 업로드 파일 조회
     */
    public List<ConversationListResponseDto> getUploadFiles(ConversationListRequestDto requestDto) throws Exception {
        logger.info("업로드 파일 조회 시작");
        try {
            return conversationHistoryMapper.selectUploadFiles(requestDto);
        } catch (Exception e) {
            logger.error("업로드 파일 조회 중 오류 발생", e);
            throw new Exception("업로드 파일 조회 중 오류가 발생했습니다: " + e.getMessage());
        }
    }
}