package com.datastreams.gpt.error.controller;

import com.datastreams.gpt.error.dto.ErrorChoiceDto;
import com.datastreams.gpt.error.dto.ErrorChoiceListResponseDto;
import com.datastreams.gpt.error.service.ErrorChoiceListService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.ArrayList;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(ErrorChoiceListController.class)
public class ErrorChoiceListControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private ErrorChoiceListService errorChoiceListService;

    @Autowired
    private ObjectMapper objectMapper;

    private ErrorChoiceListResponseDto successResponse;
    private ErrorChoiceListResponseDto errorResponse;

    @BeforeEach
    void setUp() {
        // 성공 응답 설정
        successResponse = new ErrorChoiceListResponseDto();
        successResponse.setLevelN1Cd("ERR_RPT_CD");
        successResponse.setStatus("success");
        successResponse.setTotalCount(2);
        successResponse.setProcessingTime(100L);
        
        List<ErrorChoiceDto> errorChoices = new ArrayList<>();
        ErrorChoiceDto choice1 = new ErrorChoiceDto();
        choice1.setLevelN2Seq(1L);
        choice1.setLevelN1Cd("ERR_RPT_CD");
        choice1.setLevelN2Cd("ERR001");
        choice1.setLevelN2Nm("시스템 오류");
        choice1.setUseYn("Y");
        errorChoices.add(choice1);
        
        ErrorChoiceDto choice2 = new ErrorChoiceDto();
        choice2.setLevelN2Seq(2L);
        choice2.setLevelN1Cd("ERR_RPT_CD");
        choice2.setLevelN2Cd("ERR002");
        choice2.setLevelN2Nm("네트워크 오류");
        choice2.setUseYn("Y");
        errorChoices.add(choice2);
        
        successResponse.setErrorChoices(errorChoices);
        
        // 오류 응답 설정
        errorResponse = new ErrorChoiceListResponseDto();
        errorResponse.setLevelN1Cd("ERR_RPT_CD");
        errorResponse.setStatus("error");
        errorResponse.setTotalCount(0);
        errorResponse.setProcessingTime(0L);
        errorResponse.setErrorChoices(new ArrayList<>());
    }

    @Test
    @DisplayName("L-022: 오류 선택지 목록 조회 성공")
    void getErrorChoiceList_success() throws Exception {
        // Given
        when(errorChoiceListService.getErrorChoiceList(any())).thenReturn(successResponse);

        // When & Then
        mockMvc.perform(get("/api/error/v1/choiceList/ERR_RPT_CD")
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.levelN1Cd").value("ERR_RPT_CD"))
                .andExpect(jsonPath("$.status").value("success"))
                .andExpect(jsonPath("$.totalCount").value(2))
                .andExpect(jsonPath("$.errorChoices").isArray())
                .andExpect(jsonPath("$.errorChoices.length()").value(2))
                .andExpect(jsonPath("$.errorChoices[0].levelN2Cd").value("ERR001"))
                .andExpect(jsonPath("$.errorChoices[0].levelN2Nm").value("시스템 오류"))
                .andExpect(jsonPath("$.errorChoices[1].levelN2Cd").value("ERR002"))
                .andExpect(jsonPath("$.errorChoices[1].levelN2Nm").value("네트워크 오류"));
    }

    @Test
    @DisplayName("L-022: 오류 선택지 목록 조회 실패 - 서비스 오류")
    void getErrorChoiceList_serviceError() throws Exception {
        // Given
        when(errorChoiceListService.getErrorChoiceList(any())).thenReturn(errorResponse);

        // When & Then
        mockMvc.perform(get("/api/error/v1/choiceList/ERR_RPT_CD")
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.levelN1Cd").value("ERR_RPT_CD"))
                .andExpect(jsonPath("$.status").value("error"))
                .andExpect(jsonPath("$.totalCount").value(0));
    }

    @Test
    @DisplayName("L-022: 오류 선택지 목록 조회 - 잘못된 요청")
    void getErrorChoiceList_badRequest() throws Exception {
        // Given
        when(errorChoiceListService.getErrorChoiceList(any()))
                .thenThrow(new IllegalArgumentException("레벨1 코드는 필수입니다."));

        // When & Then
        mockMvc.perform(get("/api/error/v1/choiceList/")
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isNotFound()); // 경로가 잘못된 경우 404
    }

    @Test
    @DisplayName("L-022: 오류 선택지 목록 조회 - 빈 결과")
    void getErrorChoiceList_emptyResult() throws Exception {
        // Given
        ErrorChoiceListResponseDto emptyResponse = new ErrorChoiceListResponseDto();
        emptyResponse.setLevelN1Cd("ERR_RPT_CD");
        emptyResponse.setStatus("success");
        emptyResponse.setTotalCount(0);
        emptyResponse.setProcessingTime(50L);
        emptyResponse.setErrorChoices(new ArrayList<>());
        
        when(errorChoiceListService.getErrorChoiceList(any())).thenReturn(emptyResponse);

        // When & Then
        mockMvc.perform(get("/api/error/v1/choiceList/ERR_RPT_CD")
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.levelN1Cd").value("ERR_RPT_CD"))
                .andExpect(jsonPath("$.status").value("success"))
                .andExpect(jsonPath("$.totalCount").value(0))
                .andExpect(jsonPath("$.errorChoices").isArray())
                .andExpect(jsonPath("$.errorChoices.length()").value(0));
    }
}
