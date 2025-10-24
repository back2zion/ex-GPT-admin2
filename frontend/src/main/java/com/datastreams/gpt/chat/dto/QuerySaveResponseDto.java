package com.datastreams.gpt.chat.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "L-033: 질의 저장 응답 DTO")
public class QuerySaveResponseDto {

    @Schema(description = "트랜잭션 명", example = "INS_USR_CNVS")
    @JsonProperty("TXN_NM")
    private String txnNm;

    @Schema(description = "대화 식별 아이디 (INSERT 후 반환되는 값)", example = "testuser_20251016100000000")
    @JsonProperty("CNVS_IDT_ID")
    private String cnvsIdtId;

    @Schema(description = "대화 아이디 (INSERT 후 반환되는 값)", example = "12345")
    @JsonProperty("CNVS_ID")
    private Long cnvsId;

    // Getters and Setters
    public String getTxnNm() {
        return txnNm;
    }

    public void setTxnNm(String txnNm) {
        this.txnNm = txnNm;
    }

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
}
