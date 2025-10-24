package com.datastreams.gpt.chat.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import java.math.BigDecimal;

/**
 * L-029: 사용자 대화 참조 문서 조회 및 문서별 다운로드 권한 조회 응답 DTO
 */
public class ReferenceDocumentResponseDto {
    
    @JsonProperty("ref_seq")
    @Schema(description = "참조 순번", example = "1")
    private Integer refSeq;
    
    @JsonProperty("att_doc_nm")
    @Schema(description = "첨부 문서 명", example = "기술문서_001.pdf")
    private String attDocNm;
    
    @JsonProperty("file_uid")
    @Schema(description = "파일 UUID", example = "550e8400-e29b-41d4-a716-446655440000")
    private String fileUid;
    
    @JsonProperty("file_down_url")
    @Schema(description = "파일 다운로드 URL", example = "https://example.com/download/file.pdf")
    private String fileDownUrl;
    
    @JsonProperty("doc_chnk_nm")
    @Schema(description = "문서 청크 명", example = "chunk_001")
    private String docChnkNm;
    
    @JsonProperty("doc_chnk_txt")
    @Schema(description = "문서 청크 텍스트", example = "이 문서는 기술 가이드라인에 대한 내용입니다...")
    private String docChnkTxt;
    
    @JsonProperty("smlt_rte")
    @Schema(description = "유사도율 (소수점 %)", example = "85.50")
    private BigDecimal smltRte;
    
    @JsonProperty("doc_down_alw_yn")
    @Schema(description = "문서 다운로드 가능 여부", example = "Y")
    private String docDownAlwYn;
    
    // 기본 생성자
    public ReferenceDocumentResponseDto() {}
    
    // 전체 생성자
    public ReferenceDocumentResponseDto(Integer refSeq, String attDocNm, String fileUid, 
                                       String fileDownUrl, String docChnkNm, String docChnkTxt, 
                                       BigDecimal smltRte, String docDownAlwYn) {
        this.refSeq = refSeq;
        this.attDocNm = attDocNm;
        this.fileUid = fileUid;
        this.fileDownUrl = fileDownUrl;
        this.docChnkNm = docChnkNm;
        this.docChnkTxt = docChnkTxt;
        this.smltRte = smltRte;
        this.docDownAlwYn = docDownAlwYn;
    }
    
    // Getter and Setter
    public Integer getRefSeq() {
        return refSeq;
    }
    
    public void setRefSeq(Integer refSeq) {
        this.refSeq = refSeq;
    }
    
    public String getAttDocNm() {
        return attDocNm;
    }
    
    public void setAttDocNm(String attDocNm) {
        this.attDocNm = attDocNm;
    }
    
    public String getFileUid() {
        return fileUid;
    }
    
    public void setFileUid(String fileUid) {
        this.fileUid = fileUid;
    }
    
    public String getFileDownUrl() {
        return fileDownUrl;
    }
    
    public void setFileDownUrl(String fileDownUrl) {
        this.fileDownUrl = fileDownUrl;
    }
    
    public String getDocChnkNm() {
        return docChnkNm;
    }
    
    public void setDocChnkNm(String docChnkNm) {
        this.docChnkNm = docChnkNm;
    }
    
    public String getDocChnkTxt() {
        return docChnkTxt;
    }
    
    public void setDocChnkTxt(String docChnkTxt) {
        this.docChnkTxt = docChnkTxt;
    }
    
    public BigDecimal getSmltRte() {
        return smltRte;
    }
    
    public void setSmltRte(BigDecimal smltRte) {
        this.smltRte = smltRte;
    }
    
    public String getDocDownAlwYn() {
        return docDownAlwYn;
    }
    
    public void setDocDownAlwYn(String docDownAlwYn) {
        this.docDownAlwYn = docDownAlwYn;
    }
    
    @Override
    public String toString() {
        return "ReferenceDocumentResponseDto{" +
                "refSeq=" + refSeq +
                ", attDocNm='" + attDocNm + '\'' +
                ", fileUid='" + fileUid + '\'' +
                ", fileDownUrl='" + fileDownUrl + '\'' +
                ", docChnkNm='" + docChnkNm + '\'' +
                ", docChnkTxt='" + docChnkTxt + '\'' +
                ", smltRte=" + smltRte +
                ", docDownAlwYn='" + docDownAlwYn + '\'' +
                '}';
    }
}
