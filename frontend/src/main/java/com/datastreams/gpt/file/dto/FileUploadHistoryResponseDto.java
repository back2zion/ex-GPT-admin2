package com.datastreams.gpt.file.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;

/**
 * 파일 업로드 이력 생성 응답 DTO
 * L-016 - 파일 업로드 이력 생성 (Insert)
 */
public class FileUploadHistoryResponseDto {
    
    @JsonProperty("txn_nm")
    @Schema(description = "트랜잭션 명", example = "INS_USR_UPLD_DOC_MNG,INS_USR_CNVS")
    private String txnNm;
    
    @JsonProperty("cnt")
    @Schema(description = "실행 건수", example = "2")
    private Integer cnt;
    
    @JsonProperty("file_upld_seq")
    @Schema(description = "파일 업로드 순번 (KEY 값)", example = "12345")
    private Long fileUpldSeq;
    
    @JsonProperty("cnvs_idt_id")
    @Schema(description = "대화 식별 아이디", example = "21311729_20251016140123")
    private String cnvsIdtId;
    
    // 기본 생성자
    public FileUploadHistoryResponseDto() {}
    
    // 전체 생성자
    public FileUploadHistoryResponseDto(String txnNm, Integer cnt, Long fileUpldSeq, String cnvsIdtId) {
        this.txnNm = txnNm;
        this.cnt = cnt;
        this.fileUpldSeq = fileUpldSeq;
        this.cnvsIdtId = cnvsIdtId;
    }
    
    // Getter and Setter
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
    
    public String getCnvsIdtId() {
        return cnvsIdtId;
    }
    
    public void setCnvsIdtId(String cnvsIdtId) {
        this.cnvsIdtId = cnvsIdtId;
    }
    
    @Override
    public String toString() {
        return "FileUploadHistoryResponseDto{" +
                "txnNm='" + txnNm + '\'' +
                ", cnt=" + cnt +
                ", fileUpldSeq=" + fileUpldSeq +
                ", cnvsIdtId='" + cnvsIdtId + '\'' +
                '}';
    }
}
