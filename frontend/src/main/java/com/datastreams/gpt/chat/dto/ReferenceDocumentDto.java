package com.datastreams.gpt.chat.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "참조 문서 DTO")
public class ReferenceDocumentDto {

    @Schema(description = "참조 순번", example = "1", required = true)
    @JsonProperty("REF_SEQ")
    private Long refSeq;

    @Schema(description = "문서 유형 코드 (기본값 N)", example = "N", required = true)
    @JsonProperty("DOC_TYP_CD")
    private String docTypCd;

    @Schema(description = "첨부 문서 명", example = "document.pdf", required = true)
    @JsonProperty("ATT_DOC_NM")
    private String attDocNm;

    @Schema(description = "첨부 문서 아이디", example = "doc_123", required = true)
    @JsonProperty("ATT_DOC_ID")
    private String attDocId;

    @Schema(description = "파일 UUID", example = "file_uuid_123", required = true)
    @JsonProperty("FILE_UID")
    private String fileUid;

    @Schema(description = "파일 다운로드 URL", example = "https://example.com/download/file_uuid_123", required = true)
    @JsonProperty("FILE_DOWN_URL")
    private String fileDownUrl;

    @Schema(description = "문서 청크 명", example = "Section 1", required = true)
    @JsonProperty("DOC_CHNK_NM")
    private String docChnkNm;

    @Schema(description = "문서 청크 텍스트", example = "문서 내용...", required = true)
    @JsonProperty("DOC_CHNK_TXT")
    private String docChnkTxt;

    @Schema(description = "유사도 율", example = "99.25", required = true)
    @JsonProperty("SMLT_RTE")
    private Double smltRte;

    // Getters and Setters
    public Long getRefSeq() {
        return refSeq;
    }

    public void setRefSeq(Long refSeq) {
        this.refSeq = refSeq;
    }

    public String getDocTypCd() {
        return docTypCd;
    }

    public void setDocTypCd(String docTypCd) {
        this.docTypCd = docTypCd;
    }

    public String getAttDocNm() {
        return attDocNm;
    }

    public void setAttDocNm(String attDocNm) {
        this.attDocNm = attDocNm;
    }

    public String getAttDocId() {
        return attDocId;
    }

    public void setAttDocId(String attDocId) {
        this.attDocId = attDocId;
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

    public Double getSmltRte() {
        return smltRte;
    }

    public void setSmltRte(Double smltRte) {
        this.smltRte = smltRte;
    }
}
