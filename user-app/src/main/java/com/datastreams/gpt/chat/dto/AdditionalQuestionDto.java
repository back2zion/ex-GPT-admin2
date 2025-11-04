package com.datastreams.gpt.chat.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "추가 질의 DTO")
public class AdditionalQuestionDto {

    @Schema(description = "추가 질의 순번", example = "1", required = true)
    @JsonProperty("ADD_QUES_SEQ")
    private Long addQuesSeq;

    @Schema(description = "추가 질의 텍스트", example = "관련 질문 1", required = true)
    @JsonProperty("ADD_QUES_TXT")
    private String addQuesTxt;

    @Schema(description = "RAG 구분 코드 (기본값 PUBLIC)", example = "PUBLIC", required = true)
    @JsonProperty("RAG_CLS_CD")
    private String ragClsCd;

    // Getters and Setters
    public Long getAddQuesSeq() {
        return addQuesSeq;
    }

    public void setAddQuesSeq(Long addQuesSeq) {
        this.addQuesSeq = addQuesSeq;
    }

    public String getAddQuesTxt() {
        return addQuesTxt;
    }

    public void setAddQuesTxt(String addQuesTxt) {
        this.addQuesTxt = addQuesTxt;
    }

    public String getRagClsCd() {
        return ragClsCd;
    }

    public void setRagClsCd(String ragClsCd) {
        this.ragClsCd = ragClsCd;
    }
}
