package com.datastreams.gpt.chat.dto;

/**
 * L-041: 이전 대화 이력 조회 요청 DTO
 */
public class ConversationHistoryRequestDto {
    
    private String cnvsIdtId;  // 대화 식별 아이디
    private Long cnvsId;       // 대화 아이디
    
    // 기본 생성자
    public ConversationHistoryRequestDto() {}
    
    // 전체 생성자
    public ConversationHistoryRequestDto(String cnvsIdtId, Long cnvsId) {
        this.cnvsIdtId = cnvsIdtId;
        this.cnvsId = cnvsId;
    }
    
    // Getter/Setter
    public String getCnvsIdtId() {
        return cnvsIdtId;
    }
    
    public void setCnvsIdtId(String cnvsIdtId) {
        this.cnvsIdtId = cnvsIdtId;
    }
    
    public Long getCnvsId() {
        return cnvsId;
    }
    
    public void setCnvsId(Long cnvsId) {
        this.cnvsId = cnvsId;
    }
}