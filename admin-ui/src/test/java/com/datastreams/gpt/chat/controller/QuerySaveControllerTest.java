package com.datastreams.gpt.chat.controller;

import com.datastreams.gpt.chat.dto.QuerySaveRequestDto;
import com.datastreams.gpt.chat.dto.QuerySaveResponseDto;
import com.datastreams.gpt.chat.service.QuerySaveService;
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
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(QuerySaveController.class)
class QuerySaveControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private QuerySaveService querySaveService;

    @Autowired
    private ObjectMapper objectMapper;

    private QuerySaveRequestDto validRequest;
    private QuerySaveResponseDto mockResponse;

    @BeforeEach
    void setUp() {
        validRequest = new QuerySaveRequestDto();
        validRequest.setCnvsIdtId("");
        validRequest.setQuesTxt("안녕하세요, 도움이 필요합니다.");
        validRequest.setSesnId("SESN_123456");
        validRequest.setUsrId("testuser");
        validRequest.setMenuIdtId("MENU_001");
        validRequest.setRcmQuesYn("N");

        mockResponse = new QuerySaveResponseDto();
        mockResponse.setTxnNm("INS_USR_CNVS");
        mockResponse.setCnvsIdtId("testuser_20251016100000000");
        mockResponse.setCnvsId(12345L);
    }

    @Test
    @DisplayName("L-033: 질의 저장 성공")
    void saveQuery_success() throws Exception {
        when(querySaveService.saveQuery(any(QuerySaveRequestDto.class))).thenReturn(mockResponse);

        mockMvc.perform(post("/api/chat/query/save")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.TXN_NM").value("INS_USR_CNVS"))
                .andExpect(jsonPath("$.CNVS_IDT_ID").value("testuser_20251016100000000"))
                .andExpect(jsonPath("$.CNVS_ID").value(12345L));
    }

    @Test
    @DisplayName("L-033: 질의 저장 실패 - 필수 파라미터 누락")
    void saveQuery_missingRequiredParam_returnsBadRequest() throws Exception {
        validRequest.setQuesTxt(null); // 질의 텍스트 누락

        when(querySaveService.saveQuery(any(QuerySaveRequestDto.class)))
                .thenThrow(new IllegalArgumentException("질의 텍스트는 필수입니다."));

        mockMvc.perform(post("/api/chat/query/save")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").value("질의 텍스트는 필수입니다."));
    }

    @Test
    @DisplayName("L-033: 질의 저장 실패 - 내부 서버 오류")
    void saveQuery_internalServerError_returnsInternalServerError() throws Exception {
        when(querySaveService.saveQuery(any(QuerySaveRequestDto.class)))
                .thenThrow(new RuntimeException("데이터베이스 오류"));

        mockMvc.perform(post("/api/chat/query/save")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.error").value("질의 저장 중 오류가 발생했습니다."));
    }
}
