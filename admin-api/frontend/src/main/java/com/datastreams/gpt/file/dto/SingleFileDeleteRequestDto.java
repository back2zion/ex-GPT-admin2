package com.datastreams.gpt.file.dto;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "단일 파일 삭제 요청 DTO")
public class SingleFileDeleteRequestDto {

    @Schema(description = "대화 식별 아이디", example = "USR_ID_20231026103000123456", required = true)
    private String cnvsIdtId;

    @Schema(description = "파일 아이디", example = "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34", required = true)
    private String fileUid;

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
}
