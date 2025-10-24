package com.datastreams.gpt.file.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;

/**
 * 파일 업로드 이력 생성 요청 DTO
 * L-016 - 파일 업로드 이력 생성 (Insert)
 */
public class FileUploadHistoryRequestDto {
    
    @JsonProperty("usr_id")
    @Schema(description = "사용자 아이디", example = "21311729")
    private String usrId;
    
    @JsonProperty("cnvs_idt_id")
    @Schema(description = "대화 식별 아이디 (첫 업로드 시 빈 값)", example = "")
    private String cnvsIdtId;
    
    @JsonProperty("sesn_id")
    @Schema(description = "사용자 접속 세션 아이디", example = "SESN_001")
    private String sesnId;
    
    @JsonProperty("file_nm")
    @Schema(description = "파일명", example = "document.pdf")
    private String fileNm;
    
    @JsonProperty("menu_idt_id")
    @Schema(description = "메뉴 식별 아이디", example = "MENU_001")
    private String menuIdtId;
    
    // 기본 생성자
    public FileUploadHistoryRequestDto() {}
    
    // 전체 생성자
    public FileUploadHistoryRequestDto(String usrId, String cnvsIdtId, String sesnId, String fileNm, String menuIdtId) {
        this.usrId = usrId;
        this.cnvsIdtId = cnvsIdtId;
        this.sesnId = sesnId;
        this.fileNm = fileNm;
        this.menuIdtId = menuIdtId;
    }
    
    // Getter and Setter
    public String getUsrId() {
        return usrId;
    }
    
    public void setUsrId(String usrId) {
        this.usrId = usrId;
    }
    
    public String getCnvsIdtId() {
        return cnvsIdtId;
    }
    
    public void setCnvsIdtId(String cnvsIdtId) {
        this.cnvsIdtId = cnvsIdtId;
    }
    
    public String getSesnId() {
        return sesnId;
    }
    
    public void setSesnId(String sesnId) {
        this.sesnId = sesnId;
    }
    
    public String getFileNm() {
        return fileNm;
    }
    
    public void setFileNm(String fileNm) {
        this.fileNm = fileNm;
    }
    
    public String getMenuIdtId() {
        return menuIdtId;
    }
    
    public void setMenuIdtId(String menuIdtId) {
        this.menuIdtId = menuIdtId;
    }
    
    @Override
    public String toString() {
        return "FileUploadHistoryRequestDto{" +
                "usrId='" + usrId + '\'' +
                ", cnvsIdtId='" + cnvsIdtId + '\'' +
                ", sesnId='" + sesnId + '\'' +
                ", fileNm='" + fileNm + '\'' +
                ", menuIdtId='" + menuIdtId + '\'' +
                '}';
    }
}
