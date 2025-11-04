package com.datastreams.gpt.file.service;

import com.datastreams.gpt.file.dto.FileUploadHistoryUpdateRequestDto;
import com.datastreams.gpt.file.dto.FileUploadHistoryUpdateResponseDto;
import com.datastreams.gpt.file.mapper.FileUploadHistoryUpdateMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class FileUploadHistoryUpdateServiceTest {

    @Mock
    private FileUploadHistoryUpdateMapper fileUploadHistoryUpdateMapper;

    @InjectMocks
    private FileUploadHistoryUpdateService fileUploadHistoryUpdateService;

    private FileUploadHistoryUpdateRequestDto validRequest;
    private FileUploadHistoryUpdateResponseDto mockResponse;

    @BeforeEach
    void setUp() {
        validRequest = new FileUploadHistoryUpdateRequestDto();
        validRequest.setFileUpldSeq(1L);
        validRequest.setFileUid("tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34");
        validRequest.setLogCont("ready");

        mockResponse = new FileUploadHistoryUpdateResponseDto();
        mockResponse.setTxnNm("UPD_USR_UPLD_DOC_MNG");
        mockResponse.setCnt(1);
    }

    @Test
    void updateFileUploadHistory_Success() {
        // Given
        when(fileUploadHistoryUpdateMapper.updateFileUploadHistory(any(FileUploadHistoryUpdateRequestDto.class)))
                .thenReturn(mockResponse);

        // When
        FileUploadHistoryUpdateResponseDto response = fileUploadHistoryUpdateService.updateFileUploadHistory(validRequest);

        // Then
        assertNotNull(response);
        assertEquals("UPD_USR_UPLD_DOC_MNG", response.getTxnNm());
        assertEquals(1, response.getCnt());
        assertEquals(1L, response.getFileUpldSeq());
        assertEquals("tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34", response.getFileUid());
        assertNotNull(response.getUpdatedAt());
    }

    @Test
    void updateFileUploadHistory_NullRequest_ThrowsException() {
        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            fileUploadHistoryUpdateService.updateFileUploadHistory(null);
        });
        
        assertEquals("요청 데이터가 null입니다.", thrown.getMessage());
    }

    @Test
    void updateFileUploadHistory_NullFileUpldSeq_ThrowsException() {
        // Given
        validRequest.setFileUpldSeq(null);

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            fileUploadHistoryUpdateService.updateFileUploadHistory(validRequest);
        });
        
        assertEquals("파일 업로드 순번은 필수이며 0보다 커야 합니다.", thrown.getMessage());
    }

    @Test
    void updateFileUploadHistory_ZeroFileUpldSeq_ThrowsException() {
        // Given
        validRequest.setFileUpldSeq(0L);

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            fileUploadHistoryUpdateService.updateFileUploadHistory(validRequest);
        });
        
        assertEquals("파일 업로드 순번은 필수이며 0보다 커야 합니다.", thrown.getMessage());
    }

    @Test
    void updateFileUploadHistory_EmptyFileUid_ThrowsException() {
        // Given
        validRequest.setFileUid("");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            fileUploadHistoryUpdateService.updateFileUploadHistory(validRequest);
        });
        
        assertEquals("파일 아이디는 필수입니다.", thrown.getMessage());
    }

    @Test
    void updateFileUploadHistory_EmptyLogCont_ThrowsException() {
        // Given
        validRequest.setLogCont("");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            fileUploadHistoryUpdateService.updateFileUploadHistory(validRequest);
        });
        
        assertEquals("로그 내용은 필수입니다.", thrown.getMessage());
    }

    @Test
    void updateFileUploadHistory_InvalidFileUid_ThrowsException() {
        // Given
        validRequest.setFileUid("invalid@file#id");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            fileUploadHistoryUpdateService.updateFileUploadHistory(validRequest);
        });
        
        assertEquals("유효하지 않은 파일 아이디 형식입니다.", thrown.getMessage());
    }

    @Test
    void updateFileUploadHistory_TooLongLogCont_ThrowsException() {
        // Given
        validRequest.setLogCont("a".repeat(1001));

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            fileUploadHistoryUpdateService.updateFileUploadHistory(validRequest);
        });
        
        assertEquals("로그 내용이 너무 깁니다. 최대 1000자까지 입력 가능합니다.", thrown.getMessage());
    }

    @Test
    void updateFileUploadHistory_NotFound_ThrowsException() {
        // Given
        mockResponse.setCnt(0);
        when(fileUploadHistoryUpdateMapper.updateFileUploadHistory(any(FileUploadHistoryUpdateRequestDto.class)))
                .thenReturn(mockResponse);

        // When & Then
        RuntimeException thrown = assertThrows(RuntimeException.class, () -> {
            fileUploadHistoryUpdateService.updateFileUploadHistory(validRequest);
        });
        
        assertEquals("해당 파일 업로드 순번이 존재하지 않습니다.", thrown.getMessage());
    }

    @Test
    void updateFileUploadHistory_NullResponse_ThrowsException() {
        // Given
        when(fileUploadHistoryUpdateMapper.updateFileUploadHistory(any(FileUploadHistoryUpdateRequestDto.class)))
                .thenReturn(null);

        // When & Then
        RuntimeException thrown = assertThrows(RuntimeException.class, () -> {
            fileUploadHistoryUpdateService.updateFileUploadHistory(validRequest);
        });
        
        assertEquals("해당 파일 업로드 순번이 존재하지 않습니다.", thrown.getMessage());
    }

    @Test
    void existsFileUploadHistory_ReturnsTrue() {
        // Given
        when(fileUploadHistoryUpdateMapper.updateFileUploadHistory(any(FileUploadHistoryUpdateRequestDto.class)))
                .thenReturn(mockResponse);

        // When
        boolean exists = fileUploadHistoryUpdateService.existsFileUploadHistory(1L);

        // Then
        assertTrue(exists);
    }

    @Test
    void existsFileUploadHistory_ReturnsFalse() {
        // Given
        mockResponse.setCnt(0);
        when(fileUploadHistoryUpdateMapper.updateFileUploadHistory(any(FileUploadHistoryUpdateRequestDto.class)))
                .thenReturn(mockResponse);

        // When
        boolean exists = fileUploadHistoryUpdateService.existsFileUploadHistory(1L);

        // Then
        assertFalse(exists);
    }

    @Test
    void existsFileUploadHistory_Exception_ReturnsFalse() {
        // Given
        when(fileUploadHistoryUpdateMapper.updateFileUploadHistory(any(FileUploadHistoryUpdateRequestDto.class)))
                .thenThrow(new RuntimeException("DB 오류"));

        // When
        boolean exists = fileUploadHistoryUpdateService.existsFileUploadHistory(1L);

        // Then
        assertFalse(exists);
    }
}
