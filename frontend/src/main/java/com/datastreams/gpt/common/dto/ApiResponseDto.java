package com.datastreams.gpt.common.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.List;

/**
 * 공통 API 응답 DTO
 * 
 * @param <T> 응답 데이터 타입
 */
@Schema(description = "API 응답 정보")
public class ApiResponseDto<T> {

    @Schema(description = "처리 결과 (success/error)", example = "success")
    private String result;

    @Schema(description = "응답 메시지", example = "처리가 완료되었습니다.")
    private String message;

    @Schema(description = "응답 데이터")
    private T data;

    @Schema(description = "응답 데이터 리스트")
    private List<T> dataList;

    // 기본 생성자
    public ApiResponseDto() {}

    // 생성자들
    public ApiResponseDto(String result, String message) {
        this.result = result;
        this.message = message;
    }

    public ApiResponseDto(String result, String message, T data) {
        this.result = result;
        this.message = message;
        this.data = data;
    }

    public ApiResponseDto(String result, String message, T data, List<T> dataList) {
        this.result = result;
        this.message = message;
        this.data = data;
        this.dataList = dataList;
    }

    // 정적 팩토리 메서드들
    public static <T> ApiResponseDto<T> success(String message) {
        return new ApiResponseDto<>("success", message);
    }

    public static <T> ApiResponseDto<T> success(String message, T data) {
        return new ApiResponseDto<>("success", message, data);
    }

    public static <T> ApiResponseDto<T> success(String message, List<T> dataList) {
        ApiResponseDto<T> response = new ApiResponseDto<>();
        response.result = "success";
        response.message = message;
        response.dataList = dataList;
        return response;
    }

    public static <T> ApiResponseDto<T> error(String message) {
        return new ApiResponseDto<>("error", message);
    }

    public static <T> ApiResponseDto<T> error(String message, T data) {
        return new ApiResponseDto<>("error", message, data);
    }

    // Getter and Setter methods
    public String getResult() {
        return result;
    }

    public void setResult(String result) {
        this.result = result;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public T getData() {
        return data;
    }

    public void setData(T data) {
        this.data = data;
    }

    public List<T> getDataList() {
        return dataList;
    }

    public void setDataList(List<T> dataList) {
        this.dataList = dataList;
    }

    @Override
    public String toString() {
        return "ApiResponseDto{" +
                "result='" + result + '\'' +
                ", message='" + message + '\'' +
                ", data=" + data +
                ", dataList=" + dataList +
                '}';
    }
}
