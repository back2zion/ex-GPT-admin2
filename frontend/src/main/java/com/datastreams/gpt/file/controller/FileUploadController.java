package com.datastreams.gpt.file.controller;

import com.datastreams.gpt.file.dto.FileUploadHistoryRequestDto;
import com.datastreams.gpt.file.dto.FileUploadHistoryResponseDto;
import com.datastreams.gpt.file.service.FileUploadService;
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

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 파일 업로드 관련 컨트롤러
 */
@RestController
@RequestMapping("/api/file")
@Tag(name = "파일 업로드 API", description = "파일 업로드 관련 API")
public class FileUploadController {
    
    private static final Logger logger = LoggerFactory.getLogger(FileUploadController.class);
    
    @Autowired
    private FileUploadService fileUploadService;
    
    /**
     * L-016: 파일 업로드 이력 생성 (Insert)
     */
    @PostMapping("/upload-histories")
    @Operation(
        summary = "파일 업로드 이력 생성",
        description = "파일 업로드 시 이력을 생성하고 대화 식별 ID를 반환합니다. (첫 업로드 시 대화 요약도 함께 생성)"
    )
    @ApiResponse(
        responseCode = "200",
        description = "파일 업로드 이력 생성 성공",
        content = @Content(
            mediaType = "application/json",
            schema = @Schema(implementation = FileUploadHistoryResponseDto.class)
        )
    )
    @ApiResponse(
        responseCode = "400",
        description = "잘못된 요청 데이터",
        content = @Content(mediaType = "application/json")
    )
    @ApiResponse(
        responseCode = "500",
        description = "서버 내부 오류",
        content = @Content(mediaType = "application/json")
    )
    public ResponseEntity<Map<String, Object>> createFileUploadHistory(
            @Parameter(description = "파일 업로드 이력 생성 요청 데이터")
            @RequestBody FileUploadHistoryRequestDto requestDto) {
        
        logger.info("파일 업로드 이력 생성 API 호출 - 사용자: {}", requestDto.getUsrId());
        
        Map<String, Object> response = new HashMap<>();
        
        try {
            // 파일 업로드 이력 생성
            FileUploadHistoryResponseDto result = fileUploadService.createFileUploadHistory(requestDto);
            
            // 성공 응답 구성
            response.put("result", "success");
            response.put("data", result);
            response.put("message", "파일 업로드 이력이 성공적으로 생성되었습니다.");
            
            logger.info("파일 업로드 이력 생성 완료 - 대화ID: {}, 파일순번: {}", 
                       result.getCnvsIdtId(), result.getFileUpldSeq());
            
            return ResponseEntity.ok(response);
            
        } catch (IllegalArgumentException e) {
            logger.warn("파일 업로드 이력 생성 요청 데이터 오류: {}", e.getMessage());
            
            response.put("result", "error");
            response.put("error", e.getMessage());
            response.put("message", "요청 데이터가 올바르지 않습니다.");
            
            return ResponseEntity.badRequest().body(response);
            
        } catch (Exception e) {
            logger.error("파일 업로드 이력 생성 중 오류 발생", e);
            
            response.put("result", "error");
            response.put("error", e.getMessage());
            response.put("message", "파일 업로드 이력 생성 중 오류가 발생했습니다.");
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }
    
    /**
     * 파일 업로드 순번으로 파일 정보 조회
     */
    @GetMapping("/upload-histories/{fileUpldSeq}")
    @Operation(
        summary = "파일 업로드 정보 조회",
        description = "파일 업로드 순번으로 파일 정보를 조회합니다."
    )
    @ApiResponse(
        responseCode = "200",
        description = "파일 업로드 정보 조회 성공",
        content = @Content(
            mediaType = "application/json",
            schema = @Schema(implementation = FileUploadHistoryRequestDto.class)
        )
    )
    public ResponseEntity<Map<String, Object>> getFileUploadBySeq(
            @Parameter(description = "파일 업로드 순번")
            @PathVariable Long fileUpldSeq) {
        
        logger.info("파일 업로드 정보 조회 API 호출 - 순번: {}", fileUpldSeq);
        
        Map<String, Object> response = new HashMap<>();
        
        try {
            FileUploadHistoryRequestDto fileUpload = fileUploadService.getFileUploadBySeq(fileUpldSeq);
            
            response.put("result", "success");
            response.put("data", fileUpload);
            response.put("message", "파일 업로드 정보를 성공적으로 조회했습니다.");
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("파일 업로드 정보 조회 중 오류 발생", e);
            
            response.put("result", "error");
            response.put("error", e.getMessage());
            response.put("message", "파일 업로드 정보 조회 중 오류가 발생했습니다.");
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }
    
    /**
     * 대화 식별 ID로 파일 업로드 목록 조회
     */
    @GetMapping("/conversations/{cnvsIdtId}/upload-histories")
    @Operation(
        summary = "대화별 파일 업로드 목록 조회",
        description = "대화 식별 ID로 해당 대화의 모든 파일 업로드 목록을 조회합니다."
    )
    @ApiResponse(
        responseCode = "200",
        description = "파일 업로드 목록 조회 성공",
        content = @Content(
            mediaType = "application/json",
            schema = @Schema(implementation = List.class)
        )
    )
    public ResponseEntity<Map<String, Object>> getFileUploadListByConversation(
            @Parameter(description = "대화 식별 ID")
            @PathVariable String cnvsIdtId) {
        
        logger.info("대화별 파일 업로드 목록 조회 API 호출 - 대화ID: {}", cnvsIdtId);
        
        Map<String, Object> response = new HashMap<>();
        
        try {
            List<FileUploadHistoryRequestDto> fileUploadList = fileUploadService.getFileUploadListByConversation(cnvsIdtId);
            
            response.put("result", "success");
            response.put("data", fileUploadList);
            response.put("message", "파일 업로드 목록을 성공적으로 조회했습니다.");
            response.put("count", fileUploadList.size());
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("대화별 파일 업로드 목록 조회 중 오류 발생", e);
            
            response.put("result", "error");
            response.put("error", e.getMessage());
            response.put("message", "파일 업로드 목록 조회 중 오류가 발생했습니다.");
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }
}
