package com.datastreams.gpt.chat.service;

import com.datastreams.gpt.chat.dto.ChatRequestDto;
import com.datastreams.gpt.chat.dto.ChatResponseDto;
import com.datastreams.gpt.chat.dto.ChatMessageDto;
import com.datastreams.gpt.chat.mapper.ChatMapper;
import com.datastreams.gpt.login.dto.UserInfoDto;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * ChatService 테스트 클래스
 * JUnit 5 + Mockito를 사용한 단위 테스트
 */
@ExtendWith(MockitoExtension.class)
class ChatServiceTest {

    @Mock
    private ChatMapper chatMapper;

    @Mock
    private RestTemplate restTemplate;

    @InjectMocks
    private ChatService chatService;

    private UserInfoDto userInfo;
    private ChatRequestDto chatRequest;

    @BeforeEach
    void setUp() {
        // 설정 값 주입
        ReflectionTestUtils.setField(chatService, "aiServerUrl", "http://localhost:8083");
        ReflectionTestUtils.setField(chatService, "apiKey", "test-api-key");

        // 테스트용 사용자 정보 설정
        userInfo = new UserInfoDto();
        userInfo.setUsrId("test-user");
        userInfo.setUsrNm("테스트유저");
        userInfo.setDeptCd("D001");
        userInfo.setDeptNm("테스트부서");

        // 테스트용 채팅 요청 설정
        chatRequest = new ChatRequestDto();
        chatRequest.setStream(true);
        chatRequest.setMessageId("msg-001");
        chatRequest.setSessionId("session-001");
        chatRequest.setUserId("test-user");
        chatRequest.setSearchDocuments(true);
        chatRequest.setDepartment("D001");

        // 히스토리 설정
        List<ChatMessageDto> history = new ArrayList<>();
        ChatMessageDto message = new ChatMessageDto();
        message.setRole("user");
        message.setContent("안녕하세요!");
        history.add(message);
        chatRequest.setHistory(history);
    }

    @Test
    void callPartnerApi_성공_테스트() {
        // Given
        ChatResponseDto mockResponse = new ChatResponseDto();
        mockResponse.setMessageId("msg-001");
        mockResponse.setSessionId("session-001");
        mockResponse.setUserId("test-user");
        mockResponse.setResponse("안녕하세요! 무엇을 도와드릴까요?");
        mockResponse.setStatus("success");

        ResponseEntity<ChatResponseDto> responseEntity = new ResponseEntity<>(mockResponse, HttpStatus.OK);

        when(restTemplate.exchange(
                eq("http://localhost:8083/v1/chat/"),
                eq(HttpMethod.POST),
                any(HttpEntity.class),
                eq(ChatResponseDto.class)
        )).thenReturn(responseEntity);

        // When
        ChatResponseDto result = chatService.callPartnerApi(chatRequest, userInfo);

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getResponse()).isEqualTo("안녕하세요! 무엇을 도와드릴까요?");
        assertThat(result.getStatus()).isEqualTo("success");

        // 채팅 히스토리 저장이 호출되었는지 확인
        verify(chatMapper, times(2)).saveChatMessage(
                anyString(),
                eq("test-user"),
                anyString(),
                anyString(),
                anyString()
        );
    }

    @Test
    void callPartnerApi_API_오류_테스트() {
        // Given
        when(restTemplate.exchange(
                eq("http://localhost:8083/v1/chat/"),
                eq(HttpMethod.POST),
                any(HttpEntity.class),
                eq(ChatResponseDto.class)
        )).thenThrow(new RuntimeException("API 호출 실패"));

        // When
        ChatResponseDto result = chatService.callPartnerApi(chatRequest, userInfo);

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getStatus()).isEqualTo("error");
        assertThat(result.getError()).contains("API 호출 중 오류 발생");
    }

    @Test
    void getChatHistory_테스트() {
        // Given
        String sessionId = "session-001";
        List<java.util.Map<String, Object>> mockHistory = new ArrayList<>();
        java.util.Map<String, Object> historyItem = new java.util.HashMap<>();
        historyItem.put("id", 1);
        historyItem.put("role", "user");
        historyItem.put("content", "안녕하세요!");
        mockHistory.add(historyItem);

        when(chatMapper.getChatHistory(sessionId, "test-user")).thenReturn(mockHistory);

        // When
        List<java.util.Map<String, Object>> result = chatService.getChatHistory(sessionId, userInfo);

        // Then
        assertThat(result).isNotNull();
        assertThat(result).hasSize(1);
        assertThat(result.get(0).get("content")).isEqualTo("안녕하세요!");
    }

    @Test
    void resetChatSession_테스트() {
        // Given
        String sessionId = "session-001";

        // When
        chatService.resetChatSession(sessionId, userInfo);

        // Then
        verify(chatMapper).deleteChatHistory(sessionId, "test-user");
    }
}
