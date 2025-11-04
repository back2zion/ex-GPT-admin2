package com.datastreams.gpt.menu.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;

/**
 * L-013: 추천 질의 조회 응답 DTO
 */
@Schema(description = "L-013: 추천 질의 조회 응답 DTO")
public class RecommendedQuestionDto {
    
    @JsonProperty("rcm_ques_seq")
    @Schema(description = "추천 질의 순번", example = "1")
    private Long rcmQuesSeq;
    
    @JsonProperty("rcm_ques_nm")
    @Schema(description = "추천 질의 명", example = "시스템 사용법에 대해 알려주세요")
    private String rcmQuesNm;
    
    // 기본 생성자
    public RecommendedQuestionDto() {}
    
    // 전체 생성자
    public RecommendedQuestionDto(Long rcmQuesSeq, String rcmQuesNm) {
        this.rcmQuesSeq = rcmQuesSeq;
        this.rcmQuesNm = rcmQuesNm;
    }
    
    // Getter and Setter
    public Long getRcmQuesSeq() {
        return rcmQuesSeq;
    }
    
    public void setRcmQuesSeq(Long rcmQuesSeq) {
        this.rcmQuesSeq = rcmQuesSeq;
    }
    
    public String getRcmQuesNm() {
        return rcmQuesNm;
    }
    
    public void setRcmQuesNm(String rcmQuesNm) {
        this.rcmQuesNm = rcmQuesNm;
    }
    
    @Override
    public String toString() {
        return "RecommendedQuestionDto{" +
                "rcmQuesSeq=" + rcmQuesSeq +
                ", rcmQuesNm='" + rcmQuesNm + '\'' +
                '}';
    }
}
