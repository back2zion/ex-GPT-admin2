package com.datastreams.gpt.conversation.controller;

import com.datastreams.gpt.conversation.dto.ConversationNameUpdateRequestDto;
import com.datastreams.gpt.conversation.dto.ConversationNameUpdateResponseDto;
import com.datastreams.gpt.conversation.service.ConversationNameUpdateService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(ConversationNameUpdateController.class)
public class ConversationNameUpdateControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private ConversationNameUpdateService conversationNameUpdateService;

    @Autowired
    private ObjectMapper objectMapper;

    private ConversationNameUpdateRequestDto validRequest;
    private ConversationNameUpdateResponseDto successResponse;
    private ConversationNameUpdateResponseDto errorResponse;

    @BeforeEach
    void setUp() {
        // 유효한 요청 데이터 설정
        validRequest = new ConversationNameUpdateRequestDto();
        validRequest.setCnvsIdtId("CNVS_12345");
        validRequest.setRepCnvsNm("새로운 대화명");
        validRequest.setUseYn("Y");
        
        // 성공 응답 설정
        successResponse = new ConversationNameUpdateResponseDto();
        successResponse.setCnvsIdtId("CNVS_12345");
        successResponse.setTxnNm("UPD_USR_CNVS_SMRY");
        successResponse.setCnt(1);
        successResponse.setStatus("success");
        successResponse.setProcessingTime(100L);
        successResponse.setUpdatedRepCnvsNm("새로운 대화명");
        successResponse.setUpdatedUseYn("Y");
        
        // 오류 응답 설정
        errorResponse = new ConversationNameUpdateResponseDto();
        errorResponse.setCnvsIdtId("CNVS_12345");
        errorResponse.setTxnNm("UPD_USR_CNVS_SMRY");
        errorResponse.setCnt(0);
        errorResponse.setStatus("error");
        errorResponse.setProcessingTime(0L);
    }

    @Test
    @DisplayName("L-025: 대화 대표 명 변경 성공")
    void updateConversationName_success() throws Exception {
        // Given
        when(conversationNameUpdateService.updateConversationName(any(ConversationNameUpdateRequestDto.class)))
                .thenReturn(successResponse);

        // When & Then
        mockMvc.perform(put("/api/conversation/v1/name")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.cnvsIdtId").value("CNVS_12345"))
                .andExpect(jsonPath("$.txnNm").value("UPD_USR_CNVS_SMRY"))
                .andExpect(jsonPath("$.cnt").value(1))
                .andExpect(jsonPath("$.status").value("success"))
                .andExpect(jsonPath("$.updatedRepCnvsNm").value("새로운 대화명"))
                .andExpect(jsonPath("$.updatedUseYn").value("Y"));
    }

    @Test
    @DisplayName("L-025: 대화 대표 명 변경 실패 - 서비스 오류")
    void updateConversationName_serviceError() throws Exception {
        // Given
        when(conversationNameUpdateService.updateConversationName(any(ConversationNameUpdateRequestDto.class)))
                .thenReturn(errorResponse);

        // When & Then
        mockMvc.perform(put("/api/conversation/v1/name")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.cnvsIdtId").value("CNVS_12345"))
                .andExpect(jsonPath("$.status").value("error"))
                .andExpect(jsonPath("$.cnt").value(0));
    }

    @Test
    @DisplayName("L-025: 대화 대표 명 변경 실패 - 잘못된 요청")
    void updateConversationName_badRequest() throws Exception {
        // Given
        when(conversationNameUpdateService.updateConversationName(any(ConversationNameUpdateRequestDto.class)))
                .thenThrow(new IllegalArgumentException("대화 식별 ID는 필수입니다."));

        // When & Then
        mockMvc.perform(put("/api/conversation/v1/name")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.cnvsIdtId").value("CNVS_12345"))
                .andExpect(jsonPath("$.status").value("error"));
    }

    @Test
    @DisplayName("L-025: 대화 대표 명 변경 - 대화명만 변경")
    void updateConversationName_nameOnly() throws Exception {
        // Given
        validRequest.setUseYn(null);
        when(conversationNameUpdateService.updateConversationName(any(ConversationNameUpdateRequestDto.class)))
                .thenReturn(successResponse);

        // When & Then
        mockMvc.perform(put("/api/conversation/v1/name")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("success"));
    }

    @Test
    @DisplayName("L-025: 대화 대표 명 변경 - 사용여부만 변경")
    void updateConversationName_useYnOnly() throws Exception {
        // Given
        validRequest.setRepCnvsNm(null);
        when(conversationNameUpdateService.updateConversationName(any(ConversationNameUpdateRequestDto.class)))
                .thenReturn(successResponse);

        // When & Then
        mockMvc.perform(put("/api/conversation/v1/name")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("success"));
    }

    @Test
    @DisplayName("L-025: 대화 대표 명 변경 - 빈 요청 본문")
    void updateConversationName_emptyRequestBody() throws Exception {
        // When & Then
        mockMvc.perform(put("/api/conversation/v1/name")
                .contentType(MediaType.APPLICATION_JSON)
                .content(""))
                .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("L-025: 대화 대표 명 변경 - 잘못된 JSON 형식")
    void updateConversationName_invalidJson() throws Exception {
        // When & Then
        mockMvc.perform(put("/api/conversation/v1/name")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{invalid json}"))
                .andExpect(status().isBadRequest());
    }
}
