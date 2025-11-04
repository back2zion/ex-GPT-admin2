package com.datastreams.gpt.chat.mapper;

import com.datastreams.gpt.chat.dto.*;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface ConversationHistoryMapper {
    
    /**
     * L-041: 이전 대화 이력 조회
     * @param requestDto 이전 대화 이력 조회 요청 DTO
     * @return 이전 대화 이력 조회 응답 DTO 리스트
     */
    List<ConversationHistoryResponseDto> selectConversationHistory(ConversationHistoryRequestDto requestDto);

    /**
     * L-027: 대화 목록 조회
     */
    List<ConversationListResponseDto> selectConversationList(ConversationListRequestDto requestDto);

    /**
     * L-028: 사용자 대화 조회
     */
    List<UserConversationResponseDto> selectUserConversation(ConversationListRequestDto requestDto);

    /**
     * L-029: 참조 문서 조회
     */
    List<ConversationListResponseDto> selectReferenceDocuments(ConversationListRequestDto requestDto);

    /**
     * L-030: 추가 질의 조회
     */
    List<ConversationListResponseDto> selectAdditionalQuestions(ConversationListRequestDto requestDto);

    /**
     * L-031: 업로드 파일 조회
     */
    List<ConversationListResponseDto> selectUploadFiles(ConversationListRequestDto requestDto);
}