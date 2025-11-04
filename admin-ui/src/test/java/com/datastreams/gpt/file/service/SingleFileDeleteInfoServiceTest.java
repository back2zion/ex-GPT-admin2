package com.datastreams.gpt.file.service;

import com.datastreams.gpt.file.dto.SingleFileDeleteInfoRequestDto;
import com.datastreams.gpt.file.dto.SingleFileDeleteInfoResponseDto;
import com.datastreams.gpt.file.mapper.SingleFileDeleteInfoMapper;
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
class SingleFileDeleteInfoServiceTest {

    @Mock
    private SingleFileDeleteInfoMapper singleFileDeleteInfoMapper;

    @InjectMocks
    private SingleFileDeleteInfoService singleFileDeleteInfoService;

    private SingleFileDeleteInfoRequestDto validRequest;
    private SingleFileDeleteInfoResponseDto mockResponse;

    @BeforeEach
    void setUp() {
        validRequest = new SingleFileDeleteInfoRequestDto();
        validRequest.setCnvsIdtId("USR_ID_20231026103000123456");
        validRequest.setFileUid("tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34");
        validRequest.setLogCont("Single file deleted successfully");
        validRequest.setSucYn("Y");

        mockResponse = new SingleFileDeleteInfoResponseDto();
        mockResponse.setTxnNm("UPD_USR_UPLD_DOC_MNG");
        mockResponse.setCnt(1);
    }

    @Test
    void updateSingleFileDeleteInfo_Success() {
        // Given
        when(singleFileDeleteInfoMapper.checkFileExists(anyString(), anyString())).thenReturn(1);
        when(singleFileDeleteInfoMapper.updateSingleFileDeleteInfo(any(SingleFileDeleteInfoRequestDto.class))).thenReturn(mockResponse);
        when(singleFileDeleteInfoMapper.getFileDeleteStatus(anyString(), anyString())).thenReturn("Y");

        // When
        SingleFileDeleteInfoResponseDto result = singleFileDeleteInfoService.updateSingleFileDeleteInfo(validRequest);

        // Then
        assertNotNull(result);
        assertEquals("USR_ID_20231026103000123456", result.getCnvsIdtId());
        assertEquals("tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34", result.getFileUid());
        assertEquals("UPD_USR_UPLD_DOC_MNG", result.getTxnNm());
        assertEquals(1, result.getCnt());
        assertEquals("success", result.getStatus());
        assertEquals("Y", result.getSucYn());
        assertTrue(result.getProcessingTime() >= 0);
        assertEquals(1, result.getUpdatedFileCount());
    }

    @Test
    void updateSingleFileDeleteInfo_FileNotExists() {
        // Given
        when(singleFileDeleteInfoMapper.checkFileExists(anyString(), anyString())).thenReturn(0);

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            singleFileDeleteInfoService.updateSingleFileDeleteInfo(validRequest);
        });
        
        assertEquals("해당 파일이 존재하지 않습니다.", thrown.getMessage());
    }

    @Test
    void updateSingleFileDeleteInfo_NullRequest() {
        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            singleFileDeleteInfoService.updateSingleFileDeleteInfo(null);
        });
        
        assertEquals("요청 데이터가 null입니다.", thrown.getMessage());
    }

    @Test
    void updateSingleFileDeleteInfo_EmptyCnvsIdtId() {
        // Given
        validRequest.setCnvsIdtId("");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            singleFileDeleteInfoService.updateSingleFileDeleteInfo(validRequest);
        });
        
        assertEquals("대화 식별 아이디는 필수입니다.", thrown.getMessage());
    }

    @Test
    void updateSingleFileDeleteInfo_EmptyFileUid() {
        // Given
        validRequest.setFileUid("");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            singleFileDeleteInfoService.updateSingleFileDeleteInfo(validRequest);
        });
        
        assertEquals("파일 아이디는 필수입니다.", thrown.getMessage());
    }

    @Test
    void updateSingleFileDeleteInfo_EmptyLogCont() {
        // Given
        validRequest.setLogCont("");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            singleFileDeleteInfoService.updateSingleFileDeleteInfo(validRequest);
        });
        
        assertEquals("로그 내용은 필수입니다.", thrown.getMessage());
    }

    @Test
    void updateSingleFileDeleteInfo_InvalidSucYn() {
        // Given
        validRequest.setSucYn("INVALID");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            singleFileDeleteInfoService.updateSingleFileDeleteInfo(validRequest);
        });
        
        assertEquals("성공 여부는 Y 또는 N이어야 합니다.", thrown.getMessage());
    }

    @Test
    void updateSingleFileDeleteInfo_InvalidCnvsIdtId() {
        // Given
        validRequest.setCnvsIdtId("invalid@cnvs#id");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            singleFileDeleteInfoService.updateSingleFileDeleteInfo(validRequest);
        });
        
        assertEquals("유효하지 않은 대화 식별 아이디 형식입니다.", thrown.getMessage());
    }

    @Test
    void updateSingleFileDeleteInfo_InvalidFileUid() {
        // Given
        validRequest.setFileUid("invalid@file#id");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            singleFileDeleteInfoService.updateSingleFileDeleteInfo(validRequest);
        });
        
        assertEquals("유효하지 않은 파일 아이디 형식입니다.", thrown.getMessage());
    }

    @Test
    void checkFileExists_Success() {
        // Given
        when(singleFileDeleteInfoMapper.checkFileExists(anyString(), anyString())).thenReturn(1);

        // When
        boolean result = singleFileDeleteInfoService.checkFileExists("USR_ID_20231026103000123456", "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34");

        // Then
        assertTrue(result);
    }

    @Test
    void checkFileExists_EmptyCnvsIdtId() {
        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            singleFileDeleteInfoService.checkFileExists("", "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34");
        });
        
        assertEquals("대화 식별 아이디는 필수입니다.", thrown.getMessage());
    }

    @Test
    void checkFileExists_EmptyFileUid() {
        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            singleFileDeleteInfoService.checkFileExists("USR_ID_20231026103000123456", "");
        });
        
        assertEquals("파일 아이디는 필수입니다.", thrown.getMessage());
    }

    @Test
    void getFileDeleteStatus_Success() {
        // Given
        when(singleFileDeleteInfoMapper.getFileDeleteStatus(anyString(), anyString())).thenReturn("Y");

        // When
        String result = singleFileDeleteInfoService.getFileDeleteStatus("USR_ID_20231026103000123456", "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34");

        // Then
        assertEquals("Y", result);
    }

    @Test
    void getFileDeleteStatus_EmptyCnvsIdtId() {
        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            singleFileDeleteInfoService.getFileDeleteStatus("", "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34");
        });
        
        assertEquals("대화 식별 아이디는 필수입니다.", thrown.getMessage());
    }

    @Test
    void getFileDeleteStatus_EmptyFileUid() {
        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            singleFileDeleteInfoService.getFileDeleteStatus("USR_ID_20231026103000123456", "");
        });
        
        assertEquals("파일 아이디는 필수입니다.", thrown.getMessage());
    }
}
