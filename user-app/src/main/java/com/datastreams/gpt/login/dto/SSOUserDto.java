package com.datastreams.gpt.login.dto;

import io.swagger.v3.oas.annotations.media.Schema;

/**
 * SSO 사용자 정보 DTO
 * DreamSecurity SSO 토큰에서 추출한 사용자 정보를 담는 객체
 * 
 * @author DataStreams
 * @since 2025-10-15
 */
@Schema(description = "SSO 사용자 정보 DTO")
public class SSOUserDto {

    @Schema(description = "사용자 ID (사번과 동일)", example = "21311729")
    private String userId;

    @Schema(description = "사용자 사번", example = "21311729")
    private String empCode;

    @Schema(description = "사용자 이름", example = "홍길동")
    private String name;

    @Schema(description = "부서 코드", example = "D001")
    private String deptCode;

    @Schema(description = "SSO 토큰 원본", example = "encrypted_token_string")
    private String token;

    @Schema(description = "SSO 인증 성공 여부", example = "true")
    private boolean authenticated;

    // 기본 생성자
    public SSOUserDto() {
        this.authenticated = false;
    }

    // 전체 생성자
    public SSOUserDto(String userId, String empCode, String name, String deptCode, String token) {
        this.userId = userId;
        this.empCode = empCode;
        this.name = name;
        this.deptCode = deptCode;
        this.token = token;
        this.authenticated = true;
    }

    // Getters and Setters
    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }

    public String getEmpCode() {
        return empCode;
    }

    public void setEmpCode(String empCode) {
        this.empCode = empCode;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getDeptCode() {
        return deptCode;
    }

    public void setDeptCode(String deptCode) {
        this.deptCode = deptCode;
    }

    public String getToken() {
        return token;
    }

    public void setToken(String token) {
        this.token = token;
    }

    public boolean isAuthenticated() {
        return authenticated;
    }

    public void setAuthenticated(boolean authenticated) {
        this.authenticated = authenticated;
    }

    @Override
    public String toString() {
        return "SSOUserDto{" +
                "userId='" + userId + '\'' +
                ", empCode='" + empCode + '\'' +
                ", name='" + name + '\'' +
                ", deptCode='" + deptCode + '\'' +
                ", authenticated=" + authenticated +
                '}';
    }
}

