package com.datastreams.gpt.chat.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;

import java.util.List;

@Schema(description = "L-034: 답변 저장 요청 DTO")
public class AnswerSaveRequestDto {

    @Schema(description = "대화 식별 아이디 (룸 아이디)", example = "testuser_20251016100000000", required = true)
    @JsonProperty("CNVS_IDT_ID")
    private String cnvsIdtId;

    @Schema(description = "대화 아이디", example = "12345", required = true)
    @JsonProperty("CNVS_ID")
    private Long cnvsId;

    @Schema(description = "질의 요약 텍스트", example = "질의 요약")
    @JsonProperty("QUES_SMRY_TXT")
    private String quesSmryTxt;

    @Schema(description = "추론 텍스트 (think)", example = "사용자가 도움이 필요하다고 요청했습니다.", required = true)
    @JsonProperty("INFR_TXT")
    private String infrTxt;

    @Schema(description = "답변 텍스트", example = "안녕하세요! 무엇을 도와드릴까요?", required = true)
    @JsonProperty("ANS_TXT")
    private String ansTxt;

    @Schema(description = "답변 요약 텍스트", example = "인사 및 도움 제안")
    @JsonProperty("ANS_SMRY_TXT")
    private String ansSmryTxt;

    @Schema(description = "질문 분류 코드", example = "1")
    @JsonProperty("QUES_CAT_CD")
    private Long quesCatCd;

    @Schema(description = "쿼리라우팅 유형 코드", example = "GENERAL", required = true)
    @JsonProperty("QROUT_TYP_CD")
    private String qroutTypCd;

    @Schema(description = "문서 분류 체계 코드", example = "TECHNICAL", required = true)
    @JsonProperty("DOC_CAT_SYS_CD")
    private String docCatSysCd;

    @Schema(description = "검색 시간 밀리초", example = "1234", required = true)
    @JsonProperty("SRCH_TIM_MS")
    private Long srchTimMs;

    @Schema(description = "응답 시간 밀리초", example = "98765", required = true)
    @JsonProperty("RSP_TIM_MS")
    private Long rspTimMs;

    @Schema(description = "토큰 사용 개수", example = "3456", required = true)
    @JsonProperty("TKN_USE_CNT")
    private Integer tknUseCnt;

    @Schema(description = "로그인 사용자 아이디", example = "testuser", required = true)
    @JsonProperty("USR_ID")
    private String usrId;

    @Schema(description = "답변 중지 여부 (기본값 N)", example = "N", required = true)
    @JsonProperty("ANS_ABRT_YN")
    private String ansAbrtYn;

    @Schema(description = "참조 문서 목록", required = true)
    @JsonProperty("REF_DOC_LIST")
    private List<ReferenceDocumentDto> refDocList;

    @Schema(description = "추가 질의 목록", required = true)
    @JsonProperty("ADD_QUES_LIST")
    private List<AdditionalQuestionDto> addQuesList;

    // Getters and Setters
    public String getCnvsIdtId() {
        return cnvsIdtId;
    }

    public void setCnvsIdtId(String cnvsIdtId) {
        this.cnvsIdtId = cnvsIdtId;
    }

    public Long getCnvsId() {
        return cnvsId;
    }

    public void setCnvsId(Long cnvsId) {
        this.cnvsId = cnvsId;
    }

    public String getQuesSmryTxt() {
        return quesSmryTxt;
    }

    public void setQuesSmryTxt(String quesSmryTxt) {
        this.quesSmryTxt = quesSmryTxt;
    }

    public String getInfrTxt() {
        return infrTxt;
    }

    public void setInfrTxt(String infrTxt) {
        this.infrTxt = infrTxt;
    }

    public String getAnsTxt() {
        return ansTxt;
    }

    public void setAnsTxt(String ansTxt) {
        this.ansTxt = ansTxt;
    }

    public String getAnsSmryTxt() {
        return ansSmryTxt;
    }

    public void setAnsSmryTxt(String ansSmryTxt) {
        this.ansSmryTxt = ansSmryTxt;
    }

    public Long getQuesCatCd() {
        return quesCatCd;
    }

    public void setQuesCatCd(Long quesCatCd) {
        this.quesCatCd = quesCatCd;
    }

    public String getQroutTypCd() {
        return qroutTypCd;
    }

    public void setQroutTypCd(String qroutTypCd) {
        this.qroutTypCd = qroutTypCd;
    }

    public String getDocCatSysCd() {
        return docCatSysCd;
    }

    public void setDocCatSysCd(String docCatSysCd) {
        this.docCatSysCd = docCatSysCd;
    }

    public Long getSrchTimMs() {
        return srchTimMs;
    }

    public void setSrchTimMs(Long srchTimMs) {
        this.srchTimMs = srchTimMs;
    }

    public Long getRspTimMs() {
        return rspTimMs;
    }

    public void setRspTimMs(Long rspTimMs) {
        this.rspTimMs = rspTimMs;
    }

    public Integer getTknUseCnt() {
        return tknUseCnt;
    }

    public void setTknUseCnt(Integer tknUseCnt) {
        this.tknUseCnt = tknUseCnt;
    }

    public String getUsrId() {
        return usrId;
    }

    public void setUsrId(String usrId) {
        this.usrId = usrId;
    }

    public String getAnsAbrtYn() {
        return ansAbrtYn;
    }

    public void setAnsAbrtYn(String ansAbrtYn) {
        this.ansAbrtYn = ansAbrtYn;
    }

    public List<ReferenceDocumentDto> getRefDocList() {
        return refDocList;
    }

    public void setRefDocList(List<ReferenceDocumentDto> refDocList) {
        this.refDocList = refDocList;
    }

    public List<AdditionalQuestionDto> getAddQuesList() {
        return addQuesList;
    }

    public void setAddQuesList(List<AdditionalQuestionDto> addQuesList) {
        this.addQuesList = addQuesList;
    }
}
