package com.datastreams.gpt.chat.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Chat 메시지 DTO
 * 채팅 히스토리의 개별 메시지 구조
 */
public class ChatMessageDto {
    
    @JsonProperty("role")
    private String role;
    
    @JsonProperty("content")
    private String content;
    
    // 기본 생성자
    public ChatMessageDto() {}
    
    // 생성자
    public ChatMessageDto(String role, String content) {
        this.role = role;
        this.content = content;
    }
    
    // Getters and Setters
    public String getRole() {
        return role;
    }
    
    public void setRole(String role) {
        this.role = role;
    }
    
    public String getContent() {
        return content;
    }
    
    public void setContent(String content) {
        this.content = content;
    }
    
    @Override
    public String toString() {
        return "ChatMessageDto{" +
                "role='" + role + '\'' +
                ", content='" + content + '\'' +
                '}';
    }
}
