package com.datastreams.gpt.chat.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;

/**
 * L-028: 사용자 대화 조회 요청 DTO
 */
public class UserConversationRequestDto {
    
    @JsonProperty("cnvs_idt_id")
    @Schema(description = "대화 식별 아이디", example = "21311729_20251016140123", required = true)
    private String cnvsIdtId;
    
    // 기본 생성자
    public UserConversationRequestDto() {}
    
    // 전체 생성자
    public UserConversationRequestDto(String cnvsIdtId) {
        this.cnvsIdtId = cnvsIdtId;
    }
    
    // Getter and Setter
    public String getCnvsIdtId() {
        return cnvsIdtId;
    }
    
    public void setCnvsIdtId(String cnvsIdtId) {
        this.cnvsIdtId = cnvsIdtId;
    }
    
    @Override
    public String toString() {
        return "UserConversationRequestDto{" +
                "cnvsIdtId='" + cnvsIdtId + '\'' +
                '}';
    }
}
