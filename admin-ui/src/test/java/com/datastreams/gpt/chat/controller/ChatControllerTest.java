package com.datastreams.gpt.chat.controller;

import com.datastreams.gpt.chat.dto.ChatRequestDto;
import com.datastreams.gpt.chat.dto.ChatResponseDto;
import com.datastreams.gpt.chat.service.ChatService;
import com.datastreams.gpt.login.dto.UserInfoDto;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockHttpSession;
import org.springframework.test.web.servlet.MockMvc;

import java.util.ArrayList;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * ChatController 테스트 클래스
 * Spring Boot Test + MockMvc를 사용한 통합 테스트
 */
@WebMvcTest(ChatController.class)
class ChatControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private ChatService chatService;

    @Autowired
    private ObjectMapper objectMapper;

    private MockHttpSession session;
    private UserInfoDto userInfo;

    @BeforeEach
    void setUp() {
        // 테스트용 세션 설정
        session = new MockHttpSession();
        
        // 테스트용 사용자 정보 설정
        userInfo = new UserInfoDto();
        userInfo.setUsrId("test-user");
        userInfo.setUsrNm("테스트유저");
        userInfo.setDeptCd("D001");
        userInfo.setDeptNm("테스트부서");
        
        session.setAttribute("userInfo", userInfo);
    }

    @Test
    void processChatMessage_성공_테스트() throws Exception {
        // Given
        ChatRequestDto request = new ChatRequestDto();
        request.setStream(true);
        request.setMessageId("msg-001");
        request.setSessionId("session-001");
        request.setUserId("test-user");
        request.setSearchDocuments(true);
        request.setDepartment("D001");

        ChatResponseDto mockResponse = new ChatResponseDto();
        mockResponse.setMessageId("msg-001");
        mockResponse.setSessionId("session-001");
        mockResponse.setUserId("test-user");
        mockResponse.setResponse("안녕하세요! 무엇을 도와드릴까요?");
        mockResponse.setStatus("success");

        when(chatService.callPartnerApi(any(ChatRequestDto.class), any(UserInfoDto.class)))
                .thenReturn(mockResponse);

        // When & Then
        mockMvc.perform(post("/api/chat/conversation")
                .session(session)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.data.response").value("안녕하세요! 무엇을 도와드릴까요?"));
    }

    @Test
    void processChatMessage_세션_없음_테스트() throws Exception {
        // Given
        ChatRequestDto request = new ChatRequestDto();
        request.setMessageId("msg-001");

        // When & Then
        mockMvc.perform(post("/api/chat/conversation")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.error").value("세션이 만료되었습니다."));
    }

    @Test
    void processChatMessage_사용자정보_없음_테스트() throws Exception {
        // Given
        ChatRequestDto request = new ChatRequestDto();
        request.setMessageId("msg-001");

        MockHttpSession emptySession = new MockHttpSession();
        emptySession.setAttribute("userInfo", null);

        // When & Then
        mockMvc.perform(post("/api/chat/conversation")
                .session(emptySession)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.error").value("사용자 정보를 찾을 수 없습니다."));
    }

    @Test
    void getChatHistory_성공_테스트() throws Exception {
        // Given
        List<java.util.Map<String, Object>> mockHistory = new ArrayList<>();
        java.util.Map<String, Object> historyItem = new java.util.HashMap<>();
        historyItem.put("id", 1);
        historyItem.put("role", "user");
        historyItem.put("content", "안녕하세요!");
        mockHistory.add(historyItem);

        when(chatService.getChatHistory(anyString(), any(UserInfoDto.class)))
                .thenReturn(mockHistory);

        // When & Then
        mockMvc.perform(post("/api/chat/history")
                .session(session)
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"session_id\": \"session-001\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.data").isArray())
                .andExpect(jsonPath("$.data[0].content").value("안녕하세요!"));
    }

    @Test
    void resetChatSession_성공_테스트() throws Exception {
        // When & Then
        mockMvc.perform(post("/api/chat/reset")
                .session(session))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.message").value("채팅 세션이 초기화되었습니다."));
    }
}
