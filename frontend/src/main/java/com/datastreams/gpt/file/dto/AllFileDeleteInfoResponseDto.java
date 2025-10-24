package com.datastreams.gpt.file.dto;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "L-021: 전체 파일 삭제 정보 갱신 응답 DTO")
public class AllFileDeleteInfoResponseDto {

    @Schema(description = "대화 식별 아이디", example = "USR_ID_20231026103000123456")
    private String cnvsIdtId;

    @Schema(description = "트랜잭션 명", example = "UPD_USR_UPLD_DOC_MNG")
    private String txnNm;

    @Schema(description = "실행 건수", example = "3")
    private Integer cnt;

    @Schema(description = "처리 상태", example = "success")
    private String status;

    @Schema(description = "처리 시간 (밀리초)", example = "1500")
    private Long processingTime;

    @Schema(description = "업데이트된 파일 개수", example = "3")
    private Integer updatedFileCount;

    @Schema(description = "성공 여부", example = "Y")
    private String sucYn;

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

    public Integer getUpdatedFileCount() {
        return updatedFileCount;
    }

    public void setUpdatedFileCount(Integer updatedFileCount) {
        this.updatedFileCount = updatedFileCount;
    }

    public String getSucYn() {
        return sucYn;
    }

    public void setSucYn(String sucYn) {
        this.sucYn = sucYn;
    }

    @Override
    public String toString() {
        return "AllFileDeleteInfoResponseDto{" +
                "cnvsIdtId='" + cnvsIdtId + '\'' +
                ", txnNm='" + txnNm + '\'' +
                ", cnt=" + cnt +
                ", status='" + status + '\'' +
                ", processingTime=" + processingTime +
                ", updatedFileCount=" + updatedFileCount +
                ", sucYn='" + sucYn + '\'' +
                '}';
    }
}
