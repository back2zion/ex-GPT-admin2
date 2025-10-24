package com.datastreams.gpt.file.dto;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "세션 파일 업로드 응답 DTO")
public class SessionFileUploadResponseDto {

    @Schema(description = "대화 식별 아이디", example = "user123_20231026103000")
    private String cnvsIdtId;

    @Schema(description = "파일 아이디", example = "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34")
    private String fileUid;

    @Schema(description = "파일명", example = "document.pdf")
    private String fileName;

    @Schema(description = "파일 크기 (bytes)", example = "1024000")
    private long fileSize;

    @Schema(description = "업로드 상태", example = "completed")
    private String status;

    @Schema(description = "처리 시간 (ms)", example = "1500")
    private long processingTime;

    // Getters and Setters
    public String getCnvsIdtId() {
        return cnvsIdtId;
    }

    public void setCnvsIdtId(String cnvsIdtId) {
        this.cnvsIdtId = cnvsIdtId;
    }

    public String getFileUid() {
        return fileUid;
    }

    public void setFileUid(String fileUid) {
        this.fileUid = fileUid;
    }

    public String getFileName() {
        return fileName;
    }

    public void setFileName(String fileName) {
        this.fileName = fileName;
    }

    public long getFileSize() {
        return fileSize;
    }

    public void setFileSize(long fileSize) {
        this.fileSize = fileSize;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public long getProcessingTime() {
        return processingTime;
    }

    public void setProcessingTime(long processingTime) {
        this.processingTime = processingTime;
    }
}
