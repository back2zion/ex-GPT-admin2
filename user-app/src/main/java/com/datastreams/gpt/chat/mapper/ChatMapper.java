package com.datastreams.gpt.chat.mapper;

import java.util.List;
import java.util.Map;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * Chat Mapper
 * 채팅 관련 데이터베이스 작업을 담당하는 매퍼 인터페이스
 * 
 * @Version: 1.0
 * @Author: create by TeamS
 * @Desc: AI Chat Mapper
 */
@Mapper
public interface ChatMapper {
    
    /**
     * 채팅 메시지 저장
     * 
     * @param sessionId 세션 ID
     * @param userId 사용자 ID
     * @param role 역할 (user/assistant)
     * @param content 메시지 내용
     * @param roomId 룸아이디 (CNVS_IDT_ID)
     */
    void saveChatMessage(
        @Param("sessionId") String sessionId,
        @Param("userId") String userId,
        @Param("role") String role,
        @Param("content") String content,
        @Param("roomId") String roomId
    );
    
    /**
     * 채팅 히스토리 조회
     * 
     * @param sessionId 세션 ID
     * @param userId 사용자 ID
     * @return 채팅 히스토리 목록
     */
    List<Map<String, Object>> getChatHistory(
        @Param("sessionId") String sessionId,
        @Param("userId") String userId
    );
    
    /**
     * 채팅 히스토리 삭제
     * 
     * @param sessionId 세션 ID
     * @param userId 사용자 ID
     */
    void deleteChatHistory(
        @Param("sessionId") String sessionId,
        @Param("userId") String userId
    );
    
    /**
     * 사용자별 채팅 세션 목록 조회
     * 
     * @param userId 사용자 ID
     * @return 세션 목록
     */
    List<Map<String, Object>> getUserChatSessions(@Param("userId") String userId);
    
    /**
     * 특정 세션의 메시지 수 조회
     * 
     * @param sessionId 세션 ID
     * @param userId 사용자 ID
     * @return 메시지 수
     */
    int getChatMessageCount(
        @Param("sessionId") String sessionId,
        @Param("userId") String userId
    );
    
    /**
     * 룸아이디별 채팅 히스토리 조회
     * 
     * @param roomId 룸아이디
     * @param userId 사용자 ID
     * @return 채팅 히스토리 목록
     */
    List<Map<String, Object>> getChatHistoryByRoomId(
        @Param("roomId") String roomId,
        @Param("userId") String userId
    );
    
    /**
     * 룸아이디별 메시지 수 조회
     *
     * @param roomId 룸아이디
     * @param userId 사용자 ID
     * @return 메시지 수
     */
    int getChatMessageCountByRoomId(
        @Param("roomId") String roomId,
        @Param("userId") String userId
    );

    /**
     * roomId가 특정 사용자의 것인지 검증 (Stateless 방식)
     *
     * @param roomId 룸아이디 (CNVS_IDT_ID)
     * @param userId 사용자 ID
     * @return 유효하면 true, 아니면 false
     */
    boolean isValidRoomIdForUser(
        @Param("roomId") String roomId,
        @Param("userId") String userId
    );
}
