package com.datastreams.gpt.error.dto;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * L-022: 오류 선택지 목록 조회 응답 DTO
 * 공통코드 레벨2 조회 결과 데이터
 */
public class ErrorChoiceListResponseDto {
    
    @JsonProperty("level_n1_cd")
    private String levelN1Cd;
    
    @JsonProperty("error_choices")
    private List<ErrorChoiceDto> errorChoices;
    
    @JsonProperty("total_count")
    private Integer totalCount;
    
    @JsonProperty("status")
    private String status;
    
    @JsonProperty("processing_time")
    private Long processingTime;
    
    // 기본 생성자
    public ErrorChoiceListResponseDto() {}
    
    // Getters and Setters
    public String getLevelN1Cd() {
        return levelN1Cd;
    }
    
    public void setLevelN1Cd(String levelN1Cd) {
        this.levelN1Cd = levelN1Cd;
    }
    
    public List<ErrorChoiceDto> getErrorChoices() {
        return errorChoices;
    }
    
    public void setErrorChoices(List<ErrorChoiceDto> errorChoices) {
        this.errorChoices = errorChoices;
    }
    
    public Integer getTotalCount() {
        return totalCount;
    }
    
    public void setTotalCount(Integer totalCount) {
        this.totalCount = totalCount;
    }
    
    public String getStatus() {
        return status;
    }
    
    public void setStatus(String status) {
        this.status = status;
    }
    
    public Long getProcessingTime() {
        return processingTime;
    }
    
    public void setProcessingTime(Long processingTime) {
        this.processingTime = processingTime;
    }
    
    @Override
    public String toString() {
        return "ErrorChoiceListResponseDto{" +
                "levelN1Cd='" + levelN1Cd + '\'' +
                ", errorChoices=" + errorChoices +
                ", totalCount=" + totalCount +
                ", status='" + status + '\'' +
                ", processingTime=" + processingTime +
                '}';
    }
}
