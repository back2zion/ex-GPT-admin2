package com.datastreams.gpt.error.controller;

import com.datastreams.gpt.error.dto.ErrorReportSaveRequestDto;
import com.datastreams.gpt.error.dto.ErrorReportSaveResponseDto;
import com.datastreams.gpt.error.service.ErrorReportSaveService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(ErrorReportSaveController.class)
public class ErrorReportSaveControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private ErrorReportSaveService errorReportSaveService;

    @Autowired
    private ObjectMapper objectMapper;

    private ErrorReportSaveRequestDto validRequest;
    private ErrorReportSaveResponseDto successResponse;
    private ErrorReportSaveResponseDto errorResponse;

    @BeforeEach
    void setUp() {
        // 유효한 요청 데이터 설정
        validRequest = new ErrorReportSaveRequestDto();
        validRequest.setCnvsId("CNVS_12345");
        validRequest.setUsrId("USER_001");
        validRequest.setErrRptTxt("시스템 오류가 발생했습니다.");
        validRequest.setErrRptCdList(List.of("ERR001", "ERR002"));
        
        // 성공 응답 설정
        successResponse = new ErrorReportSaveResponseDto();
        successResponse.setCnvsId("CNVS_12345");
        successResponse.setUsrId("USER_001");
        successResponse.setTxnNm("SAVE_ERROR_REPORT");
        successResponse.setCnt(3);
        successResponse.setStatus("success");
        successResponse.setProcessingTime(100L);
        successResponse.setSavedErrRptCdList(List.of("ERR001", "ERR002"));
        
        // 오류 응답 설정
        errorResponse = new ErrorReportSaveResponseDto();
        errorResponse.setCnvsId("CNVS_12345");
        errorResponse.setUsrId("USER_001");
        errorResponse.setTxnNm("SAVE_ERROR_REPORT");
        errorResponse.setCnt(0);
        errorResponse.setStatus("error");
        errorResponse.setProcessingTime(0L);
        errorResponse.setSavedErrRptCdList(List.of());
    }

    @Test
    @DisplayName("L-023: 오류 보고 저장 성공")
    void saveErrorReport_success() throws Exception {
        // Given
        when(errorReportSaveService.saveErrorReport(any(ErrorReportSaveRequestDto.class)))
                .thenReturn(successResponse);

        // When & Then
        mockMvc.perform(post("/api/error/v1/errorReport")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.cnvsId").value("CNVS_12345"))
                .andExpect(jsonPath("$.usrId").value("USER_001"))
                .andExpect(jsonPath("$.txnNm").value("SAVE_ERROR_REPORT"))
                .andExpect(jsonPath("$.cnt").value(3))
                .andExpect(jsonPath("$.status").value("success"))
                .andExpect(jsonPath("$.savedErrRptCdList").isArray())
                .andExpect(jsonPath("$.savedErrRptCdList.length()").value(2))
                .andExpect(jsonPath("$.savedErrRptCdList[0]").value("ERR001"))
                .andExpect(jsonPath("$.savedErrRptCdList[1]").value("ERR002"));
    }

    @Test
    @DisplayName("L-023: 오류 보고 저장 실패 - 서비스 오류")
    void saveErrorReport_serviceError() throws Exception {
        // Given
        when(errorReportSaveService.saveErrorReport(any(ErrorReportSaveRequestDto.class)))
                .thenReturn(errorResponse);

        // When & Then
        mockMvc.perform(post("/api/error/v1/errorReport")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.cnvsId").value("CNVS_12345"))
                .andExpect(jsonPath("$.usrId").value("USER_001"))
                .andExpect(jsonPath("$.status").value("error"))
                .andExpect(jsonPath("$.cnt").value(0));
    }

    @Test
    @DisplayName("L-023: 오류 보고 저장 실패 - 잘못된 요청")
    void saveErrorReport_badRequest() throws Exception {
        // Given
        when(errorReportSaveService.saveErrorReport(any(ErrorReportSaveRequestDto.class)))
                .thenThrow(new IllegalArgumentException("대화 ID는 필수입니다."));

        // When & Then
        mockMvc.perform(post("/api/error/v1/errorReport")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.cnvsId").value("CNVS_12345"))
                .andExpect(jsonPath("$.usrId").value("USER_001"))
                .andExpect(jsonPath("$.status").value("error"));
    }

    @Test
    @DisplayName("L-023: 오류 보고 저장 - 빈 요청 본문")
    void saveErrorReport_emptyRequestBody() throws Exception {
        // When & Then
        mockMvc.perform(post("/api/error/v1/errorReport")
                .contentType(MediaType.APPLICATION_JSON)
                .content(""))
                .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("L-023: 오류 보고 저장 - 잘못된 JSON 형식")
    void saveErrorReport_invalidJson() throws Exception {
        // When & Then
        mockMvc.perform(post("/api/error/v1/errorReport")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{invalid json}"))
                .andExpect(status().isBadRequest());
    }
}
