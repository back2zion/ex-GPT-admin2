package com.datastreams.gpt.chat.controller;

import com.datastreams.gpt.chat.dto.AnswerSaveRequestDto;
import com.datastreams.gpt.chat.dto.AnswerSaveResponseDto;
import com.datastreams.gpt.chat.service.AnswerSaveService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/chat/answers")
@Tag(name = "답변 저장 API", description = "답변 저장 관련 API")
public class AnswerSaveController {

    private static final Logger logger = LoggerFactory.getLogger(AnswerSaveController.class);

    @Autowired
    private AnswerSaveService answerSaveService;

    @PostMapping("")
    @Operation(
            summary = "L-034: 답변 저장",
            description = "AI 응답을 받아서 3개 테이블(USR_CNVS, USR_CNVS_REF_DOC_LST, USR_CNVS_ADD_QUES_LST)에 저장합니다."
    )
    @ApiResponse(
            responseCode = "200",
            description = "답변 저장 성공",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = AnswerSaveResponseDto.class))
    )
    @ApiResponse(
            responseCode = "400",
            description = "필수 파라미터 누락 또는 잘못된 값",
            content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"대화 식별 아이디는 필수입니다.\"}"))
    )
    @ApiResponse(
            responseCode = "500",
            description = "서버 오류",
            content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"답변 저장 중 오류가 발생했습니다.\"}"))
    )
    public ResponseEntity<?> saveAnswer(
            @Parameter(description = "답변 저장 요청 데이터", required = true)
            @RequestBody AnswerSaveRequestDto requestDto) {
        try {
            List<AnswerSaveResponseDto> responseList = answerSaveService.saveAnswer(requestDto);
            return ResponseEntity.ok(responseList);
        } catch (IllegalArgumentException e) {
            logger.warn("답변 저장 실패: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            logger.error("답변 저장 중 오류 발생: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", "답변 저장 중 오류가 발생했습니다."));
        }
    }
}
