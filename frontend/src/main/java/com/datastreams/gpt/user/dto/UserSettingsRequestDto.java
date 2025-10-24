package com.datastreams.gpt.user.dto;

import io.swagger.v3.oas.annotations.media.Schema;

/**
 * 사용자 설정 저장 요청 DTO
 */
@Schema(description = "사용자 설정 저장 요청")
public class UserSettingsRequestDto {

    @Schema(description = "사용자 ID", example = "21311729", required = true)
    private String userId;

    @Schema(description = "UI 테마 코드 (light/dark)", example = "light")
    private String uiThmCd;

    @Schema(description = "폰트 크기 코드 (1-5)", example = "3")
    private String fntSizeCd;

    @Schema(description = "시스템 접근 허용 여부 (Y/N)", example = "Y")
    private String sysAccsYn;

    @Schema(description = "관리자 권한 여부 (Y/N)", example = "N")
    private String mgrAuthYn;

    @Schema(description = "음성 모델 사용 여부 (Y/N)", example = "Y")
    private String vceMdlUseYn;

    @Schema(description = "이미지 모델 사용 여부 (Y/N)", example = "Y")
    private String imgMdlUseYn;

    // Getter and Setter methods
    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }

    public String getUiThmCd() {
        return uiThmCd;
    }

    public void setUiThmCd(String uiThmCd) {
        this.uiThmCd = uiThmCd;
    }

    public String getFntSizeCd() {
        return fntSizeCd;
    }

    public void setFntSizeCd(String fntSizeCd) {
        this.fntSizeCd = fntSizeCd;
    }

    public String getSysAccsYn() {
        return sysAccsYn;
    }

    public void setSysAccsYn(String sysAccsYn) {
        this.sysAccsYn = sysAccsYn;
    }

    public String getMgrAuthYn() {
        return mgrAuthYn;
    }

    public void setMgrAuthYn(String mgrAuthYn) {
        this.mgrAuthYn = mgrAuthYn;
    }

    public String getVceMdlUseYn() {
        return vceMdlUseYn;
    }

    public void setVceMdlUseYn(String vceMdlUseYn) {
        this.vceMdlUseYn = vceMdlUseYn;
    }

    public String getImgMdlUseYn() {
        return imgMdlUseYn;
    }

    public void setImgMdlUseYn(String imgMdlUseYn) {
        this.imgMdlUseYn = imgMdlUseYn;
    }
}

