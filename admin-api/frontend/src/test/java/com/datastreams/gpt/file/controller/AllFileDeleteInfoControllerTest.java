package com.datastreams.gpt.file.controller;

import com.datastreams.gpt.file.dto.AllFileDeleteInfoRequestDto;
import com.datastreams.gpt.file.dto.AllFileDeleteInfoResponseDto;
import com.datastreams.gpt.file.service.AllFileDeleteInfoService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(AllFileDeleteInfoController.class)
class AllFileDeleteInfoControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private AllFileDeleteInfoService allFileDeleteInfoService;

    @Autowired
    private ObjectMapper objectMapper;

    private String cnvsIdtId;
    private AllFileDeleteInfoRequestDto validRequest;
    private AllFileDeleteInfoResponseDto mockResponse;

    @BeforeEach
    void setUp() {
        cnvsIdtId = "USR_ID_20231026103000123456";

        validRequest = new AllFileDeleteInfoRequestDto();
        validRequest.setLogCont("Session files deleted successfully");
        validRequest.setSucYn("Y");

        mockResponse = new AllFileDeleteInfoResponseDto();
        mockResponse.setCnvsIdtId(cnvsIdtId);
        mockResponse.setTxnNm("UPD_USR_UPLD_DOC_MNG");
        mockResponse.setCnt(3);
        mockResponse.setStatus("success");
        mockResponse.setProcessingTime(1500L);
        mockResponse.setUpdatedFileCount(3);
        mockResponse.setSucYn("Y");
    }

    @Test
    void updateAllFileDeleteInfo_Success() throws Exception {
        // Given
        when(allFileDeleteInfoService.updateAllFileDeleteInfo(any(AllFileDeleteInfoRequestDto.class))).thenReturn(mockResponse);

        // When & Then
        mockMvc.perform(put("/api/file/v1/session/{cnvsIdtId}/deleteInfo", cnvsIdtId)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequest))
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.cnvsIdtId").value(cnvsIdtId))
                .andExpect(jsonPath("$.txnNm").value("UPD_USR_UPLD_DOC_MNG"))
                .andExpect(jsonPath("$.cnt").value(3))
                .andExpect(jsonPath("$.status").value("success"))
                .andExpect(jsonPath("$.sucYn").value("Y"));
    }

    @Test
    void updateAllFileDeleteInfo_ValidationError() throws Exception {
        // Given
        when(allFileDeleteInfoService.updateAllFileDeleteInfo(any(AllFileDeleteInfoRequestDto.class)))
                .thenThrow(new IllegalArgumentException("대화 식별 아이디는 필수입니다."));

        // When & Then
        mockMvc.perform(put("/api/file/v1/session/{cnvsIdtId}/deleteInfo", cnvsIdtId)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequest))
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("대화 식별 아이디는 필수입니다."));
    }

    @Test
    void updateAllFileDeleteInfo_NoFilesInSession() throws Exception {
        // Given
        when(allFileDeleteInfoService.updateAllFileDeleteInfo(any(AllFileDeleteInfoRequestDto.class)))
                .thenThrow(new IllegalArgumentException("해당 세션에 파일이 없습니다."));

        // When & Then
        mockMvc.perform(put("/api/file/v1/session/{cnvsIdtId}/deleteInfo", cnvsIdtId)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequest))
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isNotFound())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("해당 세션에 파일이 없습니다."));
    }

    @Test
    void updateAllFileDeleteInfo_ServerError() throws Exception {
        // Given
        when(allFileDeleteInfoService.updateAllFileDeleteInfo(any(AllFileDeleteInfoRequestDto.class)))
                .thenThrow(new RuntimeException("Database connection failed"));

        // When & Then
        mockMvc.perform(put("/api/file/v1/session/{cnvsIdtId}/deleteInfo", cnvsIdtId)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequest))
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isInternalServerError())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("전체 파일 삭제 정보 갱신 중 오류가 발생했습니다."));
    }

    @Test
    void getFileCountBySession_Success() throws Exception {
        // Given
        when(allFileDeleteInfoService.getFileCountBySession(anyString())).thenReturn(5);

        // When & Then
        mockMvc.perform(get("/api/file/v1/session/{cnvsIdtId}/fileCount", cnvsIdtId)
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.cnvsIdtId").value(cnvsIdtId))
                .andExpect(jsonPath("$.fileCount").value(5));
    }

    @Test
    void getFileCountBySession_ValidationError() throws Exception {
        // Given
        when(allFileDeleteInfoService.getFileCountBySession(anyString()))
                .thenThrow(new IllegalArgumentException("대화 식별 아이디는 필수입니다."));

        // When & Then
        mockMvc.perform(get("/api/file/v1/session/{cnvsIdtId}/fileCount", cnvsIdtId)
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("대화 식별 아이디는 필수입니다."));
    }

    @Test
    void getDeletedFileCountBySession_Success() throws Exception {
        // Given
        when(allFileDeleteInfoService.getDeletedFileCountBySession(anyString())).thenReturn(3);

        // When & Then
        mockMvc.perform(get("/api/file/v1/session/{cnvsIdtId}/deletedFileCount", cnvsIdtId)
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.cnvsIdtId").value(cnvsIdtId))
                .andExpect(jsonPath("$.deletedFileCount").value(3));
    }

    @Test
    void getDeletedFileCountBySession_ValidationError() throws Exception {
        // Given
        when(allFileDeleteInfoService.getDeletedFileCountBySession(anyString()))
                .thenThrow(new IllegalArgumentException("대화 식별 아이디는 필수입니다."));

        // When & Then
        mockMvc.perform(get("/api/file/v1/session/{cnvsIdtId}/deletedFileCount", cnvsIdtId)
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("대화 식별 아이디는 필수입니다."));
    }
}
