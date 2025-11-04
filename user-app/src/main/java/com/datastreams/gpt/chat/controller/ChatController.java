package com.datastreams.gpt.chat.controller;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.apache.http.HttpEntity;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.datastreams.gpt.chat.dto.ChatRequestDto;
import com.datastreams.gpt.chat.dto.QuerySaveRequestDto;
import com.datastreams.gpt.chat.dto.QuerySaveResponseDto;
import com.datastreams.gpt.chat.service.QuerySaveService;
import com.datastreams.gpt.chat.mapper.ChatMapper;
import com.datastreams.gpt.login.dto.UserInfoDto;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;

import jakarta.servlet.ServletInputStream;
import jakarta.servlet.ServletOutputStream;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

/**
 * Chat API Controller
 * /v1/chat API와 연동하여 채팅 기능 제공
 * 
 * @Version: 1.0
 * @Author: create by TeamS
 * @Desc: AI Chat API Controller
 */
@RestController
@RequestMapping("/api/chat")
@Tag(name = "Chat API", description = "AI 채팅 기능 API")
public class ChatController {
    
    private static final Logger logger = LoggerFactory.getLogger(ChatController.class);
    
    @Autowired
    private ChatMapper chatMapper;
    
    @Autowired
    private QuerySaveService querySaveService;
    
    @Value("${ds.ai.server.url:http://localhost:8083}")
    private String aiServerUrl;
    
    @Value("${ds.ai.api.key:z3JE1M8huXmNux6y}")
    private String apiKey;
    
    @Value("${ds.ssoUse:false}")
    private boolean ssoUse;
    
    /**
     * 채팅 메시지 처리 (스트리밍 방식)
     * FirstController와 동일한 방식으로 외부 API 호출
     * 
     * @param requestDto 채팅 요청 데이터
     * @param request HTTP 요청 객체
     * @param response HTTP 응답 객체
     */
    @PostMapping("/conversation")
    @Operation(
        summary = "채팅 메시지 처리",
        description = "사용자의 채팅 메시지를 처리하고 AI 응답을 스트리밍 방식으로 반환합니다."
    )
    @ApiResponse(
        responseCode = "200",
        description = "스트리밍 응답 성공",
        content = @Content(
            mediaType = "text/event-stream",
            schema = @Schema(type = "string")
        )
    )
    public void processChatMessage(
            @Parameter(description = "채팅 요청 데이터")
            @RequestBody(required = false) ChatRequestDto requestDto,
            HttpServletRequest request, 
            HttpServletResponse response) {
        String targetUrl = aiServerUrl + "/v1/chat/";
        HttpSession session = request.getSession(false);
        
        try (
                CloseableHttpClient httpClient = HttpClients.createDefault();
                ServletOutputStream out = response.getOutputStream();
                ServletInputStream input = request.getInputStream()
        ) {
            // 세션 확인
            if (session == null) {
                response.setContentType("text/event-stream; charset=UTF-8");
                response.setHeader("Cache-Control", "no-cache");
                response.setHeader("Connection", "keep-alive");
                
                out.write("data: {\"error\":\"세션이 만료되었습니다\"}\n\n".getBytes("UTF-8"));
                out.write("data: [DONE]\n\n".getBytes("UTF-8"));
                out.flush();
                return;
            }
            
            UserInfoDto userInfo = (UserInfoDto) session.getAttribute("userInfo");
            if (userInfo == null) {
                response.setContentType("text/event-stream; charset=UTF-8");
                response.setHeader("Cache-Control", "no-cache");
                response.setHeader("Connection", "keep-alive");
                
                out.write("data: {\"error\":\"사용자 정보를 찾을 수 없습니다\"}\n\n".getBytes("UTF-8"));
                out.write("data: [DONE]\n\n".getBytes("UTF-8"));
                out.flush();
                return;
            }
            
            // 요청 본문 처리
            ObjectMapper mapper = new ObjectMapper();
            Map<String, Object> body;

            if (requestDto != null) {
                // ChatRequestDto를 Map으로 변환
                body = mapper.convertValue(requestDto, new TypeReference<Map<String, Object>>() {});
            } else {
                // InputStream에서 직접 읽기 (기존 방식)
                body = mapper.readValue(input, new TypeReference<Map<String, Object>>() {});
            }

            // ⚠️ Stateless 방식: RequestDto에서 cnvsIdtId 가져오기 (HTTP 세션 사용 안 함)
            String cnvsIdtId = null;
            if (requestDto != null && requestDto.getCnvsIdtId() != null) {
                cnvsIdtId = requestDto.getCnvsIdtId();
            }

            // 빈 스트링인 경우 null로 처리 (새 대화 시작)
            if (cnvsIdtId != null && cnvsIdtId.trim().isEmpty()) {
                cnvsIdtId = null;
            }

            // 룸아이디 생성/확인 로직 (DB 기반, Stateless)
            String roomId;
            boolean isNewRoom = false;

            if (cnvsIdtId == null) {
                // 새 대화 시작 - DB에서 roomId 생성
                roomId = createNewRoomId(userInfo, session);
                isNewRoom = true;
                logger.info("새 대화 시작 - 사용자: {}, 생성된 roomId: {}", userInfo.getUsrId(), roomId);
            } else {
                // 기존 대화 이어가기 - DB에서 검증
                roomId = validateRoomIdFromDB(cnvsIdtId, userInfo);
                logger.info("기존 대화 이어가기 - 사용자: {}, roomId: {}", userInfo.getUsrId(), roomId);
            }
            
            // 사용자 정보 설정
            body.put("user_id", userInfo.getUsrId());
            body.put("department", userInfo.getDeptCd());
            body.put("authorization", "Bearer " + apiKey);
            body.put("stream", true);
            body.put("current_time", getNowDate());
            body.put("room_id", roomId); // 룸아이디 추가
            
            // 히스토리 처리
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> history = (List<Map<String, Object>>) body.get("history");
            String query = "";
            if (history == null || history.isEmpty()) {
                history = new ArrayList<>();
                Map<String, Object> newHistoryEntry = new HashMap<>();
                newHistoryEntry.put("role", "user");
                newHistoryEntry.put("content", body.get("message"));
                history.add(newHistoryEntry);
                body.put("history", history);
                query = (String) body.get("message");
            } else {
                Map<String, Object> lastEntry = history.get(history.size() - 1);
                if ("user".equals(lastEntry.get("role"))) {
                    query = (String) lastEntry.get("content");
                } else {
                    query = (String) body.get("message");
                }
            }
            
            // JSON 문자열로 직렬화
            String jsonBody = mapper.writeValueAsString(body);
            
            // CWE-489: Active Debug Code 제거 - 운영 환경에서 상세 로그 제거
            logger.info("Chat API 요청 - 사용자: {}, 질문 길이: {} 문자", userInfo.getUsrId(), query.length());
            
            // 외부 API 호출
            HttpPost post = new HttpPost(targetUrl);
            post.setHeader("Content-Type", "application/json");
            post.setHeader("X-API-Key", apiKey);
            post.setEntity(new StringEntity(jsonBody, "UTF-8"));
            
            // 응답 헤더 설정
            response.setContentType("text/event-stream; charset=UTF-8");
            response.setHeader("Cache-Control", "no-cache");
            response.setHeader("Connection", "keep-alive");
            
            // 스트리밍 응답 전송
            try (CloseableHttpResponse upstreamResponse = httpClient.execute(post)) {
                HttpEntity entity = upstreamResponse.getEntity();
                if (entity != null) {
                    try (InputStream in = entity.getContent()) {
                        byte[] buffer = new byte[1024];
                        int len;
                        StringBuilder fullContent = new StringBuilder();
                        
                        while ((len = in.read(buffer)) != -1) {
                            out.write(buffer, 0, len);
                            out.flush();
                            fullContent.append(new String(buffer, 0, len, StandardCharsets.UTF_8));
                        }
                        
                        // 히스토리 저장 (FirstController 방식)
                        saveChatHistory(fullContent.toString(), query, userInfo, session.getId(), mapper, roomId);
                        
                        // 새 룸 생성 시 룸아이디 정보 전송
                        if (isNewRoom) {
                            sendRoomIdInfo(out, roomId);
                        }
                    }
                }
            }
            
        } catch (IllegalArgumentException e) {
            // CWE-209: Information Exposure 방지 - 클라이언트에 상세 오류 메시지 노출 금지
            logger.warn("요청 데이터 오류: {}", e.getMessage());
            try {
                response.setContentType("text/event-stream; charset=UTF-8");
                response.setHeader("Cache-Control", "no-cache");
                response.setHeader("Connection", "keep-alive");
                
                ServletOutputStream out = response.getOutputStream();
                out.write("data: {\"error\":\"요청 데이터가 올바르지 않습니다\"}\n\n".getBytes("UTF-8"));
                out.write("data: [DONE]\n\n".getBytes("UTF-8"));
                out.flush();
            } catch (Exception ex) {
                logger.error("오류 응답 작성 실패: ", ex);
            }
        } catch (Exception e) {
            // CWE-209: Information Exposure 방지 - 일반적인 오류 메시지만 사용
            logger.error("Chat processing error: ", e);
            try {
                response.setContentType("text/event-stream; charset=UTF-8");
                response.setHeader("Cache-Control", "no-cache");
                response.setHeader("Connection", "keep-alive");
                
                ServletOutputStream out = response.getOutputStream();
                out.write("data: {\"error\":\"서버 오류가 발생했습니다\"}\n\n".getBytes("UTF-8"));
                out.write("data: [DONE]\n\n".getBytes("UTF-8"));
                out.flush();
            } catch (Exception ex) {
                logger.error("오류 응답 작성 실패: ", ex);
            }
        }
    }
    
    /**
     * roomId 검증 (DB에서 직접 확인 - Stateless 방식)
     *
     * @param cnvsIdtId 클라이언트에서 전송한 대화방 ID
     * @param userInfo 사용자 정보
     * @return 검증된 roomId
     * @throws IllegalArgumentException roomId가 유효하지 않거나 접근 권한이 없는 경우
     */
    private String validateRoomIdFromDB(String cnvsIdtId, UserInfoDto userInfo) {
        // CWE-476: NULL Pointer Dereference 방지
        if (cnvsIdtId == null || cnvsIdtId.trim().isEmpty()) {
            logger.error("cnvsIdtId가 null이거나 비어있습니다.");
            throw new IllegalArgumentException("대화방 ID가 유효하지 않습니다.");
        }

        if (userInfo == null || userInfo.getUsrId() == null) {
            logger.error("사용자 정보가 null입니다.");
            throw new IllegalArgumentException("사용자 정보가 유효하지 않습니다.");
        }

        try {
            // DB에서 roomId가 해당 사용자의 것인지 확인
            // SELECT COUNT(*) FROM TB_QUES_HIS WHERE CNVS_IDT_ID = ? AND USR_ID = ?
            boolean isValid = chatMapper.isValidRoomIdForUser(cnvsIdtId, userInfo.getUsrId());

            if (!isValid) {
                logger.warn("유효하지 않은 roomId 또는 접근 거부 - roomId: {}, userId: {}",
                           cnvsIdtId, userInfo.getUsrId());
                throw new IllegalArgumentException("유효하지 않은 대화방 ID이거나 접근 권한이 없습니다.");
            }

            logger.info("roomId 검증 성공 - roomId: {}, userId: {}", cnvsIdtId, userInfo.getUsrId());
            return cnvsIdtId;

        } catch (IllegalArgumentException e) {
            throw e; // 이미 처리된 예외는 그대로 전파
        } catch (Exception e) {
            logger.error("roomId 검증 중 DB 오류 발생 - roomId: {}, userId: {}, error: {}",
                        cnvsIdtId, userInfo.getUsrId(), e.getMessage());
            throw new IllegalArgumentException("대화방 ID 검증 중 오류가 발생했습니다.");
        }
    }

    /**
     * 새 roomId 생성 (DB INSERT - Stateless 방식)
     *
     * @param userInfo 사용자 정보
     * @param session HTTP 세션 (session_id만 사용, roomId 저장 안 함)
     * @return DB에서 생성된 CNVS_IDT_ID
     */
    private String createNewRoomId(UserInfoDto userInfo, HttpSession session) {
        try {
            // QuerySaveService를 통해 DB에서 실제 CNVS_IDT_ID 생성
            QuerySaveRequestDto requestDto = new QuerySaveRequestDto();
            requestDto.setCnvsIdtId(""); // 빈 값으로 설정하여 새 대화 생성
            requestDto.setQuesTxt("새 대화 시작"); // 임시 질의
            requestDto.setSesnId(session.getId());
            requestDto.setUsrId(userInfo.getUsrId());
            requestDto.setMenuIdtId("DEFAULT"); // 기본 메뉴
            requestDto.setRcmQuesYn("N");
            
            QuerySaveResponseDto response = querySaveService.saveQuery(requestDto);
            
            logger.info("DB에서 CNVS_IDT_ID 생성 완료: {}", response.getCnvsIdtId());
            return response.getCnvsIdtId();
            
        } catch (Exception e) {
            logger.error("DB에서 CNVS_IDT_ID 생성 실패: {}", e.getMessage());
            // 실패 시 기존 방식으로 폴백
            return generateRoomId(userInfo.getUsrId());
        }
    }
    
    /**
     * 룸아이디 생성 (폴백용)
     * 
     * @param userId 사용자 ID
     * @return 생성된 룸아이디
     */
    private String generateRoomId(String userId) {
        // CWE-476: NULL Pointer Dereference 방지
        if (userId == null || userId.trim().isEmpty()) {
            logger.error("사용자 ID가 null이거나 비어있습니다.");
            throw new IllegalArgumentException("사용자 ID가 유효하지 않습니다.");
        }
        
        // DB 쿼리와 동일한 형식으로 생성: USR_ID_yyyymmddhh24missus
        LocalDateTime now = LocalDateTime.now();
        String timestamp = now.format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
        // 마이크로초 추가 (DB의 missus 형식과 동일하게)
        String microseconds = String.format("%06d", now.getNano() / 1000);
        return userId + "_" + timestamp + microseconds;
    }
    
    /**
     * 룸아이디 정보를 클라이언트에 전송
     * 
     * @param out 출력 스트림
     * @param roomId 룸아이디
     */
    private void sendRoomIdInfo(ServletOutputStream out, String roomId) {
        // CWE-390: Error Detection Without Action 방지 - 예외 무시 금지
        if (out == null) {
            logger.error("출력 스트림이 null입니다.");
            return;
        }
        
        if (roomId == null || roomId.trim().isEmpty()) {
            logger.error("룸아이디가 null이거나 비어있습니다.");
            return;
        }
        
        try {
            Map<String, Object> roomInfo = new HashMap<>();
            roomInfo.put("type", "room_created");
            roomInfo.put("room_id", roomId);
            roomInfo.put("timestamp", getNowDate());
            
            ObjectMapper mapper = new ObjectMapper();
            String roomInfoJson = mapper.writeValueAsString(roomInfo);
            
            out.write(("data: " + roomInfoJson + "\n\n").getBytes("UTF-8"));
            out.flush();
            
            logger.info("룸아이디 정보 전송 성공: {}", roomId);
        } catch (java.io.IOException e) {
            logger.error("룸아이디 정보 전송 중 IO 오류 발생: {}", e.getMessage());
        } catch (Exception e) {
            logger.error("룸아이디 정보 전송 중 예상치 못한 오류 발생: {}", e.getMessage());
        }
    }
    
    /**
     * 채팅 히스토리 저장 (FirstController 방식)
     * 
     * @param fullContent 스트리밍 전체 내용
     * @param query 사용자 질문
     * @param userInfo 사용자 정보
     * @param sessionId 세션 ID
     * @param mapper ObjectMapper
     * @param roomId 룸아이디
     */
    private void saveChatHistory(String fullContent, String query, UserInfoDto userInfo, String sessionId, ObjectMapper mapper, String roomId) {
        try {
            String[] lines = fullContent.toString().split("\n");
            for (int i = 0; i < lines.length; i++) {
                if (lines[i].startsWith("data: [DONE]")) {
                    // DONE 직전 라인 찾기
                    for (int j = i - 1; j >= 0; j--) {
                        if (lines[j].startsWith("data: ")) {
                            String jsonString = lines[j].substring("data: ".length()).trim();
                            try {
                                JsonNode root = mapper.readTree(jsonString);
                                JsonNode contentNode = root.path("content").path("response");
                                
                                if (!contentNode.isMissingNode()) {
                                    String finalResponse = contentNode.asText();
                                    
                                    // CWE-489: Active Debug Code 제거 - 운영 환경에서 상세 로그 제거
                                    logger.info("Chat API 응답 완료 - 사용자: {}, 룸아이디: {}, 답변 길이: {} 문자", 
                                               userInfo.getUsrId(), roomId, finalResponse.length());
                                    
                                    // 채팅 히스토리 저장 (룸아이디 포함)
                                    chatMapper.saveChatMessage(sessionId, userInfo.getUsrId(), "user", query, roomId);
                                    chatMapper.saveChatMessage(sessionId, userInfo.getUsrId(), "assistant", finalResponse, roomId);
                                }
                                
                            } catch (com.fasterxml.jackson.core.JsonProcessingException e) {
                                logger.error("JSON 파싱 오류: {}", e.getMessage());
                            } catch (Exception e) {
                                logger.error("히스토리 저장 중 예상치 못한 오류: {}", e.getMessage());
                            }
                        }
                    }
                    break;
                }
            }
        } catch (Exception e) {
            logger.error("히스토리 저장 중 예상치 못한 오류: {}", e.getMessage());
        }
    }
    
    /**
     * 간단한 채팅 테스트 (룸 아이디 생성 테스트용)
     *
     * @deprecated Stateless 방식으로 전환되어 더 이상 사용되지 않습니다.
     *             클라이언트에서 cnvsIdtId를 관리하므로 이 엔드포인트는 필요 없습니다.
     */
    @Deprecated
    @PostMapping("/test")
    @Operation(
        summary = "채팅 테스트 (Deprecated)",
        description = "⚠️ Deprecated - Stateless 방식으로 전환되어 더 이상 사용되지 않습니다."
    )
    public ResponseEntity<Map<String, Object>> testChat(
            @RequestBody ChatRequestDto requestDto,
            HttpServletRequest request) {

        Map<String, Object> response = new HashMap<>();
        HttpSession session = request.getSession(false);

        if (session == null) {
            response.put("result", "error");
            response.put("message", "세션이 만료되었습니다.");
            return ResponseEntity.status(401).body(response);
        }

        UserInfoDto userInfo = (UserInfoDto) session.getAttribute("userInfo");
        if (userInfo == null) {
            response.put("result", "error");
            response.put("message", "사용자 정보를 찾을 수 없습니다.");
            return ResponseEntity.status(401).body(response);
        }

        try {
            // Stateless 방식으로 테스트 - DB에서 새 roomId 생성만 수행
            String roomId = createNewRoomId(userInfo, session);

            response.put("result", "success");
            response.put("room_id", roomId);
            response.put("is_new_room", true);
            response.put("message", "⚠️ Deprecated - 채팅 테스트 성공 (Stateless 모드)");
            response.put("user_id", userInfo.getUsrId());
            response.put("timestamp", getNowDate());

            logger.info("채팅 테스트 성공 (Stateless) - 사용자: {}, 룸아이디: {}",
                userInfo.getUsrId(), roomId);

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            logger.error("채팅 테스트 실패: {}", e.getMessage(), e);
            response.put("result", "error");
            response.put("message", "채팅 테스트 실패: " + e.getMessage());
            return ResponseEntity.status(500).body(response);
        }
    }

    /**
     * 룸아이디 리셋 (새 채팅방 시작)
     *
     * @deprecated Stateless 방식으로 전환되어 서버에서 roomId를 저장하지 않습니다.
     *             클라이언트에서 roomIdStore.clearRoomId()를 호출하여 리셋하세요.
     */
    @Deprecated
    @PostMapping("/reset")
    @Operation(
        summary = "룸아이디 리셋 (Deprecated)",
        description = "⚠️ Deprecated - Stateless 방식으로 전환되어 더 이상 사용되지 않습니다. " +
                      "클라이언트에서 roomIdStore.clearRoomId()를 호출하세요."
    )
    @ApiResponse(
        responseCode = "200",
        description = "룸아이디 리셋 성공",
        content = @Content(
            mediaType = "application/json",
            schema = @Schema(example = "{\"result\":\"success\",\"message\":\"⚠️ Deprecated - 클라이언트에서 roomId를 관리하세요.\"}")
        )
    )
    public ResponseEntity<Map<String, Object>> resetRoom(HttpServletRequest request) {
        HttpSession session = request.getSession(false);
        Map<String, Object> response = new HashMap<>();

        if (session == null) {
            response.put("result", "error");
            response.put("message", "세션이 만료되었습니다.");
            return ResponseEntity.status(401).body(response);
        }

        // ⚠️ Stateless 모드: 세션에서 roomId를 관리하지 않으므로 제거할 것이 없음
        // 이전 버전 호환성을 위해 엔드포인트는 유지하지만 아무 작업도 하지 않음

        logger.info("⚠️ Deprecated /reset 호출 - Stateless 모드에서는 클라이언트가 roomId 관리");

        response.put("result", "success");
        response.put("message", "⚠️ Deprecated - 클라이언트에서 roomIdStore.clearRoomId()를 사용하세요.");
        response.put("timestamp", getNowDate());

        return ResponseEntity.ok(response);
    }
    
    /**
     * 현재 룸아이디 조회
     *
     * @deprecated Stateless 방식으로 전환되어 서버에서 roomId를 저장하지 않습니다.
     *             클라이언트에서 roomIdStore.roomId를 참조하세요.
     */
    @Deprecated
    @GetMapping("/room-id")
    @Operation(
        summary = "현재 룸아이디 조회 (Deprecated)",
        description = "⚠️ Deprecated - Stateless 방식으로 전환되어 더 이상 사용되지 않습니다. " +
                      "클라이언트에서 roomIdStore.roomId를 참조하세요."
    )
    @ApiResponse(
        responseCode = "200",
        description = "룸아이디 조회 결과",
        content = @Content(
            mediaType = "application/json",
            schema = @Schema(example = "{\"result\":\"success\",\"room_id\":null,\"message\":\"⚠️ Deprecated\"}")
        )
    )
    public ResponseEntity<Map<String, Object>> getCurrentRoomId(HttpServletRequest request) {
        HttpSession session = request.getSession(false);
        Map<String, Object> response = new HashMap<>();

        if (session == null) {
            response.put("result", "error");
            response.put("message", "세션이 만료되었습니다.");
            return ResponseEntity.status(401).body(response);
        }

        // ⚠️ Stateless 모드: 서버에서 roomId를 저장하지 않음
        response.put("result", "success");
        response.put("room_id", null);
        response.put("message", "⚠️ Deprecated - 클라이언트에서 roomIdStore.roomId를 사용하세요.");
        response.put("timestamp", getNowDate());

        logger.info("⚠️ Deprecated /room-id 호출 - Stateless 모드에서는 클라이언트가 roomId 관리");

        return ResponseEntity.ok(response);
    }
    
    /**
     * 룸아이디별 채팅 히스토리 조회
     */
    @GetMapping("/history/{roomId}")
    @Operation(
        summary = "룸아이디별 채팅 히스토리 조회",
        description = "특정 룸아이디의 채팅 히스토리를 조회합니다."
    )
    @ApiResponse(
        responseCode = "200",
        description = "채팅 히스토리 조회 성공",
        content = @Content(
            mediaType = "application/json",
            schema = @Schema(example = "{\"result\":\"success\",\"data\":[{\"role\":\"user\",\"content\":\"안녕하세요\"}]}")
        )
    )
    public ResponseEntity<Map<String, Object>> getChatHistoryByRoomId(
            @Parameter(description = "룸아이디", required = true) @PathVariable String roomId,
            HttpServletRequest request) {
        
        HttpSession session = request.getSession(false);
        Map<String, Object> response = new HashMap<>();
        
        if (session == null) {
            response.put("result", "error");
            response.put("message", "세션이 만료되었습니다.");
            return ResponseEntity.status(401).body(response);
        }
        
        UserInfoDto userInfo = (UserInfoDto) session.getAttribute("userInfo");
        if (userInfo == null) {
            response.put("result", "error");
            response.put("message", "사용자 정보를 찾을 수 없습니다.");
            return ResponseEntity.status(401).body(response);
        }
        
        try {
            List<Map<String, Object>> chatHistory = chatMapper.getChatHistoryByRoomId(roomId, userInfo.getUsrId());
            
            response.put("result", "success");
            response.put("data", chatHistory);
            response.put("count", chatHistory.size());
            response.put("room_id", roomId);
            response.put("message", "채팅 히스토리를 성공적으로 조회했습니다.");
            response.put("timestamp", getNowDate());
            
            logger.info("룸아이디별 채팅 히스토리 조회 완료 - 룸아이디: {}, 메시지 수: {}", roomId, chatHistory.size());
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("룸아이디별 채팅 히스토리 조회 중 오류 발생", e);
            
            response.put("result", "error");
            response.put("message", "채팅 히스토리 조회 중 오류가 발생했습니다.");
            response.put("timestamp", getNowDate());
            
            return ResponseEntity.status(500).body(response);
        }
    }
    
    /**
     * 현재 시간 반환
     * 
     * @return 현재 시간 문자열
     */
    private String getNowDate() {
        return LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
    }
}
