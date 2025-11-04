package com.datastreams.gpt.notice.dto;

/**
 * 공지사항 상세보기 DTO
 * L-011: 공지사항 상세보기 기능정의서 기준
 */
public class NoticeDetailDto {
    
    private Long brdId;           // BRD_ID: 게시판 아이디 (입력)
    private Long pstId;           // PST_ID: 게시글 아이디 (입력/출력)
    private String titleNm;       // TITLE_NM: 게시글 제목 (출력)
    private String pstCont;       // PST_CONT: 게시글 내용 (출력)
    private String regYmd;        // REG_YMD: 등록 일자 (출력)
    
    // 기본 생성자
    public NoticeDetailDto() {}
    
    // 전체 생성자
    public NoticeDetailDto(Long brdId, Long pstId, String titleNm, String pstCont, String regYmd) {
        this.brdId = brdId;
        this.pstId = pstId;
        this.titleNm = titleNm;
        this.pstCont = pstCont;
        this.regYmd = regYmd;
    }
    
    // Getter/Setter
    public Long getBrdId() {
        return brdId;
    }
    
    public void setBrdId(Long brdId) {
        this.brdId = brdId;
    }
    
    public Long getPstId() {
        return pstId;
    }
    
    public void setPstId(Long pstId) {
        this.pstId = pstId;
    }
    
    public String getTitleNm() {
        return titleNm;
    }
    
    public void setTitleNm(String titleNm) {
        this.titleNm = titleNm;
    }
    
    public String getPstCont() {
        return pstCont;
    }
    
    public void setPstCont(String pstCont) {
        this.pstCont = pstCont;
    }
    
    public String getRegYmd() {
        return regYmd;
    }
    
    public void setRegYmd(String regYmd) {
        this.regYmd = regYmd;
    }
    
    @Override
    public String toString() {
        return "NoticeDetailDto{" +
                "brdId=" + brdId +
                ", pstId=" + pstId +
                ", titleNm='" + titleNm + '\'' +
                ", pstCont='" + pstCont + '\'' +
                ", regYmd='" + regYmd + '\'' +
                '}';
    }
}
