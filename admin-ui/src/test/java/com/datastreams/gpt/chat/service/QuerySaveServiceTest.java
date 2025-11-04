package com.datastreams.gpt.chat.service;

import com.datastreams.gpt.chat.dto.QuerySaveRequestDto;
import com.datastreams.gpt.chat.dto.QuerySaveResponseDto;
import com.datastreams.gpt.chat.mapper.QuerySaveMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class QuerySaveServiceTest {

    @Mock
    private QuerySaveMapper querySaveMapper;

    @InjectMocks
    private QuerySaveService querySaveService;

    private QuerySaveRequestDto validRequest;
    private QuerySaveResponseDto mockResponse;

    @BeforeEach
    void setUp() {
        validRequest = new QuerySaveRequestDto();
        validRequest.setCnvsIdtId(""); // 첫 대화 시 빈 값
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
    @DisplayName("질의 저장 성공 - 첫 대화")
    void saveQuery_success_firstConversation() throws Exception {
        when(querySaveMapper.insertQuerySave(any(QuerySaveRequestDto.class))).thenReturn(mockResponse);

        QuerySaveResponseDto response = querySaveService.saveQuery(validRequest);

        assertNotNull(response);
        assertEquals("INS_USR_CNVS", response.getTxnNm());
        assertEquals("testuser_20251016100000000", response.getCnvsIdtId());
        assertEquals(12345L, response.getCnvsId());
    }

    @Test
    @DisplayName("질의 저장 성공 - 기존 대화")
    void saveQuery_success_existingConversation() throws Exception {
        validRequest.setCnvsIdtId("existing_cnvs_id_123");
        mockResponse.setCnvsIdtId("existing_cnvs_id_123");

        when(querySaveMapper.insertQuerySave(any(QuerySaveRequestDto.class))).thenReturn(mockResponse);

        QuerySaveResponseDto response = querySaveService.saveQuery(validRequest);

        assertNotNull(response);
        assertEquals("INS_USR_CNVS", response.getTxnNm());
        assertEquals("existing_cnvs_id_123", response.getCnvsIdtId());
        assertEquals(12345L, response.getCnvsId());
    }

    @Test
    @DisplayName("질의 저장 실패 - 필수 파라미터 누락 (질의 텍스트)")
    void saveQuery_missingQuesTxt_throwsException() {
        validRequest.setQuesTxt(null);
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            querySaveService.saveQuery(validRequest);
        });
        assertEquals("질의 텍스트는 필수입니다.", thrown.getMessage());
    }

    @Test
    @DisplayName("질의 저장 실패 - 필수 파라미터 누락 (사용자 ID)")
    void saveQuery_missingUsrId_throwsException() {
        validRequest.setUsrId("");
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            querySaveService.saveQuery(validRequest);
        });
        assertEquals("사용자 ID는 필수입니다.", thrown.getMessage());
    }

    @Test
    @DisplayName("질의 저장 실패 - 잘못된 추천 질의 여부")
    void saveQuery_invalidRcmQuesYn_throwsException() {
        validRequest.setRcmQuesYn("X");
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            querySaveService.saveQuery(validRequest);
        });
        assertEquals("추천 질의 여부는 Y 또는 N이어야 합니다.", thrown.getMessage());
    }
}
