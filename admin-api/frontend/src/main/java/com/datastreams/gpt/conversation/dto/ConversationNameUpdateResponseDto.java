package com.datastreams.gpt.conversation.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * L-025: 대화 대표 명 변경 응답 DTO
 * 대화 대표 명 업데이트 결과 데이터
 */
public class ConversationNameUpdateResponseDto {
    
    @JsonProperty("cnvs_idt_id")
    private String cnvsIdtId;
    
    @JsonProperty("txn_nm")
    private String txnNm;
    
    @JsonProperty("cnt")
    private Integer cnt;
    
    @JsonProperty("status")
    private String status;
    
    @JsonProperty("processing_time")
    private Long processingTime;
    
    @JsonProperty("updated_rep_cnvs_nm")
    private String updatedRepCnvsNm;
    
    @JsonProperty("updated_use_yn")
    private String updatedUseYn;
    
    // 기본 생성자
    public ConversationNameUpdateResponseDto() {}
    
    // Getters and Setters
    public String getCnvsIdtId() {
        return cnvsIdtId;
    }
    
    public void setCnvsIdtId(String cnvsIdtId) {
        this.cnvsIdtId = cnvsIdtId;
    }
    
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
    
    public String getStatus() {
        return status;
    }
    
    public void setStatus(String status) {
        this.status = status;
    }
    
    public Long getProcessingTime() {
        return processingTime;
    }
    
    public void setProcessingTime(Long processingTime) {
        this.processingTime = processingTime;
    }
    
    public String getUpdatedRepCnvsNm() {
        return updatedRepCnvsNm;
    }
    
    public void setUpdatedRepCnvsNm(String updatedRepCnvsNm) {
        this.updatedRepCnvsNm = updatedRepCnvsNm;
    }
    
    public String getUpdatedUseYn() {
        return updatedUseYn;
    }
    
    public void setUpdatedUseYn(String updatedUseYn) {
        this.updatedUseYn = updatedUseYn;
    }
    
    @Override
    public String toString() {
        return "ConversationNameUpdateResponseDto{" +
                "cnvsIdtId='" + cnvsIdtId + '\'' +
                ", txnNm='" + txnNm + '\'' +
                ", cnt=" + cnt +
                ", status='" + status + '\'' +
                ", processingTime=" + processingTime +
                ", updatedRepCnvsNm='" + updatedRepCnvsNm + '\'' +
                ", updatedUseYn='" + updatedUseYn + '\'' +
                '}';
    }
}
