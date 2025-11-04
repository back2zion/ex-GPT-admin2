package com.datastreams.gpt.chat.service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import com.datastreams.gpt.chat.dto.ChatRequestDto;
import com.datastreams.gpt.chat.dto.ChatResponseDto;
import com.datastreams.gpt.chat.dto.ChatMessageDto;
import com.datastreams.gpt.chat.dto.SearchConfigDto;
import com.datastreams.gpt.chat.mapper.ChatMapper;
import com.datastreams.gpt.login.dto.UserInfoDto;

/**
 * Chat Service
 * /v1/chat API와 연동하여 채팅 기능 제공
 * 
 * @Version: 1.0
 * @Author: create by TeamS
 * @Desc: AI Chat Service
 */
@Service
public class ChatService {
    
    private static final Logger logger = LoggerFactory.getLogger(ChatService.class);
    
    @Autowired
    private ChatMapper chatMapper;
    
    @Autowired
    private RestTemplate restTemplate;
    
    @Value("${ds.ai.server.url:http://localhost:8083}")
    private String aiServerUrl;
    
    @Value("${ds.ai.api.key:z3JE1M8huXmNux6y}")
    private String apiKey;
    
    
    /**
     * 외부 API 호출
     * 
     * @param request 채팅 요청 데이터
     * @param userInfo 사용자 정보
     * @return 채팅 응답 데이터
     */
    public ChatResponseDto callPartnerApi(ChatRequestDto request, UserInfoDto userInfo) {
        logger.debug("### callPartnerApi ###");
        logger.debug("Request: {}", request);
        logger.debug("UserInfo: {}", userInfo);
        
        try {
            // 요청 데이터 준비
            ChatRequestDto partnerRequest = preparePartnerRequest(request, userInfo);
            
            // HTTP 헤더 설정 (FirstController 방식 적용)
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("X-API-Key", apiKey);  // FirstController와 동일한 방식
            headers.set("X-User-ID", userInfo.getUsrId());
            headers.set("X-Department", userInfo.getDeptCd());
            
            // HTTP 엔티티 생성
            HttpEntity<ChatRequestDto> entity = new HttpEntity<>(partnerRequest, headers);
            
            // 외부 API 호출
            String apiUrl = aiServerUrl + "/v1/chat/";
            logger.debug("Calling partner API: {}", apiUrl);
            
            ResponseEntity<ChatResponseDto> response = restTemplate.exchange(
                apiUrl, 
                HttpMethod.POST, 
                entity, 
                ChatResponseDto.class
            );
            
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                ChatResponseDto chatResponse = response.getBody();
                
                // 채팅 히스토리 저장
                saveChatHistory(partnerRequest, chatResponse, userInfo);
                
                return chatResponse;
            } else {
                logger.error("Partner API call failed: {}", response.getStatusCode());
                return createErrorResponse("외부 API 호출 실패");
            }
            
        } catch (Exception e) {
            logger.error("Error calling partner API: ", e);
            return createErrorResponse("API 호출 중 오류 발생: " + e.getMessage());
        }
    }
    
    /**
     * 외부 API 요청 데이터 준비
     * 
     * @param request 원본 요청
     * @param userInfo 사용자 정보
     * @return 외부 API 요청 데이터
     */
    private ChatRequestDto preparePartnerRequest(ChatRequestDto request, UserInfoDto userInfo) {
        ChatRequestDto partnerRequest = new ChatRequestDto();
        
        // 기본 설정
        partnerRequest.setStream(request.getStream() != null ? request.getStream() : true);
        partnerRequest.setHistory(request.getHistory() != null ? request.getHistory() : new ArrayList<>());
        partnerRequest.setMessageId(request.getMessageId());
        partnerRequest.setSessionId(request.getSessionId());
        partnerRequest.setUserId(userInfo.getUsrId());
        partnerRequest.setSearchDocuments(request.getSearchDocuments() != null ? request.getSearchDocuments() : true);
        partnerRequest.setDepartment(userInfo.getDeptCd());
        partnerRequest.setAuthorization("Bearer " + apiKey);  // FirstController와 동일한 방식
        partnerRequest.setSearchScope(request.getSearchScope());
        
        // 검색 설정
        SearchConfigDto searchConfig = new SearchConfigDto();
        searchConfig.setMaxDocuments(20);
        searchConfig.setMinRelevanceScore(0.4);
        searchConfig.setDocumentTypes(new ArrayList<>());
        searchConfig.setDateRange(new HashMap<>());
        searchConfig.setPrioritySources(new ArrayList<>());
        searchConfig.setDoRerank(true);
        partnerRequest.setSearchConfig(searchConfig);
                       
        // 기타 설정
        partnerRequest.setMaxContextTokens(10000);
        partnerRequest.setTemperature(0.3);
        partnerRequest.setSuggestQuestions(false);
        partnerRequest.setGenerateSearchQuery(true);
        partnerRequest.setThinkMode(true);
        partnerRequest.setCurrentTime(String.valueOf(System.currentTimeMillis()));
        
        return partnerRequest;
    }
    
    /**
     * 채팅 히스토리 저장
     * 
     * @param request 요청 데이터
     * @param response 응답 데이터
     * @param userInfo 사용자 정보
     */
    private void saveChatHistory(ChatRequestDto request, ChatResponseDto response, UserInfoDto userInfo) {
        try {
            // 사용자 메시지 저장
            if (request.getHistory() != null && !request.getHistory().isEmpty()) {
                ChatMessageDto lastMessage = request.getHistory().get(request.getHistory().size() - 1);
                if ("user".equals(lastMessage.getRole())) {
                    chatMapper.saveChatMessage(
                        request.getSessionId(),
                        userInfo.getUsrId(),
                        "user",
                        lastMessage.getContent(),
                        null
                    );
                }
            }
            
            // AI 응답 저장
            if (response.getResponse() != null) {
                chatMapper.saveChatMessage(
                    response.getSessionId(),
                    userInfo.getUsrId(),
                    "assistant",
                    response.getResponse(),
                    response.getCitations() != null ? response.getCitations().toString() : null
                );
            }
            
        } catch (Exception e) {
            logger.error("Error saving chat history: ", e);
        }
    }
    
    /**
     * 채팅 히스토리 조회
     * 
     * @param sessionId 세션 ID
     * @param userInfo 사용자 정보
     * @return 채팅 히스토리
     */
    public List<Map<String, Object>> getChatHistory(String sessionId, UserInfoDto userInfo) {
        logger.debug("### getChatHistory ###");
        logger.debug("SessionId: {}, UserId: {}", sessionId, userInfo.getUsrId());
        
        try {
            return chatMapper.getChatHistory(sessionId, userInfo.getUsrId());
        } catch (Exception e) {
            logger.error("Error getting chat history: ", e);
            return new ArrayList<>();
        }
    }
    
    /**
     * 채팅 세션 초기화
     * 
     * @param sessionId 세션 ID
     * @param userInfo 사용자 정보
     */
    public void resetChatSession(String sessionId, UserInfoDto userInfo) {
        logger.debug("### resetChatSession ###");
        logger.debug("SessionId: {}, UserId: {}", sessionId, userInfo.getUsrId());
        
        try {
            chatMapper.deleteChatHistory(sessionId, userInfo.getUsrId());
        } catch (Exception e) {
            logger.error("Error resetting chat session: ", e);
        }
    }
    
    /**
     * 에러 응답 생성
     * 
     * @param errorMessage 에러 메시지
     * @return 에러 응답
     */
    private ChatResponseDto createErrorResponse(String errorMessage) {
        ChatResponseDto errorResponse = new ChatResponseDto();
        errorResponse.setStatus("error");
        errorResponse.setError(errorMessage);
        return errorResponse;
    }
}
