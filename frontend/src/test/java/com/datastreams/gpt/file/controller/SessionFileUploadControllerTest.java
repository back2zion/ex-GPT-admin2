package com.datastreams.gpt.file.controller;

import com.datastreams.gpt.file.dto.SessionFileUploadResponseDto;
import com.datastreams.gpt.file.service.SessionFileUploadService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(SessionFileUploadController.class)
class SessionFileUploadControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private SessionFileUploadService sessionFileUploadService;

    @Autowired
    private ObjectMapper objectMapper;

    private MockMultipartFile mockFile;
    private SessionFileUploadResponseDto mockResponseDto;

    @BeforeEach
    void setUp() {
        // Mock 파일 설정
        mockFile = new MockMultipartFile(
            "file",
            "test.pdf",
            MediaType.APPLICATION_PDF_VALUE,
            "test content".getBytes()
        );

        // Mock 응답 DTO 설정
        mockResponseDto = new SessionFileUploadResponseDto();
        mockResponseDto.setCnvsIdtId("user123_20231026103000");
        mockResponseDto.setFileUid("tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34");
        mockResponseDto.setFileName("test.pdf");
        mockResponseDto.setFileSize(1024L);
        mockResponseDto.setStatus("completed");
        mockResponseDto.setProcessingTime(1500L);
    }

    @Test
    void uploadSessionFile_Success() throws Exception {
        // Given
        when(sessionFileUploadService.uploadSessionFile(any())).thenReturn(mockResponseDto);

        // When & Then
        mockMvc.perform(multipart("/v1/session/{cnvsIdtId}/files", "user123_20231026103000")
                .file(mockFile)
                .param("userId", "user123")
                .param("wait", "true"))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.cnvsIdtId").value("user123_20231026103000"))
                .andExpect(jsonPath("$.fileUid").value("tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34"))
                .andExpect(jsonPath("$.fileName").value("test.pdf"))
                .andExpect(jsonPath("$.fileSize").value(1024))
                .andExpect(jsonPath("$.status").value("completed"))
                .andExpect(jsonPath("$.processingTime").value(1500));
    }

    @Test
    void uploadSessionFile_ValidationError() throws Exception {
        // Given
        when(sessionFileUploadService.uploadSessionFile(any()))
                .thenThrow(new IllegalArgumentException("업로드할 파일이 없습니다."));

        // When & Then
        mockMvc.perform(multipart("/v1/session/{cnvsIdtId}/files", "user123_20231026103000")
                .file(mockFile)
                .param("userId", "user123")
                .param("wait", "true"))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("업로드할 파일이 없습니다."));
    }

    @Test
    void uploadSessionFile_ServerError() throws Exception {
        // Given
        when(sessionFileUploadService.uploadSessionFile(any()))
                .thenThrow(new RuntimeException("FastAPI 서버 연결 오류"));

        // When & Then
        mockMvc.perform(multipart("/v1/session/{cnvsIdtId}/files", "user123_20231026103000")
                .file(mockFile)
                .param("userId", "user123")
                .param("wait", "true"))
                .andExpect(status().isInternalServerError())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("세션 파일 업로드 중 오류가 발생했습니다."));
    }

    @Test
    void checkSessionHealth_Success() throws Exception {
        // When & Then
        mockMvc.perform(get("/v1/session/{cnvsIdtId}/health", "user123_20231026103000"))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.status").value("healthy"))
                .andExpect(jsonPath("$.message").value("FastAPI 서버 연결 정상"))
                .andExpect(jsonPath("$.sessionId").value("user123_20231026103000"))
                .andExpect(jsonPath("$.timestamp").exists());
    }
}
