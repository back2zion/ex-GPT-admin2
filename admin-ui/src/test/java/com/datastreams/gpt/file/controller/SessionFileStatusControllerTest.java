package com.datastreams.gpt.file.controller;

import com.datastreams.gpt.file.dto.SessionFileStatusResponseDto;
import com.datastreams.gpt.file.service.SessionFileStatusService;
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
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(SessionFileStatusController.class)
class SessionFileStatusControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private SessionFileStatusService sessionFileStatusService;

    @Autowired
    private ObjectMapper objectMapper;

    private SessionFileStatusResponseDto mockResponseDto;

    @BeforeEach
    void setUp() {
        // Mock 응답 DTO 설정
        mockResponseDto = new SessionFileStatusResponseDto();
        mockResponseDto.setFileUid("tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34");
        mockResponseDto.setStatus("ready");
        mockResponseDto.setFileName("test.pdf");
        mockResponseDto.setFileSize(1024L);
        mockResponseDto.setProgress(100);
        mockResponseDto.setCheckedAt("2025-10-17T14:30:00Z");
    }

    @Test
    void getSessionFileStatus_Success() throws Exception {
        // Given
        when(sessionFileStatusService.getSessionFileStatus(any())).thenReturn(mockResponseDto);
        when(sessionFileStatusService.isFileReady("ready")).thenReturn(true);
        when(sessionFileStatusService.isFileError("ready")).thenReturn(false);
        when(sessionFileStatusService.isFileProcessing("ready")).thenReturn(false);

        // When & Then
        mockMvc.perform(get("/v1/file/{fileUid}/status", "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34"))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.fileUid").value("tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34"))
                .andExpect(jsonPath("$.status").value("ready"))
                .andExpect(jsonPath("$.fileName").value("test.pdf"))
                .andExpect(jsonPath("$.fileSize").value(1024))
                .andExpect(jsonPath("$.progress").value(100))
                .andExpect(jsonPath("$.checkedAt").value("2025-10-17T14:30:00Z"));
    }

    @Test
    void getSessionFileStatus_ValidationError() throws Exception {
        // Given
        when(sessionFileStatusService.getSessionFileStatus(any()))
                .thenThrow(new IllegalArgumentException("파일 아이디는 필수입니다."));

        // When & Then
        mockMvc.perform(get("/v1/file/{fileUid}/status", ""))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("파일 아이디는 필수입니다."));
    }

    @Test
    void getSessionFileStatus_ServerError() throws Exception {
        // Given
        when(sessionFileStatusService.getSessionFileStatus(any()))
                .thenThrow(new RuntimeException("FastAPI 서버 연결 오류"));

        // When & Then
        mockMvc.perform(get("/v1/file/{fileUid}/status", "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34"))
                .andExpect(status().isInternalServerError())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("파일 상태 조회 중 오류가 발생했습니다."));
    }

    @Test
    void getSimpleFileStatus_Success() throws Exception {
        // Given
        when(sessionFileStatusService.getSessionFileStatus(any())).thenReturn(mockResponseDto);
        when(sessionFileStatusService.isFileReady("ready")).thenReturn(true);
        when(sessionFileStatusService.isFileError("ready")).thenReturn(false);
        when(sessionFileStatusService.isFileProcessing("ready")).thenReturn(false);

        // When & Then
        mockMvc.perform(get("/v1/file/{fileUid}/status/simple", "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34"))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.fileUid").value("tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34"))
                .andExpect(jsonPath("$.status").value("ready"))
                .andExpect(jsonPath("$.isReady").value(true))
                .andExpect(jsonPath("$.isError").value(false))
                .andExpect(jsonPath("$.isProcessing").value(false));
    }

    @Test
    void getSimpleFileStatus_Processing() throws Exception {
        // Given
        mockResponseDto.setStatus("processed");
        when(sessionFileStatusService.getSessionFileStatus(any())).thenReturn(mockResponseDto);
        when(sessionFileStatusService.isFileReady("processed")).thenReturn(false);
        when(sessionFileStatusService.isFileError("processed")).thenReturn(false);
        when(sessionFileStatusService.isFileProcessing("processed")).thenReturn(true);

        // When & Then
        mockMvc.perform(get("/v1/file/{fileUid}/status/simple", "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34"))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.status").value("processed"))
                .andExpect(jsonPath("$.isReady").value(false))
                .andExpect(jsonPath("$.isError").value(false))
                .andExpect(jsonPath("$.isProcessing").value(true));
    }

    @Test
    void getSimpleFileStatus_Error() throws Exception {
        // Given
        mockResponseDto.setStatus("error");
        mockResponseDto.setError("파일 파싱 실패");
        when(sessionFileStatusService.getSessionFileStatus(any())).thenReturn(mockResponseDto);
        when(sessionFileStatusService.isFileReady("error")).thenReturn(false);
        when(sessionFileStatusService.isFileError("error")).thenReturn(true);
        when(sessionFileStatusService.isFileProcessing("error")).thenReturn(false);

        // When & Then
        mockMvc.perform(get("/v1/file/{fileUid}/status/simple", "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34"))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.status").value("error"))
                .andExpect(jsonPath("$.isReady").value(false))
                .andExpect(jsonPath("$.isError").value(true))
                .andExpect(jsonPath("$.isProcessing").value(false));
    }
}
