package com.datastreams.gpt.file.dto;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "세션 파일 삭제 요청 DTO")
public class SessionFileDeleteRequestDto {

    @Schema(description = "대화 식별 아이디", example = "USR_ID_20231026103000123456", required = true)
    private String cnvsIdtId;

    // Getters and Setters
    public String getCnvsIdtId() {
        return cnvsIdtId;
    }

    public void setCnvsIdtId(String cnvsIdtId) {
        this.cnvsIdtId = cnvsIdtId;
    }
}
