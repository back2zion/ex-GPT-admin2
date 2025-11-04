package com.datastreams.gpt.chat.controller;

import com.datastreams.gpt.chat.dto.QuerySaveRequestDto;
import com.datastreams.gpt.chat.dto.QuerySaveResponseDto;
import com.datastreams.gpt.chat.service.QuerySaveService;
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

import java.util.Map;

@RestController
@RequestMapping("/api/chat/queries")
@Tag(name = "질의 저장 API", description = "질의 저장 관련 API")
public class QuerySaveController {

    private static final Logger logger = LoggerFactory.getLogger(QuerySaveController.class);

    @Autowired
    private QuerySaveService querySaveService;

    @PostMapping("")
    @Operation(
            summary = "L-033: 질의 저장",
            description = "사용자의 질의를 데이터베이스에 저장하고, 첫 대화 시 대화 식별 ID를 생성합니다."
    )
    @ApiResponse(
            responseCode = "200",
            description = "질의 저장 성공",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = QuerySaveResponseDto.class))
    )
    @ApiResponse(
            responseCode = "400",
            description = "필수 파라미터 누락 또는 잘못된 값",
            content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"질의 텍스트는 필수입니다.\"}"))
    )
    @ApiResponse(
            responseCode = "500",
            description = "서버 오류",
            content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"error\": \"질의 저장 중 오류가 발생했습니다.\"}"))
    )
    public ResponseEntity<?> saveQuery(
            @Parameter(description = "질의 저장 요청 데이터", required = true)
            @RequestBody QuerySaveRequestDto requestDto) {
        try {
            QuerySaveResponseDto response = querySaveService.saveQuery(requestDto);
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            logger.warn("질의 저장 실패: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            logger.error("질의 저장 중 오류 발생: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", "질의 저장 중 오류가 발생했습니다."));
        }
    }
}
