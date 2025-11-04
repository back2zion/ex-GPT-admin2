package com.datastreams.gpt.file.dto;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "파일 업로드 이력 생성 요청 DTO")
public class FileUploadHistoryCreateRequestDto {

    @Schema(description = "사용자 아이디", example = "user123", required = true)
    private String usrId;

    @Schema(description = "대화 식별 아이디", example = "user123_20231026103000")
    private String cnvsIdtId;

    @Schema(description = "세션 아이디", example = "session_abc123", required = true)
    private String sesnId;

    @Schema(description = "파일명", example = "document.pdf", required = true)
    private String fileNm;

    @Schema(description = "메뉴 식별 아이디", example = "MENU001", required = true)
    private String menuIdtId;

    // Getters and Setters
    public String getUsrId() {
        return usrId;
    }

    public void setUsrId(String usrId) {
        this.usrId = usrId;
    }

    public String getCnvsIdtId() {
        return cnvsIdtId;
    }

    public void setCnvsIdtId(String cnvsIdtId) {
        this.cnvsIdtId = cnvsIdtId;
    }

    public String getSesnId() {
        return sesnId;
    }

    public void setSesnId(String sesnId) {
        this.sesnId = sesnId;
    }

    public String getFileNm() {
        return fileNm;
    }

    public void setFileNm(String fileNm) {
        this.fileNm = fileNm;
    }

    public String getMenuIdtId() {
        return menuIdtId;
    }

    public void setMenuIdtId(String menuIdtId) {
        this.menuIdtId = menuIdtId;
    }
}
