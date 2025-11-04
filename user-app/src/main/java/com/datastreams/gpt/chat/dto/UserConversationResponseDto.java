package com.datastreams.gpt.chat.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;

/**
 * L-028: 사용자 대화 조회 응답 DTO
 */
public class UserConversationResponseDto {
    
    @JsonProperty("cnvs_id")
    @Schema(description = "대화 아이디", example = "CNVS_001")
    private String cnvsId;
    
    @JsonProperty("ques_txt")
    @Schema(description = "질의 텍스트", example = "안녕하세요! 오늘 날씨는 어때요?")
    private String quesTxt;
    
    @JsonProperty("ans_txt")
    @Schema(description = "답변 텍스트", example = "안녕하세요! 현재 실시간 날씨 정보는 제공할 수 없습니다...")
    private String ansTxt;
    
    @JsonProperty("reg_ymd")
    @Schema(description = "등록 일시 (YYYY-MM-DD HH24:MI:SS)", example = "2025-10-16 14:01:23")
    private String regYmd;
    
    // 기본 생성자
    public UserConversationResponseDto() {}
    
    // 전체 생성자
    public UserConversationResponseDto(String cnvsId, String quesTxt, String ansTxt, String regYmd) {
        this.cnvsId = cnvsId;
        this.quesTxt = quesTxt;
        this.ansTxt = ansTxt;
        this.regYmd = regYmd;
    }
    
    // Getter and Setter
    public String getCnvsId() {
        return cnvsId;
    }
    
    public void setCnvsId(String cnvsId) {
        this.cnvsId = cnvsId;
    }
    
    public String getQuesTxt() {
        return quesTxt;
    }
    
    public void setQuesTxt(String quesTxt) {
        this.quesTxt = quesTxt;
    }
    
    public String getAnsTxt() {
        return ansTxt;
    }
    
    public void setAnsTxt(String ansTxt) {
        this.ansTxt = ansTxt;
    }
    
    public String getRegYmd() {
        return regYmd;
    }
    
    public void setRegYmd(String regYmd) {
        this.regYmd = regYmd;
    }
    
    @Override
    public String toString() {
        return "UserConversationResponseDto{" +
                "cnvsId='" + cnvsId + '\'' +
                ", quesTxt='" + quesTxt + '\'' +
                ", ansTxt='" + ansTxt + '\'' +
                ", regYmd='" + regYmd + '\'' +
                '}';
    }
}
