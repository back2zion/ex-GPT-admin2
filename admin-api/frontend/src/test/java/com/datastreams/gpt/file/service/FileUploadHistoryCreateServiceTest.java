package com.datastreams.gpt.file.service;

import com.datastreams.gpt.file.dto.FileUploadHistoryCreateRequestDto;
import com.datastreams.gpt.file.dto.FileUploadHistoryCreateResponseDto;
import com.datastreams.gpt.file.mapper.FileUploadHistoryCreateMapper;
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
class FileUploadHistoryCreateServiceTest {

    @Mock
    private FileUploadHistoryCreateMapper fileUploadHistoryCreateMapper;

    @InjectMocks
    private FileUploadHistoryCreateService fileUploadHistoryCreateService;

    private FileUploadHistoryCreateRequestDto validRequestDto;
    private FileUploadHistoryCreateResponseDto mockResponseDto;

    @BeforeEach
    void setUp() {
        // 유효한 요청 DTO 설정
        validRequestDto = new FileUploadHistoryCreateRequestDto();
        validRequestDto.setUsrId("testUser");
        validRequestDto.setSesnId("testSession123");
        validRequestDto.setFileNm("test.pdf");
        validRequestDto.setMenuIdtId("MENU001");
        validRequestDto.setCnvsIdtId(""); // 빈 값으로 설정 (첫 업로드)

        // Mock 응답 DTO 설정
        mockResponseDto = new FileUploadHistoryCreateResponseDto();
        mockResponseDto.setTxnNm("INS_USR_UPLD_DOC_MNG,INS_USR_CNVS");
        mockResponseDto.setCnt(2);
        mockResponseDto.setCnvsIdtId("testUser_20231026103000");
        mockResponseDto.setFileUpldSeq(12345L);
    }

    @Test
    void createFileUploadHistory_Success() throws Exception {
        // Given
        when(fileUploadHistoryCreateMapper.createFileUploadHistory(any(FileUploadHistoryCreateRequestDto.class)))
                .thenReturn(mockResponseDto);

        // When
        FileUploadHistoryCreateResponseDto result = fileUploadHistoryCreateService.createFileUploadHistory(validRequestDto);

        // Then
        assertNotNull(result);
        assertEquals("INS_USR_UPLD_DOC_MNG,INS_USR_CNVS", result.getTxnNm());
        assertEquals(2, result.getCnt());
        assertEquals("testUser_20231026103000", result.getCnvsIdtId());
        assertEquals(12345L, result.getFileUpldSeq());
    }

    @Test
    void createFileUploadHistory_NullRequest_ThrowsException() {
        // When & Then
        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () -> {
            fileUploadHistoryCreateService.createFileUploadHistory(null);
        });
        
        assertEquals("요청 데이터가 null입니다.", exception.getMessage());
    }

    @Test
    void createFileUploadHistory_EmptyUserId_ThrowsException() {
        // Given
        validRequestDto.setUsrId("");

        // When & Then
        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () -> {
            fileUploadHistoryCreateService.createFileUploadHistory(validRequestDto);
        });
        
        assertEquals("사용자 아이디는 필수입니다.", exception.getMessage());
    }

    @Test
    void createFileUploadHistory_EmptySessionId_ThrowsException() {
        // Given
        validRequestDto.setSesnId("");

        // When & Then
        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () -> {
            fileUploadHistoryCreateService.createFileUploadHistory(validRequestDto);
        });
        
        assertEquals("세션 아이디는 필수입니다.", exception.getMessage());
    }

    @Test
    void createFileUploadHistory_EmptyFileName_ThrowsException() {
        // Given
        validRequestDto.setFileNm("");

        // When & Then
        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () -> {
            fileUploadHistoryCreateService.createFileUploadHistory(validRequestDto);
        });
        
        assertEquals("파일명은 필수입니다.", exception.getMessage());
    }

    @Test
    void createFileUploadHistory_EmptyMenuId_ThrowsException() {
        // Given
        validRequestDto.setMenuIdtId("");

        // When & Then
        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () -> {
            fileUploadHistoryCreateService.createFileUploadHistory(validRequestDto);
        });
        
        assertEquals("메뉴 식별 아이디는 필수입니다.", exception.getMessage());
    }
}
