package com.datastreams.gpt.chat.service;

import com.datastreams.gpt.chat.dto.ConversationHistoryRequestDto;
import com.datastreams.gpt.chat.dto.ConversationHistoryResponseDto;
import com.datastreams.gpt.chat.mapper.ConversationHistoryMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ConversationHistoryServiceTest {

    @Mock
    private ConversationHistoryMapper conversationHistoryMapper;

    @InjectMocks
    private ConversationHistoryService conversationHistoryService;

    private ConversationHistoryRequestDto validRequest;
    private List<ConversationHistoryResponseDto> mockResponseList;

    @BeforeEach
    void setUp() {
        validRequest = new ConversationHistoryRequestDto();
        validRequest.setCnvsIdtId("testuser_20251016100000000");
        validRequest.setCnvsId(12345L);

        ConversationHistoryResponseDto response1 = new ConversationHistoryResponseDto();
        response1.setRowSeq(1);
        response1.setQuesTxt("첫 번째 질문입니다.");
        response1.setAnsTxt("첫 번째 답변입니다.");

        ConversationHistoryResponseDto response2 = new ConversationHistoryResponseDto();
        response2.setRowSeq(2);
        response2.setQuesTxt("두 번째 질문입니다.");
        response2.setAnsTxt("두 번째 답변입니다.");

        mockResponseList = Arrays.asList(response1, response2);
    }

    @Test
    @DisplayName("이전 대화 이력 조회 성공")
    void getConversationHistory_success() throws Exception {
        when(conversationHistoryMapper.selectConversationHistory(any(ConversationHistoryRequestDto.class)))
                .thenReturn(mockResponseList);

        List<ConversationHistoryResponseDto> result = conversationHistoryService.getConversationHistory(validRequest);

        assertNotNull(result);
        assertEquals(2, result.size());
        assertEquals("첫 번째 질문입니다.", result.get(0).getQuesTxt());
        assertEquals("첫 번째 답변입니다.", result.get(0).getAnsTxt());
        assertEquals("두 번째 질문입니다.", result.get(1).getQuesTxt());
        assertEquals("두 번째 답변입니다.", result.get(1).getAnsTxt());
    }

    @Test
    @DisplayName("이전 대화 이력 조회 실패 - 필수 파라미터 누락 (대화 식별 아이디)")
    void getConversationHistory_missingCnvsIdtId_throwsException() {
        validRequest.setCnvsIdtId(null);
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            conversationHistoryService.getConversationHistory(validRequest);
        });
        assertEquals("대화 식별 아이디는 필수입니다.", thrown.getMessage());
    }

    @Test
    @DisplayName("이전 대화 이력 조회 실패 - 필수 파라미터 누락 (대화 아이디)")
    void getConversationHistory_missingCnvsId_throwsException() {
        validRequest.setCnvsId(null);
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            conversationHistoryService.getConversationHistory(validRequest);
        });
        assertEquals("대화 아이디는 필수입니다.", thrown.getMessage());
    }

    @Test
    @DisplayName("이전 대화 이력 조회 실패 - 빈 대화 식별 아이디")
    void getConversationHistory_emptyCnvsIdtId_throwsException() {
        validRequest.setCnvsIdtId("");
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            conversationHistoryService.getConversationHistory(validRequest);
        });
        assertEquals("대화 식별 아이디는 필수입니다.", thrown.getMessage());
    }
}