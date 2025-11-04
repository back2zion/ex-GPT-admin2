package com.datastreams.gpt.file.controller;

import com.datastreams.gpt.file.dto.FileUploadHistoryCreateRequestDto;
import com.datastreams.gpt.file.dto.FileUploadHistoryCreateResponseDto;
import com.datastreams.gpt.file.service.FileUploadHistoryCreateService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(FileUploadHistoryCreateController.class)
class FileUploadHistoryCreateControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private FileUploadHistoryCreateService fileUploadHistoryCreateService;

    @Autowired
    private ObjectMapper objectMapper;

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
        validRequestDto.setCnvsIdtId("");

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
        when(fileUploadHistoryCreateService.createFileUploadHistory(any(FileUploadHistoryCreateRequestDto.class)))
                .thenReturn(mockResponseDto);

        // When & Then
        mockMvc.perform(post("/api/file/uploadHistory")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequestDto)))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.txnNm").value("INS_USR_UPLD_DOC_MNG,INS_USR_CNVS"))
                .andExpect(jsonPath("$.cnt").value(2))
                .andExpect(jsonPath("$.cnvsIdtId").value("testUser_20231026103000"))
                .andExpect(jsonPath("$.fileUpldSeq").value(12345));
    }

    @Test
    void createFileUploadHistory_ValidationError() throws Exception {
        // Given - 필수 필드가 누락된 요청
        FileUploadHistoryCreateRequestDto invalidRequestDto = new FileUploadHistoryCreateRequestDto();
        invalidRequestDto.setUsrId(""); // 빈 사용자 ID

        when(fileUploadHistoryCreateService.createFileUploadHistory(any(FileUploadHistoryCreateRequestDto.class)))
                .thenThrow(new IllegalArgumentException("사용자 아이디는 필수입니다."));

        // When & Then
        mockMvc.perform(post("/api/file/uploadHistory")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(invalidRequestDto)))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("사용자 아이디는 필수입니다."));
    }

    @Test
    void createFileUploadHistory_ServerError() throws Exception {
        // Given
        when(fileUploadHistoryCreateService.createFileUploadHistory(any(FileUploadHistoryCreateRequestDto.class)))
                .thenThrow(new RuntimeException("데이터베이스 연결 오류"));

        // When & Then
        mockMvc.perform(post("/api/file/uploadHistory")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validRequestDto)))
                .andExpect(status().isInternalServerError())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("파일 업로드 이력 생성 중 오류가 발생했습니다."));
    }
}
