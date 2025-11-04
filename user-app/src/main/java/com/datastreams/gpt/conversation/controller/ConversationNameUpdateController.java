package com.datastreams.gpt.conversation.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.datastreams.gpt.conversation.dto.ConversationNameUpdateRequestDto;
import com.datastreams.gpt.conversation.dto.ConversationNameUpdateResponseDto;
import com.datastreams.gpt.conversation.service.ConversationNameUpdateService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;

/**
 * L-025: 대화 대표 명 변경 Controller
 * 대화 대표 명 및 사용 여부를 업데이트하는 REST API 엔드포인트
 */
@RestController
@RequestMapping("/api/conversation/v1")
@Tag(name = "대화 대표 명 변경 API", description = "대화 대표 명 변경 API")
public class ConversationNameUpdateController {
    
    private static final Logger logger = LoggerFactory.getLogger(ConversationNameUpdateController.class);
    
    @Autowired
    private ConversationNameUpdateService conversationNameUpdateService;
    
    /**
     * L-025: 대화 대표 명 변경
     * @param requestDto 요청 데이터
     * @return 업데이트 결과
     */
    @PostMapping("/name")
    @Operation(
        summary = "L-025: 대화 대표 명 변경",
        description = "대화 대표 명 및 사용 여부를 업데이트합니다."
    )
    @ApiResponses(value = {
        @ApiResponse(
            responseCode = "200",
            description = "업데이트 성공",
            content = @Content(
                mediaType = "application/json",
                schema = @Schema(implementation = ConversationNameUpdateResponseDto.class)
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
    public ResponseEntity<ConversationNameUpdateResponseDto> updateConversationName(
            @RequestBody ConversationNameUpdateRequestDto requestDto) {
        
        try {
            logger.info("L-025: 대화 대표 명 변경 요청 - 대화ID: {}", requestDto.getCnvsIdtId());
            
            // 서비스 호출
            ConversationNameUpdateResponseDto responseDto = conversationNameUpdateService.updateConversationName(requestDto);
            
            // 응답 상태 확인
            if ("success".equals(responseDto.getStatus())) {
                logger.info("L-025: 대화 대표 명 변경 성공 - 대화ID: {}, 업데이트건수: {}", 
                           requestDto.getCnvsIdtId(), responseDto.getCnt());
                return ResponseEntity.ok(responseDto);
            } else {
                logger.error("L-025: 대화 대표 명 변경 실패 - 대화ID: {}", requestDto.getCnvsIdtId());
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(responseDto);
            }
            
        } catch (IllegalArgumentException e) {
            logger.error("L-025: 잘못된 요청 - 대화ID: {}, 오류: {}", 
                        requestDto.getCnvsIdtId(), e.getMessage());
            
            ConversationNameUpdateResponseDto errorResponse = new ConversationNameUpdateResponseDto();
            errorResponse.setCnvsIdtId(requestDto.getCnvsIdtId());
            errorResponse.setTxnNm("UPD_USR_CNVS_SMRY");
            errorResponse.setCnt(0);
            errorResponse.setStatus("error");
            errorResponse.setProcessingTime(0L);
            
            return ResponseEntity.badRequest().body(errorResponse);
            
        } catch (Exception e) {
            logger.error("L-025: 서버 내부 오류 - 대화ID: {}", requestDto.getCnvsIdtId(), e);
            
            ConversationNameUpdateResponseDto errorResponse = new ConversationNameUpdateResponseDto();
            errorResponse.setCnvsIdtId(requestDto.getCnvsIdtId());
            errorResponse.setTxnNm("UPD_USR_CNVS_SMRY");
            errorResponse.setCnt(0);
            errorResponse.setStatus("error");
            errorResponse.setProcessingTime(0L);
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }
}
