package com.datastreams.gpt.chat.controller;

import com.datastreams.gpt.chat.dto.*;
import com.datastreams.gpt.chat.service.ConversationHistoryService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;
import com.datastreams.gpt.login.dto.UserInfoDto;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/chat/history")
@Tag(name = "대화 이력 API", description = "이전 대화 이력 조회 관련 API")
public class ConversationHistoryController {

    private static final Logger logger = LoggerFactory.getLogger(ConversationHistoryController.class);

    @Autowired
    private ConversationHistoryService conversationHistoryService;
    
    /**
     * 세션 검증 및 사용자 정보 추출
     * @param request HTTP 요청
     * @return 사용자 정보 (검증 실패시 null)
     */
    private ResponseEntity<?> validateSession(HttpServletRequest request, String operation) {
        HttpSession session = request.getSession(false);
        if (session == null) {
            logger.warn("{} 실패: 세션이 만료되었습니다.", operation);
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(Map.of("error", "세션이 만료되었습니다. 로그인을 다시 해주세요."));
        }
        
        UserInfoDto userInfo = (UserInfoDto) session.getAttribute("userInfo");
        if (userInfo == null) {
            logger.warn("{} 실패: 사용자 정보를 찾을 수 없습니다.", operation);
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(Map.of("error", "사용자 정보를 찾을 수 없습니다. 로그인을 다시 해주세요."));
        }
        
        return null; // 검증 성공
    }

    @PostMapping("/previous")
    @Operation(
            summary = "L-041: 이전 대화 이력 조회",
            description = "현재 대화의 이전 대화 이력을 조회하여 AI에게 컨텍스트를 제공합니다."
    )
    @ApiResponse(
            responseCode = "200",
            description = "이전 대화 이력 조회 성공",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = ConversationHistoryResponseDto.class))
    )
    @ApiResponse(
            responseCode = "400",
            description = "필수 파라미터 누락 또는 잘못된 값",
            content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"대화 식별 아이디는 필수입니다.\"}"))
    )
    @ApiResponse(
            responseCode = "500",
            description = "서버 오류",
            content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"이전 대화 이력 조회 중 오류가 발생했습니다.\"}"))
    )
    public ResponseEntity<?> getConversationHistory(
            @Parameter(description = "이전 대화 이력 조회 요청 데이터", required = true)
            @RequestBody ConversationHistoryRequestDto requestDto,
            HttpServletRequest request) {
        
        // 세션 검증
        ResponseEntity<?> validationError = validateSession(request, "이전 대화 이력 조회");
        if (validationError != null) {
            return validationError;
        }
        
        UserInfoDto userInfo = (UserInfoDto) request.getSession(false).getAttribute("userInfo");
        if (userInfo == null) {
            logger.warn("이전 대화 이력 조회 실패: 세션에서 사용자 정보를 찾을 수 없습니다.");
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(Map.of("error", "세션에서 사용자 정보를 찾을 수 없습니다. 로그인을 다시 해주세요."));
        }
        
        try {
            logger.info("이전 대화 이력 조회 요청 - 사용자: {}, 대화ID: {}", userInfo.getUsrId(), requestDto.getCnvsIdtId());
            List<ConversationHistoryResponseDto> historyList = conversationHistoryService.getConversationHistory(requestDto);
            logger.info("이전 대화 이력 조회 성공 - 사용자: {}, 조회 건수: {}", userInfo.getUsrId(), historyList.size());
            
            // 표준 JSON 응답 형식 적용
            Map<String, Object> response = new java.util.HashMap<>();
            response.put("result", "success");
            response.put("message", "이전 대화 이력 조회 성공");
            response.put("data", historyList);
            
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            logger.warn("이전 대화 이력 조회 실패: {}", e.getMessage());
            Map<String, Object> response = new java.util.HashMap<>();
            response.put("result", "error");
            response.put("message", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
        } catch (Exception e) {
            logger.error("이전 대화 이력 조회 중 오류 발생: {}", e.getMessage(), e);
            Map<String, Object> response = new java.util.HashMap<>();
            response.put("result", "error");
            response.put("message", "이전 대화 이력 조회 중 오류가 발생했습니다.");
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }

    @PostMapping("/list")
    @Operation(
            summary = "L-027: 대화 목록 조회",
            description = "사용자의 대화 목록을 조회합니다."
    )
    @ApiResponse(
            responseCode = "200",
            description = "대화 목록 조회 성공",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = ConversationListResponseDto.class))
    )
    public ResponseEntity<?> getConversationList(
            @Parameter(description = "대화 목록 조회 요청 데이터", required = true)
            @RequestBody ConversationListRequestDto requestDto,
            HttpServletRequest request) {
        
        // 세션 검증
        ResponseEntity<?> validationError = validateSession(request, "대화 목록 조회");
        if (validationError != null) {
            return validationError;
        }
        
        UserInfoDto userInfo = (UserInfoDto) request.getSession(false).getAttribute("userInfo");
        if (userInfo == null) {
            logger.warn("대화 목록 조회 실패: 세션에서 사용자 정보를 찾을 수 없습니다.");
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(Map.of("error", "세션에서 사용자 정보를 찾을 수 없습니다. 로그인을 다시 해주세요."));
        }
        
        try {
            logger.info("대화 목록 조회 요청 - 사용자: {}", userInfo.getUsrId());
            List<ConversationListResponseDto> conversationList = conversationHistoryService.getConversationList(requestDto);
            logger.info("대화 목록 조회 성공 - 사용자: {}, 조회 건수: {}", userInfo.getUsrId(), conversationList.size());
            
            // 표준 JSON 응답 형식 적용
            Map<String, Object> response = new java.util.HashMap<>();
            response.put("result", "success");
            response.put("message", "대화 목록 조회 성공");
            response.put("data", conversationList);
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("대화 목록 조회 중 오류 발생: {}", e.getMessage(), e);
            Map<String, Object> response = new java.util.HashMap<>();
            response.put("result", "error");
            response.put("message", "대화 목록 조회 중 오류가 발생했습니다.");
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }

    @PostMapping("/conversation")
    @Operation(
            summary = "L-028: 사용자 대화 조회",
            description = "특정 사용자의 대화 내용을 조회합니다."
    )
    @ApiResponse(
            responseCode = "200",
            description = "사용자 대화 조회 성공",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = UserConversationResponseDto.class))
    )
    public ResponseEntity<?> getUserConversation(
            @Parameter(description = "사용자 대화 조회 요청 데이터", required = true)
            @RequestBody ConversationListRequestDto requestDto) {
        try {
            List<UserConversationResponseDto> conversationList = conversationHistoryService.getUserConversation(requestDto);
            
            // 표준 JSON 응답 형식 적용
            Map<String, Object> response = new java.util.HashMap<>();
            response.put("result", "success");
            response.put("message", "사용자 대화 조회 성공");
            response.put("data", conversationList);
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("사용자 대화 조회 중 오류 발생: {}", e.getMessage(), e);
            Map<String, Object> response = new java.util.HashMap<>();
            response.put("result", "error");
            response.put("message", "사용자 대화 조회 중 오류가 발생했습니다.");
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }

    @PostMapping("/referenceDocuments")
    @Operation(
            summary = "L-029: 참조 문서 조회",
            description = "대화에서 참조된 문서 목록을 조회합니다."
    )
    @ApiResponse(
            responseCode = "200",
            description = "참조 문서 조회 성공",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = ConversationListResponseDto.class))
    )
    public ResponseEntity<?> getReferenceDocuments(
            @Parameter(description = "참조 문서 조회 요청 데이터", required = true)
            @RequestBody ConversationListRequestDto requestDto) {
        try {
            List<ConversationListResponseDto> documentList = conversationHistoryService.getReferenceDocuments(requestDto);
            
            // 표준 JSON 응답 형식 적용
            Map<String, Object> response = new java.util.HashMap<>();
            response.put("result", "success");
            response.put("message", "참조 문서 조회 성공");
            response.put("data", documentList);
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("참조 문서 조회 중 오류 발생: {}", e.getMessage(), e);
            Map<String, Object> response = new java.util.HashMap<>();
            response.put("result", "error");
            response.put("message", "참조 문서 조회 중 오류가 발생했습니다.");
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }

    @PostMapping("/additionalQuestions")
    @Operation(
            summary = "L-030: 추가 질의 조회",
            description = "대화에서 생성된 추가 질의 목록을 조회합니다."
    )
    @ApiResponse(
            responseCode = "200",
            description = "추가 질의 조회 성공",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = ConversationListResponseDto.class))
    )
    public ResponseEntity<?> getAdditionalQuestions(
            @Parameter(description = "추가 질의 조회 요청 데이터", required = true)
            @RequestBody ConversationListRequestDto requestDto) {
        try {
            List<ConversationListResponseDto> questionList = conversationHistoryService.getAdditionalQuestions(requestDto);
            
            // 표준 JSON 응답 형식 적용
            Map<String, Object> response = new java.util.HashMap<>();
            response.put("result", "success");
            response.put("message", "추가 질의 조회 성공");
            response.put("data", questionList);
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("추가 질의 조회 중 오류 발생: {}", e.getMessage(), e);
            Map<String, Object> response = new java.util.HashMap<>();
            response.put("result", "error");
            response.put("message", "추가 질의 조회 중 오류가 발생했습니다.");
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }

    @PostMapping("/uploaded-files")
    @Operation(
            summary = "L-031: 업로드 파일 조회",
            description = "대화에서 업로드된 파일 목록을 조회합니다."
    )
    @ApiResponse(
            responseCode = "200",
            description = "업로드 파일 조회 성공",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = ConversationListResponseDto.class))
    )
    public ResponseEntity<?> getUploadFiles(
            @Parameter(description = "업로드 파일 조회 요청 데이터", required = true)
            @RequestBody ConversationListRequestDto requestDto) {
        try {
            List<ConversationListResponseDto> fileList = conversationHistoryService.getUploadFiles(requestDto);
            
            // 표준 JSON 응답 형식 적용
            Map<String, Object> response = new java.util.HashMap<>();
            response.put("result", "success");
            response.put("message", "업로드 파일 조회 성공");
            response.put("data", fileList);
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("업로드 파일 조회 중 오류 발생: {}", e.getMessage(), e);
            Map<String, Object> response = new java.util.HashMap<>();
            response.put("result", "error");
            response.put("message", "업로드 파일 조회 중 오류가 발생했습니다.");
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }
}