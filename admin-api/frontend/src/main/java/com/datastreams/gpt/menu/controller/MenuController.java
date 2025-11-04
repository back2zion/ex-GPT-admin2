package com.datastreams.gpt.menu.controller;

import com.datastreams.gpt.menu.dto.MenuInfoDto;
import com.datastreams.gpt.menu.dto.RecommendedQuestionDto;
import com.datastreams.gpt.menu.service.MenuService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 메뉴 관련 API 컨트롤러
 * Swagger 문서화 포함
 */
@RestController
@RequestMapping("/api/menu")
@CrossOrigin(origins = "*")
@Tag(name = "메뉴 API", description = "메뉴 조회 관련 API")
public class MenuController {

    private static final Logger log = LoggerFactory.getLogger(MenuController.class);

    @Autowired
    private MenuService menuService;

    /**
     * 사용자별 메뉴 목록 조회 API (L-007)
     * @param usrId 사용자 ID
     * @return 메뉴 목록
     */
    @GetMapping("/user/{usrId}")
    @Operation(summary = "사용자별 메뉴 조회", description = "특정 사용자가 접근 가능한 메뉴 목록을 조회하는 API")
    public ResponseEntity<Map<String, Object>> getUserMenus(
            @Parameter(description = "사용자 ID") @PathVariable String usrId) {
        
        Map<String, Object> responseData = new HashMap<>();
        
        try {
            List<MenuInfoDto> menuList = menuService.getUserMenus(usrId);
            
            if (menuList != null && !menuList.isEmpty()) {
                responseData.put("result", "success");
                responseData.put("message", "메뉴 조회 성공");
                responseData.put("data", menuList);
                responseData.put("count", menuList.size());
                
                log.info("[L-007] 메뉴 조회 API 성공 - 사용자: {}, 메뉴 수: {}", usrId, menuList.size());
            } else {
                responseData.put("result", "fail");
                responseData.put("message", "메뉴 정보를 찾을 수 없습니다");
                responseData.put("data", null);
                responseData.put("count", 0);
                
                log.warn("[L-007] 메뉴 조회 API - 메뉴 없음 - 사용자: {}", usrId);
            }
            
            return ResponseEntity.ok(responseData);
        } catch (Exception e) {
            responseData.put("result", "error");
            responseData.put("message", "메뉴 조회 중 오류 발생: " + e.getMessage());
            responseData.put("data", null);
            responseData.put("count", 0);
            
            log.error("[L-007] 메뉴 조회 API 오류 - 사용자: {}, 에러: {}", usrId, e.getMessage());
            return ResponseEntity.ok(responseData);
        }
    }

    /**
     * 전체 메뉴 목록 조회 API (관리자용)
     * @return 전체 메뉴 목록
     */
    @GetMapping("/all")
    @Operation(summary = "전체 메뉴 조회", description = "시스템의 전체 메뉴 목록을 조회하는 API (관리자용)")
    public ResponseEntity<Map<String, Object>> getAllMenus() {
        Map<String, Object> responseData = new HashMap<>();
        
        try {
            // TODO: 나중에 권한 시스템 도입 시 관리자 권한 체크 추가
            // 임시로 admin 사용자로 전체 메뉴 조회
            List<MenuInfoDto> menuList = menuService.getUserMenus("admin");
            
            responseData.put("result", "success");
            responseData.put("message", "전체 메뉴 조회 성공");
            responseData.put("data", menuList);
            responseData.put("count", menuList != null ? menuList.size() : 0);
            
            log.info("[L-007] 전체 메뉴 조회 API 성공 - 메뉴 수: {}", menuList != null ? menuList.size() : 0);
            
            return ResponseEntity.ok(responseData);
        } catch (Exception e) {
            responseData.put("result", "error");
            responseData.put("message", "전체 메뉴 조회 중 오류 발생: " + e.getMessage());
            responseData.put("data", null);
            responseData.put("count", 0);
            
            log.error("[L-007] 전체 메뉴 조회 API 오류 - 에러: {}", e.getMessage());
            return ResponseEntity.ok(responseData);
        }
    }

    /**
     * L-013: 메뉴별 추천 질의 조회 API
     * @param menuId 메뉴 ID
     * @return 추천 질의 목록
     */
    @GetMapping("/recommended-questions/{menuId}")
    @Operation(summary = "L-013: 메뉴별 추천 질의 조회", description = "특정 메뉴의 추천 질의 목록을 조회하는 API")
    public ResponseEntity<Map<String, Object>> getRecommendedQuestions(
            @Parameter(description = "메뉴 ID") @PathVariable Long menuId) {
        
        Map<String, Object> responseData = new HashMap<>();
        
        try {
            List<RecommendedQuestionDto> questionList = menuService.getRecommendedQuestions(menuId);
            
            if (questionList != null && !questionList.isEmpty()) {
                responseData.put("result", "success");
                responseData.put("message", "추천 질의 조회 성공");
                responseData.put("data", questionList);
                responseData.put("count", questionList.size());
                
                log.info("[L-013] 추천 질의 조회 API 성공 - 메뉴 ID: {}, 질의 수: {}", menuId, questionList.size());
            } else {
                responseData.put("result", "fail");
                responseData.put("message", "추천 질의 정보를 찾을 수 없습니다");
                responseData.put("data", null);
                responseData.put("count", 0);
                
                log.warn("[L-013] 추천 질의 조회 API - 질의 없음 - 메뉴 ID: {}", menuId);
            }
            
            return ResponseEntity.ok(responseData);
        } catch (Exception e) {
            responseData.put("result", "error");
            responseData.put("message", "추천 질의 조회 중 오류 발생: " + e.getMessage());
            responseData.put("data", null);
            responseData.put("count", 0);
            
            log.error("[L-013] 추천 질의 조회 API 오류 - 메뉴 ID: {}, 에러: {}", menuId, e.getMessage());
            return ResponseEntity.ok(responseData);
        }
    }
}
