package com.datastreams.gpt.chat.controller;

import com.datastreams.gpt.chat.dto.AnswerSaveRequestDto;
import com.datastreams.gpt.chat.dto.AnswerSaveResponseDto;
import com.datastreams.gpt.chat.dto.ReferenceDocumentDto;
import com.datastreams.gpt.chat.dto.AdditionalQuestionDto;
import com.datastreams.gpt.chat.service.AnswerSaveService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Arrays;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(AnswerSaveController.class)
class AnswerSaveControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private AnswerSaveService answerSaveService;

    @Autowired
    private ObjectMapper objectMapper;

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
    @DisplayName("L-034: 답변 저장 성공")
    void saveAnswer_success() throws Exception {
        when(answerSaveService.saveAnswer(any(AnswerSaveRequestDto.class))).thenReturn(mockResponseList);

        mockMvc.perform(post("/api/chat/answer/save")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].TXN_NM").value("UPD_USR_CNVS"))
                .andExpect(jsonPath("$[0].CNT").value(1))
                .andExpect(jsonPath("$[1].TXN_NM").value("INS_USR_CNVS_REF_DOC_LST"))
                .andExpect(jsonPath("$[1].CNT").value(1))
                .andExpect(jsonPath("$[2].TXN_NM").value("INS_USR_CNVS_ADD_QUES_LST"))
                .andExpect(jsonPath("$[2].CNT").value(1));
    }

    @Test
    @DisplayName("L-034: 답변 저장 실패 - 필수 파라미터 누락")
    void saveAnswer_missingRequiredParam_returnsBadRequest() throws Exception {
        validRequest.setCnvsIdtId(null); // 대화 식별 아이디 누락

        when(answerSaveService.saveAnswer(any(AnswerSaveRequestDto.class)))
                .thenThrow(new IllegalArgumentException("대화 식별 아이디는 필수입니다."));

        mockMvc.perform(post("/api/chat/answer/save")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").value("대화 식별 아이디는 필수입니다."));
    }

    @Test
    @DisplayName("L-034: 답변 저장 실패 - 내부 서버 오류")
    void saveAnswer_internalServerError_returnsInternalServerError() throws Exception {
        when(answerSaveService.saveAnswer(any(AnswerSaveRequestDto.class)))
                .thenThrow(new RuntimeException("데이터베이스 오류"));

        mockMvc.perform(post("/api/chat/answer/save")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.error").value("답변 저장 중 오류가 발생했습니다."));
    }
}
