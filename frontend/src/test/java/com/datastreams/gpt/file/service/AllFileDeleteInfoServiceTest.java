package com.datastreams.gpt.file.service;

import com.datastreams.gpt.file.dto.AllFileDeleteInfoRequestDto;
import com.datastreams.gpt.file.dto.AllFileDeleteInfoResponseDto;
import com.datastreams.gpt.file.mapper.AllFileDeleteInfoMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class AllFileDeleteInfoServiceTest {

    @Mock
    private AllFileDeleteInfoMapper allFileDeleteInfoMapper;

    @InjectMocks
    private AllFileDeleteInfoService allFileDeleteInfoService;

    private AllFileDeleteInfoRequestDto validRequest;
    private AllFileDeleteInfoResponseDto mockResponse;

    @BeforeEach
    void setUp() {
        validRequest = new AllFileDeleteInfoRequestDto();
        validRequest.setCnvsIdtId("USR_ID_20231026103000123456");
        validRequest.setLogCont("Session files deleted successfully");
        validRequest.setSucYn("Y");

        mockResponse = new AllFileDeleteInfoResponseDto();
        mockResponse.setTxnNm("UPD_USR_UPLD_DOC_MNG");
        mockResponse.setCnt(3);
    }

    @Test
    void updateAllFileDeleteInfo_Success() {
        // Given
        when(allFileDeleteInfoMapper.countFilesBySession(anyString())).thenReturn(3);
        when(allFileDeleteInfoMapper.updateAllFileDeleteInfo(any(AllFileDeleteInfoRequestDto.class))).thenReturn(mockResponse);
        when(allFileDeleteInfoMapper.countDeletedFilesBySession(anyString())).thenReturn(3);

        // When
        AllFileDeleteInfoResponseDto result = allFileDeleteInfoService.updateAllFileDeleteInfo(validRequest);

        // Then
        assertNotNull(result);
        assertEquals("USR_ID_20231026103000123456", result.getCnvsIdtId());
        assertEquals("UPD_USR_UPLD_DOC_MNG", result.getTxnNm());
        assertEquals(3, result.getCnt());
        assertEquals("success", result.getStatus());
        assertEquals("Y", result.getSucYn());
        assertTrue(result.getProcessingTime() >= 0);
        assertEquals(3, result.getUpdatedFileCount());
    }

    @Test
    void updateAllFileDeleteInfo_NoFilesInSession() {
        // Given
        when(allFileDeleteInfoMapper.countFilesBySession(anyString())).thenReturn(0);

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            allFileDeleteInfoService.updateAllFileDeleteInfo(validRequest);
        });
        
        assertEquals("해당 세션에 파일이 없습니다.", thrown.getMessage());
    }

    @Test
    void updateAllFileDeleteInfo_NullRequest() {
        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            allFileDeleteInfoService.updateAllFileDeleteInfo(null);
        });
        
        assertEquals("요청 데이터가 null입니다.", thrown.getMessage());
    }

    @Test
    void updateAllFileDeleteInfo_EmptyCnvsIdtId() {
        // Given
        validRequest.setCnvsIdtId("");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            allFileDeleteInfoService.updateAllFileDeleteInfo(validRequest);
        });
        
        assertEquals("대화 식별 아이디는 필수입니다.", thrown.getMessage());
    }

    @Test
    void updateAllFileDeleteInfo_EmptyLogCont() {
        // Given
        validRequest.setLogCont("");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            allFileDeleteInfoService.updateAllFileDeleteInfo(validRequest);
        });
        
        assertEquals("로그 내용은 필수입니다.", thrown.getMessage());
    }

    @Test
    void updateAllFileDeleteInfo_InvalidSucYn() {
        // Given
        validRequest.setSucYn("INVALID");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            allFileDeleteInfoService.updateAllFileDeleteInfo(validRequest);
        });
        
        assertEquals("성공 여부는 Y 또는 N이어야 합니다.", thrown.getMessage());
    }

    @Test
    void updateAllFileDeleteInfo_InvalidCnvsIdtId() {
        // Given
        validRequest.setCnvsIdtId("invalid@cnvs#id");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            allFileDeleteInfoService.updateAllFileDeleteInfo(validRequest);
        });
        
        assertEquals("유효하지 않은 대화 식별 아이디 형식입니다.", thrown.getMessage());
    }

    @Test
    void getFileCountBySession_Success() {
        // Given
        when(allFileDeleteInfoMapper.countFilesBySession(anyString())).thenReturn(5);

        // When
        Integer result = allFileDeleteInfoService.getFileCountBySession("USR_ID_20231026103000123456");

        // Then
        assertEquals(5, result);
    }

    @Test
    void getFileCountBySession_EmptyCnvsIdtId() {
        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            allFileDeleteInfoService.getFileCountBySession("");
        });
        
        assertEquals("대화 식별 아이디는 필수입니다.", thrown.getMessage());
    }

    @Test
    void getDeletedFileCountBySession_Success() {
        // Given
        when(allFileDeleteInfoMapper.countDeletedFilesBySession(anyString())).thenReturn(3);

        // When
        Integer result = allFileDeleteInfoService.getDeletedFileCountBySession("USR_ID_20231026103000123456");

        // Then
        assertEquals(3, result);
    }

    @Test
    void getDeletedFileCountBySession_EmptyCnvsIdtId() {
        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            allFileDeleteInfoService.getDeletedFileCountBySession("");
        });
        
        assertEquals("대화 식별 아이디는 필수입니다.", thrown.getMessage());
    }
}
