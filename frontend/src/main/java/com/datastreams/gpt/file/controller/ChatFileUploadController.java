package com.datastreams.gpt.file.controller;

import com.datastreams.gpt.file.dto.SessionFileUploadRequestDto;
import com.datastreams.gpt.file.dto.SessionFileUploadResponseDto;
import com.datastreams.gpt.file.service.SessionFileUploadService;
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
import org.springframework.web.multipart.MultipartFile;

import jakarta.servlet.http.HttpSession;
import java.util.HashMap;
import java.util.Map;

/**
 * 채팅 파일 업로드 컨트롤러 - FastAPI 스타일 엔드포인트
 * 프론트엔드(layout.html)에서 사용하는 개인 사용자 파일 업로드 API
 */
@RestController
@RequestMapping("/api/v1/files")
@Tag(name = "채팅 파일 업로드 API", description = "개인 사용자 채팅 파일 업로드 (6개월 보관, room_id 기반)")
public class ChatFileUploadController {

    private static final Logger logger = LoggerFactory.getLogger(ChatFileUploadController.class);

    @Autowired
    private SessionFileUploadService sessionFileUploadService;

    /**
     * 채팅 파일 업로드 - FastAPI 스타일 엔드포인트
     * layout.html에서 호출하는 개인 사용자 파일 업로드
     *
     * NOTE: 이 엔드포인트는 개인 사용자의 채팅 첨부파일 업로드용입니다.
     *       관리자가 전역 벡터 DB에 업로드하는 것은 /api/v1/admin/vector-documents/upload 사용
     */
    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @Operation(
            summary = "채팅 파일 업로드",
            description = "개인 사용자의 채팅 첨부파일을 업로드합니다. (6개월 보관, room_id 기반 관리)"
    )
    @ApiResponses(value = {
            @ApiResponse(
                    responseCode = "200",
                    description = "파일 업로드 성공",
                    content = @Content(mediaType = "application/json", schema = @Schema(example = "{\"success\": true, \"file_uid\": \"tmp-20251124-xxx\", \"filename\": \"test.pdf\", \"size\": 1024, \"download_url\": \"http://...\" }"))
            ),
            @ApiResponse(
                    responseCode = "400",
                    description = "잘못된 요청",
                    content = @Content(mediaType = "application/json")
            ),
            @ApiResponse(
                    responseCode = "413",
                    description = "파일 크기 초과 (최대 200MB)",
                    content = @Content(mediaType = "application/json")
            ),
            @ApiResponse(
                    responseCode = "500",
                    description = "서버 오류",
                    content = @Content(mediaType = "application/json")
            )
    })
    public ResponseEntity<?> uploadChatFile(
            @Parameter(description = "업로드할 파일 (최대 200MB)", required = true)
            @RequestParam("file") MultipartFile file,

            @Parameter(description = "대화 식별자 (room_id 형식: {user_id}_{timestamp})", example = "user123_1761055118793", required = true)
            @RequestParam("room_id") String roomId,

            @Parameter(description = "동기 처리 여부", example = "true")
            @RequestParam(value = "wait", defaultValue = "true") boolean wait,

            HttpSession session) {

        try {
            logger.info("채팅 파일 업로드 API 호출 - room_id: {}, 파일: {}, 크기: {} bytes",
                       roomId, file.getOriginalFilename(), file.getSize());

            // 세션에서 userId 추출 (없으면 room_id의 앞부분 사용)
            String userId = extractUserIdFromSession(session, roomId);

            // 파일 크기 검증 (200MB)
            if (file.getSize() > 200 * 1024 * 1024) {
                logger.warn("파일 크기 초과 - 파일: {}, 크기: {} bytes", file.getOriginalFilename(), file.getSize());
                Map<String, Object> errorResponse = new HashMap<>();
                errorResponse.put("success", false);
                errorResponse.put("error", "파일 크기가 200MB를 초과합니다.");
                return ResponseEntity.status(HttpStatus.PAYLOAD_TOO_LARGE).body(errorResponse);
            }

            // 요청 DTO 생성
            SessionFileUploadRequestDto requestDto = new SessionFileUploadRequestDto();
            requestDto.setCnvsIdtId(roomId);  // room_id를 cnvsIdtId로 매핑
            requestDto.setFile(file);
            requestDto.setUserId(userId);
            requestDto.setWait(wait);

            // 세션 파일 업로드 처리 (FastAPI로 전달)
            SessionFileUploadResponseDto responseDto = sessionFileUploadService.uploadSessionFile(requestDto);

            // FastAPI 스타일 응답 생성
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("file_uid", responseDto.getFileUid());
            response.put("filename", responseDto.getFileName());
            response.put("size", responseDto.getFileSize());
            response.put("download_url", generateDownloadUrl(responseDto.getFileUid()));
            response.put("room_id", roomId);
            response.put("upload_time", System.currentTimeMillis());

            logger.info("채팅 파일 업로드 성공 - room_id: {}, file_uid: {}", roomId, responseDto.getFileUid());

            return ResponseEntity.ok(response);

        } catch (IllegalArgumentException e) {
            logger.warn("채팅 파일 업로드 실패 (잘못된 요청): {}", e.getMessage());
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("success", false);
            errorResponse.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse);

        } catch (Exception e) {
            logger.error("채팅 파일 업로드 중 오류 발생: {}", e.getMessage(), e);
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("success", false);
            errorResponse.put("error", "파일 업로드 중 오류가 발생했습니다: " + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    /**
     * 세션에서 userId 추출 (없으면 room_id의 user 부분 사용)
     */
    private String extractUserIdFromSession(HttpSession session, String roomId) {
        // 세션에 userId가 있으면 사용
        Object userIdObj = session.getAttribute("userId");
        if (userIdObj != null) {
            return userIdObj.toString();
        }

        // 없으면 room_id에서 추출 (형식: {user_id}_{timestamp})
        if (roomId != null && roomId.contains("_")) {
            String[] parts = roomId.split("_");
            if (parts.length >= 2) {
                return parts[0];  // user_id 부분 반환
            }
        }

        // 그것도 안되면 "anonymous" 사용
        return "anonymous";
    }

    /**
     * 다운로드 URL 생성 (file_uid 기반)
     */
    private String generateDownloadUrl(String fileUid) {
        // TODO: 실제 다운로드 엔드포인트 URL로 변경 필요
        return "/api/v1/files/download/" + fileUid;
    }
}
