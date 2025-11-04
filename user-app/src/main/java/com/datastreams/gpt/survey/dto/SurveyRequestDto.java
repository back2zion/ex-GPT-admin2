package com.datastreams.gpt.survey.dto;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "만족도 저장 요청 DTO")
public class SurveyRequestDto {

    @Schema(description = "사용자 아이디", example = "21311729", required = true)
    private String usrId;

    @Schema(description = "만족도 평가 내용", example = "매우 만족합니다. 빠른 응답과 정확한 답변에 감사합니다.")
    private String ractTxt;

    @Schema(description = "만족도 레벨 값 (1~5)", example = "5", required = true)
    private Integer ractLevelVal;

    @Schema(description = "세션 아이디", example = "A1B2C3D4E5F6")
    private String sesnId;

    // Getters and Setters
    public String getUsrId() {
        return usrId;
    }

    public void setUsrId(String usrId) {
        this.usrId = usrId;
    }

    public String getRactTxt() {
        return ractTxt;
    }

    public void setRactTxt(String ractTxt) {
        this.ractTxt = ractTxt;
    }

    public Integer getRactLevelVal() {
        return ractLevelVal;
    }

    public void setRactLevelVal(Integer ractLevelVal) {
        this.ractLevelVal = ractLevelVal;
    }

    public String getSesnId() {
        return sesnId;
    }

    public void setSesnId(String sesnId) {
        this.sesnId = sesnId;
    }
}
