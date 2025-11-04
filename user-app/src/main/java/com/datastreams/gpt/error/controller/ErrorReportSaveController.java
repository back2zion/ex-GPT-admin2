package com.datastreams.gpt.error.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.datastreams.gpt.error.dto.ErrorReportSaveRequestDto;
import com.datastreams.gpt.error.dto.ErrorReportSaveResponseDto;
import com.datastreams.gpt.error.service.ErrorReportSaveService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;

/**
 * L-023: 오류 보고/오류 선택지 목록 저장 Controller
 * 오류 보고 및 선택된 오류 코드들을 저장하는 REST API 엔드포인트
 */
@RestController
@RequestMapping("/api/error/v1")
@Tag(name = "Error Report Save", description = "오류 보고/오류 선택지 목록 저장 API")
public class ErrorReportSaveController {
    
    private static final Logger logger = LoggerFactory.getLogger(ErrorReportSaveController.class);
    
    @Autowired
    private ErrorReportSaveService errorReportSaveService;
    
    /**
     * L-023: 오류 보고/오류 선택지 목록 저장
     * @param requestDto 요청 데이터
     * @return 저장 결과
     */
    @PostMapping("/errorReport")
    @Operation(
        summary = "L-023: 오류 보고/오류 선택지 목록 저장",
        description = "오류 보고 텍스트와 선택된 오류 코드들을 저장합니다."
    )
    @ApiResponses(value = {
        @ApiResponse(
            responseCode = "200",
            description = "저장 성공",
            content = @Content(
                mediaType = "application/json",
                schema = @Schema(implementation = ErrorReportSaveResponseDto.class)
            )
        ),
        @ApiResponse(
            responseCode = "400",
            description = "잘못된 요청",
            content = @Content(mediaType = "application/json")
        ),
        @ApiResponse(
            responseCode = "500",
            description = "서버 내부 오류",
            content = @Content(mediaType = "application/json")
        )
    })
    public ResponseEntity<ErrorReportSaveResponseDto> saveErrorReport(
            @RequestBody ErrorReportSaveRequestDto requestDto) {
        
        try {
            logger.info("L-023: 오류 보고 저장 요청 - 대화ID: {}, 사용자ID: {}", 
                       requestDto.getCnvsId(), requestDto.getUsrId());
            
            // 서비스 호출
            ErrorReportSaveResponseDto responseDto = errorReportSaveService.saveErrorReport(requestDto);
            
            // 응답 상태 확인
            if ("success".equals(responseDto.getStatus())) {
                logger.info("L-023: 오류 보고 저장 성공 - 대화ID: {}, 사용자ID: {}, 저장건수: {}", 
                           requestDto.getCnvsId(), requestDto.getUsrId(), responseDto.getCnt());
                return ResponseEntity.ok(responseDto);
            } else {
                logger.error("L-023: 오류 보고 저장 실패 - 대화ID: {}, 사용자ID: {}", 
                           requestDto.getCnvsId(), requestDto.getUsrId());
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(responseDto);
            }
            
        } catch (IllegalArgumentException e) {
            logger.error("L-023: 잘못된 요청 - 대화ID: {}, 사용자ID: {}, 오류: {}", 
                        requestDto.getCnvsId(), requestDto.getUsrId(), e.getMessage());
            
            ErrorReportSaveResponseDto errorResponse = new ErrorReportSaveResponseDto();
            errorResponse.setCnvsId(requestDto.getCnvsId());
            errorResponse.setUsrId(requestDto.getUsrId());
            errorResponse.setTxnNm("SAVE_ERROR_REPORT");
            errorResponse.setCnt(0);
            errorResponse.setStatus("error");
            errorResponse.setProcessingTime(0L);
            
            return ResponseEntity.badRequest().body(errorResponse);
            
        } catch (Exception e) {
            logger.error("L-023: 서버 내부 오류 - 대화ID: {}, 사용자ID: {}", 
                        requestDto.getCnvsId(), requestDto.getUsrId(), e);
            
            ErrorReportSaveResponseDto errorResponse = new ErrorReportSaveResponseDto();
            errorResponse.setCnvsId(requestDto.getCnvsId());
            errorResponse.setUsrId(requestDto.getUsrId());
            errorResponse.setTxnNm("SAVE_ERROR_REPORT");
            errorResponse.setCnt(0);
            errorResponse.setStatus("error");
            errorResponse.setProcessingTime(0L);
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }
}
