package com.datastreams.gpt.chat.dto;

/**
 * L-041: 이전 대화 이력 조회 응답 DTO
 */
public class ConversationHistoryResponseDto {
    
    private Integer rowSeq;     // 순번
    private String quesTxt;     // 질의 텍스트
    private String ansTxt;      // 답변 텍스트
    
    // 기본 생성자
    public ConversationHistoryResponseDto() {}
    
    // 전체 생성자
    public ConversationHistoryResponseDto(Integer rowSeq, String quesTxt, String ansTxt) {
        this.rowSeq = rowSeq;
        this.quesTxt = quesTxt;
        this.ansTxt = ansTxt;
    }
    
    // Getter/Setter
    public Integer getRowSeq() {
        return rowSeq;
    }
    
    public void setRowSeq(Integer rowSeq) {
        this.rowSeq = rowSeq;
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
}