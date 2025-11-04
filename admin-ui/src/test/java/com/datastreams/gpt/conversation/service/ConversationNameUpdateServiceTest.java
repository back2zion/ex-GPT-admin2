package com.datastreams.gpt.conversation.service;

import com.datastreams.gpt.conversation.dto.ConversationNameUpdateRequestDto;
import com.datastreams.gpt.conversation.dto.ConversationNameUpdateResponseDto;
import com.datastreams.gpt.conversation.mapper.ConversationNameUpdateMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
public class ConversationNameUpdateServiceTest {

    @Mock
    private ConversationNameUpdateMapper conversationNameUpdateMapper;

    @InjectMocks
    private ConversationNameUpdateService conversationNameUpdateService;

    private ConversationNameUpdateRequestDto validRequest;
    private List<Map<String, Object>> mockResultList;
    private Map<String, Object> mockUpdatedInfo;

    @BeforeEach
    void setUp() {
        validRequest = new ConversationNameUpdateRequestDto();
        validRequest.setCnvsIdtId("CNVS_12345");
        validRequest.setRepCnvsNm("새로운 대화명");
        validRequest.setUseYn("Y");
        
        mockResultList = new ArrayList<>();
        Map<String, Object> result = new HashMap<>();
        result.put("TXN_NM", "UPD_USR_CNVS_SMRY");
        result.put("CNT", 1);
        mockResultList.add(result);
        
        mockUpdatedInfo = new HashMap<>();
        mockUpdatedInfo.put("CNVS_IDT_ID", "CNVS_12345");
        mockUpdatedInfo.put("REP_CNVS_NM", "새로운 대화명");
        mockUpdatedInfo.put("USE_YN", "Y");
        mockUpdatedInfo.put("MOD_DT", "2025-10-17 16:30:00");
    }

    @Test
    @DisplayName("L-025: 대화 대표 명 변경 성공")
    void updateConversationName_success() {
        // Given
        when(conversationNameUpdateMapper.updateConversationName(any(ConversationNameUpdateRequestDto.class)))
                .thenReturn(mockResultList);
        when(conversationNameUpdateMapper.selectUpdatedConversationInfo(anyString()))
                .thenReturn(mockUpdatedInfo);

        // When
        ConversationNameUpdateResponseDto result = conversationNameUpdateService.updateConversationName(validRequest);

        // Then
        assertNotNull(result);
        assertEquals("CNVS_12345", result.getCnvsIdtId());
        assertEquals("UPD_USR_CNVS_SMRY", result.getTxnNm());
        assertEquals(1, result.getCnt());
        assertEquals("success", result.getStatus());
        assertEquals("새로운 대화명", result.getUpdatedRepCnvsNm());
        assertEquals("Y", result.getUpdatedUseYn());
        assertTrue(result.getProcessingTime() >= 0);
    }

    @Test
    @DisplayName("L-025: 대화 대표 명 변경 실패 - null 요청")
    void updateConversationName_fail_nullRequest() {
        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            conversationNameUpdateService.updateConversationName(null);
        });
        
        assertEquals("요청 데이터가 null입니다.", thrown.getMessage());
    }

    @Test
    @DisplayName("L-025: 대화 대표 명 변경 실패 - 빈 대화 식별 ID")
    void updateConversationName_fail_emptyCnvsIdtId() {
        // Given
        validRequest.setCnvsIdtId("");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            conversationNameUpdateService.updateConversationName(validRequest);
        });
        
        assertEquals("대화 식별 ID는 필수입니다.", thrown.getMessage());
    }

    @Test
    @DisplayName("L-025: 대화 대표 명 변경 실패 - 빈 대화명과 사용여부")
    void updateConversationName_fail_emptyBothFields() {
        // Given
        validRequest.setRepCnvsNm("");
        validRequest.setUseYn("");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            conversationNameUpdateService.updateConversationName(validRequest);
        });
        
        assertEquals("대화 대표 명 또는 사용 여부 중 하나는 필수입니다.", thrown.getMessage());
    }

    @Test
    @DisplayName("L-025: 대화 대표 명 변경 실패 - 잘못된 사용여부 값")
    void updateConversationName_fail_invalidUseYn() {
        // Given
        validRequest.setUseYn("X");

        // When & Then
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            conversationNameUpdateService.updateConversationName(validRequest);
        });
        
        assertEquals("사용 여부는 'Y' 또는 'N'만 가능합니다.", thrown.getMessage());
    }

    @Test
    @DisplayName("L-025: 대화 대표 명 변경 - 대화명만 변경")
    void updateConversationName_nameOnly() {
        // Given
        validRequest.setUseYn(null);
        when(conversationNameUpdateMapper.updateConversationName(any(ConversationNameUpdateRequestDto.class)))
                .thenReturn(mockResultList);
        when(conversationNameUpdateMapper.selectUpdatedConversationInfo(anyString()))
                .thenReturn(mockUpdatedInfo);

        // When
        ConversationNameUpdateResponseDto result = conversationNameUpdateService.updateConversationName(validRequest);

        // Then
        assertNotNull(result);
        assertEquals("success", result.getStatus());
        assertEquals(1, result.getCnt());
    }

    @Test
    @DisplayName("L-025: 대화 대표 명 변경 - 사용여부만 변경")
    void updateConversationName_useYnOnly() {
        // Given
        validRequest.setRepCnvsNm(null);
        when(conversationNameUpdateMapper.updateConversationName(any(ConversationNameUpdateRequestDto.class)))
                .thenReturn(mockResultList);
        when(conversationNameUpdateMapper.selectUpdatedConversationInfo(anyString()))
                .thenReturn(mockUpdatedInfo);

        // When
        ConversationNameUpdateResponseDto result = conversationNameUpdateService.updateConversationName(validRequest);

        // Then
        assertNotNull(result);
        assertEquals("success", result.getStatus());
        assertEquals(1, result.getCnt());
    }

    @Test
    @DisplayName("L-025: 대화 대표 명 변경 - 데이터베이스 오류")
    void updateConversationName_databaseError() {
        // Given
        when(conversationNameUpdateMapper.updateConversationName(any(ConversationNameUpdateRequestDto.class)))
                .thenThrow(new RuntimeException("Database connection failed"));

        // When
        ConversationNameUpdateResponseDto result = conversationNameUpdateService.updateConversationName(validRequest);

        // Then
        assertNotNull(result);
        assertEquals("CNVS_12345", result.getCnvsIdtId());
        assertEquals("error", result.getStatus());
        assertEquals(0, result.getCnt());
    }
}
