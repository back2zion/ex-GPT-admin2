package com.datastreams.gpt.file.service;

import com.datastreams.gpt.file.dto.SessionFileDeleteRequestDto;
import com.datastreams.gpt.file.dto.SessionFileDeleteResponseDto;
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

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class SessionFileDeleteServiceTest {

    @InjectMocks
    private SessionFileDeleteService sessionFileDeleteService;

    private RestTemplate restTemplate;
    private SessionFileDeleteRequestDto validRequest;

    @BeforeEach
    void setUp() {
        restTemplate = mock(RestTemplate.class);
        ReflectionTestUtils.setField(sessionFileDeleteService, "restTemplate", restTemplate);
        ReflectionTestUtils.setField(sessionFileDeleteService, "fastApiBaseUrl", "http://localhost:8000");
        ReflectionTestUtils.setField(sessionFileDeleteService, "apiKey", "test-api-key");

        validRequest = new SessionFileDeleteRequestDto();
        validRequest.setCnvsIdtId("USR_ID_20231026103000123456");
    }

    @Test
    void deleteSessionFiles_Success() throws Exception {
        // Given
        String mockResponse = "3 files deleted successfully";
        ResponseEntity<String> responseEntity = new ResponseEntity<>(mockResponse, HttpStatus.OK);
        
        when(restTemplate.exchange(
                any(String.class),
                eq(HttpMethod.DELETE),
                any(),
                eq(String.class)
        )).thenReturn(responseEntity);

        // When
        SessionFileDeleteResponseDto result = sessionFileDeleteService.deleteSessionFiles(validRequest);

        // Then
        assertNotNull(result);
        assertEquals("USR_ID_20231026103000123456", result.getCnvsIdtId());
        assertEquals("success", result.getStatus());
        assertEquals(3, result.getDeletedFileCount());
        assertNotNull(result.getDeletedAt());
        assertTrue(result.getProcessingTime() >= 0);
    }

    @Test
    void deleteSessionFiles_Success_JsonResponse() throws Exception {
        // Given
        String mockResponse = "{\"deleted_count\": 2, \"deleted_files\": [\"tmp-123\", \"tmp-456\"]}";
        ResponseEntity<String> responseEntity = new ResponseEntity<>(mockResponse, HttpStatus.OK);
        
        when(restTemplate.exchange(
                any(String.class),
                eq(HttpMethod.DELETE),
                any(),
                eq(String.class)
        )).thenReturn(responseEntity);

        // When
        SessionFileDeleteResponseDto result = sessionFileDeleteService.deleteSessionFiles(validRequest);

        // Then
        assertNotNull(result);
        assertEquals("USR_ID_20231026103000123456", result.getCnvsIdtId());
        assertEquals("success", result.getStatus());
        assertEquals(2, result.getDeletedFileCount());
        assertNotNull(result.getDeletedFiles());
    }

    @Test
    void deleteSessionFiles_NullRequest_ThrowsException() {
        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            sessionFileDeleteService.deleteSessionFiles(null);
        });
        
        assertEquals("요청 데이터가 null입니다.", thrown.getMessage());
    }

    @Test
    void deleteSessionFiles_EmptyCnvsIdtId_ThrowsException() {
        // Given
        validRequest.setCnvsIdtId("");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            sessionFileDeleteService.deleteSessionFiles(validRequest);
        });
        
        assertEquals("대화 식별 아이디는 필수입니다.", thrown.getMessage());
    }

    @Test
    void deleteSessionFiles_InvalidCnvsIdtId_ThrowsException() {
        // Given
        validRequest.setCnvsIdtId("invalid@cnvs#id");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            sessionFileDeleteService.deleteSessionFiles(validRequest);
        });
        
        assertEquals("유효하지 않은 대화 식별 아이디 형식입니다.", thrown.getMessage());
    }

    @Test
    void deleteSessionFiles_FastApiError_ThrowsException() {
        // Given
        ResponseEntity<String> errorResponse = new ResponseEntity<>("Server Error", HttpStatus.INTERNAL_SERVER_ERROR);
        
        when(restTemplate.exchange(
                any(String.class),
                eq(HttpMethod.DELETE),
                any(),
                eq(String.class)
        )).thenReturn(errorResponse);

        // When & Then
        Exception exception = assertThrows(Exception.class, () -> {
            sessionFileDeleteService.deleteSessionFiles(validRequest);
        });
        
        assertTrue(exception.getMessage().contains("FastAPI 세션 파일 삭제 실패"));
    }

    @Test
    void checkFastApiHealth_ReturnsTrue() {
        // Given
        ResponseEntity<String> healthResponse = new ResponseEntity<>("{\"n_chunks\": 0}", HttpStatus.OK);
        
        when(restTemplate.getForEntity(any(String.class), eq(String.class)))
                .thenReturn(healthResponse);

        // When
        boolean result = sessionFileDeleteService.checkFastApiHealth();

        // Then
        assertTrue(result);
    }

    @Test
    void checkFastApiHealth_ReturnsFalse() {
        // Given
        when(restTemplate.getForEntity(any(String.class), eq(String.class)))
                .thenThrow(new RuntimeException("Connection refused"));

        // When
        boolean result = sessionFileDeleteService.checkFastApiHealth();

        // Then
        assertFalse(result);
    }
}
