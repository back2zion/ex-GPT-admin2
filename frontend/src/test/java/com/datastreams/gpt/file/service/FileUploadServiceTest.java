package com.datastreams.gpt.file.service;

import com.datastreams.gpt.file.dto.FileUploadHistoryRequestDto;
import com.datastreams.gpt.file.dto.FileUploadHistoryResponseDto;
import com.datastreams.gpt.file.mapper.FileUploadMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * FileUploadService 테스트 클래스
 */
@ExtendWith(MockitoExtension.class)
class FileUploadServiceTest {
    
    @Mock
    private FileUploadMapper fileUploadMapper;
    
    @InjectMocks
    private FileUploadService fileUploadService;
    
    private FileUploadHistoryRequestDto validRequestDto;
    private FileUploadHistoryResponseDto validResponseDto;
    
    @BeforeEach
    void setUp() {
        // 유효한 요청 데이터 설정
        validRequestDto = new FileUploadHistoryRequestDto();
        validRequestDto.setUsrId("21311729");
        validRequestDto.setCnvsIdtId("");
        validRequestDto.setSesnId("SESN_001");
        validRequestDto.setFileNm("test_document.pdf");
        validRequestDto.setMenuIdtId("MENU_001");
        
        // 유효한 응답 데이터 설정
        validResponseDto = new FileUploadHistoryResponseDto();
        validResponseDto.setTxnNm("INS_USR_UPLD_DOC_MNG,INS_USR_CNVS");
        validResponseDto.setCnt(2);
        validResponseDto.setFileUpldSeq(12345L);
        validResponseDto.setCnvsIdtId("21311729_20251016140123");
    }
    
    @Test
    void createFileUploadHistory_유효한_요청_성공() throws Exception {
        // Given
        when(fileUploadMapper.insertFileUploadHistory(any(FileUploadHistoryRequestDto.class)))
            .thenReturn(validResponseDto);
        
        // When
        FileUploadHistoryResponseDto result = fileUploadService.createFileUploadHistory(validRequestDto);
        
        // Then
        assertNotNull(result);
        assertEquals("INS_USR_UPLD_DOC_MNG,INS_USR_CNVS", result.getTxnNm());
        assertEquals(2, result.getCnt());
        assertEquals(12345L, result.getFileUpldSeq());
        assertEquals("21311729_20251016140123", result.getCnvsIdtId());
        
        verify(fileUploadMapper, times(1)).insertFileUploadHistory(validRequestDto);
    }
    
    @Test
    void createFileUploadHistory_null_요청_실패() {
        // When & Then
        Exception exception = assertThrows(IllegalArgumentException.class, () -> {
            fileUploadService.createFileUploadHistory(null);
        });
        
        assertEquals("요청 데이터는 필수입니다.", exception.getMessage());
        verify(fileUploadMapper, never()).insertFileUploadHistory(any());
    }
    
    @Test
    void createFileUploadHistory_사용자ID_누락_실패() {
        // Given
        validRequestDto.setUsrId(null);
        
        // When & Then
        Exception exception = assertThrows(IllegalArgumentException.class, () -> {
            fileUploadService.createFileUploadHistory(validRequestDto);
        });
        
        assertEquals("사용자 아이디는 필수입니다.", exception.getMessage());
        verify(fileUploadMapper, never()).insertFileUploadHistory(any());
    }
    
    @Test
    void createFileUploadHistory_세션ID_누락_실패() {
        // Given
        validRequestDto.setSesnId("");
        
        // When & Then
        Exception exception = assertThrows(IllegalArgumentException.class, () -> {
            fileUploadService.createFileUploadHistory(validRequestDto);
        });
        
        assertEquals("세션 아이디는 필수입니다.", exception.getMessage());
        verify(fileUploadMapper, never()).insertFileUploadHistory(any());
    }
    
    @Test
    void createFileUploadHistory_파일명_누락_실패() {
        // Given
        validRequestDto.setFileNm(null);
        
        // When & Then
        Exception exception = assertThrows(IllegalArgumentException.class, () -> {
            fileUploadService.createFileUploadHistory(validRequestDto);
        });
        
        assertEquals("파일명은 필수입니다.", exception.getMessage());
        verify(fileUploadMapper, never()).insertFileUploadHistory(any());
    }
    
    @Test
    void createFileUploadHistory_메뉴ID_누락_실패() {
        // Given
        validRequestDto.setMenuIdtId("   ");
        
        // When & Then
        Exception exception = assertThrows(IllegalArgumentException.class, () -> {
            fileUploadService.createFileUploadHistory(validRequestDto);
        });
        
        assertEquals("메뉴 식별 아이디는 필수입니다.", exception.getMessage());
        verify(fileUploadMapper, never()).insertFileUploadHistory(any());
    }
    
    @Test
    void createFileUploadHistory_매퍼_응답_null_실패() throws Exception {
        // Given
        when(fileUploadMapper.insertFileUploadHistory(any(FileUploadHistoryRequestDto.class)))
            .thenReturn(null);
        
        // When & Then
        Exception exception = assertThrows(Exception.class, () -> {
            fileUploadService.createFileUploadHistory(validRequestDto);
        });
        
        assertTrue(exception.getMessage().contains("파일 업로드 이력 생성 실패"));
        verify(fileUploadMapper, times(1)).insertFileUploadHistory(validRequestDto);
    }
    
    @Test
    void createFileUploadHistory_매퍼_예외_발생_실패() throws Exception {
        // Given
        when(fileUploadMapper.insertFileUploadHistory(any(FileUploadHistoryRequestDto.class)))
            .thenThrow(new RuntimeException("데이터베이스 오류"));
        
        // When & Then
        Exception exception = assertThrows(Exception.class, () -> {
            fileUploadService.createFileUploadHistory(validRequestDto);
        });
        
        assertTrue(exception.getMessage().contains("파일 업로드 이력 생성 중 오류가 발생했습니다"));
        verify(fileUploadMapper, times(1)).insertFileUploadHistory(validRequestDto);
    }
}
