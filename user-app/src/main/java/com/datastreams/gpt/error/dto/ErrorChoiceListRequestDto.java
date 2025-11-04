package com.datastreams.gpt.error.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * L-022: 오류 선택지 목록 조회 요청 DTO
 * 공통코드 레벨2 조회를 위한 요청 데이터
 */
public class ErrorChoiceListRequestDto {
    
    @JsonProperty("level_n1_cd")
    private String levelN1Cd;
    
    // 기본 생성자
    public ErrorChoiceListRequestDto() {}
    
    // 생성자
    public ErrorChoiceListRequestDto(String levelN1Cd) {
        this.levelN1Cd = levelN1Cd;
    }
    
    // Getters and Setters
    public String getLevelN1Cd() {
        return levelN1Cd;
    }
    
    public void setLevelN1Cd(String levelN1Cd) {
        this.levelN1Cd = levelN1Cd;
    }
    
    @Override
    public String toString() {
        return "ErrorChoiceListRequestDto{" +
                "levelN1Cd='" + levelN1Cd + '\'' +
                '}';
    }
}
