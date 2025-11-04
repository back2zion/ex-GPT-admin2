package com.datastreams.gpt.file.dto;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "세션 파일 삭제 응답 DTO")
public class SessionFileDeleteResponseDto {

    @Schema(description = "대화 식별 아이디", example = "USR_ID_20231026103000123456")
    private String cnvsIdtId;

    @Schema(description = "삭제 상태", example = "success")
    private String status;

    @Schema(description = "삭제된 파일 개수", example = "3")
    private Integer deletedFileCount;

    @Schema(description = "삭제된 파일 목록", example = "[\"tmp-123\", \"tmp-456\", \"tmp-789\"]")
    private String[] deletedFiles;

    @Schema(description = "삭제 시간", example = "2025-10-17T14:30:00Z")
    private String deletedAt;

    @Schema(description = "처리 시간 (밀리초)", example = "1500")
    private Long processingTime;

    // Getters and Setters
    public String getCnvsIdtId() {
        return cnvsIdtId;
    }

    public void setCnvsIdtId(String cnvsIdtId) {
        this.cnvsIdtId = cnvsIdtId;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public Integer getDeletedFileCount() {
        return deletedFileCount;
    }

    public void setDeletedFileCount(Integer deletedFileCount) {
        this.deletedFileCount = deletedFileCount;
    }

    public String[] getDeletedFiles() {
        return deletedFiles;
    }

    public void setDeletedFiles(String[] deletedFiles) {
        this.deletedFiles = deletedFiles;
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
}
