package com.datastreams.gpt.file.controller;

import com.datastreams.gpt.file.dto.FileUploadHistoryRequestDto;
import com.datastreams.gpt.file.dto.FileUploadHistoryResponseDto;
import com.datastreams.gpt.file.service.FileUploadService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Arrays;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * FileUploadController 테스트 클래스
 */
@WebMvcTest(FileUploadController.class)
class FileUploadControllerTest {
    
    @Autowired
    private MockMvc mockMvc;
    
    @MockBean
    private FileUploadService fileUploadService;
    
    @Autowired
    private ObjectMapper objectMapper;
    
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
        when(fileUploadService.createFileUploadHistory(any(FileUploadHistoryRequestDto.class)))
            .thenReturn(validResponseDto);
        
        // When & Then
        mockMvc.perform(post("/api/file/upload/history")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequestDto)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.result").value("success"))
                .andExpect(jsonPath("$.data.txn_nm").value("INS_USR_UPLD_DOC_MNG,INS_USR_CNVS"))
                .andExpect(jsonPath("$.data.cnt").value(2))
                .andExpect(jsonPath("$.data.file_upld_seq").value(12345))
                .andExpect(jsonPath("$.data.cnvs_idt_id").value("21311729_20251016140123"))
                .andExpect(jsonPath("$.message").value("파일 업로드 이력이 성공적으로 생성되었습니다."));
    }
    
    @Test
    void createFileUploadHistory_잘못된_요청_400() throws Exception {
        // Given
        validRequestDto.setUsrId(null); // 필수 필드 누락
        
        when(fileUploadService.createFileUploadHistory(any(FileUploadHistoryRequestDto.class)))
            .thenThrow(new IllegalArgumentException("사용자 아이디는 필수입니다."));
        
        // When & Then
        mockMvc.perform(post("/api/file/upload/history")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequestDto)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.result").value("error"))
                .andExpect(jsonPath("$.error").value("사용자 아이디는 필수입니다."))
                .andExpect(jsonPath("$.message").value("요청 데이터가 올바르지 않습니다."));
    }
    
    @Test
    void createFileUploadHistory_서버_오류_500() throws Exception {
        // Given
        when(fileUploadService.createFileUploadHistory(any(FileUploadHistoryRequestDto.class)))
            .thenThrow(new RuntimeException("데이터베이스 연결 오류"));
        
        // When & Then
        mockMvc.perform(post("/api/file/upload/history")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequestDto)))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.result").value("error"))
                .andExpect(jsonPath("$.error").value("데이터베이스 연결 오류"))
                .andExpect(jsonPath("$.message").value("파일 업로드 이력 생성 중 오류가 발생했습니다."));
    }
    
    @Test
    void getFileUploadBySeq_유효한_요청_성공() throws Exception {
        // Given
        when(fileUploadService.getFileUploadBySeq(anyLong()))
            .thenReturn(validRequestDto);
        
        // When & Then
        mockMvc.perform(get("/api/file/upload/12345"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.result").value("success"))
                .andExpect(jsonPath("$.data.usr_id").value("21311729"))
                .andExpect(jsonPath("$.data.file_nm").value("test_document.pdf"))
                .andExpect(jsonPath("$.message").value("파일 업로드 정보를 성공적으로 조회했습니다."));
    }
    
    @Test
    void getFileUploadBySeq_찾을수없음_500() throws Exception {
        // Given
        when(fileUploadService.getFileUploadBySeq(anyLong()))
            .thenThrow(new RuntimeException("해당 파일 업로드 정보를 찾을 수 없습니다."));
        
        // When & Then
        mockMvc.perform(get("/api/file/upload/99999"))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.result").value("error"))
                .andExpect(jsonPath("$.message").value("파일 업로드 정보 조회 중 오류가 발생했습니다."));
    }
    
    @Test
    void getFileUploadListByConversation_유효한_요청_성공() throws Exception {
        // Given
        List<FileUploadHistoryRequestDto> fileList = Arrays.asList(validRequestDto);
        when(fileUploadService.getFileUploadListByConversation(anyString()))
            .thenReturn(fileList);
        
        // When & Then
        mockMvc.perform(get("/api/file/upload/conversation/21311729_20251016140123"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.result").value("success"))
                .andExpect(jsonPath("$.data").isArray())
                .andExpect(jsonPath("$.data[0].usr_id").value("21311729"))
                .andExpect(jsonPath("$.data[0].file_nm").value("test_document.pdf"))
                .andExpect(jsonPath("$.count").value(1))
                .andExpect(jsonPath("$.message").value("파일 업로드 목록을 성공적으로 조회했습니다."));
    }
    
    @Test
    void getFileUploadListByConversation_잘못된_대화ID_500() throws Exception {
        // Given
        when(fileUploadService.getFileUploadListByConversation(anyString()))
            .thenThrow(new IllegalArgumentException("대화 식별 ID는 필수입니다."));
        
        // When & Then
        mockMvc.perform(get("/api/file/upload/conversation/"))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.result").value("error"))
                .andExpect(jsonPath("$.message").value("파일 업로드 목록 조회 중 오류가 발생했습니다."));
    }
}
