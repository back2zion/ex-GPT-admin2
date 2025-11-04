package com.datastreams.gpt.error.service;

import com.datastreams.gpt.error.dto.ErrorChoiceDto;
import com.datastreams.gpt.error.dto.ErrorChoiceListRequestDto;
import com.datastreams.gpt.error.dto.ErrorChoiceListResponseDto;
import com.datastreams.gpt.error.mapper.ErrorChoiceListMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
public class ErrorChoiceListServiceTest {

    @Mock
    private ErrorChoiceListMapper errorChoiceListMapper;

    @InjectMocks
    private ErrorChoiceListService errorChoiceListService;

    private ErrorChoiceListRequestDto validRequest;
    private List<Map<String, Object>> mockResultList;

    @BeforeEach
    void setUp() {
        validRequest = new ErrorChoiceListRequestDto("ERR_RPT_CD");
        
        mockResultList = new ArrayList<>();
        Map<String, Object> mockRow1 = new HashMap<>();
        mockRow1.put("LEVEL_N2_SEQ", 1L);
        mockRow1.put("LEVEL_N1_CD", "ERR_RPT_CD");
        mockRow1.put("LEVEL_N2_CD", "ERR001");
        mockRow1.put("LEVEL_N2_NM", "시스템 오류");
        mockRow1.put("USE_YN", "Y");
        mockRow1.put("CD_SEQ", 1L);
        mockRow1.put("CD_SORT_SEQ", 1L);
        mockRow1.put("TOT_CD_CNT", 2L);
        mockResultList.add(mockRow1);
        
        Map<String, Object> mockRow2 = new HashMap<>();
        mockRow2.put("LEVEL_N2_SEQ", 2L);
        mockRow2.put("LEVEL_N1_CD", "ERR_RPT_CD");
        mockRow2.put("LEVEL_N2_CD", "ERR002");
        mockRow2.put("LEVEL_N2_NM", "네트워크 오류");
        mockRow2.put("USE_YN", "Y");
        mockRow2.put("CD_SEQ", 2L);
        mockRow2.put("CD_SORT_SEQ", 2L);
        mockRow2.put("TOT_CD_CNT", 2L);
        mockResultList.add(mockRow2);
    }

    @Test
    @DisplayName("L-022: 오류 선택지 목록 조회 성공")
    void getErrorChoiceList_success() {
        // Given
        when(errorChoiceListMapper.selectErrorChoiceList(any(ErrorChoiceListRequestDto.class)))
                .thenReturn(mockResultList);
        when(errorChoiceListMapper.selectErrorChoiceCount(anyString()))
                .thenReturn(2);

        // When
        ErrorChoiceListResponseDto result = errorChoiceListService.getErrorChoiceList(validRequest);

        // Then
        assertNotNull(result);
        assertEquals("ERR_RPT_CD", result.getLevelN1Cd());
        assertEquals("success", result.getStatus());
        assertEquals(2, result.getTotalCount());
        assertEquals(2, result.getErrorChoices().size());
        assertTrue(result.getProcessingTime() >= 0);
        
        // 첫 번째 항목 검증
        ErrorChoiceDto firstChoice = result.getErrorChoices().get(0);
        assertEquals(1L, firstChoice.getLevelN2Seq());
        assertEquals("ERR_RPT_CD", firstChoice.getLevelN1Cd());
        assertEquals("ERR001", firstChoice.getLevelN2Cd());
        assertEquals("시스템 오류", firstChoice.getLevelN2Nm());
        assertEquals("Y", firstChoice.getUseYn());
    }

    @Test
    @DisplayName("L-022: 오류 선택지 목록 조회 실패 - null 요청")
    void getErrorChoiceList_fail_nullRequest() {
        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            errorChoiceListService.getErrorChoiceList(null);
        });
        
        assertEquals("요청 데이터가 null입니다.", thrown.getMessage());
    }

    @Test
    @DisplayName("L-022: 오류 선택지 목록 조회 실패 - 빈 레벨1 코드")
    void getErrorChoiceList_fail_emptyLevelN1Cd() {
        // Given
        validRequest.setLevelN1Cd("");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            errorChoiceListService.getErrorChoiceList(validRequest);
        });
        
        assertEquals("레벨1 코드는 필수입니다.", thrown.getMessage());
    }

    @Test
    @DisplayName("L-022: 오류 선택지 목록 조회 실패 - null 레벨1 코드")
    void getErrorChoiceList_fail_nullLevelN1Cd() {
        // Given
        validRequest.setLevelN1Cd(null);

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            errorChoiceListService.getErrorChoiceList(validRequest);
        });
        
        assertEquals("레벨1 코드는 필수입니다.", thrown.getMessage());
    }

    @Test
    @DisplayName("L-022: 오류 선택지 목록 조회 - 빈 결과")
    void getErrorChoiceList_emptyResult() {
        // Given
        when(errorChoiceListMapper.selectErrorChoiceList(any(ErrorChoiceListRequestDto.class)))
                .thenReturn(new ArrayList<>());
        when(errorChoiceListMapper.selectErrorChoiceCount(anyString()))
                .thenReturn(0);

        // When
        ErrorChoiceListResponseDto result = errorChoiceListService.getErrorChoiceList(validRequest);

        // Then
        assertNotNull(result);
        assertEquals("ERR_RPT_CD", result.getLevelN1Cd());
        assertEquals("success", result.getStatus());
        assertEquals(0, result.getTotalCount());
        assertEquals(0, result.getErrorChoices().size());
    }

    @Test
    @DisplayName("L-022: 오류 선택지 목록 조회 - 데이터베이스 오류")
    void getErrorChoiceList_databaseError() {
        // Given
        when(errorChoiceListMapper.selectErrorChoiceList(any(ErrorChoiceListRequestDto.class)))
                .thenThrow(new RuntimeException("Database connection failed"));

        // When
        ErrorChoiceListResponseDto result = errorChoiceListService.getErrorChoiceList(validRequest);

        // Then
        assertNotNull(result);
        assertEquals("ERR_RPT_CD", result.getLevelN1Cd());
        assertEquals("error", result.getStatus());
        assertEquals(0, result.getTotalCount());
        assertEquals(0, result.getErrorChoices().size());
    }
}
