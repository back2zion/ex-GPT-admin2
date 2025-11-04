package com.datastreams.gpt.chat.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;

/**
 * L-031: 사용자 대화 업로드 파일 조회 응답 DTO
 */
public class UploadFileResponseDto {
    
    @JsonProperty("file_upld_seq")
    @Schema(description = "파일 업로드 순번", example = "1")
    private Integer fileUpldSeq;
    
    @JsonProperty("file_nm")
    @Schema(description = "파일 명", example = "기술문서_001.pdf")
    private String fileNm;
    
    @JsonProperty("file_id")
    @Schema(description = "파일 아이디", example = "FILE_001")
    private String fileId;
    
    // 기본 생성자
    public UploadFileResponseDto() {}
    
    // 전체 생성자
    public UploadFileResponseDto(Integer fileUpldSeq, String fileNm, String fileId) {
        this.fileUpldSeq = fileUpldSeq;
        this.fileNm = fileNm;
        this.fileId = fileId;
    }
    
    // Getter and Setter
    public Integer getFileUpldSeq() {
        return fileUpldSeq;
    }
    
    public void setFileUpldSeq(Integer fileUpldSeq) {
        this.fileUpldSeq = fileUpldSeq;
    }
    
    public String getFileNm() {
        return fileNm;
    }
    
    public void setFileNm(String fileNm) {
        this.fileNm = fileNm;
    }
    
    public String getFileId() {
        return fileId;
    }
    
    public void setFileId(String fileId) {
        this.fileId = fileId;
    }
    
    @Override
    public String toString() {
        return "UploadFileResponseDto{" +
                "fileUpldSeq=" + fileUpldSeq +
                ", fileNm='" + fileNm + '\'' +
                ", fileId='" + fileId + '\'' +
                '}';
    }
}
