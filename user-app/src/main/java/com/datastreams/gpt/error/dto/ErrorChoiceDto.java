package com.datastreams.gpt.error.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * 오류 선택지 DTO
 * 공통코드 레벨2 개별 항목 데이터
 */
public class ErrorChoiceDto {
    
    @JsonProperty("level_n2_seq")
    private Long levelN2Seq;
    
    @JsonProperty("level_n1_cd")
    private String levelN1Cd;
    
    @JsonProperty("level_n2_cd")
    private String levelN2Cd;
    
    @JsonProperty("level_n2_nm")
    private String levelN2Nm;
    
    @JsonProperty("use_yn")
    private String useYn;
    
    @JsonProperty("cd_seq")
    private Long cdSeq;
    
    @JsonProperty("cd_sort_seq")
    private Long cdSortSeq;
    
    @JsonProperty("tot_cd_cnt")
    private Long totCdCnt;
    
    // 기본 생성자
    public ErrorChoiceDto() {}
    
    // Getters and Setters
    public Long getLevelN2Seq() {
        return levelN2Seq;
    }
    
    public void setLevelN2Seq(Long levelN2Seq) {
        this.levelN2Seq = levelN2Seq;
    }
    
    public String getLevelN1Cd() {
        return levelN1Cd;
    }
    
    public void setLevelN1Cd(String levelN1Cd) {
        this.levelN1Cd = levelN1Cd;
    }
    
    public String getLevelN2Cd() {
        return levelN2Cd;
    }
    
    public void setLevelN2Cd(String levelN2Cd) {
        this.levelN2Cd = levelN2Cd;
    }
    
    public String getLevelN2Nm() {
        return levelN2Nm;
    }
    
    public void setLevelN2Nm(String levelN2Nm) {
        this.levelN2Nm = levelN2Nm;
    }
    
    public String getUseYn() {
        return useYn;
    }
    
    public void setUseYn(String useYn) {
        this.useYn = useYn;
    }
    
    public Long getCdSeq() {
        return cdSeq;
    }
    
    public void setCdSeq(Long cdSeq) {
        this.cdSeq = cdSeq;
    }
    
    public Long getCdSortSeq() {
        return cdSortSeq;
    }
    
    public void setCdSortSeq(Long cdSortSeq) {
        this.cdSortSeq = cdSortSeq;
    }
    
    public Long getTotCdCnt() {
        return totCdCnt;
    }
    
    public void setTotCdCnt(Long totCdCnt) {
        this.totCdCnt = totCdCnt;
    }
    
    @Override
    public String toString() {
        return "ErrorChoiceDto{" +
                "levelN2Seq=" + levelN2Seq +
                ", levelN1Cd='" + levelN1Cd + '\'' +
                ", levelN2Cd='" + levelN2Cd + '\'' +
                ", levelN2Nm='" + levelN2Nm + '\'' +
                ", useYn='" + useYn + '\'' +
                ", cdSeq=" + cdSeq +
                ", cdSortSeq=" + cdSortSeq +
                ", totCdCnt=" + totCdCnt +
                '}';
    }
}
