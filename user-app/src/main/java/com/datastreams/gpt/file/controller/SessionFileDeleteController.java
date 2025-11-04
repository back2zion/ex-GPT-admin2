package com.datastreams.gpt.file.controller;

import com.datastreams.gpt.file.dto.SessionFileDeleteRequestDto;
import com.datastreams.gpt.file.dto.SessionFileDeleteResponseDto;
import com.datastreams.gpt.file.service.SessionFileDeleteService;
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
@RequestMapping("/api/file/v1/session")
@Tag(name = "세션 파일 삭제 API", description = "세션 파일 삭제 관련 API")
public class SessionFileDeleteController {

    private static final Logger logger = LoggerFactory.getLogger(SessionFileDeleteController.class);

    @Autowired
    private SessionFileDeleteService sessionFileDeleteService;

    @PostMapping("/{cnvsIdtId}")
    @Operation(
            summary = "L-019: Session File Delete",
            description = "FastAPI에서 지정된 세션의 모든 파일을 삭제합니다."
    )
    @ApiResponses(value = {
            @ApiResponse(
                    responseCode = "200",
                    description = "세션 파일 삭제 성공",
                    content = @Content(mediaType = "application/json", schema = @Schema(implementation = SessionFileDeleteResponseDto.class))
            ),
            @ApiResponse(
                    responseCode = "400",
                    description = "필수 파라미터 누락 또는 잘못된 대화 식별 아이디",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"대화 식별 아이디는 필수입니다.\"}"))
            ),
            @ApiResponse(
                    responseCode = "404",
                    description = "세션을 찾을 수 없음",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"해당 세션을 찾을 수 없습니다.\"}"))
            ),
            @ApiResponse(
                    responseCode = "500",
                    description = "서버 오류",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"세션 파일 삭제 중 오류가 발생했습니다.\"}"))
            )
    })
    public ResponseEntity<?> deleteSessionFiles(
            @Parameter(description = "대화 식별 아이디", example = "USR_ID_20231026103000123456", required = true)
            @PathVariable("cnvsIdtId") String cnvsIdtId) {
        
        try {
            logger.info("L-019 세션 파일 삭제 API 호출 - cnvsIdtId: {}", cnvsIdtId);
            
            // 요청 DTO 생성
            SessionFileDeleteRequestDto requestDto = new SessionFileDeleteRequestDto();
            requestDto.setCnvsIdtId(cnvsIdtId);
            
            // 세션 파일 삭제 처리
            SessionFileDeleteResponseDto responseDto = sessionFileDeleteService.deleteSessionFiles(requestDto);
            
            logger.info("L-019 세션 파일 삭제 성공 - cnvsIdtId: {}, deletedCount: {}", 
                       cnvsIdtId, responseDto.getDeletedFileCount());
            
            return ResponseEntity.ok(responseDto);
            
        } catch (IllegalArgumentException e) {
            logger.warn("L-019 세션 파일 삭제 실패: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            if (e.getMessage().contains("찾을 수 없습니다") || e.getMessage().contains("not found")) {
                logger.warn("L-019 세션 파일 삭제 실패: {}", e.getMessage());
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", "해당 세션을 찾을 수 없습니다."));
            } else {
                logger.error("L-019 세션 파일 삭제 중 오류 발생: {}", e.getMessage(), e);
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", "세션 파일 삭제 중 오류가 발생했습니다."));
            }
        }
    }

    @PostMapping("/{cnvsIdtId}/confirmation")
    @Operation(
            summary = "세션 파일 삭제 확인",
            description = "세션 파일 삭제를 확인하고 상세 정보를 반환합니다."
    )
    @ApiResponses(value = {
            @ApiResponse(
                    responseCode = "200",
                    description = "세션 파일 삭제 확인 성공",
                    content = @Content(mediaType = "application/json", schema = @Schema(implementation = SessionFileDeleteResponseDto.class))
            ),
            @ApiResponse(
                    responseCode = "400",
                    description = "잘못된 대화 식별 아이디",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"대화 식별 아이디는 필수입니다.\"}"))
            )
    })
    public ResponseEntity<?> confirmSessionFileDelete(
            @Parameter(description = "대화 식별 아이디", example = "USR_ID_20231026103000123456", required = true)
            @PathVariable("cnvsIdtId") String cnvsIdtId) {
        
        try {
            logger.info("세션 파일 삭제 확인 API 호출 - cnvsIdtId: {}", cnvsIdtId);
            
            // 요청 DTO 생성
            SessionFileDeleteRequestDto requestDto = new SessionFileDeleteRequestDto();
            requestDto.setCnvsIdtId(cnvsIdtId);
            
            // 세션 파일 삭제 처리
            SessionFileDeleteResponseDto responseDto = sessionFileDeleteService.deleteSessionFiles(requestDto);
            
            // 확인 응답 생성
            Map<String, Object> confirmResponse = Map.of(
                "cnvsIdtId", responseDto.getCnvsIdtId(),
                "status", responseDto.getStatus(),
                "deletedFileCount", responseDto.getDeletedFileCount(),
                "deletedAt", responseDto.getDeletedAt(),
                "processingTime", responseDto.getProcessingTime(),
                "confirmed", true
            );
            
            logger.info("세션 파일 삭제 확인 성공 - cnvsIdtId: {}, deletedCount: {}", 
                       cnvsIdtId, responseDto.getDeletedFileCount());
            
            return ResponseEntity.ok(confirmResponse);
            
        } catch (IllegalArgumentException e) {
            logger.warn("세션 파일 삭제 확인 실패: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            logger.error("세션 파일 삭제 확인 중 오류 발생: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", "세션 파일 삭제 확인 중 오류가 발생했습니다."));
        }
    }

    @GetMapping("/{cnvsIdtId}/health")
    @Operation(
            summary = "L-019 관련: FastAPI 헬스체크",
            description = "FastAPI 서버의 상태를 확인합니다."
    )
    @ApiResponses(value = {
            @ApiResponse(
                    responseCode = "200",
                    description = "FastAPI 서버 정상",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"status\": \"UP\"}"))
            ),
            @ApiResponse(
                    responseCode = "503",
                    description = "FastAPI 서버 비정상",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"status\": \"DOWN\", \"error\": \"FastAPI 서버에 연결할 수 없습니다.\"}"))
            )
    })
    public ResponseEntity<?> checkFastApiHealth(
            @Parameter(description = "대화 식별 아이디 (경로 변수이지만 실제 헬스체크 로직에서는 사용되지 않음)", required = true, example = "anyCnvsIdtId")
            @PathVariable("cnvsIdtId") String cnvsIdtId) {
        
        if (sessionFileDeleteService.checkFastApiHealth()) {
            return ResponseEntity.ok(Map.of("status", "UP"));
        } else {
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(Map.of("status", "DOWN", "error", "FastAPI 서버에 연결할 수 없습니다."));
        }
    }
}
