package com.datastreams.gpt.error.dto;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * L-023: 오류 보고/오류 선택지 목록 저장 응답 DTO
 * 오류 보고 저장 결과 데이터
 */
public class ErrorReportSaveResponseDto {
    
    @JsonProperty("cnvs_id")
    private String cnvsId;
    
    @JsonProperty("usr_id")
    private String usrId;
    
    @JsonProperty("txn_nm")
    private String txnNm;
    
    @JsonProperty("cnt")
    private Integer cnt;
    
    @JsonProperty("status")
    private String status;
    
    @JsonProperty("processing_time")
    private Long processingTime;
    
    @JsonProperty("saved_err_rpt_cd_list")
    private List<String> savedErrRptCdList;
    
    // 기본 생성자
    public ErrorReportSaveResponseDto() {}
    
    // Getters and Setters
    public String getCnvsId() {
        return cnvsId;
    }
    
    public void setCnvsId(String cnvsId) {
        this.cnvsId = cnvsId;
    }
    
    public String getUsrId() {
        return usrId;
    }
    
    public void setUsrId(String usrId) {
        this.usrId = usrId;
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
    
    public List<String> getSavedErrRptCdList() {
        return savedErrRptCdList;
    }
    
    public void setSavedErrRptCdList(List<String> savedErrRptCdList) {
        this.savedErrRptCdList = savedErrRptCdList;
    }
    
    @Override
    public String toString() {
        return "ErrorReportSaveResponseDto{" +
                "cnvsId='" + cnvsId + '\'' +
                ", usrId='" + usrId + '\'' +
                ", txnNm='" + txnNm + '\'' +
                ", cnt=" + cnt +
                ", status='" + status + '\'' +
                ", processingTime=" + processingTime +
                ", savedErrRptCdList=" + savedErrRptCdList +
                '}';
    }
}
