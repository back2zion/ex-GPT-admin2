package com.datastreams.gpt.chat.dto;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Chat API 요청 DTO
 * /v1/chat API 요청 형식에 맞춘 데이터 구조
 */
public class ChatRequestDto {
    
    // Room ID (대화방 식별자) - 프론트엔드에서 전송
    @JsonProperty("cnvsIdtId")
    private String cnvsIdtId;

    @JsonProperty("stream")
    private Boolean stream;

    @JsonProperty("history")
    private List<ChatMessageDto> history;

    @JsonProperty("message_id")
    private String messageId;

    @JsonProperty("session_id")
    private String sessionId;

    @JsonProperty("user_id")
    private String userId;
    
    @JsonProperty("search_documents")
    private Boolean searchDocuments;
    
    @JsonProperty("department")
    private String department;
    
    @JsonProperty("authorization")
    private String authorization;
    
    @JsonProperty("search_scope")
    private List<String> searchScope;
    
    @JsonProperty("search_config")
    private SearchConfigDto searchConfig;
    
    
    @JsonProperty("max_context_tokens")
    private Integer maxContextTokens;
    
    @JsonProperty("temperature")
    private Double temperature;
    
    @JsonProperty("suggest_questions")
    private Boolean suggestQuestions;
    
    @JsonProperty("generate_search_query")
    private Boolean generateSearchQuery;
    
    @JsonProperty("think_mode")
    private Boolean thinkMode;
    
    @JsonProperty("current_time")
    private String currentTime;
    
    // 기본 생성자
    public ChatRequestDto() {}

    // Getters and Setters
    public String getCnvsIdtId() {
        return cnvsIdtId;
    }

    public void setCnvsIdtId(String cnvsIdtId) {
        this.cnvsIdtId = cnvsIdtId;
    }

    public Boolean getStream() {
        return stream;
    }
    
    public void setStream(Boolean stream) {
        this.stream = stream;
    }
    
    public List<ChatMessageDto> getHistory() {
        return history;
    }
    
    public void setHistory(List<ChatMessageDto> history) {
        this.history = history;
    }
    
    public String getMessageId() {
        return messageId;
    }
    
    public void setMessageId(String messageId) {
        this.messageId = messageId;
    }
    
    public String getSessionId() {
        return sessionId;
    }
    
    public void setSessionId(String sessionId) {
        this.sessionId = sessionId;
    }
    
    public String getUserId() {
        return userId;
    }
    
    public void setUserId(String userId) {
        this.userId = userId;
    }
    
    public Boolean getSearchDocuments() {
        return searchDocuments;
    }
    
    public void setSearchDocuments(Boolean searchDocuments) {
        this.searchDocuments = searchDocuments;
    }
    
    public String getDepartment() {
        return department;
    }
    
    public void setDepartment(String department) {
        this.department = department;
    }
    
    public String getAuthorization() {
        return authorization;
    }
    
    public void setAuthorization(String authorization) {
        this.authorization = authorization;
    }
    
    public List<String> getSearchScope() {
        return searchScope;
    }
    
    public void setSearchScope(List<String> searchScope) {
        this.searchScope = searchScope;
    }
    
    public SearchConfigDto getSearchConfig() {
        return searchConfig;
    }
    
    public void setSearchConfig(SearchConfigDto searchConfig) {
        this.searchConfig = searchConfig;
    }
    
    
    public Integer getMaxContextTokens() {
        return maxContextTokens;
    }
    
    public void setMaxContextTokens(Integer maxContextTokens) {
        this.maxContextTokens = maxContextTokens;
    }
    
    public Double getTemperature() {
        return temperature;
    }
    
    public void setTemperature(Double temperature) {
        this.temperature = temperature;
    }
    
    public Boolean getSuggestQuestions() {
        return suggestQuestions;
    }
    
    public void setSuggestQuestions(Boolean suggestQuestions) {
        this.suggestQuestions = suggestQuestions;
    }
    
    public Boolean getGenerateSearchQuery() {
        return generateSearchQuery;
    }
    
    public void setGenerateSearchQuery(Boolean generateSearchQuery) {
        this.generateSearchQuery = generateSearchQuery;
    }
    
    public Boolean getThinkMode() {
        return thinkMode;
    }
    
    public void setThinkMode(Boolean thinkMode) {
        this.thinkMode = thinkMode;
    }
    
    public String getCurrentTime() {
        return currentTime;
    }
    
    public void setCurrentTime(String currentTime) {
        this.currentTime = currentTime;
    }
    
    @Override
    public String toString() {
        return "ChatRequestDto{" +
                "cnvsIdtId='" + cnvsIdtId + '\'' +
                ", stream=" + stream +
                ", history=" + history +
                ", messageId='" + messageId + '\'' +
                ", sessionId='" + sessionId + '\'' +
                ", userId='" + userId + '\'' +
                ", searchDocuments=" + searchDocuments +
                ", department='" + department + '\'' +
                ", authorization='" + authorization + '\'' +
                ", searchScope=" + searchScope +
                ", searchConfig=" + searchConfig +
                ", maxContextTokens=" + maxContextTokens +
                ", temperature=" + temperature +
                ", suggestQuestions=" + suggestQuestions +
                ", generateSearchQuery=" + generateSearchQuery +
                ", thinkMode=" + thinkMode +
                ", currentTime='" + currentTime + '\'' +
                '}';
    }
}
