package com.datastreams.gpt.file.controller;

import com.datastreams.gpt.file.dto.FileUploadHistoryUpdateRequestDto;
import com.datastreams.gpt.file.dto.FileUploadHistoryUpdateResponseDto;
import com.datastreams.gpt.file.service.FileUploadHistoryUpdateService;
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

@WebMvcTest(FileUploadHistoryUpdateController.class)
class FileUploadHistoryUpdateControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private FileUploadHistoryUpdateService fileUploadHistoryUpdateService;

    @Autowired
    private ObjectMapper objectMapper;

    private FileUploadHistoryUpdateRequestDto validRequest;
    private FileUploadHistoryUpdateResponseDto mockResponse;

    @BeforeEach
    void setUp() {
        validRequest = new FileUploadHistoryUpdateRequestDto();
        validRequest.setFileUpldSeq(1L);
        validRequest.setFileUid("tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34");
        validRequest.setLogCont("ready");

        mockResponse = new FileUploadHistoryUpdateResponseDto();
        mockResponse.setTxnNm("UPD_USR_UPLD_DOC_MNG");
        mockResponse.setCnt(1);
        mockResponse.setFileUpldSeq(1L);
        mockResponse.setFileUid("tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34");
        mockResponse.setUpdatedAt("2025-10-17T14:30:00Z");
    }

    @Test
    void updateFileUploadHistory_Success() throws Exception {
        // Given
        when(fileUploadHistoryUpdateService.updateFileUploadHistory(any(FileUploadHistoryUpdateRequestDto.class)))
                .thenReturn(mockResponse);

        // When & Then
        mockMvc.perform(put("/api/file/uploadHistory/{fileUpldSeq}", 1L)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.txnNm").value("UPD_USR_UPLD_DOC_MNG"))
                .andExpect(jsonPath("$.cnt").value(1))
                .andExpect(jsonPath("$.fileUpldSeq").value(1L))
                .andExpect(jsonPath("$.fileUid").value("tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34"))
                .andExpect(jsonPath("$.updatedAt").value("2025-10-17T14:30:00Z"));
    }

    @Test
    void updateFileUploadHistory_PathVariableMismatch() throws Exception {
        // Given
        validRequest.setFileUpldSeq(2L); // Different from path variable

        // When & Then
        mockMvc.perform(put("/api/file/uploadHistory/{fileUpldSeq}", 1L)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("Path Variable과 Request Body의 fileUpldSeq가 일치하지 않습니다."));
    }

    @Test
    void updateFileUploadHistory_ValidationError() throws Exception {
        // Given
        validRequest.setFileUid(""); // Invalid file UID
        when(fileUploadHistoryUpdateService.updateFileUploadHistory(any(FileUploadHistoryUpdateRequestDto.class)))
                .thenThrow(new IllegalArgumentException("파일 아이디는 필수입니다."));

        // When & Then
        mockMvc.perform(put("/api/file/uploadHistory/{fileUpldSeq}", 1L)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("파일 아이디는 필수입니다."));
    }

    @Test
    void updateFileUploadHistory_NotFound() throws Exception {
        // Given
        when(fileUploadHistoryUpdateService.updateFileUploadHistory(any(FileUploadHistoryUpdateRequestDto.class)))
                .thenThrow(new RuntimeException("해당 파일 업로드 순번이 존재하지 않습니다."));

        // When & Then
        mockMvc.perform(put("/api/file/uploadHistory/{fileUpldSeq}", 1L)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isNotFound())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("해당 파일 업로드 순번이 존재하지 않습니다."));
    }

    @Test
    void updateFileUploadHistory_ServerError() throws Exception {
        // Given
        when(fileUploadHistoryUpdateService.updateFileUploadHistory(any(FileUploadHistoryUpdateRequestDto.class)))
                .thenThrow(new RuntimeException("DB 연결 오류"));

        // When & Then
        mockMvc.perform(put("/api/file/uploadHistory/{fileUpldSeq}", 1L)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isInternalServerError())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("파일 업로드 이력 갱신 중 오류가 발생했습니다."));
    }

    @Test
    void checkFileUploadHistoryExists_Success() throws Exception {
        // Given
        when(fileUploadHistoryUpdateService.existsFileUploadHistory(1L)).thenReturn(true);

        // When & Then
        mockMvc.perform(get("/api/file/uploadHistory/{fileUpldSeq}/exists", 1L))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.fileUpldSeq").value(1L))
                .andExpect(jsonPath("$.exists").value(true));
    }

    @Test
    void checkFileUploadHistoryExists_NotFound() throws Exception {
        // Given
        when(fileUploadHistoryUpdateService.existsFileUploadHistory(1L)).thenReturn(false);

        // When & Then
        mockMvc.perform(get("/api/file/uploadHistory/{fileUpldSeq}/exists", 1L))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.fileUpldSeq").value(1L))
                .andExpect(jsonPath("$.exists").value(false));
    }

    @Test
    void checkFileUploadHistoryExists_InvalidFileUpldSeq() throws Exception {
        // When & Then
        mockMvc.perform(get("/api/file/uploadHistory/{fileUpldSeq}/exists", 0L))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("파일 업로드 순번은 필수이며 0보다 커야 합니다."));
    }

    @Test
    void checkFileUploadHistoryExists_ServerError() throws Exception {
        // Given
        when(fileUploadHistoryUpdateService.existsFileUploadHistory(1L))
                .thenThrow(new RuntimeException("DB 연결 오류"));

        // When & Then
        mockMvc.perform(get("/api/file/uploadHistory/{fileUpldSeq}/exists", 1L))
                .andExpect(status().isInternalServerError())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("파일 업로드 이력 존재 여부 확인 중 오류가 발생했습니다."));
    }
}
