package com.datastreams.gpt.error.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.datastreams.gpt.error.dto.ErrorChoiceListRequestDto;
import com.datastreams.gpt.error.dto.ErrorChoiceListResponseDto;
import com.datastreams.gpt.error.service.ErrorChoiceListService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;

/**
 * L-022: 오류 선택지 목록 조회 Controller
 * 공통코드 레벨2 조회 REST API 엔드포인트
 */
@RestController
@RequestMapping("/api/error/v1")
@Tag(name = "Error Choice List", description = "오류 선택지 목록 조회 API")
public class ErrorChoiceListController {
    
    private static final Logger logger = LoggerFactory.getLogger(ErrorChoiceListController.class);
    
    @Autowired
    private ErrorChoiceListService errorChoiceListService;
    
    /**
     * L-022: 오류 선택지 목록 조회
     * @param levelN1Cd 레벨1 코드 (ERR_RPT_CD)
     * @return 오류 선택지 목록
     */
    @GetMapping("/choiceList/{levelN1Cd}")
    @Operation(
        summary = "L-022: 오류 선택지 목록 조회",
        description = "공통코드 레벨2를 조회하여 오류 선택지 목록을 반환합니다."
    )
    @ApiResponses(value = {
        @ApiResponse(
            responseCode = "200",
            description = "조회 성공",
            content = @Content(
                mediaType = "application/json",
                schema = @Schema(implementation = ErrorChoiceListResponseDto.class)
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
    public ResponseEntity<ErrorChoiceListResponseDto> getErrorChoiceList(
            @Parameter(description = "레벨1 코드 (ERR_RPT_CD)", required = true)
            @PathVariable("levelN1Cd") String levelN1Cd) {
        
        try {
            logger.info("L-022: 오류 선택지 목록 조회 요청 - 레벨1코드: {}", levelN1Cd);
            
            // 요청 DTO 생성
            ErrorChoiceListRequestDto requestDto = new ErrorChoiceListRequestDto(levelN1Cd);
            
            // 서비스 호출
            ErrorChoiceListResponseDto responseDto = errorChoiceListService.getErrorChoiceList(requestDto);
            
            // 응답 상태 확인
            if ("success".equals(responseDto.getStatus())) {
                logger.info("L-022: 오류 선택지 목록 조회 성공 - 레벨1코드: {}, 조회건수: {}", 
                           levelN1Cd, responseDto.getTotalCount());
                return ResponseEntity.ok(responseDto);
            } else {
                logger.error("L-022: 오류 선택지 목록 조회 실패 - 레벨1코드: {}", levelN1Cd);
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(responseDto);
            }
            
        } catch (IllegalArgumentException e) {
            logger.error("L-022: 잘못된 요청 - 레벨1코드: {}, 오류: {}", levelN1Cd, e.getMessage());
            
            ErrorChoiceListResponseDto errorResponse = new ErrorChoiceListResponseDto();
            errorResponse.setLevelN1Cd(levelN1Cd);
            errorResponse.setStatus("error");
            errorResponse.setProcessingTime(0L);
            
            return ResponseEntity.badRequest().body(errorResponse);
            
        } catch (Exception e) {
            logger.error("L-022: 서버 내부 오류 - 레벨1코드: {}", levelN1Cd, e);
            
            ErrorChoiceListResponseDto errorResponse = new ErrorChoiceListResponseDto();
            errorResponse.setLevelN1Cd(levelN1Cd);
            errorResponse.setStatus("error");
            errorResponse.setProcessingTime(0L);
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }
}
