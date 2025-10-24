package com.datastreams.gpt.file.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

@Schema(description = "L-021: 전체 파일 삭제 정보 갱신 요청 DTO")
public class AllFileDeleteInfoRequestDto {

    @NotBlank(message = "대화 식별 아이디는 필수입니다.")
    @Schema(description = "대화 식별 아이디", example = "USR_ID_20231026103000123456", required = true)
    private String cnvsIdtId;

    @NotBlank(message = "로그 내용은 필수입니다.")
    @Schema(description = "로그 내용 (API 실행 결과)", example = "Session files deleted successfully", required = true)
    private String logCont;

    @NotBlank(message = "성공 여부는 필수입니다.")
    @Pattern(regexp = "^[YN]$", message = "성공 여부는 Y 또는 N이어야 합니다.")
    @Schema(description = "성공 여부 (Y: 성공, N: 실패)", example = "Y", required = true)
    private String sucYn;

    // Getters and Setters
    public String getCnvsIdtId() {
        return cnvsIdtId;
    }

    public void setCnvsIdtId(String cnvsIdtId) {
        this.cnvsIdtId = cnvsIdtId;
    }

    public String getLogCont() {
        return logCont;
    }

    public void setLogCont(String logCont) {
        this.logCont = logCont;
    }

    public String getSucYn() {
        return sucYn;
    }

    public void setSucYn(String sucYn) {
        this.sucYn = sucYn;
    }

    @Override
    public String toString() {
        return "AllFileDeleteInfoRequestDto{" +
                "cnvsIdtId='" + cnvsIdtId + '\'' +
                ", logCont='" + logCont + '\'' +
                ", sucYn='" + sucYn + '\'' +
                '}';
    }
}
