package com.datastreams.gpt.file.service;

import com.datastreams.gpt.file.dto.SessionFileStatusRequestDto;
import com.datastreams.gpt.file.dto.SessionFileStatusResponseDto;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class SessionFileStatusServiceTest {

    @InjectMocks
    private SessionFileStatusService sessionFileStatusService;

    private RestTemplate restTemplate;
    private SessionFileStatusRequestDto validRequestDto;

    @BeforeEach
    void setUp() {
        restTemplate = mock(RestTemplate.class);
        ReflectionTestUtils.setField(sessionFileStatusService, "restTemplate", restTemplate);
        ReflectionTestUtils.setField(sessionFileStatusService, "fastApiBaseUrl", "http://localhost:8000");
        ReflectionTestUtils.setField(sessionFileStatusService, "apiKey", "test-api-key");

        // 유효한 요청 DTO 설정
        validRequestDto = new SessionFileStatusRequestDto();
        validRequestDto.setFileUid("tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34");
    }

    @Test
    void getSessionFileStatus_Success_Ready() throws Exception {
        // Given
        Map<String, Object> responseMap = new HashMap<>();
        responseMap.put("status", "ready");
        responseMap.put("file_name", "test.pdf");
        responseMap.put("file_size", 1024L);
        responseMap.put("progress", 100);
        
        String jsonResponse = "{\"status\":\"ready\",\"file_name\":\"test.pdf\",\"file_size\":1024,\"progress\":100}";
        ResponseEntity<String> mockResponse = new ResponseEntity<>(jsonResponse, HttpStatus.OK);
        
        when(restTemplate.exchange(anyString(), eq(HttpMethod.GET), any(), eq(String.class)))
                .thenReturn(mockResponse);

        // When
        SessionFileStatusResponseDto result = sessionFileStatusService.getSessionFileStatus(validRequestDto);

        // Then
        assertNotNull(result);
        assertEquals("tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34", result.getFileUid());
        assertEquals("ready", result.getStatus());
        assertEquals("test.pdf", result.getFileName());
        assertEquals(1024L, result.getFileSize());
        assertEquals(100, result.getProgress());
        assertNotNull(result.getCheckedAt());
    }

    @Test
    void getSessionFileStatus_Success_Processing() throws Exception {
        // Given
        Map<String, Object> responseMap = new HashMap<>();
        responseMap.put("status", "processed");
        responseMap.put("next_step", "ready");
        responseMap.put("progress", 75);
        
        String jsonResponse = "{\"status\":\"processed\",\"next_step\":\"ready\",\"progress\":75}";
        ResponseEntity<String> mockResponse = new ResponseEntity<>(jsonResponse, HttpStatus.OK);
        
        when(restTemplate.exchange(anyString(), eq(HttpMethod.GET), any(), eq(String.class)))
                .thenReturn(mockResponse);

        // When
        SessionFileStatusResponseDto result = sessionFileStatusService.getSessionFileStatus(validRequestDto);

        // Then
        assertNotNull(result);
        assertEquals("processed", result.getStatus());
        assertEquals("ready", result.getNextStep());
        assertEquals(75, result.getProgress());
    }

    @Test
    void getSessionFileStatus_Success_Error() throws Exception {
        // Given
        Map<String, Object> responseMap = new HashMap<>();
        responseMap.put("status", "error");
        responseMap.put("error", "파일 파싱 실패");
        
        String jsonResponse = "{\"status\":\"error\",\"error\":\"파일 파싱 실패\"}";
        ResponseEntity<String> mockResponse = new ResponseEntity<>(jsonResponse, HttpStatus.OK);
        
        when(restTemplate.exchange(anyString(), eq(HttpMethod.GET), any(), eq(String.class)))
                .thenReturn(mockResponse);

        // When
        SessionFileStatusResponseDto result = sessionFileStatusService.getSessionFileStatus(validRequestDto);

        // Then
        assertNotNull(result);
        assertEquals("error", result.getStatus());
        assertEquals("파일 파싱 실패", result.getError());
    }

    @Test
    void getSessionFileStatus_NullRequest_ThrowsException() {
        // When & Then
        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () -> {
            sessionFileStatusService.getSessionFileStatus(null);
        });
        
        assertEquals("요청 데이터가 null입니다.", exception.getMessage());
    }

    @Test
    void getSessionFileStatus_EmptyFileUid_ThrowsException() {
        // Given
        validRequestDto.setFileUid("");

        // When & Then
        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () -> {
            sessionFileStatusService.getSessionFileStatus(validRequestDto);
        });
        
        assertEquals("파일 아이디는 필수입니다.", exception.getMessage());
    }

    @Test
    void getSessionFileStatus_InvalidFileUid_ThrowsException() {
        // Given
        validRequestDto.setFileUid("invalid@file#id");

        // When & Then
        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () -> {
            sessionFileStatusService.getSessionFileStatus(validRequestDto);
        });
        
        assertEquals("유효하지 않은 파일 아이디 형식입니다.", exception.getMessage());
    }

    @Test
    void getSessionFileStatus_FastApiError_ThrowsException() {
        // Given
        ResponseEntity<String> errorResponse = new ResponseEntity<>("Server Error", HttpStatus.INTERNAL_SERVER_ERROR);
        
        when(restTemplate.exchange(anyString(), eq(HttpMethod.GET), any(), eq(String.class)))
                .thenReturn(errorResponse);

        // When & Then
        Exception exception = assertThrows(Exception.class, () -> {
            sessionFileStatusService.getSessionFileStatus(validRequestDto);
        });
        
        assertTrue(exception.getMessage().contains("FastAPI 파일 상태 조회 실패"));
    }

    @Test
    void isFileReady_ReturnsCorrect() {
        assertTrue(sessionFileStatusService.isFileReady("ready"));
        assertFalse(sessionFileStatusService.isFileReady("processing"));
        assertFalse(sessionFileStatusService.isFileReady("error"));
    }

    @Test
    void isFileError_ReturnsCorrect() {
        assertTrue(sessionFileStatusService.isFileError("error"));
        assertFalse(sessionFileStatusService.isFileError("ready"));
        assertFalse(sessionFileStatusService.isFileError("processing"));
    }

    @Test
    void isFileProcessing_ReturnsCorrect() {
        assertTrue(sessionFileStatusService.isFileProcessing("uploaded"));
        assertTrue(sessionFileStatusService.isFileProcessing("parsed"));
        assertTrue(sessionFileStatusService.isFileProcessing("processed"));
        assertFalse(sessionFileStatusService.isFileProcessing("ready"));
        assertFalse(sessionFileStatusService.isFileProcessing("error"));
    }
}
