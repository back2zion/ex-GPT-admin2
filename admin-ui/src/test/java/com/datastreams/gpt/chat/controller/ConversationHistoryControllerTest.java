package com.datastreams.gpt.chat.controller;

import com.datastreams.gpt.chat.dto.ConversationHistoryRequestDto;
import com.datastreams.gpt.chat.dto.ConversationHistoryResponseDto;
import com.datastreams.gpt.chat.service.ConversationHistoryService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Arrays;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(ConversationHistoryController.class)
class ConversationHistoryControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private ConversationHistoryService conversationHistoryService;

    @Autowired
    private ObjectMapper objectMapper;

    private ConversationHistoryRequestDto validRequest;
    private List<ConversationHistoryResponseDto> mockResponseList;

    @BeforeEach
    void setUp() {
        validRequest = new ConversationHistoryRequestDto();
        validRequest.setCnvsIdtId("testuser_20251016100000000");
        validRequest.setCnvsId(12345L);

        ConversationHistoryResponseDto response1 = new ConversationHistoryResponseDto();
        response1.setRowSeq(1);
        response1.setQuesTxt("첫 번째 질문입니다.");
        response1.setAnsTxt("첫 번째 답변입니다.");

        ConversationHistoryResponseDto response2 = new ConversationHistoryResponseDto();
        response2.setRowSeq(2);
        response2.setQuesTxt("두 번째 질문입니다.");
        response2.setAnsTxt("두 번째 답변입니다.");

        mockResponseList = Arrays.asList(response1, response2);
    }

    @Test
    @DisplayName("L-041: 이전 대화 이력 조회 성공")
    void getConversationHistory_success() throws Exception {
        when(conversationHistoryService.getConversationHistory(any(ConversationHistoryRequestDto.class)))
                .thenReturn(mockResponseList);

        mockMvc.perform(post("/api/chat/history/previous")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].ROW_SEQ").value(1))
                .andExpect(jsonPath("$[0].QUES_TXT").value("첫 번째 질문입니다."))
                .andExpect(jsonPath("$[0].ANS_TXT").value("첫 번째 답변입니다."))
                .andExpect(jsonPath("$[1].ROW_SEQ").value(2))
                .andExpect(jsonPath("$[1].QUES_TXT").value("두 번째 질문입니다."))
                .andExpect(jsonPath("$[1].ANS_TXT").value("두 번째 답변입니다."));
    }

    @Test
    @DisplayName("L-041: 이전 대화 이력 조회 실패 - 필수 파라미터 누락")
    void getConversationHistory_missingRequiredParam_returnsBadRequest() throws Exception {
        validRequest.setCnvsIdtId(null); // 대화 식별 아이디 누락

        when(conversationHistoryService.getConversationHistory(any(ConversationHistoryRequestDto.class)))
                .thenThrow(new IllegalArgumentException("대화 식별 아이디는 필수입니다."));

        mockMvc.perform(post("/api/chat/history/previous")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").value("대화 식별 아이디는 필수입니다."));
    }

    @Test
    @DisplayName("L-041: 이전 대화 이력 조회 실패 - 내부 서버 오류")
    void getConversationHistory_internalServerError_returnsInternalServerError() throws Exception {
        when(conversationHistoryService.getConversationHistory(any(ConversationHistoryRequestDto.class)))
                .thenThrow(new RuntimeException("데이터베이스 오류"));

        mockMvc.perform(post("/api/chat/history/previous")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.error").value("이전 대화 이력 조회 중 오류가 발생했습니다."));
    }
}