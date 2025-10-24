package com.datastreams.gpt.user.controller;

import com.datastreams.gpt.common.dto.ApiResponseDto;
import com.datastreams.gpt.user.dto.UserSettingsDto;
import com.datastreams.gpt.user.dto.UserSettingsRequestDto;
import com.datastreams.gpt.user.service.UserSettingsService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * 사용자 설정 관련 API 컨트롤러
 */
@RestController
@RequestMapping("/api/user")
@Tag(name = "사용자 설정 API", description = "사용자 설정 관리 API")
public class UserController {

    private static final Logger log = LoggerFactory.getLogger(UserController.class);
    
    @Autowired
    private UserSettingsService userSettingsService;

    /**
     * 간단한 테스트 API
     */
    @GetMapping("/health")
    @Operation(summary = "API 테스트", description = "User API가 정상 작동하는지 확인합니다.")
    public ResponseEntity<ApiResponseDto<Long>> test() {
        log.info("[테스트 API] 호출됨");
        return ResponseEntity.ok(ApiResponseDto.success(
            "테스트 API가 정상 작동합니다.",
            System.currentTimeMillis()
        ));
    }

    /**
     * 사용자 설정 저장 API
     * 
     * @param request 사용자 설정 저장 요청 DTO
     * @return 저장 결과
     */
    @PostMapping("/settings")
    @Operation(summary = "사용자 설정 저장", description = "테마, 폰트 크기 등 사용자 개인 설정을 저장합니다.")
    public ResponseEntity<ApiResponseDto<UserSettingsDto>> setUserInfo(
            @RequestBody UserSettingsRequestDto request) {
        
        log.info("[사용자 설정 저장] 사용자: {}, 테마: {}, 폰트: {}", 
            request.getUserId(), request.getUiThmCd(), request.getFntSizeCd());
        
        try {
            // Request DTO → UserSettingsDto 변환
            UserSettingsDto settings = new UserSettingsDto();
            settings.setUiThmCd(request.getUiThmCd());
            settings.setFntSizeCd(request.getFntSizeCd());
            
            // NOT NULL 제약조건이 있는 필드들에 기본값 설정
            settings.setSystemAccessYn(request.getSysAccsYn() != null ? 
                request.getSysAccsYn() : "Y");
            settings.setManagerAuthYn(request.getMgrAuthYn() != null ? 
                request.getMgrAuthYn() : "N");
            settings.setVoiceModelUseYn(request.getVceMdlUseYn() != null ? 
                request.getVceMdlUseYn() : "Y");
            settings.setImageModelUseYn(request.getImgMdlUseYn() != null ? 
                request.getImgMdlUseYn() : "Y");

            // Service 호출하여 실제 DB 저장
            boolean saveResult = userSettingsService.saveUserSettings(request.getUserId(), settings);

            if (saveResult) {
                return ResponseEntity.ok(ApiResponseDto.success(
                    "사용자 설정이 성공적으로 저장되었습니다.",
                    settings
                ));
            } else {
                return ResponseEntity.internalServerError().body(ApiResponseDto.error(
                    "사용자 설정 저장에 실패했습니다."
                ));
            }

        } catch (Exception e) {
            log.error("[사용자 설정 저장] 오류 발생: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(ApiResponseDto.error(
                "서버 오류가 발생했습니다: " + e.getMessage()
            ));
        }
    }

    /**
     * 사용자 설정 조회 API
     * 
     * @param userId 사용자 ID
     * @return 사용자 설정 정보
     */
    @GetMapping("/settings")
    @Operation(summary = "사용자 설정 조회", description = "저장된 사용자 개인 설정을 조회합니다.")
    public ResponseEntity<ApiResponseDto<UserSettingsDto>> getUserInfo(@RequestParam String userId) {
        
        log.info("[사용자 설정 조회] 사용자: {}", userId);
        
        try {
            UserSettingsDto settings = userSettingsService.getUserSettings(userId);
            
            if (settings != null) {
                return ResponseEntity.ok(ApiResponseDto.success(
                    "사용자 설정을 성공적으로 조회했습니다.",
                    settings
                ));
            } else {
                return ResponseEntity.ok(ApiResponseDto.success(
                    "저장된 사용자 설정이 없습니다."
                ));
            }
            
        } catch (Exception e) {
            log.error("[사용자 설정 조회] 오류 발생: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(ApiResponseDto.error(
                "서버 오류가 발생했습니다: " + e.getMessage()
            ));
        }
    }
}
