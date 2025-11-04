package com.datastreams.gpt.file.controller;

import com.datastreams.gpt.file.dto.FileUploadHistoryCreateRequestDto;
import com.datastreams.gpt.file.dto.FileUploadHistoryCreateResponseDto;
import com.datastreams.gpt.file.service.FileUploadHistoryCreateService;
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
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/file")
@Tag(name = "파일 업로드 이력 생성 API", description = "파일 업로드 이력 관련 API")
public class FileUploadHistoryCreateController {

    private static final Logger logger = LoggerFactory.getLogger(FileUploadHistoryCreateController.class);

    @Autowired
    private FileUploadHistoryCreateService fileUploadHistoryCreateService;

    @PostMapping("/upload-histories-create")
    @Operation(
            summary = "L-016: 파일 업로드 이력 생성",
            description = "파일 업로드 시 대화 이력과 파일 관리 정보를 생성합니다."
    )
    @ApiResponses(value = {
            @ApiResponse(
                    responseCode = "200",
                    description = "파일 업로드 이력 생성 성공",
                    content = @Content(mediaType = "application/json", schema = @Schema(implementation = FileUploadHistoryCreateResponseDto.class))
            ),
            @ApiResponse(
                    responseCode = "400",
                    description = "필수 파라미터 누락 또는 잘못된 값",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"사용자 아이디는 필수입니다.\"}"))
            ),
            @ApiResponse(
                    responseCode = "500",
                    description = "서버 오류",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"파일 업로드 이력 생성 중 오류가 발생했습니다.\"}"))
            )
    })
    public ResponseEntity<?> createFileUploadHistoryRecord(
            @Parameter(description = "파일 업로드 이력 생성 요청 데이터", required = true)
            @RequestBody FileUploadHistoryCreateRequestDto requestDto) {
        
        try {
            logger.info("파일 업로드 이력 생성 API 호출 - 사용자: {}, 세션: {}", 
                       requestDto.getUsrId(), requestDto.getSesnId());
            
            FileUploadHistoryCreateResponseDto responseDto = fileUploadHistoryCreateService.createFileUploadHistory(requestDto);
            
            logger.info("파일 업로드 이력 생성 성공 - TXN: {}, CNVS_IDT_ID: {}", 
                       responseDto.getTxnNm(), responseDto.getCnvsIdtId());
            
            return ResponseEntity.ok(responseDto);
            
        } catch (IllegalArgumentException e) {
            logger.warn("파일 업로드 이력 생성 실패: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            logger.error("파일 업로드 이력 생성 중 오류 발생: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", "파일 업로드 이력 생성 중 오류가 발생했습니다."));
        }
    }
}
