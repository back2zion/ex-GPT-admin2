package com.datastreams.gpt.chat.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;

/**
 * L-030: 사용자 대화 추가 질의 조회 요청 DTO
 */
public class AdditionalQuestionRequestDto {
    
    @JsonProperty("cnvs_id")
    @Schema(description = "대화 아이디", example = "1", required = true)
    private String cnvsId;
    
    @JsonProperty("usr_id")
    @Schema(description = "사용자 아이디", example = "21311729", required = true)
    private String usrId;
    
    // 기본 생성자
    public AdditionalQuestionRequestDto() {}
    
    // 전체 생성자
    public AdditionalQuestionRequestDto(String cnvsId, String usrId) {
        this.cnvsId = cnvsId;
        this.usrId = usrId;
    }
    
    // Getter and Setter
    public String getCnvsId() {
        return cnvsId;
    }
    
    public void setCnvsId(String cnvsId) {
        this.cnvsId = cnvsId;
    }
    
    public String getUsrId() {
        return usrId;
    }
    
    public void setUsrId(String usrId) {
        this.usrId = usrId;
    }
    
    @Override
    public String toString() {
        return "AdditionalQuestionRequestDto{" +
                "cnvsId='" + cnvsId + '\'' +
                ", usrId='" + usrId + '\'' +
                '}';
    }
}
