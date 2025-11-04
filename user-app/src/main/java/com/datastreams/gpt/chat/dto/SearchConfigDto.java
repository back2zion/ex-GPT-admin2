package com.datastreams.gpt.chat.dto;

import java.util.List;
import java.util.Map;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * 검색 설정 DTO
 * 문서 검색 관련 설정 정보
 */
public class SearchConfigDto {
    
    @JsonProperty("max_documents")
    private Integer maxDocuments;
    
    @JsonProperty("min_relevance_score")
    private Double minRelevanceScore;
    
    @JsonProperty("document_types")
    private List<String> documentTypes;
    
    @JsonProperty("date_range")
    private Map<String, Object> dateRange;
    
    @JsonProperty("priority_sources")
    private List<String> prioritySources;
    
    @JsonProperty("do_rerank")
    private Boolean doRerank;
    
    // 기본 생성자
    public SearchConfigDto() {}
    
    // Getters and Setters
    public Integer getMaxDocuments() {
        return maxDocuments;
    }
    
    public void setMaxDocuments(Integer maxDocuments) {
        this.maxDocuments = maxDocuments;
    }
    
    public Double getMinRelevanceScore() {
        return minRelevanceScore;
    }
    
    public void setMinRelevanceScore(Double minRelevanceScore) {
        this.minRelevanceScore = minRelevanceScore;
    }
    
    public List<String> getDocumentTypes() {
        return documentTypes;
    }
    
    public void setDocumentTypes(List<String> documentTypes) {
        this.documentTypes = documentTypes;
    }
    
    public Map<String, Object> getDateRange() {
        return dateRange;
    }
    
    public void setDateRange(Map<String, Object> dateRange) {
        this.dateRange = dateRange;
    }
    
    public List<String> getPrioritySources() {
        return prioritySources;
    }
    
    public void setPrioritySources(List<String> prioritySources) {
        this.prioritySources = prioritySources;
    }
    
    public Boolean getDoRerank() {
        return doRerank;
    }
    
    public void setDoRerank(Boolean doRerank) {
        this.doRerank = doRerank;
    }
    
    @Override
    public String toString() {
        return "SearchConfigDto{" +
                "maxDocuments=" + maxDocuments +
                ", minRelevanceScore=" + minRelevanceScore +
                ", documentTypes=" + documentTypes +
                ", dateRange=" + dateRange +
                ", prioritySources=" + prioritySources +
                ", doRerank=" + doRerank +
                '}';
    }
}
