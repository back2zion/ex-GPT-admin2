package com.datastreams.gpt.chat.dto;

/**
 * L-027~L-031: 대화 관련 조회 응답 DTO
 */
public class ConversationListResponseDto {
    
    private String cnvsIdtId;      // 대화 식별 아이디
    private String cnvsSmryTxt;    // 대화 요약 텍스트
    private String regDt;          // 등록일시
    private String usrId;          // 사용자 아이디
    
    // 기본 생성자
    public ConversationListResponseDto() {}
    
    // 전체 생성자
    public ConversationListResponseDto(String cnvsIdtId, String cnvsSmryTxt, String regDt, String usrId) {
        this.cnvsIdtId = cnvsIdtId;
        this.cnvsSmryTxt = cnvsSmryTxt;
        this.regDt = regDt;
        this.usrId = usrId;
    }
    
    // Getter/Setter
    public String getCnvsIdtId() {
        return cnvsIdtId;
    }
    
    public void setCnvsIdtId(String cnvsIdtId) {
        this.cnvsIdtId = cnvsIdtId;
    }
    
    
    public String getCnvsSmryTxt() {
        return cnvsSmryTxt;
    }
    
    public void setCnvsSmryTxt(String cnvsSmryTxt) {
        this.cnvsSmryTxt = cnvsSmryTxt;
    }
    
    public String getRegDt() {
        return regDt;
    }
    
    public void setRegDt(String regDt) {
        this.regDt = regDt;
    }
    
    public String getUsrId() {
        return usrId;
    }
    
    public void setUsrId(String usrId) {
        this.usrId = usrId;
    }
}