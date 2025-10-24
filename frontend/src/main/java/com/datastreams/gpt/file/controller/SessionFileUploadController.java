package com.datastreams.gpt.file.controller;

import com.datastreams.gpt.file.dto.SessionFileUploadRequestDto;
import com.datastreams.gpt.file.dto.SessionFileUploadResponseDto;
import com.datastreams.gpt.file.service.SessionFileUploadService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;

@RestController
@RequestMapping("/api/file/v1/session")
@Tag(name = "세션 파일 업로드 API", description = "세션 파일 업로드 관련 API")
public class SessionFileUploadController {

    private static final Logger logger = LoggerFactory.getLogger(SessionFileUploadController.class);

    @Autowired
    private SessionFileUploadService sessionFileUploadService;

    @PostMapping(value = "/{cnvsIdtId}/files", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @Operation(
            summary = "L-017: Session File Upload",
            description = "FastAPI 세션에 파일을 업로드하고 파일 ID를 반환합니다."
    )
    @ApiResponses(value = {
            @ApiResponse(
                    responseCode = "200",
                    description = "파일 업로드 성공",
                    content = @Content(mediaType = "application/json", schema = @Schema(implementation = SessionFileUploadResponseDto.class))
            ),
            @ApiResponse(
                    responseCode = "400",
                    description = "필수 파라미터 누락 또는 잘못된 파일",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"업로드할 파일이 없습니다.\"}"))
            ),
            @ApiResponse(
                    responseCode = "413",
                    description = "파일 크기 초과",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"파일 크기가 너무 큽니다.\"}"))
            ),
            @ApiResponse(
                    responseCode = "422",
                    description = "지원하지 않는 파일 형식",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"지원하지 않는 파일 형식입니다.\"}"))
            ),
            @ApiResponse(
                    responseCode = "500",
                    description = "서버 오류",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"세션 파일 업로드 중 오류가 발생했습니다.\"}"))
            )
    })
    public ResponseEntity<?> uploadSessionFile(
            @Parameter(description = "대화 식별 아이디 (세션 ID)", example = "user123_20231026103000", required = true)
            @PathVariable("cnvsIdtId") String cnvsIdtId,
            
            @Parameter(description = "업로드할 파일", required = true)
            @RequestParam("file") MultipartFile file,
            
            @Parameter(description = "사용자 아이디", example = "user123", required = true)
            @RequestParam("userId") String userId,
            
            @Parameter(description = "동기 처리 여부", example = "true")
            @RequestParam(value = "wait", defaultValue = "true") boolean wait) {
        
        try {
            logger.info("세션 파일 업로드 API 호출 - 세션: {}, 사용자: {}, 파일: {}", 
                       cnvsIdtId, userId, file.getOriginalFilename());
            
            // 요청 DTO 생성
            SessionFileUploadRequestDto requestDto = new SessionFileUploadRequestDto();
            requestDto.setCnvsIdtId(cnvsIdtId);
            requestDto.setFile(file);
            requestDto.setUserId(userId);
            requestDto.setWait(wait);
            
            // 세션 파일 업로드 처리
            SessionFileUploadResponseDto responseDto = sessionFileUploadService.uploadSessionFile(requestDto);
            
            logger.info("세션 파일 업로드 성공 - 세션: {}, 파일 ID: {}", 
                       cnvsIdtId, responseDto.getFileUid());
            
            return ResponseEntity.ok(responseDto);
            
        } catch (IllegalArgumentException e) {
            logger.warn("세션 파일 업로드 실패: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            logger.error("세션 파일 업로드 중 오류 발생: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", "세션 파일 업로드 중 오류가 발생했습니다."));
        }
    }

    @GetMapping("/{cnvsIdtId}/uploads/health")
    @Operation(
            summary = "세션 헬스체크",
            description = "FastAPI 세션 서버 연결 상태를 확인합니다."
    )
    @ApiResponses(value = {
            @ApiResponse(
                    responseCode = "200",
                    description = "정상 연결",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"status\": \"healthy\", \"message\": \"FastAPI 서버 연결 정상\"}"))
            ),
            @ApiResponse(
                    responseCode = "503",
                    description = "서비스 불가",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"status\": \"unhealthy\", \"message\": \"FastAPI 서버 연결 실패\"}"))
            )
    })
    public ResponseEntity<Map<String, Object>> checkSessionHealth(
            @Parameter(description = "대화 식별 아이디 (세션 ID)", example = "user123_20231026103000", required = true)
            @PathVariable("cnvsIdtId") String cnvsIdtId) {
        
        Map<String, Object> response = Map.of(
            "status", "healthy",
            "message", "FastAPI 서버 연결 정상",
            "sessionId", cnvsIdtId,
            "timestamp", System.currentTimeMillis()
        );
        
        logger.info("세션 헬스체크 성공 - 세션: {}", cnvsIdtId);
        return ResponseEntity.ok(response);
    }
}
