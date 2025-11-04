package com.datastreams.gpt.file.controller;

import com.datastreams.gpt.file.dto.SingleFileDeleteInfoRequestDto;
import com.datastreams.gpt.file.dto.SingleFileDeleteInfoResponseDto;
import com.datastreams.gpt.file.service.SingleFileDeleteInfoService;
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
@Tag(name = "단일 파일 삭제 정보 API", description = "단일 파일 삭제 정보 갱신 관련 API")
public class SingleFileDeleteInfoController {

    private static final Logger logger = LoggerFactory.getLogger(SingleFileDeleteInfoController.class);

    @Autowired
    private SingleFileDeleteInfoService singleFileDeleteInfoService;

    @PostMapping("/v1/session/{cnvsIdtId}/files/{fileUid}/deletion-status")
    @Operation(
            summary = "L-039: 단일 파일 삭제 정보 갱신",
            description = "특정 세션의 특정 파일 삭제 상태를 DB에 업데이트합니다."
    )
    @ApiResponses(value = {
            @ApiResponse(
                    responseCode = "200",
                    description = "단일 파일 삭제 정보 갱신 성공",
                    content = @Content(mediaType = "application/json", schema = @Schema(implementation = SingleFileDeleteInfoResponseDto.class))
            ),
            @ApiResponse(
                    responseCode = "400",
                    description = "필수 파라미터 누락 또는 잘못된 파라미터",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"대화 식별 아이디는 필수입니다.\"}"))
            ),
            @ApiResponse(
                    responseCode = "404",
                    description = "해당 파일이 존재하지 않음",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"해당 파일이 존재하지 않습니다.\"}"))
            ),
            @ApiResponse(
                    responseCode = "500",
                    description = "서버 오류",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"단일 파일 삭제 정보 갱신 중 오류가 발생했습니다.\"}"))
            )
    })
    public ResponseEntity<?> updateSingleFileDeleteInfo(
            @Parameter(description = "대화 식별 아이디", example = "USR_ID_20231026103000123456", required = true)
            @PathVariable("cnvsIdtId") String cnvsIdtId,
            
            @Parameter(description = "파일 아이디", example = "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34", required = true)
            @PathVariable("fileUid") String fileUid,
            
            @Parameter(description = "단일 파일 삭제 정보 갱신 요청 데이터", required = true)
            @RequestBody SingleFileDeleteInfoRequestDto requestDto) {
        
        try {
            logger.info("L-039 단일 파일 삭제 정보 갱신 API 호출 - cnvsIdtId: {}, fileUid: {}", cnvsIdtId, fileUid);
            
            // Path Variable을 Request Body에 설정
            requestDto.setCnvsIdtId(cnvsIdtId);
            requestDto.setFileUid(fileUid);
            
            // 단일 파일 삭제 정보 갱신 처리
            SingleFileDeleteInfoResponseDto responseDto = singleFileDeleteInfoService.updateSingleFileDeleteInfo(requestDto);
            
            logger.info("L-039 단일 파일 삭제 정보 갱신 성공 - cnvsIdtId: {}, fileUid: {}, updatedCount: {}, processingTime: {}ms", 
                       cnvsIdtId, fileUid, responseDto.getCnt(), responseDto.getProcessingTime());
            
            return ResponseEntity.ok(responseDto);
            
        } catch (IllegalArgumentException e) {
            logger.warn("L-039 단일 파일 삭제 정보 갱신 실패: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            if (e.getMessage().contains("해당 파일이 존재하지 않습니다")) {
                logger.warn("L-039 단일 파일 삭제 정보 갱신 실패: {}", e.getMessage());
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", e.getMessage()));
            } else {
                logger.error("L-039 단일 파일 삭제 정보 갱신 중 오류 발생: {}", e.getMessage(), e);
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", "단일 파일 삭제 정보 갱신 중 오류가 발생했습니다."));
            }
        }
    }

    @GetMapping("/v1/session/{cnvsIdtId}/files/{fileUid}/existence")
    @Operation(
            summary = "L-039 관련: 특정 파일 존재 여부 조회",
            description = "특정 세션의 특정 파일이 존재하는지 조회합니다."
    )
    @ApiResponses(value = {
            @ApiResponse(
                    responseCode = "200",
                    description = "특정 파일 존재 여부 조회 성공",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"cnvsIdtId\": \"USR_ID_20231026103000123456\", \"fileUid\": \"tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34\", \"exists\": true}"))
            ),
            @ApiResponse(
                    responseCode = "400",
                    description = "잘못된 파라미터",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"대화 식별 아이디는 필수입니다.\"}"))
            )
    })
    public ResponseEntity<?> checkFileExists(
            @Parameter(description = "대화 식별 아이디", example = "USR_ID_20231026103000123456", required = true)
            @PathVariable("cnvsIdtId") String cnvsIdtId,
            
            @Parameter(description = "파일 아이디", example = "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34", required = true)
            @PathVariable("fileUid") String fileUid) {
        
        try {
            logger.info("L-039 특정 파일 존재 여부 조회 API 호출 - cnvsIdtId: {}, fileUid: {}", cnvsIdtId, fileUid);
            
            boolean exists = singleFileDeleteInfoService.checkFileExists(cnvsIdtId, fileUid);
            
            logger.info("L-039 특정 파일 존재 여부 조회 성공 - cnvsIdtId: {}, fileUid: {}, exists: {}", cnvsIdtId, fileUid, exists);
            
            return ResponseEntity.ok(Map.of(
                "cnvsIdtId", cnvsIdtId,
                "fileUid", fileUid,
                "exists", exists
            ));
            
        } catch (IllegalArgumentException e) {
            logger.warn("L-039 특정 파일 존재 여부 조회 실패: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            logger.error("L-039 특정 파일 존재 여부 조회 중 오류 발생: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", "특정 파일 존재 여부 조회 중 오류가 발생했습니다."));
        }
    }

    @GetMapping("/v1/session/{cnvsIdtId}/files/{fileUid}/deleteStatus")
    @Operation(
            summary = "L-039 관련: 특정 파일 삭제 상태 조회",
            description = "특정 세션의 특정 파일 삭제 상태를 조회합니다."
    )
    @ApiResponses(value = {
            @ApiResponse(
                    responseCode = "200",
                    description = "특정 파일 삭제 상태 조회 성공",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"cnvsIdtId\": \"USR_ID_20231026103000123456\", \"fileUid\": \"tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34\", \"deleteStatus\": \"Y\"}"))
            ),
            @ApiResponse(
                    responseCode = "400",
                    description = "잘못된 파라미터",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"대화 식별 아이디는 필수입니다.\"}"))
            )
    })
    public ResponseEntity<?> getFileDeleteStatus(
            @Parameter(description = "대화 식별 아이디", example = "USR_ID_20231026103000123456", required = true)
            @PathVariable("cnvsIdtId") String cnvsIdtId,
            
            @Parameter(description = "파일 아이디", example = "tmp-20251124-79c7ac0a-ff40-457f-9d8e-f97e13587a34", required = true)
            @PathVariable("fileUid") String fileUid) {
        
        try {
            logger.info("L-039 특정 파일 삭제 상태 조회 API 호출 - cnvsIdtId: {}, fileUid: {}", cnvsIdtId, fileUid);
            
            String deleteStatus = singleFileDeleteInfoService.getFileDeleteStatus(cnvsIdtId, fileUid);
            
            logger.info("L-039 특정 파일 삭제 상태 조회 성공 - cnvsIdtId: {}, fileUid: {}, deleteStatus: {}", cnvsIdtId, fileUid, deleteStatus);
            
            return ResponseEntity.ok(Map.of(
                "cnvsIdtId", cnvsIdtId,
                "fileUid", fileUid,
                "deleteStatus", deleteStatus
            ));
            
        } catch (IllegalArgumentException e) {
            logger.warn("L-039 특정 파일 삭제 상태 조회 실패: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            logger.error("L-039 특정 파일 삭제 상태 조회 중 오류 발생: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", "특정 파일 삭제 상태 조회 중 오류가 발생했습니다."));
        }
    }
}
