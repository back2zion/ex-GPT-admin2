package com.datastreams.gpt.file.controller;

import com.datastreams.gpt.file.dto.FileUploadHistoryUpdateRequestDto;
import com.datastreams.gpt.file.dto.FileUploadHistoryUpdateResponseDto;
import com.datastreams.gpt.file.service.FileUploadHistoryUpdateService;
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
@Tag(name = "파일 업로드 이력 갱신 API", description = "파일 업로드 이력 갱신 관련 API")
public class FileUploadHistoryUpdateController {

    private static final Logger logger = LoggerFactory.getLogger(FileUploadHistoryUpdateController.class);

    @Autowired
    private FileUploadHistoryUpdateService fileUploadHistoryUpdateService;

    @PostMapping("/upload-histories/{fileUpldSeq}")
    @Operation(
            summary = "L-018: 파일 업로드 이력 갱신",
            description = "L-017에서 업로드한 파일의 상태를 DB에 갱신하고 로그를 기록합니다."
    )
    @ApiResponses(value = {
            @ApiResponse(
                    responseCode = "200",
                    description = "파일 업로드 이력 갱신 성공",
                    content = @Content(mediaType = "application/json", schema = @Schema(implementation = FileUploadHistoryUpdateResponseDto.class))
            ),
            @ApiResponse(
                    responseCode = "400",
                    description = "필수 파라미터 누락 또는 잘못된 값",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"파일 업로드 순번은 필수입니다.\"}"))
            ),
            @ApiResponse(
                    responseCode = "404",
                    description = "파일 업로드 이력을 찾을 수 없음",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"해당 파일 업로드 순번이 존재하지 않습니다.\"}"))
            ),
            @ApiResponse(
                    responseCode = "500",
                    description = "서버 오류",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"파일 업로드 이력 갱신 중 오류가 발생했습니다.\"}"))
            )
    })
    public ResponseEntity<?> updateFileUploadHistory(
            @Parameter(description = "파일 업로드 순번", example = "1", required = true)
            @PathVariable("fileUpldSeq") Long fileUpldSeq,
            
            @Parameter(description = "파일 업로드 이력 갱신 요청 데이터", required = true)
            @RequestBody FileUploadHistoryUpdateRequestDto requestDto) {
        
        try {
            logger.info("L-018 파일 업로드 이력 갱신 API 호출 - 파일 업로드 순번: {}", fileUpldSeq);
            
            // Path Variable과 Request Body의 fileUpldSeq 일치 확인
            if (!fileUpldSeq.equals(requestDto.getFileUpldSeq())) {
                logger.warn("L-018 파일 업로드 이력 갱신 실패: Path Variable과 Request Body의 fileUpldSeq가 일치하지 않습니다. Path: {}, Body: {}", 
                           fileUpldSeq, requestDto.getFileUpldSeq());
                return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                        .body(Map.of("error", "Path Variable과 Request Body의 fileUpldSeq가 일치하지 않습니다."));
            }
            
            // 파일 업로드 이력 갱신 처리
            FileUploadHistoryUpdateResponseDto responseDto = fileUploadHistoryUpdateService.updateFileUploadHistory(requestDto);
            
            logger.info("L-018 파일 업로드 이력 갱신 성공 - 파일 업로드 순번: {}, 실행 건수: {}", 
                       fileUpldSeq, responseDto.getCnt());
            
            return ResponseEntity.ok(responseDto);
            
        } catch (IllegalArgumentException e) {
            logger.warn("L-018 파일 업로드 이력 갱신 실패: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        } catch (RuntimeException e) {
            if (e.getMessage().contains("존재하지 않습니다")) {
                logger.warn("L-018 파일 업로드 이력 갱신 실패: {}", e.getMessage());
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", e.getMessage()));
            } else {
                logger.error("L-018 파일 업로드 이력 갱신 중 오류 발생: {}", e.getMessage(), e);
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", "파일 업로드 이력 갱신 중 오류가 발생했습니다."));
            }
        } catch (Exception e) {
            logger.error("L-018 파일 업로드 이력 갱신 중 예상치 못한 오류 발생: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", "파일 업로드 이력 갱신 중 오류가 발생했습니다."));
        }
    }

    @GetMapping("/upload-histories/{fileUpldSeq}/existence")
    @Operation(
            summary = "파일 업로드 이력 존재 여부 확인",
            description = "지정된 파일 업로드 순번의 이력이 존재하는지 확인합니다."
    )
    @ApiResponses(value = {
            @ApiResponse(
                    responseCode = "200",
                    description = "존재 여부 확인 성공",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"fileUpldSeq\": 1, \"exists\": true}"))
            ),
            @ApiResponse(
                    responseCode = "400",
                    description = "잘못된 파일 업로드 순번",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"파일 업로드 순번은 필수입니다.\"}"))
            )
    })
    public ResponseEntity<?> checkFileUploadHistoryExists(
            @Parameter(description = "파일 업로드 순번", example = "1", required = true)
            @PathVariable("fileUpldSeq") Long fileUpldSeq) {
        
        try {
            logger.info("파일 업로드 이력 존재 여부 확인 API 호출 - 파일 업로드 순번: {}", fileUpldSeq);
            
            if (fileUpldSeq == null || fileUpldSeq <= 0) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                        .body(Map.of("error", "파일 업로드 순번은 필수이며 0보다 커야 합니다."));
            }
            
            boolean exists = fileUploadHistoryUpdateService.existsFileUploadHistory(fileUpldSeq);
            
            logger.info("파일 업로드 이력 존재 여부 확인 완료 - 파일 업로드 순번: {}, 존재: {}", fileUpldSeq, exists);
            
            return ResponseEntity.ok(Map.of(
                "fileUpldSeq", fileUpldSeq,
                "exists", exists
            ));
            
        } catch (Exception e) {
            logger.error("파일 업로드 이력 존재 여부 확인 중 오류 발생: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", "파일 업로드 이력 존재 여부 확인 중 오류가 발생했습니다."));
        }
    }
}
