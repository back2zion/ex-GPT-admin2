package com.datastreams.gpt.notice.dto;

import io.swagger.v3.oas.annotations.media.Schema;

/**
 * 오늘 기준 팝업 게시글 조회 DTO
 * L-011: 오늘 기준 팝업 게시글 조회 기능정의서 기준
 */
@Schema(description = "오늘 기준 팝업 게시글 조회 DTO")
public class NoticeTodayDto {

    @Schema(description = "게시글 순번", example = "1")
    private Integer pstSeq;

    @Schema(description = "게시글 아이디", example = "12345", required = true)
    private Long pstId;

    @Schema(description = "게시판 아이디", example = "1", required = true)
    private Long brdId;

    @Schema(description = "게시판 명", example = "공지사항")
    private String brdNm;

    @Schema(description = "게시글 제목", example = "시스템 점검 안내", required = true)
    private String titleNm;

    @Schema(description = "게시글 내용", example = "시스템 점검으로 인한 서비스 일시 중단 안내드립니다.")
    private String contTxt;

    @Schema(description = "등록 일자", example = "2025-01-15", required = true)
    private String regYmd;

    // 기본 생성자
    public NoticeTodayDto() {}

    // 전체 생성자
    public NoticeTodayDto(Integer pstSeq, Long pstId, Long brdId, String brdNm, 
                         String titleNm, String contTxt, String regYmd) {
        this.pstSeq = pstSeq;
        this.pstId = pstId;
        this.brdId = brdId;
        this.brdNm = brdNm;
        this.titleNm = titleNm;
        this.contTxt = contTxt;
        this.regYmd = regYmd;
    }

    // Getter/Setter
    public Integer getPstSeq() {
        return pstSeq;
    }

    public void setPstSeq(Integer pstSeq) {
        this.pstSeq = pstSeq;
    }

    public Long getPstId() {
        return pstId;
    }

    public void setPstId(Long pstId) {
        this.pstId = pstId;
    }

    public Long getBrdId() {
        return brdId;
    }

    public void setBrdId(Long brdId) {
        this.brdId = brdId;
    }

    public String getBrdNm() {
        return brdNm;
    }

    public void setBrdNm(String brdNm) {
        this.brdNm = brdNm;
    }

    public String getTitleNm() {
        return titleNm;
    }

    public void setTitleNm(String titleNm) {
        this.titleNm = titleNm;
    }

    public String getContTxt() {
        return contTxt;
    }

    public void setContTxt(String contTxt) {
        this.contTxt = contTxt;
    }

    public String getRegYmd() {
        return regYmd;
    }

    public void setRegYmd(String regYmd) {
        this.regYmd = regYmd;
    }

    @Override
    public String toString() {
        return "NoticeTodayDto{" +
                "pstSeq=" + pstSeq +
                ", pstId=" + pstId +
                ", brdId=" + brdId +
                ", brdNm='" + brdNm + '\'' +
                ", titleNm='" + titleNm + '\'' +
                ", contTxt='" + contTxt + '\'' +
                ", regYmd='" + regYmd + '\'' +
                '}';
    }
}
