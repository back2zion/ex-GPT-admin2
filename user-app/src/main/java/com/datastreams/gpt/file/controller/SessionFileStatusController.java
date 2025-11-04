package com.datastreams.gpt.file.controller;

import com.datastreams.gpt.file.dto.SessionFileStatusRequestDto;
import com.datastreams.gpt.file.dto.SessionFileStatusResponseDto;
import com.datastreams.gpt.file.service.SessionFileStatusService;
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

import java.util.Map;

@RestController
@RequestMapping("/api/file/v1")
@Tag(name = "Session File Status API", description = "세션 파일 상태 조회 관련 API")
public class SessionFileStatusController {

    private static final Logger logger = LoggerFactory.getLogger(SessionFileStatusController.class);

    @Autowired
    private SessionFileStatusService sessionFileStatusService;

    @GetMapping("/{fileUid}/status")
    @Operation(
            summary = "L-040: Session File Status",
            description = "FastAPI에서 파일 처리 상태를 조회합니다."
    )
    @ApiResponses(value = {
            @ApiResponse(
                    responseCode = "200",
                    description = "파일 상태 조회 성공",
                    content = @Content(mediaType = "application/json", schema = @Schema(implementation = SessionFileStatusResponseDto.class))
            ),
            @ApiResponse(
                    responseCode = "400",
                    description = "필수 파라미터 누락 또는 잘못된 파일 ID",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"파일 아이디는 필수입니다.\"}"))
            ),
            @ApiResponse(
                    responseCode = "404",
                    description = "파일을 찾을 수 없음",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"파일을 찾을 수 없습니다.\"}"))
            ),
            @ApiResponse(
                    responseCode = "500",
                    description = "서버 오류",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"파일 상태 조회 중 오류가 발생했습니다.\"}"))
            )
    })
    public ResponseEntity<?> getSessionFileStatus(
            @Parameter(description = "파일 아이디", example = "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34", required = true)
            @PathVariable("fileUid") String fileUid) {
        
        try {
            logger.info("세션 파일 상태 조회 API 호출 - 파일 ID: {}", fileUid);
            
            // 요청 DTO 생성
            SessionFileStatusRequestDto requestDto = new SessionFileStatusRequestDto();
            requestDto.setFileUid(fileUid);
            
            // 세션 파일 상태 조회 처리
            SessionFileStatusResponseDto responseDto = sessionFileStatusService.getSessionFileStatus(requestDto);
            
            logger.info("세션 파일 상태 조회 성공 - 파일 ID: {}, 상태: {}", 
                       fileUid, responseDto.getStatus());
            
            return ResponseEntity.ok(responseDto);
            
        } catch (IllegalArgumentException e) {
            logger.warn("세션 파일 상태 조회 실패: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            logger.error("세션 파일 상태 조회 중 오류 발생: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", "파일 상태 조회 중 오류가 발생했습니다."));
        }
    }

    @GetMapping("/{fileUid}/status/simple")
    @Operation(
            summary = "파일 상태 간단 조회",
            description = "파일의 기본 상태 정보만 간단히 조회합니다."
    )
    @ApiResponses(value = {
            @ApiResponse(
                    responseCode = "200",
                    description = "파일 상태 조회 성공",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"fileUid\": \"tmp-123\", \"status\": \"ready\", \"isReady\": true}"))
            ),
            @ApiResponse(
                    responseCode = "400",
                    description = "필수 파라미터 누락",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"파일 아이디는 필수입니다.\"}"))
            )
    })
    public ResponseEntity<?> getSimpleFileStatus(
            @Parameter(description = "파일 아이디", example = "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34", required = true)
            @PathVariable("fileUid") String fileUid) {
        
        try {
            logger.info("파일 상태 간단 조회 API 호출 - 파일 ID: {}", fileUid);
            
            // 요청 DTO 생성
            SessionFileStatusRequestDto requestDto = new SessionFileStatusRequestDto();
            requestDto.setFileUid(fileUid);
            
            // 세션 파일 상태 조회 처리
            SessionFileStatusResponseDto responseDto = sessionFileStatusService.getSessionFileStatus(requestDto);
            
            // 간단한 응답 생성
            Map<String, Object> simpleResponse = Map.of(
                "fileUid", responseDto.getFileUid(),
                "status", responseDto.getStatus(),
                "isReady", sessionFileStatusService.isFileReady(responseDto.getStatus()),
                "isError", sessionFileStatusService.isFileError(responseDto.getStatus()),
                "isProcessing", sessionFileStatusService.isFileProcessing(responseDto.getStatus())
            );
            
            logger.info("파일 상태 간단 조회 성공 - 파일 ID: {}, 상태: {}", 
                       fileUid, responseDto.getStatus());
            
            return ResponseEntity.ok(simpleResponse);
            
        } catch (IllegalArgumentException e) {
            logger.warn("파일 상태 간단 조회 실패: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            logger.error("파일 상태 간단 조회 중 오류 발생: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", "파일 상태 조회 중 오류가 발생했습니다."));
        }
    }
}
