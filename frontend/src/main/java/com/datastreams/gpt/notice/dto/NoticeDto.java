package com.datastreams.gpt.notice.dto;

/**
 * 공지사항 조회 DTO
 * L-011: 공지사항 조회 기능정의서 기준
 */
public class NoticeDto {
    
    private Integer pstSeq;        // PST_SEQ: 게시글 순번
    private Long pstId;           // PST_ID: 게시글 아이디
    private Long brdId;           // BRD_ID: 게시판 아이디
    private String brdNm;         // BRD_NM: 게시판 명 (사용안함)
    private String titleNm;       // TITLE_NM: 게시글 제목
    private String contTxt;       // CONT_TXT: 게시글 내용 (간략)
    private String regYmd;        // REG_YMD: 등록 일자
    
    // 기본 생성자
    public NoticeDto() {}
    
    // 전체 생성자
    public NoticeDto(Integer pstSeq, Long pstId, Long brdId, String brdNm, 
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
        return "NoticeDto{" +
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
