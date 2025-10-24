package com.datastreams.gpt.file.service;

import com.datastreams.gpt.file.dto.SessionFileUploadRequestDto;
import com.datastreams.gpt.file.dto.SessionFileUploadResponseDto;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.MockedStatic;
import org.mockito.Mockito;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.core.io.InputStreamResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class SessionFileUploadServiceTest {

    @InjectMocks
    private SessionFileUploadService sessionFileUploadService;

    private RestTemplate restTemplate;
    private SessionFileUploadRequestDto validRequestDto;
    private MultipartFile mockFile;

    @BeforeEach
    void setUp() {
        restTemplate = mock(RestTemplate.class);
        ReflectionTestUtils.setField(sessionFileUploadService, "restTemplate", restTemplate);
        ReflectionTestUtils.setField(sessionFileUploadService, "fastApiBaseUrl", "http://localhost:8000");
        ReflectionTestUtils.setField(sessionFileUploadService, "apiKey", "test-api-key");

        // Mock MultipartFile 설정
        mockFile = mock(MultipartFile.class);
        when(mockFile.getOriginalFilename()).thenReturn("test.pdf");
        when(mockFile.getSize()).thenReturn(1024L);
        when(mockFile.isEmpty()).thenReturn(false);
        
        try {
            InputStream inputStream = new ByteArrayInputStream("test content".getBytes());
            when(mockFile.getInputStream()).thenReturn(inputStream);
        } catch (Exception e) {
            fail("Mock file setup failed: " + e.getMessage());
        }

        // 유효한 요청 DTO 설정
        validRequestDto = new SessionFileUploadRequestDto();
        validRequestDto.setCnvsIdtId("user123_20231026103000");
        validRequestDto.setFile(mockFile);
        validRequestDto.setUserId("user123");
        validRequestDto.setWait(true);
    }

    @Test
    void uploadSessionFile_Success() throws Exception {
        // Given
        Map<String, Object> responseMap = new HashMap<>();
        responseMap.put("file_id", "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34");
        
        String jsonResponse = "{\"file_id\":\"tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34\"}";
        ResponseEntity<String> mockResponse = new ResponseEntity<>(jsonResponse, HttpStatus.OK);
        
        when(restTemplate.exchange(anyString(), eq(HttpMethod.POST), any(HttpEntity.class), eq(String.class)))
                .thenReturn(mockResponse);

        // When
        SessionFileUploadResponseDto result = sessionFileUploadService.uploadSessionFile(validRequestDto);

        // Then
        assertNotNull(result);
        assertEquals("user123_20231026103000", result.getCnvsIdtId());
        assertEquals("tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34", result.getFileUid());
        assertEquals("test.pdf", result.getFileName());
        assertEquals(1024L, result.getFileSize());
        assertEquals("completed", result.getStatus());
        assertTrue(result.getProcessingTime() > 0);
    }

    @Test
    void uploadSessionFile_NullRequest_ThrowsException() {
        // When & Then
        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () -> {
            sessionFileUploadService.uploadSessionFile(null);
        });
        
        assertEquals("요청 데이터가 null입니다.", exception.getMessage());
    }

    @Test
    void uploadSessionFile_EmptySessionId_ThrowsException() {
        // Given
        validRequestDto.setCnvsIdtId("");

        // When & Then
        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () -> {
            sessionFileUploadService.uploadSessionFile(validRequestDto);
        });
        
        assertEquals("대화 식별 아이디는 필수입니다.", exception.getMessage());
    }

    @Test
    void uploadSessionFile_EmptyUserId_ThrowsException() {
        // Given
        validRequestDto.setUserId("");

        // When & Then
        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () -> {
            sessionFileUploadService.uploadSessionFile(validRequestDto);
        });
        
        assertEquals("사용자 아이디는 필수입니다.", exception.getMessage());
    }

    @Test
    void uploadSessionFile_EmptyFile_ThrowsException() {
        // Given
        when(mockFile.isEmpty()).thenReturn(true);
        validRequestDto.setFile(mockFile);

        // When & Then
        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () -> {
            sessionFileUploadService.uploadSessionFile(validRequestDto);
        });
        
        assertEquals("업로드할 파일이 없습니다.", exception.getMessage());
    }

    @Test
    void uploadSessionFile_FileTooLarge_ThrowsException() {
        // Given
        when(mockFile.getSize()).thenReturn(101L * 1024 * 1024); // 101MB

        // When & Then
        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () -> {
            sessionFileUploadService.uploadSessionFile(validRequestDto);
        });
        
        assertEquals("파일 크기가 너무 큽니다. 최대 100MB까지 업로드 가능합니다.", exception.getMessage());
    }

    @Test
    void uploadSessionFile_InvalidFileExtension_ThrowsException() {
        // Given
        when(mockFile.getOriginalFilename()).thenReturn("test.xyz");

        // When & Then
        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () -> {
            sessionFileUploadService.uploadSessionFile(validRequestDto);
        });
        
        assertEquals("지원하지 않는 파일 형식입니다. 허용 형식: pdf, hwp, hwpx, doc, docx, ppt, pptx, txt, xls, xlsx", exception.getMessage());
    }

    @Test
    void uploadSessionFile_FastApiError_ThrowsException() {
        // Given
        ResponseEntity<String> errorResponse = new ResponseEntity<>("Server Error", HttpStatus.INTERNAL_SERVER_ERROR);
        
        when(restTemplate.exchange(anyString(), eq(HttpMethod.POST), any(HttpEntity.class), eq(String.class)))
                .thenReturn(errorResponse);

        // When & Then
        Exception exception = assertThrows(Exception.class, () -> {
            sessionFileUploadService.uploadSessionFile(validRequestDto);
        });
        
        assertTrue(exception.getMessage().contains("FastAPI 세션 파일 업로드 실패"));
    }
}
