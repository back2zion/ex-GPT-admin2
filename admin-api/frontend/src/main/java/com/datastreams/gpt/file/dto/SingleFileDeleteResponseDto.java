package com.datastreams.gpt.file.dto;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "단일 파일 삭제 응답 DTO")
public class SingleFileDeleteResponseDto {

    @Schema(description = "대화 식별 아이디", example = "USR_ID_20231026103000123456")
    private String cnvsIdtId;

    @Schema(description = "파일 아이디", example = "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34")
    private String fileUid;

    @Schema(description = "삭제 상태", example = "success")
    private String status;

    @Schema(description = "삭제 시간", example = "2025-10-17T14:30:00Z")
    private String deletedAt;

    @Schema(description = "처리 시간 (밀리초)", example = "500")
    private Long processingTime;

    @Schema(description = "삭제된 파일 크기 (바이트)", example = "1024000")
    private Long fileSize;

    @Schema(description = "삭제된 파일명", example = "document.pdf")
    private String fileName;

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

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getDeletedAt() {
        return deletedAt;
    }

    public void setDeletedAt(String deletedAt) {
        this.deletedAt = deletedAt;
    }

    public Long getProcessingTime() {
        return processingTime;
    }

    public void setProcessingTime(Long processingTime) {
        this.processingTime = processingTime;
    }

    public Long getFileSize() {
        return fileSize;
    }

    public void setFileSize(Long fileSize) {
        this.fileSize = fileSize;
    }

    public String getFileName() {
        return fileName;
    }

    public void setFileName(String fileName) {
        this.fileName = fileName;
    }
}
