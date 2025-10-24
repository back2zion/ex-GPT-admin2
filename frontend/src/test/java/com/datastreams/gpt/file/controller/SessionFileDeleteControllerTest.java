package com.datastreams.gpt.file.controller;

import com.datastreams.gpt.file.dto.SessionFileDeleteResponseDto;
import com.datastreams.gpt.file.service.SessionFileDeleteService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(SessionFileDeleteController.class)
class SessionFileDeleteControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private SessionFileDeleteService sessionFileDeleteService;

    @Autowired
    private ObjectMapper objectMapper;

    private String cnvsIdtId;
    private SessionFileDeleteResponseDto mockResponse;

    @BeforeEach
    void setUp() {
        cnvsIdtId = "USR_ID_20231026103000123456";

        mockResponse = new SessionFileDeleteResponseDto();
        mockResponse.setCnvsIdtId(cnvsIdtId);
        mockResponse.setStatus("success");
        mockResponse.setDeletedFileCount(3);
        mockResponse.setDeletedFiles(new String[]{"tmp-123", "tmp-456", "tmp-789"});
        mockResponse.setDeletedAt("2025-10-17T14:30:00Z");
        mockResponse.setProcessingTime(1500L);
    }

    @Test
    void deleteSessionFiles_Success() throws Exception {
        // Given
        when(sessionFileDeleteService.deleteSessionFiles(any())).thenReturn(mockResponse);

        // When & Then
        mockMvc.perform(delete("/v1/session/{cnvsIdtId}", cnvsIdtId)
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.cnvsIdtId").value(cnvsIdtId))
                .andExpect(jsonPath("$.status").value("success"))
                .andExpect(jsonPath("$.deletedFileCount").value(3))
                .andExpect(jsonPath("$.deletedFiles").isArray())
                .andExpect(jsonPath("$.deletedAt").value("2025-10-17T14:30:00Z"))
                .andExpect(jsonPath("$.processingTime").value(1500L));
    }

    @Test
    void deleteSessionFiles_ValidationError() throws Exception {
        // Given
        when(sessionFileDeleteService.deleteSessionFiles(any()))
                .thenThrow(new IllegalArgumentException("대화 식별 아이디는 필수입니다."));

        // When & Then
        mockMvc.perform(delete("/v1/session/{cnvsIdtId}", " ")
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("대화 식별 아이디는 필수입니다."));
    }

    @Test
    void deleteSessionFiles_NotFound() throws Exception {
        // Given
        when(sessionFileDeleteService.deleteSessionFiles(any()))
                .thenThrow(new RuntimeException("Session not found"));

        // When & Then
        mockMvc.perform(delete("/v1/session/{cnvsIdtId}", cnvsIdtId)
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isNotFound())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("해당 세션을 찾을 수 없습니다."));
    }

    @Test
    void deleteSessionFiles_ServerError() throws Exception {
        // Given
        when(sessionFileDeleteService.deleteSessionFiles(any()))
                .thenThrow(new RuntimeException("FastAPI connection failed"));

        // When & Then
        mockMvc.perform(delete("/v1/session/{cnvsIdtId}", cnvsIdtId)
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isInternalServerError())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("세션 파일 삭제 중 오류가 발생했습니다."));
    }

    @Test
    void confirmSessionFileDelete_Success() throws Exception {
        // Given
        when(sessionFileDeleteService.deleteSessionFiles(any())).thenReturn(mockResponse);

        // When & Then
        mockMvc.perform(delete("/v1/session/{cnvsIdtId}/confirm", cnvsIdtId)
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.cnvsIdtId").value(cnvsIdtId))
                .andExpect(jsonPath("$.status").value("success"))
                .andExpect(jsonPath("$.deletedFileCount").value(3))
                .andExpect(jsonPath("$.confirmed").value(true));
    }

    @Test
    void confirmSessionFileDelete_ValidationError() throws Exception {
        // Given
        when(sessionFileDeleteService.deleteSessionFiles(any()))
                .thenThrow(new IllegalArgumentException("대화 식별 아이디는 필수입니다."));

        // When & Then
        mockMvc.perform(delete("/v1/session/{cnvsIdtId}/confirm", " ")
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("대화 식별 아이디는 필수입니다."));
    }

    @Test
    void checkFastApiHealth_Up() throws Exception {
        // Given
        when(sessionFileDeleteService.checkFastApiHealth()).thenReturn(true);

        // When & Then
        mockMvc.perform(get("/v1/session/{cnvsIdtId}/health", cnvsIdtId)
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.status").value("UP"));
    }

    @Test
    void checkFastApiHealth_Down() throws Exception {
        // Given
        when(sessionFileDeleteService.checkFastApiHealth()).thenReturn(false);

        // When & Then
        mockMvc.perform(get("/v1/session/{cnvsIdtId}/health", cnvsIdtId)
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isServiceUnavailable())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.status").value("DOWN"))
                .andExpect(jsonPath("$.error").value("FastAPI 서버에 연결할 수 없습니다."));
    }
}
