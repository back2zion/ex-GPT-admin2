package com.datastreams.gpt.chat.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;

/**
 * L-030: 사용자 대화 추가 질의 조회 응답 DTO
 */
public class AdditionalQuestionResponseDto {
    
    @JsonProperty("add_ques_seq")
    @Schema(description = "추가 질의 순번", example = "1")
    private Integer addQuesSeq;
    
    @JsonProperty("add_ques_txt")
    @Schema(description = "추가 질의 텍스트", example = "이 기능에 대해 더 자세히 설명해주세요.")
    private String addQuesTxt;
    
    // 기본 생성자
    public AdditionalQuestionResponseDto() {}
    
    // 전체 생성자
    public AdditionalQuestionResponseDto(Integer addQuesSeq, String addQuesTxt) {
        this.addQuesSeq = addQuesSeq;
        this.addQuesTxt = addQuesTxt;
    }
    
    // Getter and Setter
    public Integer getAddQuesSeq() {
        return addQuesSeq;
    }
    
    public void setAddQuesSeq(Integer addQuesSeq) {
        this.addQuesSeq = addQuesSeq;
    }
    
    public String getAddQuesTxt() {
        return addQuesTxt;
    }
    
    public void setAddQuesTxt(String addQuesTxt) {
        this.addQuesTxt = addQuesTxt;
    }
    
    @Override
    public String toString() {
        return "AdditionalQuestionResponseDto{" +
                "addQuesSeq=" + addQuesSeq +
                ", addQuesTxt='" + addQuesTxt + '\'' +
                '}';
    }
}
