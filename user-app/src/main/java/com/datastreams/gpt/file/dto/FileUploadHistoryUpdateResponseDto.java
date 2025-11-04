package com.datastreams.gpt.file.dto;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "파일 업로드 이력 갱신 응답 DTO")
public class FileUploadHistoryUpdateResponseDto {

    @Schema(description = "트랜잭션 명", example = "UPD_USR_UPLD_DOC_MNG")
    private String txnNm;

    @Schema(description = "실행 건수", example = "1")
    private Integer cnt;

    @Schema(description = "파일 업로드 순번", example = "1")
    private Long fileUpldSeq;

    @Schema(description = "파일 아이디", example = "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34")
    private String fileUid;

    @Schema(description = "갱신 시간", example = "2025-10-17T14:30:00Z")
    private String updatedAt;

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

    public Long getFileUpldSeq() {
        return fileUpldSeq;
    }

    public void setFileUpldSeq(Long fileUpldSeq) {
        this.fileUpldSeq = fileUpldSeq;
    }

    public String getFileUid() {
        return fileUid;
    }

    public void setFileUid(String fileUid) {
        this.fileUid = fileUid;
    }

    public String getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(String updatedAt) {
        this.updatedAt = updatedAt;
    }
}
