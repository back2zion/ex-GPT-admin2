package com.datastreams.gpt.error.dto;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * L-023: 오류 보고/오류 선택지 목록 저장 요청 DTO
 * 오류 보고 및 선택된 오류 코드들을 저장하기 위한 요청 데이터
 */
public class ErrorReportSaveRequestDto {
    
    @JsonProperty("cnvs_id")
    private String cnvsId;
    
    @JsonProperty("usr_id")
    private String usrId;
    
    @JsonProperty("err_rpt_txt")
    private String errRptTxt;
    
    @JsonProperty("err_rpt_cd_list")
    private List<String> errRptCdList;
    
    // 기본 생성자
    public ErrorReportSaveRequestDto() {}
    
    // 생성자
    public ErrorReportSaveRequestDto(String cnvsId, String usrId, String errRptTxt, List<String> errRptCdList) {
        this.cnvsId = cnvsId;
        this.usrId = usrId;
        this.errRptTxt = errRptTxt;
        this.errRptCdList = errRptCdList;
    }
    
    // Getters and Setters
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
    
    public String getErrRptTxt() {
        return errRptTxt;
    }
    
    public void setErrRptTxt(String errRptTxt) {
        this.errRptTxt = errRptTxt;
    }
    
    public List<String> getErrRptCdList() {
        return errRptCdList;
    }
    
    public void setErrRptCdList(List<String> errRptCdList) {
        this.errRptCdList = errRptCdList;
    }
    
    @Override
    public String toString() {
        return "ErrorReportSaveRequestDto{" +
                "cnvsId='" + cnvsId + '\'' +
                ", usrId='" + usrId + '\'' +
                ", errRptTxt='" + errRptTxt + '\'' +
                ", errRptCdList=" + errRptCdList +
                '}';
    }
}
