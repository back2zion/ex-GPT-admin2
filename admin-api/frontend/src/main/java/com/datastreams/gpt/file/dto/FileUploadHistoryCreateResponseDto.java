package com.datastreams.gpt.file.dto;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "파일 업로드 이력 생성 응답 DTO")
public class FileUploadHistoryCreateResponseDto {

    @Schema(description = "트랜잭션 명", example = "INS_USR_UPLD_DOC_MNG,INS_USR_CNVS")
    private String txnNm;

    @Schema(description = "실행 건수", example = "2")
    private int cnt;

    @Schema(description = "대화 식별 아이디", example = "user123_20231026103000")
    private String cnvsIdtId;

    @Schema(description = "파일 업로드 순번", example = "12345")
    private Long fileUpldSeq;

    // Getters and Setters
    public String getTxnNm() {
        return txnNm;
    }

    public void setTxnNm(String txnNm) {
        this.txnNm = txnNm;
    }

    public int getCnt() {
        return cnt;
    }

    public void setCnt(int cnt) {
        this.cnt = cnt;
    }

    public String getCnvsIdtId() {
        return cnvsIdtId;
    }

    public void setCnvsIdtId(String cnvsIdtId) {
        this.cnvsIdtId = cnvsIdtId;
    }

    public Long getFileUpldSeq() {
        return fileUpldSeq;
    }

    public void setFileUpldSeq(Long fileUpldSeq) {
        this.fileUpldSeq = fileUpldSeq;
    }
}
