package com.datastreams.gpt.survey.controller;

import com.datastreams.gpt.survey.dto.SurveyRequestDto;
import com.datastreams.gpt.survey.service.SurveyService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

/**
 * 만족도 저장 API 컨트롤러
 */
@RestController
@RequestMapping("/api/surveys")
@Tag(name = "만족도 API", description = "만족도 저장 관련 API")
public class SurveyController {

    private static final Logger log = LoggerFactory.getLogger(SurveyController.class);

    @Autowired
    private SurveyService surveyService;

    /**
     * 만족도 저장 API
     * L-012 기능정의서 기준
     * 
     * @param request 만족도 저장 요청 DTO
     * @return 저장 결과
     */
    @PostMapping("")
    @Operation(summary = "만족도 저장", description = "사용자의 만족도 평가를 저장합니다.")
    public ResponseEntity<Map<String, Object>> setSurvey(
            @RequestBody SurveyRequestDto request) {
        
        Map<String, Object> responseData = new HashMap<>();
        
        log.info("[만족도 저장 API] 사용자: {}, 만족도: {}", 
            request.getUsrId(), request.getRactLevelVal());
        
        try {
            // 필수 필드 검증
            if (request.getUsrId() == null || request.getUsrId().trim().isEmpty()) {
                responseData.put("result", "fail");
                responseData.put("message", "사용자 ID는 필수입니다.");
                return ResponseEntity.badRequest().body(responseData);
            }
            
            if (request.getRactLevelVal() == null) {
                responseData.put("result", "fail");
                responseData.put("message", "만족도 레벨 값은 필수입니다.");
                return ResponseEntity.badRequest().body(responseData);
            }
            
            // Service 호출하여 실제 DB 저장
            boolean saveResult = surveyService.saveSurvey(request);

            if (saveResult) {
                responseData.put("result", "success");
                responseData.put("message", "만족도가 성공적으로 저장되었습니다.");
                
                // null 값을 허용하는 HashMap 사용
                Map<String, Object> data = new HashMap<>();
                data.put("usrId", request.getUsrId());
                data.put("ractLevelVal", request.getRactLevelVal());
                data.put("sesnId", request.getSesnId()); // null 가능
                responseData.put("data", data);
                
                return ResponseEntity.ok(responseData);
            } else {
                responseData.put("result", "fail");
                responseData.put("message", "만족도 저장에 실패했습니다.");
                return ResponseEntity.internalServerError().body(responseData);
            }

        } catch (Exception e) {
            log.error("[만족도 저장 API] 오류 발생: {}", e.getMessage(), e);
            responseData.put("result", "error");
            responseData.put("message", "서버 오류가 발생했습니다: " + e.getMessage());
            return ResponseEntity.internalServerError().body(responseData);
        }
    }

    /**
     * 테스트 API
     */
    @GetMapping("/health")
    @Operation(summary = "만족도 API 테스트", description = "만족도 API가 정상 작동하는지 확인합니다.")
    public ResponseEntity<Map<String, Object>> test() {
        log.info("[만족도 API 테스트] 호출됨");
        
        Map<String, Object> responseData = new HashMap<>();
        responseData.put("result", "success");
        responseData.put("message", "만족도 API가 정상 작동합니다.");
        responseData.put("data", Map.of(
            "timestamp", System.currentTimeMillis(),
            "api", "survey"
        ));
        
        return ResponseEntity.ok(responseData);
    }
}
