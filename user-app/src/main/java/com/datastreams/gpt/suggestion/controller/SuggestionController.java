package com.datastreams.gpt.suggestion.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

/**
 * 제안 목록 API 컨트롤러
 */
@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
@Tag(name = "제안 목록 API", description = "제안 목록 관련 API")
public class SuggestionController {

    private static final Logger log = LoggerFactory.getLogger(SuggestionController.class);

    /**
     * 제안 목록 조회 API
     * @return 제안 목록
     */
    @GetMapping("/suggestionList")
    @Operation(summary = "제안 목록 조회", description = "제안 목록을 조회하는 API")
    public ResponseEntity<Map<String, Object>> getSuggestionList() {
        
        Map<String, Object> responseData = new HashMap<>();
        
        try {
            // 임시 제안 목록 데이터
            String[] suggestions = {
                "한국도로공사 관련 질문을 해보세요",
                "도로 상태 확인 방법을 알려드릴게요",
                "교통 정보에 대해 문의하세요",
                "건설 현황을 확인해보세요"
            };

            responseData.put("result", "success");
            responseData.put("message", "제안 목록 조회 성공");
            responseData.put("data", suggestions);
            responseData.put("count", suggestions.length);

            log.info("[제안 목록 조회] 성공 - 제안 수: {}", suggestions.length);
            return ResponseEntity.ok(responseData);
            
        } catch (Exception e) {
            responseData.put("result", "error");
            responseData.put("message", "제안 목록 조회 중 오류 발생: " + e.getMessage());
            responseData.put("data", null);

            log.error("[제안 목록 조회] 오류 발생: {}", e.getMessage(), e);
            return ResponseEntity.ok(responseData);
        }
    }
}
