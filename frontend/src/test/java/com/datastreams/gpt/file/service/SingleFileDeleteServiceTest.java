package com.datastreams.gpt.file.service;

import com.datastreams.gpt.file.dto.SingleFileDeleteRequestDto;
import com.datastreams.gpt.file.dto.SingleFileDeleteResponseDto;
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
class SingleFileDeleteServiceTest {

    @InjectMocks
    private SingleFileDeleteService singleFileDeleteService;

    private RestTemplate restTemplate;
    private SingleFileDeleteRequestDto validRequest;

    @BeforeEach
    void setUp() {
        restTemplate = mock(RestTemplate.class);
        ReflectionTestUtils.setField(singleFileDeleteService, "restTemplate", restTemplate);
        ReflectionTestUtils.setField(singleFileDeleteService, "fastApiBaseUrl", "http://localhost:8000");
        ReflectionTestUtils.setField(singleFileDeleteService, "apiKey", "test-api-key");

        validRequest = new SingleFileDeleteRequestDto();
        validRequest.setCnvsIdtId("USR_ID_20231026103000123456");
        validRequest.setFileUid("tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34");
    }

    @Test
    void deleteSingleFile_Success() throws Exception {
        // Given
        String mockResponse = "File 'document.pdf' deleted successfully (1024000 bytes)";
        ResponseEntity<String> responseEntity = new ResponseEntity<>(mockResponse, HttpStatus.OK);
        
        when(restTemplate.exchange(
                any(String.class),
                eq(HttpMethod.DELETE),
                any(),
                eq(String.class)
        )).thenReturn(responseEntity);

        // When
        SingleFileDeleteResponseDto result = singleFileDeleteService.deleteSingleFile(validRequest);

        // Then
        assertNotNull(result);
        assertEquals("USR_ID_20231026103000123456", result.getCnvsIdtId());
        assertEquals("tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34", result.getFileUid());
        assertEquals("success", result.getStatus());
        assertNotNull(result.getDeletedAt());
        assertTrue(result.getProcessingTime() >= 0);
        assertEquals(1024000L, result.getFileSize());
        assertEquals("document.pdf", result.getFileName());
    }

    @Test
    void deleteSingleFile_Success_JsonResponse() throws Exception {
        // Given
        String mockResponse = "{\"file_name\": \"document.pdf\", \"file_size\": 2048000}";
        ResponseEntity<String> responseEntity = new ResponseEntity<>(mockResponse, HttpStatus.OK);
        
        when(restTemplate.exchange(
                any(String.class),
                eq(HttpMethod.DELETE),
                any(),
                eq(String.class)
        )).thenReturn(responseEntity);

        // When
        SingleFileDeleteResponseDto result = singleFileDeleteService.deleteSingleFile(validRequest);

        // Then
        assertNotNull(result);
        assertEquals("USR_ID_20231026103000123456", result.getCnvsIdtId());
        assertEquals("tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34", result.getFileUid());
        assertEquals("success", result.getStatus());
        assertEquals(2048000L, result.getFileSize());
        assertEquals("document.pdf", result.getFileName());
    }

    @Test
    void deleteSingleFile_NullRequest_ThrowsException() {
        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            singleFileDeleteService.deleteSingleFile(null);
        });
        
        assertEquals("요청 데이터가 null입니다.", thrown.getMessage());
    }

    @Test
    void deleteSingleFile_EmptyCnvsIdtId_ThrowsException() {
        // Given
        validRequest.setCnvsIdtId("");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            singleFileDeleteService.deleteSingleFile(validRequest);
        });
        
        assertEquals("대화 식별 아이디는 필수입니다.", thrown.getMessage());
    }

    @Test
    void deleteSingleFile_EmptyFileUid_ThrowsException() {
        // Given
        validRequest.setFileUid("");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            singleFileDeleteService.deleteSingleFile(validRequest);
        });
        
        assertEquals("파일 아이디는 필수입니다.", thrown.getMessage());
    }

    @Test
    void deleteSingleFile_InvalidCnvsIdtId_ThrowsException() {
        // Given
        validRequest.setCnvsIdtId("invalid@cnvs#id");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            singleFileDeleteService.deleteSingleFile(validRequest);
        });
        
        assertEquals("유효하지 않은 대화 식별 아이디 형식입니다.", thrown.getMessage());
    }

    @Test
    void deleteSingleFile_InvalidFileUid_ThrowsException() {
        // Given
        validRequest.setFileUid("invalid@file#id");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            singleFileDeleteService.deleteSingleFile(validRequest);
        });
        
        assertEquals("유효하지 않은 파일 아이디 형식입니다.", thrown.getMessage());
    }

    @Test
    void deleteSingleFile_FastApiError_ThrowsException() {
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
            singleFileDeleteService.deleteSingleFile(validRequest);
        });
        
        assertTrue(exception.getMessage().contains("FastAPI 단일 파일 삭제 실패"));
    }

    @Test
    void checkFastApiHealth_ReturnsTrue() {
        // Given
        ResponseEntity<String> healthResponse = new ResponseEntity<>("{\"n_chunks\": 0}", HttpStatus.OK);
        
        when(restTemplate.getForEntity(any(String.class), eq(String.class)))
                .thenReturn(healthResponse);

        // When
        boolean result = singleFileDeleteService.checkFastApiHealth();

        // Then
        assertTrue(result);
    }

    @Test
    void checkFastApiHealth_ReturnsFalse() {
        // Given
        when(restTemplate.getForEntity(any(String.class), eq(String.class)))
                .thenThrow(new RuntimeException("Connection refused"));

        // When
        boolean result = singleFileDeleteService.checkFastApiHealth();

        // Then
        assertFalse(result);
    }
}
