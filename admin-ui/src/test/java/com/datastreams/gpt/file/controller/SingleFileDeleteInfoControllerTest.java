package com.datastreams.gpt.file.controller;

import com.datastreams.gpt.file.dto.SingleFileDeleteInfoRequestDto;
import com.datastreams.gpt.file.dto.SingleFileDeleteInfoResponseDto;
import com.datastreams.gpt.file.service.SingleFileDeleteInfoService;
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

@WebMvcTest(SingleFileDeleteInfoController.class)
class SingleFileDeleteInfoControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private SingleFileDeleteInfoService singleFileDeleteInfoService;

    @Autowired
    private ObjectMapper objectMapper;

    private String cnvsIdtId;
    private String fileUid;
    private SingleFileDeleteInfoRequestDto validRequest;
    private SingleFileDeleteInfoResponseDto mockResponse;

    @BeforeEach
    void setUp() {
        cnvsIdtId = "USR_ID_20231026103000123456";
        fileUid = "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34";

        validRequest = new SingleFileDeleteInfoRequestDto();
        validRequest.setLogCont("Single file deleted successfully");
        validRequest.setSucYn("Y");

        mockResponse = new SingleFileDeleteInfoResponseDto();
        mockResponse.setCnvsIdtId(cnvsIdtId);
        mockResponse.setFileUid(fileUid);
        mockResponse.setTxnNm("UPD_USR_UPLD_DOC_MNG");
        mockResponse.setCnt(1);
        mockResponse.setStatus("success");
        mockResponse.setProcessingTime(800L);
        mockResponse.setUpdatedFileCount(1);
        mockResponse.setSucYn("Y");
    }

    @Test
    void updateSingleFileDeleteInfo_Success() throws Exception {
        // Given
        when(singleFileDeleteInfoService.updateSingleFileDeleteInfo(any(SingleFileDeleteInfoRequestDto.class))).thenReturn(mockResponse);

        // When & Then
        mockMvc.perform(put("/api/file/v1/session/{cnvsIdtId}/files/{fileUid}/deleteInfo", cnvsIdtId, fileUid)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequest))
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.cnvsIdtId").value(cnvsIdtId))
                .andExpect(jsonPath("$.fileUid").value(fileUid))
                .andExpect(jsonPath("$.txnNm").value("UPD_USR_UPLD_DOC_MNG"))
                .andExpect(jsonPath("$.cnt").value(1))
                .andExpect(jsonPath("$.status").value("success"))
                .andExpect(jsonPath("$.sucYn").value("Y"));
    }

    @Test
    void updateSingleFileDeleteInfo_ValidationError() throws Exception {
        // Given
        when(singleFileDeleteInfoService.updateSingleFileDeleteInfo(any(SingleFileDeleteInfoRequestDto.class)))
                .thenThrow(new IllegalArgumentException("대화 식별 아이디는 필수입니다."));

        // When & Then
        mockMvc.perform(put("/api/file/v1/session/{cnvsIdtId}/files/{fileUid}/deleteInfo", cnvsIdtId, fileUid)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequest))
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("대화 식별 아이디는 필수입니다."));
    }

    @Test
    void updateSingleFileDeleteInfo_FileNotExists() throws Exception {
        // Given
        when(singleFileDeleteInfoService.updateSingleFileDeleteInfo(any(SingleFileDeleteInfoRequestDto.class)))
                .thenThrow(new IllegalArgumentException("해당 파일이 존재하지 않습니다."));

        // When & Then
        mockMvc.perform(put("/api/file/v1/session/{cnvsIdtId}/files/{fileUid}/deleteInfo", cnvsIdtId, fileUid)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequest))
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isNotFound())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("해당 파일이 존재하지 않습니다."));
    }

    @Test
    void updateSingleFileDeleteInfo_ServerError() throws Exception {
        // Given
        when(singleFileDeleteInfoService.updateSingleFileDeleteInfo(any(SingleFileDeleteInfoRequestDto.class)))
                .thenThrow(new RuntimeException("Database connection failed"));

        // When & Then
        mockMvc.perform(put("/api/file/v1/session/{cnvsIdtId}/files/{fileUid}/deleteInfo", cnvsIdtId, fileUid)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequest))
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isInternalServerError())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("단일 파일 삭제 정보 갱신 중 오류가 발생했습니다."));
    }

    @Test
    void checkFileExists_Success() throws Exception {
        // Given
        when(singleFileDeleteInfoService.checkFileExists(anyString(), anyString())).thenReturn(true);

        // When & Then
        mockMvc.perform(get("/api/file/v1/session/{cnvsIdtId}/files/{fileUid}/exists", cnvsIdtId, fileUid)
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.cnvsIdtId").value(cnvsIdtId))
                .andExpect(jsonPath("$.fileUid").value(fileUid))
                .andExpect(jsonPath("$.exists").value(true));
    }

    @Test
    void checkFileExists_ValidationError() throws Exception {
        // Given
        when(singleFileDeleteInfoService.checkFileExists(anyString(), anyString()))
                .thenThrow(new IllegalArgumentException("대화 식별 아이디는 필수입니다."));

        // When & Then
        mockMvc.perform(get("/api/file/v1/session/{cnvsIdtId}/files/{fileUid}/exists", cnvsIdtId, fileUid)
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("대화 식별 아이디는 필수입니다."));
    }

    @Test
    void getFileDeleteStatus_Success() throws Exception {
        // Given
        when(singleFileDeleteInfoService.getFileDeleteStatus(anyString(), anyString())).thenReturn("Y");

        // When & Then
        mockMvc.perform(get("/api/file/v1/session/{cnvsIdtId}/files/{fileUid}/deleteStatus", cnvsIdtId, fileUid)
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.cnvsIdtId").value(cnvsIdtId))
                .andExpect(jsonPath("$.fileUid").value(fileUid))
                .andExpect(jsonPath("$.deleteStatus").value("Y"));
    }

    @Test
    void getFileDeleteStatus_ValidationError() throws Exception {
        // Given
        when(singleFileDeleteInfoService.getFileDeleteStatus(anyString(), anyString()))
                .thenThrow(new IllegalArgumentException("대화 식별 아이디는 필수입니다."));

        // When & Then
        mockMvc.perform(get("/api/file/v1/session/{cnvsIdtId}/files/{fileUid}/deleteStatus", cnvsIdtId, fileUid)
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("대화 식별 아이디는 필수입니다."));
    }
}
