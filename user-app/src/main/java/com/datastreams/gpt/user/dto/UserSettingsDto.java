package com.datastreams.gpt.user.dto;

import io.swagger.v3.oas.annotations.media.Schema;

/**
 * 사용자 설정 정보 DTO
 */
@Schema(description = "사용자 개인 설정 정보")
public class UserSettingsDto {

    @Schema(description = "UI 테마 코드 (light/dark)", example = "light")
    private String uiThmCd;

    @Schema(description = "폰트 크기 코드 (small/medium/large)", example = "medium")
    private String fntSizeCd;

    @Schema(description = "시스템 접근 허용 여부", example = "Y")
    private String systemAccessYn;

    @Schema(description = "관리자 권한 여부", example = "N")
    private String managerAuthYn;

    @Schema(description = "음성 모델 사용 여부", example = "Y")
    private String voiceModelUseYn;

    @Schema(description = "이미지 모델 사용 여부", example = "Y")
    private String imageModelUseYn;

    // Getter and Setter methods
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

    public String getSystemAccessYn() {
        return systemAccessYn;
    }

    public void setSystemAccessYn(String systemAccessYn) {
        this.systemAccessYn = systemAccessYn;
    }

    public String getManagerAuthYn() {
        return managerAuthYn;
    }

    public void setManagerAuthYn(String managerAuthYn) {
        this.managerAuthYn = managerAuthYn;
    }

    public String getVoiceModelUseYn() {
        return voiceModelUseYn;
    }

    public void setVoiceModelUseYn(String voiceModelUseYn) {
        this.voiceModelUseYn = voiceModelUseYn;
    }

    public String getImageModelUseYn() {
        return imageModelUseYn;
    }

    public void setImageModelUseYn(String imageModelUseYn) {
        this.imageModelUseYn = imageModelUseYn;
    }
}
