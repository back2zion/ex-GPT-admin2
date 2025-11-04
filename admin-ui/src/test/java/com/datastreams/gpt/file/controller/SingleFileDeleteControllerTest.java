package com.datastreams.gpt.file.controller;

import com.datastreams.gpt.file.dto.SingleFileDeleteResponseDto;
import com.datastreams.gpt.file.service.SingleFileDeleteService;
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

@WebMvcTest(SingleFileDeleteController.class)
class SingleFileDeleteControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private SingleFileDeleteService singleFileDeleteService;

    @Autowired
    private ObjectMapper objectMapper;

    private String cnvsIdtId;
    private String fileUid;
    private SingleFileDeleteResponseDto mockResponse;

    @BeforeEach
    void setUp() {
        cnvsIdtId = "USR_ID_20231026103000123456";
        fileUid = "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34";

        mockResponse = new SingleFileDeleteResponseDto();
        mockResponse.setCnvsIdtId(cnvsIdtId);
        mockResponse.setFileUid(fileUid);
        mockResponse.setStatus("success");
        mockResponse.setDeletedAt("2025-10-17T14:30:00Z");
        mockResponse.setProcessingTime(500L);
        mockResponse.setFileSize(1024000L);
        mockResponse.setFileName("document.pdf");
    }

    @Test
    void deleteSingleFile_Success() throws Exception {
        // Given
        when(singleFileDeleteService.deleteSingleFile(any())).thenReturn(mockResponse);

        // When & Then
        mockMvc.perform(delete("/v1/session/{cnvsIdtId}/files/{fileUid}", cnvsIdtId, fileUid)
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.cnvsIdtId").value(cnvsIdtId))
                .andExpect(jsonPath("$.fileUid").value(fileUid))
                .andExpect(jsonPath("$.status").value("success"))
                .andExpect(jsonPath("$.deletedAt").value("2025-10-17T14:30:00Z"))
                .andExpect(jsonPath("$.processingTime").value(500L))
                .andExpect(jsonPath("$.fileSize").value(1024000L))
                .andExpect(jsonPath("$.fileName").value("document.pdf"));
    }

    @Test
    void deleteSingleFile_ValidationError() throws Exception {
        // Given
        when(singleFileDeleteService.deleteSingleFile(any()))
                .thenThrow(new IllegalArgumentException("파일 아이디는 필수입니다."));

        // When & Then
        mockMvc.perform(delete("/v1/session/{cnvsIdtId}/files/{fileUid}", cnvsIdtId, " ")
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("파일 아이디는 필수입니다."));
    }

    @Test
    void deleteSingleFile_NotFound() throws Exception {
        // Given
        when(singleFileDeleteService.deleteSingleFile(any()))
                .thenThrow(new RuntimeException("File not found"));

        // When & Then
        mockMvc.perform(delete("/v1/session/{cnvsIdtId}/files/{fileUid}", cnvsIdtId, fileUid)
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isNotFound())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("해당 파일을 찾을 수 없습니다."));
    }

    @Test
    void deleteSingleFile_ServerError() throws Exception {
        // Given
        when(singleFileDeleteService.deleteSingleFile(any()))
                .thenThrow(new RuntimeException("FastAPI connection failed"));

        // When & Then
        mockMvc.perform(delete("/v1/session/{cnvsIdtId}/files/{fileUid}", cnvsIdtId, fileUid)
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isInternalServerError())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("단일 파일 삭제 중 오류가 발생했습니다."));
    }

    @Test
    void confirmSingleFileDelete_Success() throws Exception {
        // Given
        when(singleFileDeleteService.deleteSingleFile(any())).thenReturn(mockResponse);

        // When & Then
        mockMvc.perform(delete("/v1/session/{cnvsIdtId}/files/{fileUid}/confirm", cnvsIdtId, fileUid)
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.cnvsIdtId").value(cnvsIdtId))
                .andExpect(jsonPath("$.fileUid").value(fileUid))
                .andExpect(jsonPath("$.status").value("success"))
                .andExpect(jsonPath("$.confirmed").value(true));
    }

    @Test
    void confirmSingleFileDelete_ValidationError() throws Exception {
        // Given
        when(singleFileDeleteService.deleteSingleFile(any()))
                .thenThrow(new IllegalArgumentException("파일 아이디는 필수입니다."));

        // When & Then
        mockMvc.perform(delete("/v1/session/{cnvsIdtId}/files/{fileUid}/confirm", cnvsIdtId, " ")
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("파일 아이디는 필수입니다."));
    }

    @Test
    void checkFastApiHealth_Up() throws Exception {
        // Given
        when(singleFileDeleteService.checkFastApiHealth()).thenReturn(true);

        // When & Then
        mockMvc.perform(get("/v1/session/{cnvsIdtId}/files/{fileUid}/health", cnvsIdtId, fileUid)
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.status").value("UP"));
    }

    @Test
    void checkFastApiHealth_Down() throws Exception {
        // Given
        when(singleFileDeleteService.checkFastApiHealth()).thenReturn(false);

        // When & Then
        mockMvc.perform(get("/v1/session/{cnvsIdtId}/files/{fileUid}/health", cnvsIdtId, fileUid)
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isServiceUnavailable())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.status").value("DOWN"))
                .andExpect(jsonPath("$.error").value("FastAPI 서버에 연결할 수 없습니다."));
    }
}
