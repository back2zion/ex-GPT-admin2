package com.datastreams.gpt.chat.dto;

/**
 * L-027~L-031: 대화 관련 조회 요청 DTO
 */
public class ConversationListRequestDto {
    
    private String usrId;      // 사용자 아이디
    
    // 기본 생성자
    public ConversationListRequestDto() {}
    
    // 생성자
    public ConversationListRequestDto(String usrId) {
        this.usrId = usrId;
    }
    
    // Getter/Setter
    public String getUsrId() {
        return usrId;
    }
    
    public void setUsrId(String usrId) {
        this.usrId = usrId;
    }
    
    @Override
    public String toString() {
        return "ConversationListRequestDto{" +
                "usrId='" + usrId + '\'' +
                '}';
    }
}