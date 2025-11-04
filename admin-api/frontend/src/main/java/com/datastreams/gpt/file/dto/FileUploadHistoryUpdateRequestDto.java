package com.datastreams.gpt.file.dto;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "파일 업로드 이력 갱신 요청 DTO")
public class FileUploadHistoryUpdateRequestDto {

    @Schema(description = "파일 업로드 순번", example = "1", required = true)
    private Long fileUpldSeq;

    @Schema(description = "파일 아이디 (FastAPI에서 반환받은 FILE_UID)", example = "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34", required = true)
    private String fileUid;

    @Schema(description = "로그 내용 (L-017 Session File Upload 결과 상태)", example = "ready", required = true)
    private String logCont;

    // Getters and Setters
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

    public String getLogCont() {
        return logCont;
    }

    public void setLogCont(String logCont) {
        this.logCont = logCont;
    }
}
