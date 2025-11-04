package com.datastreams.gpt.file.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import org.springframework.web.multipart.MultipartFile;

@Schema(description = "세션 파일 업로드 요청 DTO")
public class SessionFileUploadRequestDto {

    @Schema(description = "대화 식별 아이디 (세션 ID)", example = "user123_20231026103000", required = true)
    private String cnvsIdtId;

    @Schema(description = "업로드할 파일", required = true)
    private MultipartFile file;

    @Schema(description = "사용자 아이디", example = "user123", required = true)
    private String userId;

    @Schema(description = "동기 처리 여부", example = "true", defaultValue = "true")
    private boolean wait = true;

    // Getters and Setters
    public String getCnvsIdtId() {
        return cnvsIdtId;
    }

    public void setCnvsIdtId(String cnvsIdtId) {
        this.cnvsIdtId = cnvsIdtId;
    }

    public MultipartFile getFile() {
        return file;
    }

    public void setFile(MultipartFile file) {
        this.file = file;
    }

    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }

    public boolean isWait() {
        return wait;
    }

    public void setWait(boolean wait) {
        this.wait = wait;
    }
}
