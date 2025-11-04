package com.datastreams.gpt.error.service;

import com.datastreams.gpt.error.dto.ErrorReportSaveRequestDto;
import com.datastreams.gpt.error.dto.ErrorReportSaveResponseDto;
import com.datastreams.gpt.error.mapper.ErrorReportSaveMapper;
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
public class ErrorReportSaveServiceTest {

    @Mock
    private ErrorReportSaveMapper errorReportSaveMapper;

    @InjectMocks
    private ErrorReportSaveService errorReportSaveService;

    private ErrorReportSaveRequestDto validRequest;
    private List<Map<String, Object>> mockResultList;
    private List<String> mockSavedCodes;

    @BeforeEach
    void setUp() {
        validRequest = new ErrorReportSaveRequestDto();
        validRequest.setCnvsId("CNVS_12345");
        validRequest.setUsrId("USER_001");
        validRequest.setErrRptTxt("시스템 오류가 발생했습니다.");
        validRequest.setErrRptCdList(List.of("ERR001", "ERR002"));
        
        mockResultList = new ArrayList<>();
        Map<String, Object> result1 = new HashMap<>();
        result1.put("TXN_NM", "INS_USR_ERR_RPT");
        result1.put("CNT", 1);
        mockResultList.add(result1);
        
        Map<String, Object> result2 = new HashMap<>();
        result2.put("TXN_NM", "INS_USR_ERR_RPT_SEL_LST");
        result2.put("CNT", 2);
        mockResultList.add(result2);
        
        mockSavedCodes = List.of("ERR001", "ERR002");
    }

    @Test
    @DisplayName("L-023: 오류 보고 저장 성공")
    void saveErrorReport_success() {
        // Given
        when(errorReportSaveMapper.saveErrorReport(any(ErrorReportSaveRequestDto.class)))
                .thenReturn(mockResultList);
        when(errorReportSaveMapper.selectSavedErrorReportCodes(anyString(), anyString()))
                .thenReturn(mockSavedCodes);

        // When
        ErrorReportSaveResponseDto result = errorReportSaveService.saveErrorReport(validRequest);

        // Then
        assertNotNull(result);
        assertEquals("CNVS_12345", result.getCnvsId());
        assertEquals("USER_001", result.getUsrId());
        assertEquals("SAVE_ERROR_REPORT", result.getTxnNm());
        assertEquals(3, result.getCnt()); // 1 + 2
        assertEquals("success", result.getStatus());
        assertEquals(2, result.getSavedErrRptCdList().size());
        assertTrue(result.getProcessingTime() >= 0);
    }

    @Test
    @DisplayName("L-023: 오류 보고 저장 실패 - null 요청")
    void saveErrorReport_fail_nullRequest() {
        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            errorReportSaveService.saveErrorReport(null);
        });
        
        assertEquals("요청 데이터가 null입니다.", thrown.getMessage());
    }

    @Test
    @DisplayName("L-023: 오류 보고 저장 실패 - 빈 대화 ID")
    void saveErrorReport_fail_emptyCnvsId() {
        // Given
        validRequest.setCnvsId("");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            errorReportSaveService.saveErrorReport(validRequest);
        });
        
        assertEquals("대화 ID는 필수입니다.", thrown.getMessage());
    }

    @Test
    @DisplayName("L-023: 오류 보고 저장 실패 - 빈 사용자 ID")
    void saveErrorReport_fail_emptyUsrId() {
        // Given
        validRequest.setUsrId("");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            errorReportSaveService.saveErrorReport(validRequest);
        });
        
        assertEquals("사용자 ID는 필수입니다.", thrown.getMessage());
    }

    @Test
    @DisplayName("L-023: 오류 보고 저장 실패 - 빈 오류 보고 텍스트")
    void saveErrorReport_fail_emptyErrRptTxt() {
        // Given
        validRequest.setErrRptTxt("");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            errorReportSaveService.saveErrorReport(validRequest);
        });
        
        assertEquals("오류 보고 텍스트는 필수입니다.", thrown.getMessage());
    }

    @Test
    @DisplayName("L-023: 오류 보고 저장 실패 - 빈 오류 보고 코드 목록")
    void saveErrorReport_fail_emptyErrRptCdList() {
        // Given
        validRequest.setErrRptCdList(new ArrayList<>());

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            errorReportSaveService.saveErrorReport(validRequest);
        });
        
        assertEquals("오류 보고 코드 목록은 필수입니다.", thrown.getMessage());
    }

    @Test
    @DisplayName("L-023: 오류 보고 저장 실패 - null 오류 보고 코드 목록")
    void saveErrorReport_fail_nullErrRptCdList() {
        // Given
        validRequest.setErrRptCdList(null);

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            errorReportSaveService.saveErrorReport(validRequest);
        });
        
        assertEquals("오류 보고 코드 목록은 필수입니다.", thrown.getMessage());
    }

    @Test
    @DisplayName("L-023: 오류 보고 저장 실패 - 빈 오류 보고 코드")
    void saveErrorReport_fail_emptyErrRptCd() {
        // Given
        validRequest.setErrRptCdList(List.of("ERR001", ""));

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            errorReportSaveService.saveErrorReport(validRequest);
        });
        
        assertEquals("오류 보고 코드는 빈 값일 수 없습니다.", thrown.getMessage());
    }

    @Test
    @DisplayName("L-023: 오류 보고 저장 - 데이터베이스 오류")
    void saveErrorReport_databaseError() {
        // Given
        when(errorReportSaveMapper.saveErrorReport(any(ErrorReportSaveRequestDto.class)))
                .thenThrow(new RuntimeException("Database connection failed"));

        // When
        ErrorReportSaveResponseDto result = errorReportSaveService.saveErrorReport(validRequest);

        // Then
        assertNotNull(result);
        assertEquals("CNVS_12345", result.getCnvsId());
        assertEquals("USER_001", result.getUsrId());
        assertEquals("error", result.getStatus());
        assertEquals(0, result.getCnt());
        assertEquals(0, result.getSavedErrRptCdList().size());
    }
}
