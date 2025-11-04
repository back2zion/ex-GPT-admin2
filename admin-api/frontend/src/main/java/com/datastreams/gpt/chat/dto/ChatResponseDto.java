package com.datastreams.gpt.chat.dto;

import java.util.List;
import java.util.Map;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Chat API 응답 DTO
 * /v1/chat API 응답 형식에 맞춘 데이터 구조
 */
public class ChatResponseDto {
    
    @JsonProperty("message_id")
    private String messageId;
    
    @JsonProperty("session_id")
    private String sessionId;
    
    @JsonProperty("user_id")
    private String userId;
    
    @JsonProperty("response")
    private String response;
    
    @JsonProperty("citations")
    private List<Map<String, Object>> citations;
    
    @JsonProperty("search_query")
    private String searchQuery;
    
    @JsonProperty("suggested_questions")
    private List<String> suggestedQuestions;
    
    @JsonProperty("thinking")
    private String thinking;
    
    @JsonProperty("metadata")
    private Map<String, Object> metadata;
    
    @JsonProperty("stream")
    private Boolean stream;
    
    @JsonProperty("status")
    private String status;
    
    @JsonProperty("error")
    private String error;
    
    // 기본 생성자
    public ChatResponseDto() {}
    
    // Getters and Setters
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
    
    public String getResponse() {
        return response;
    }
    
    public void setResponse(String response) {
        this.response = response;
    }
    
    public List<Map<String, Object>> getCitations() {
        return citations;
    }
    
    public void setCitations(List<Map<String, Object>> citations) {
        this.citations = citations;
    }
    
    public String getSearchQuery() {
        return searchQuery;
    }
    
    public void setSearchQuery(String searchQuery) {
        this.searchQuery = searchQuery;
    }
    
    public List<String> getSuggestedQuestions() {
        return suggestedQuestions;
    }
    
    public void setSuggestedQuestions(List<String> suggestedQuestions) {
        this.suggestedQuestions = suggestedQuestions;
    }
    
    public String getThinking() {
        return thinking;
    }
    
    public void setThinking(String thinking) {
        this.thinking = thinking;
    }
    
    public Map<String, Object> getMetadata() {
        return metadata;
    }
    
    public void setMetadata(Map<String, Object> metadata) {
        this.metadata = metadata;
    }
    
    public Boolean getStream() {
        return stream;
    }
    
    public void setStream(Boolean stream) {
        this.stream = stream;
    }
    
    public String getStatus() {
        return status;
    }
    
    public void setStatus(String status) {
        this.status = status;
    }
    
    public String getError() {
        return error;
    }
    
    public void setError(String error) {
        this.error = error;
    }
    
    @Override
    public String toString() {
        return "ChatResponseDto{" +
                "messageId='" + messageId + '\'' +
                ", sessionId='" + sessionId + '\'' +
                ", userId='" + userId + '\'' +
                ", response='" + response + '\'' +
                ", citations=" + citations +
                ", searchQuery='" + searchQuery + '\'' +
                ", suggestedQuestions=" + suggestedQuestions +
                ", thinking='" + thinking + '\'' +
                ", metadata=" + metadata +
                ", stream=" + stream +
                ", status='" + status + '\'' +
                ", error='" + error + '\'' +
                '}';
    }
}
