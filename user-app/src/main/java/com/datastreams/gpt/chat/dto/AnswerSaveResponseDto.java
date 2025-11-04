package com.datastreams.gpt.chat.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "L-034: 답변 저장 응답 DTO")
public class AnswerSaveResponseDto {

    @Schema(description = "트랜잭션 명", example = "UPD_USR_CNVS")
    @JsonProperty("TXN_NM")
    private String txnNm;

    @Schema(description = "처리 건수", example = "1")
    @JsonProperty("CNT")
    private Integer cnt;

    // Getters and Setters
    public String getTxnNm() {
        return txnNm;
    }

    public void setTxnNm(String txnNm) {
        this.txnNm = txnNm;
    }

    public Integer getCnt() {
        return cnt;
    }

    public void setCnt(Integer cnt) {
        this.cnt = cnt;
    }
}
