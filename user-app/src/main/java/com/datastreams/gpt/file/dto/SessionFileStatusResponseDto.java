package com.datastreams.gpt.file.dto;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "세션 파일 상태 조회 응답 DTO")
public class SessionFileStatusResponseDto {

    @Schema(description = "파일 아이디", example = "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34")
    private String fileUid;

    @Schema(description = "파일 처리 상태", example = "ready", allowableValues = {"uploaded", "parsed", "processed", "ready", "error"})
    private String status;

    @Schema(description = "오류 메시지 (상태가 error인 경우)", example = "파일 파싱 실패")
    private String error;

    @Schema(description = "다음 단계 작업", example = "process", allowableValues = {"parse", "process"})
    private String nextStep;

    @Schema(description = "파일명", example = "document.pdf")
    private String fileName;

    @Schema(description = "파일 크기 (bytes)", example = "1024000")
    private Long fileSize;

    @Schema(description = "처리 진행률 (%)", example = "100")
    private Integer progress;

    @Schema(description = "상태 조회 시간", example = "2025-10-17T14:30:00Z")
    private String checkedAt;

    // Getters and Setters
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

    public String getError() {
        return error;
    }

    public void setError(String error) {
        this.error = error;
    }

    public String getNextStep() {
        return nextStep;
    }

    public void setNextStep(String nextStep) {
        this.nextStep = nextStep;
    }

    public String getFileName() {
        return fileName;
    }

    public void setFileName(String fileName) {
        this.fileName = fileName;
    }

    public Long getFileSize() {
        return fileSize;
    }

    public void setFileSize(Long fileSize) {
        this.fileSize = fileSize;
    }

    public Integer getProgress() {
        return progress;
    }

    public void setProgress(Integer progress) {
        this.progress = progress;
    }

    public String getCheckedAt() {
        return checkedAt;
    }

    public void setCheckedAt(String checkedAt) {
        this.checkedAt = checkedAt;
    }
}
