package com.datastreams.gpt.conversation.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * L-025: 대화 대표 명 변경 요청 DTO
 * 대화 대표 명 및 사용 여부를 업데이트하기 위한 요청 데이터
 */
public class ConversationNameUpdateRequestDto {
    
    @JsonProperty("cnvs_idt_id")
    private String cnvsIdtId;
    
    @JsonProperty("rep_cnvs_nm")
    private String repCnvsNm;
    
    @JsonProperty("use_yn")
    private String useYn;
    
    // 기본 생성자
    public ConversationNameUpdateRequestDto() {}
    
    // 생성자
    public ConversationNameUpdateRequestDto(String cnvsIdtId, String repCnvsNm, String useYn) {
        this.cnvsIdtId = cnvsIdtId;
        this.repCnvsNm = repCnvsNm;
        this.useYn = useYn;
    }
    
    // Getters and Setters
    public String getCnvsIdtId() {
        return cnvsIdtId;
    }
    
    public void setCnvsIdtId(String cnvsIdtId) {
        this.cnvsIdtId = cnvsIdtId;
    }
    
    public String getRepCnvsNm() {
        return repCnvsNm;
    }
    
    public void setRepCnvsNm(String repCnvsNm) {
        this.repCnvsNm = repCnvsNm;
    }
    
    public String getUseYn() {
        return useYn;
    }
    
    public void setUseYn(String useYn) {
        this.useYn = useYn;
    }
    
    @Override
    public String toString() {
        return "ConversationNameUpdateRequestDto{" +
                "cnvsIdtId='" + cnvsIdtId + '\'' +
                ", repCnvsNm='" + repCnvsNm + '\'' +
                ", useYn='" + useYn + '\'' +
                '}';
    }
}
