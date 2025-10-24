package com.datastreams.gpt.chat.service;

import com.datastreams.gpt.chat.dto.AnswerSaveRequestDto;
import com.datastreams.gpt.chat.dto.AnswerSaveResponseDto;
import com.datastreams.gpt.chat.dto.ReferenceDocumentDto;
import com.datastreams.gpt.chat.dto.AdditionalQuestionDto;
import com.datastreams.gpt.chat.mapper.AnswerSaveMapper;
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
class AnswerSaveServiceTest {

    @Mock
    private AnswerSaveMapper answerSaveMapper;

    @InjectMocks
    private AnswerSaveService answerSaveService;

    private AnswerSaveRequestDto validRequest;
    private List<AnswerSaveResponseDto> mockResponseList;

    @BeforeEach
    void setUp() {
        validRequest = new AnswerSaveRequestDto();
        validRequest.setCnvsIdtId("testuser_20251016100000000");
        validRequest.setCnvsId(12345L);
        validRequest.setQuesSmryTxt("질의 요약");
        validRequest.setInfrTxt("추론 텍스트");
        validRequest.setAnsTxt("답변 텍스트");
        validRequest.setAnsSmryTxt("답변 요약");
        validRequest.setQuesCatCd(1L);
        validRequest.setQroutTypCd("GENERAL");
        validRequest.setDocCatSysCd("TECHNICAL");
        validRequest.setSrchTimMs(1234L);
        validRequest.setRspTimMs(98765L);
        validRequest.setTknUseCnt(3456);
        validRequest.setUsrId("testuser");
        validRequest.setAnsAbrtYn("N");

        // 참조 문서 목록
        ReferenceDocumentDto refDoc1 = new ReferenceDocumentDto();
        refDoc1.setRefSeq(1L);
        refDoc1.setDocTypCd("N");
        refDoc1.setAttDocNm("document1.pdf");
        refDoc1.setAttDocId("doc_123");
        refDoc1.setFileUid("file_uuid_123");
        refDoc1.setFileDownUrl("https://example.com/download/file_uuid_123");
        refDoc1.setDocChnkNm("Section 1");
        refDoc1.setDocChnkTxt("문서 내용 1");
        refDoc1.setSmltRte(99.25);

        validRequest.setRefDocList(Arrays.asList(refDoc1));

        // 추가 질의 목록
        AdditionalQuestionDto addQues1 = new AdditionalQuestionDto();
        addQues1.setAddQuesSeq(1L);
        addQues1.setAddQuesTxt("관련 질문 1");
        addQues1.setRagClsCd("PUBLIC");

        validRequest.setAddQuesList(Arrays.asList(addQues1));

        // 응답 목록
        AnswerSaveResponseDto response1 = new AnswerSaveResponseDto();
        response1.setTxnNm("UPD_USR_CNVS");
        response1.setCnt(1);

        AnswerSaveResponseDto response2 = new AnswerSaveResponseDto();
        response2.setTxnNm("INS_USR_CNVS_REF_DOC_LST");
        response2.setCnt(1);

        AnswerSaveResponseDto response3 = new AnswerSaveResponseDto();
        response3.setTxnNm("INS_USR_CNVS_ADD_QUES_LST");
        response3.setCnt(1);

        mockResponseList = Arrays.asList(response1, response2, response3);
    }

    @Test
    @DisplayName("답변 저장 성공")
    void saveAnswer_success() throws Exception {
        when(answerSaveMapper.insertAnswerSave(any(AnswerSaveRequestDto.class))).thenReturn(mockResponseList);

        List<AnswerSaveResponseDto> result = answerSaveService.saveAnswer(validRequest);

        assertNotNull(result);
        assertEquals(3, result.size());
        assertEquals("UPD_USR_CNVS", result.get(0).getTxnNm());
        assertEquals(1, result.get(0).getCnt());
        assertEquals("INS_USR_CNVS_REF_DOC_LST", result.get(1).getTxnNm());
        assertEquals(1, result.get(1).getCnt());
        assertEquals("INS_USR_CNVS_ADD_QUES_LST", result.get(2).getTxnNm());
        assertEquals(1, result.get(2).getCnt());
    }

    @Test
    @DisplayName("답변 저장 실패 - 필수 파라미터 누락 (대화 식별 아이디)")
    void saveAnswer_missingCnvsIdtId_throwsException() {
        validRequest.setCnvsIdtId(null);
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            answerSaveService.saveAnswer(validRequest);
        });
        assertEquals("대화 식별 아이디는 필수입니다.", thrown.getMessage());
    }

    @Test
    @DisplayName("답변 저장 실패 - 필수 파라미터 누락 (답변 텍스트)")
    void saveAnswer_missingAnsTxt_throwsException() {
        validRequest.setAnsTxt(null);
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            answerSaveService.saveAnswer(validRequest);
        });
        assertEquals("답변 텍스트는 필수입니다.", thrown.getMessage());
    }

    @Test
    @DisplayName("답변 저장 실패 - 잘못된 답변 중지 여부")
    void saveAnswer_invalidAnsAbrtYn_throwsException() {
        validRequest.setAnsAbrtYn("X");
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            answerSaveService.saveAnswer(validRequest);
        });
        assertEquals("답변 중지 여부는 Y 또는 N이어야 합니다.", thrown.getMessage());
    }

    @Test
    @DisplayName("답변 저장 실패 - 빈 참조 문서 목록")
    void saveAnswer_emptyRefDocList_throwsException() {
        validRequest.setRefDocList(Arrays.asList());
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            answerSaveService.saveAnswer(validRequest);
        });
        assertEquals("참조 문서 목록은 필수입니다.", thrown.getMessage());
    }

    @Test
    @DisplayName("답변 저장 실패 - 빈 추가 질의 목록")
    void saveAnswer_emptyAddQuesList_throwsException() {
        validRequest.setAddQuesList(Arrays.asList());
        IllegalArgumentException thrown = assertThrows(IllegalArgumentException.class, () -> {
            answerSaveService.saveAnswer(validRequest);
        });
        assertEquals("추가 질의 목록은 필수입니다.", thrown.getMessage());
    }
}
