package com.datastreams.gpt.chat.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "L-033: 질의 저장 요청 DTO")
public class QuerySaveRequestDto {

    @Schema(description = "대화 식별 아이디 (최초 대화 시는 빈 값)", example = "")
    @JsonProperty("CNVS_IDT_ID")
    private String cnvsIdtId;

    @Schema(description = "질의 텍스트", example = "안녕하세요, 도움이 필요합니다.", required = true)
    @JsonProperty("QUES_TXT")
    private String quesTxt;

    @Schema(description = "세션 아이디", example = "SESN_123456", required = true)
    @JsonProperty("SESN_ID")
    private String sesnId;

    @Schema(description = "사용자 ID", example = "testuser", required = true)
    @JsonProperty("USR_ID")
    private String usrId;

    @Schema(description = "메뉴 식별 아이디", example = "MENU_001", required = true)
    @JsonProperty("MENU_IDT_ID")
    private String menuIdtId;

    @Schema(description = "추천 질의 여부 (Y: 추천질의, N: 일반질의)", example = "N", required = true)
    @JsonProperty("RCM_QUES_YN")
    private String rcmQuesYn;

    // Getters and Setters
    public String getCnvsIdtId() {
        return cnvsIdtId;
    }

    public void setCnvsIdtId(String cnvsIdtId) {
        this.cnvsIdtId = cnvsIdtId;
    }

    public String getQuesTxt() {
        return quesTxt;
    }

    public void setQuesTxt(String quesTxt) {
        this.quesTxt = quesTxt;
    }

    public String getSesnId() {
        return sesnId;
    }

    public void setSesnId(String sesnId) {
        this.sesnId = sesnId;
    }

    public String getUsrId() {
        return usrId;
    }

    public void setUsrId(String usrId) {
        this.usrId = usrId;
    }

    public String getMenuIdtId() {
        return menuIdtId;
    }

    public void setMenuIdtId(String menuIdtId) {
        this.menuIdtId = menuIdtId;
    }

    public String getRcmQuesYn() {
        return rcmQuesYn;
    }

    public void setRcmQuesYn(String rcmQuesYn) {
        this.rcmQuesYn = rcmQuesYn;
    }
}
