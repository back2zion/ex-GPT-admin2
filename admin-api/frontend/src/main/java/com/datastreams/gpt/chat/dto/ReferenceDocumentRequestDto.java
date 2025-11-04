package com.datastreams.gpt.chat.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;

/**
 * L-029: 사용자 대화 참조 문서 조회 및 문서별 다운로드 권한 조회 요청 DTO
 */
public class ReferenceDocumentRequestDto {
    
    @JsonProperty("cnvs_id")
    @Schema(description = "대화 아이디", example = "1", required = true)
    private String cnvsId;
    
    @JsonProperty("usr_id")
    @Schema(description = "사용자 아이디", example = "21311729", required = true)
    private String usrId;
    
    // 기본 생성자
    public ReferenceDocumentRequestDto() {}
    
    // 전체 생성자
    public ReferenceDocumentRequestDto(String cnvsId, String usrId) {
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
        return "ReferenceDocumentRequestDto{" +
                "cnvsId='" + cnvsId + '\'' +
                ", usrId='" + usrId + '\'' +
                '}';
    }
}
