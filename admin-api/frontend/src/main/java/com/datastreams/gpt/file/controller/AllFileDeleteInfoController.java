package com.datastreams.gpt.file.controller;

import com.datastreams.gpt.file.dto.AllFileDeleteInfoRequestDto;
import com.datastreams.gpt.file.dto.AllFileDeleteInfoResponseDto;
import com.datastreams.gpt.file.service.AllFileDeleteInfoService;
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
@RequestMapping("/api/file")
@Tag(name = "전체 파일 삭제 정보 API", description = "전체 파일 삭제 정보 갱신 관련 API")
public class AllFileDeleteInfoController {

    private static final Logger logger = LoggerFactory.getLogger(AllFileDeleteInfoController.class);

    @Autowired
    private AllFileDeleteInfoService allFileDeleteInfoService;

    @PostMapping("/v1/session/{cnvsIdtId}/deletion-status")
    @Operation(
            summary = "L-021: 전체 파일 삭제 정보 갱신",
            description = "특정 세션의 모든 파일 삭제 상태를 DB에 업데이트합니다."
    )
    @ApiResponses(value = {
            @ApiResponse(
                    responseCode = "200",
                    description = "전체 파일 삭제 정보 갱신 성공",
                    content = @Content(mediaType = "application/json", schema = @Schema(implementation = AllFileDeleteInfoResponseDto.class))
            ),
            @ApiResponse(
                    responseCode = "400",
                    description = "필수 파라미터 누락 또는 잘못된 파라미터",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"대화 식별 아이디는 필수입니다.\"}"))
            ),
            @ApiResponse(
                    responseCode = "404",
                    description = "해당 세션에 파일이 없음",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"해당 세션에 파일이 없습니다.\"}"))
            ),
            @ApiResponse(
                    responseCode = "500",
                    description = "서버 오류",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"전체 파일 삭제 정보 갱신 중 오류가 발생했습니다.\"}"))
            )
    })
    public ResponseEntity<?> updateAllFileDeleteInfo(
            @Parameter(description = "대화 식별 아이디", example = "USR_ID_20231026103000123456", required = true)
            @PathVariable("cnvsIdtId") String cnvsIdtId,
            
            @Parameter(description = "전체 파일 삭제 정보 갱신 요청 데이터", required = true)
            @RequestBody AllFileDeleteInfoRequestDto requestDto) {
        
        try {
            logger.info("L-021 전체 파일 삭제 정보 갱신 API 호출 - cnvsIdtId: {}", cnvsIdtId);
            
            // Path Variable을 Request Body에 설정
            requestDto.setCnvsIdtId(cnvsIdtId);
            
            // 전체 파일 삭제 정보 갱신 처리
            AllFileDeleteInfoResponseDto responseDto = allFileDeleteInfoService.updateAllFileDeleteInfo(requestDto);
            
            logger.info("L-021 전체 파일 삭제 정보 갱신 성공 - cnvsIdtId: {}, updatedCount: {}, processingTime: {}ms", 
                       cnvsIdtId, responseDto.getCnt(), responseDto.getProcessingTime());
            
            return ResponseEntity.ok(responseDto);
            
        } catch (IllegalArgumentException e) {
            logger.warn("L-021 전체 파일 삭제 정보 갱신 실패: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            if (e.getMessage().contains("해당 세션에 파일이 없습니다")) {
                logger.warn("L-021 전체 파일 삭제 정보 갱신 실패: {}", e.getMessage());
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", e.getMessage()));
            } else {
                logger.error("L-021 전체 파일 삭제 정보 갱신 중 오류 발생: {}", e.getMessage(), e);
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", "전체 파일 삭제 정보 갱신 중 오류가 발생했습니다."));
            }
        }
    }

    @GetMapping("/v1/session/{cnvsIdtId}/fileCount")
    @Operation(
            summary = "L-021 관련: 세션별 파일 개수 조회",
            description = "특정 세션에 속한 파일 개수를 조회합니다."
    )
    @ApiResponses(value = {
            @ApiResponse(
                    responseCode = "200",
                    description = "세션별 파일 개수 조회 성공",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"cnvsIdtId\": \"USR_ID_20231026103000123456\", \"fileCount\": 3}"))
            ),
            @ApiResponse(
                    responseCode = "400",
                    description = "잘못된 파라미터",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"대화 식별 아이디는 필수입니다.\"}"))
            )
    })
    public ResponseEntity<?> getFileCountBySession(
            @Parameter(description = "대화 식별 아이디", example = "USR_ID_20231026103000123456", required = true)
            @PathVariable("cnvsIdtId") String cnvsIdtId) {
        
        try {
            logger.info("L-021 세션별 파일 개수 조회 API 호출 - cnvsIdtId: {}", cnvsIdtId);
            
            Integer fileCount = allFileDeleteInfoService.getFileCountBySession(cnvsIdtId);
            
            logger.info("L-021 세션별 파일 개수 조회 성공 - cnvsIdtId: {}, fileCount: {}", cnvsIdtId, fileCount);
            
            return ResponseEntity.ok(Map.of(
                "cnvsIdtId", cnvsIdtId,
                "fileCount", fileCount
            ));
            
        } catch (IllegalArgumentException e) {
            logger.warn("L-021 세션별 파일 개수 조회 실패: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            logger.error("L-021 세션별 파일 개수 조회 중 오류 발생: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", "세션별 파일 개수 조회 중 오류가 발생했습니다."));
        }
    }

    @GetMapping("/v1/session/{cnvsIdtId}/deletedFileCount")
    @Operation(
            summary = "L-021 관련: 세션별 삭제된 파일 개수 조회",
            description = "특정 세션에서 삭제된 파일 개수를 조회합니다."
    )
    @ApiResponses(value = {
            @ApiResponse(
                    responseCode = "200",
                    description = "세션별 삭제된 파일 개수 조회 성공",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"cnvsIdtId\": \"USR_ID_20231026103000123456\", \"deletedFileCount\": 2}"))
            ),
            @ApiResponse(
                    responseCode = "400",
                    description = "잘못된 파라미터",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"대화 식별 아이디는 필수입니다.\"}"))
            )
    })
    public ResponseEntity<?> getDeletedFileCountBySession(
            @Parameter(description = "대화 식별 아이디", example = "USR_ID_20231026103000123456", required = true)
            @PathVariable("cnvsIdtId") String cnvsIdtId) {
        
        try {
            logger.info("L-021 세션별 삭제된 파일 개수 조회 API 호출 - cnvsIdtId: {}", cnvsIdtId);
            
            Integer deletedFileCount = allFileDeleteInfoService.getDeletedFileCountBySession(cnvsIdtId);
            
            logger.info("L-021 세션별 삭제된 파일 개수 조회 성공 - cnvsIdtId: {}, deletedFileCount: {}", cnvsIdtId, deletedFileCount);
            
            return ResponseEntity.ok(Map.of(
                "cnvsIdtId", cnvsIdtId,
                "deletedFileCount", deletedFileCount
            ));
            
        } catch (IllegalArgumentException e) {
            logger.warn("L-021 세션별 삭제된 파일 개수 조회 실패: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            logger.error("L-021 세션별 삭제된 파일 개수 조회 중 오류 발생: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", "세션별 삭제된 파일 개수 조회 중 오류가 발생했습니다."));
        }
    }
}
