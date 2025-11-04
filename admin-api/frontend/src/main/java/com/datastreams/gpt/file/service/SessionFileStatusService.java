package com.datastreams.gpt.file.service;

import com.datastreams.gpt.file.dto.SessionFileStatusRequestDto;
import com.datastreams.gpt.file.dto.SessionFileStatusResponseDto;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.time.Instant;
import java.util.Map;

@Service
@Transactional(readOnly = true)
public class SessionFileStatusService {

    private static final Logger logger = LoggerFactory.getLogger(SessionFileStatusService.class);

    @Value("${ds.ai.server.url}")
    private String fastApiBaseUrl;

    @Value("${ds.ai.api.key}")
    private String apiKey;

    private final RestTemplate restTemplate;

    public SessionFileStatusService(@Qualifier("fileUploadRestTemplate") RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    /**
     * L-040: 세션 파일 상태 조회
     * FastAPI에서 파일 처리 상태를 조회하고 상세 정보를 반환
     * 
     * @param requestDto 세션 파일 상태 조회 요청 DTO
     * @return 세션 파일 상태 조회 응답 DTO
     * @throws Exception 조회 실패 시
     */
    public SessionFileStatusResponseDto getSessionFileStatus(SessionFileStatusRequestDto requestDto) throws Exception {
        logger.info("세션 파일 상태 조회 시작 - 파일 ID: {}", requestDto.getFileUid());

        try {
            // 입력 파라미터 검증
            validateSessionFileStatusRequest(requestDto);

            // FastAPI 파일 상태 조회
            Map<String, Object> statusData = getFileStatusFromFastApi(requestDto.getFileUid());

            // 응답 DTO 생성
            SessionFileStatusResponseDto responseDto = new SessionFileStatusResponseDto();
            responseDto.setFileUid(requestDto.getFileUid());
            responseDto.setStatus((String) statusData.get("status"));
            responseDto.setError((String) statusData.get("error"));
            responseDto.setNextStep((String) statusData.get("next_step"));
            responseDto.setFileName((String) statusData.get("file_name"));
            
            // 파일 크기 처리 (숫자 타입 변환)
            Object fileSizeObj = statusData.get("file_size");
            if (fileSizeObj != null) {
                if (fileSizeObj instanceof Number) {
                    responseDto.setFileSize(((Number) fileSizeObj).longValue());
                } else {
                    try {
                        responseDto.setFileSize(Long.parseLong(fileSizeObj.toString()));
                    } catch (NumberFormatException e) {
                        logger.warn("파일 크기 파싱 실패: {}", fileSizeObj);
                    }
                }
            }
            
            // 진행률 처리
            Object progressObj = statusData.get("progress");
            if (progressObj != null) {
                if (progressObj instanceof Number) {
                    responseDto.setProgress(((Number) progressObj).intValue());
                } else {
                    try {
                        responseDto.setProgress(Integer.parseInt(progressObj.toString()));
                    } catch (NumberFormatException e) {
                        logger.warn("진행률 파싱 실패: {}", progressObj);
                    }
                }
            }
            
            responseDto.setCheckedAt(Instant.now().toString());

            logger.info("세션 파일 상태 조회 완료 - 파일 ID: {}, 상태: {}", 
                       requestDto.getFileUid(), responseDto.getStatus());

            return responseDto;

        } catch (IllegalArgumentException e) {
            logger.warn("세션 파일 상태 조회 요청 데이터 오류: {}", e.getMessage());
            throw e;
        } catch (Exception e) {
            logger.error("세션 파일 상태 조회 중 오류 발생", e);
            throw new Exception("세션 파일 상태 조회 중 오류가 발생했습니다: " + e.getMessage());
        }
    }

    /**
     * FastAPI에서 파일 상태 조회
     * 
     * @param fileUid 파일 아이디
     * @return 파일 상태 정보 Map
     * @throws Exception 조회 실패 시
     */
    private Map<String, Object> getFileStatusFromFastApi(String fileUid) throws Exception {
        String apiUrl = fastApiBaseUrl + "/v1/file/" + fileUid + "/status";
        
        logger.info("FastAPI 파일 상태 조회 요청: {}", apiUrl);

        try {
            // 헤더 설정
            HttpHeaders headers = new HttpHeaders();
            headers.set("X-API-Key", apiKey);

            HttpEntity<Void> requestEntity = new HttpEntity<>(headers);

            // FastAPI 호출
            ResponseEntity<String> response = restTemplate.exchange(
                apiUrl, 
                HttpMethod.GET, 
                requestEntity, 
                String.class
            );

            if (response.getStatusCode().is2xxSuccessful()) {
                // JSON 응답 파싱
                Map<String, Object> responseMap = parseJsonResponse(response.getBody());
                
                logger.info("FastAPI 파일 상태 조회 성공 - 파일 ID: {}, 상태: {}", 
                           fileUid, responseMap.get("status"));
                
                return responseMap;
            } else {
                throw new Exception("FastAPI 파일 상태 조회 실패 - 상태코드: " + response.getStatusCode());
            }

        } catch (Exception e) {
            logger.error("FastAPI 파일 상태 조회 중 오류 발생", e);
            throw new Exception("FastAPI 파일 상태 조회 실패: " + e.getMessage(), e);
        }
    }

    /**
     * JSON 응답 파싱
     * 
     * @param jsonResponse JSON 응답 문자열
     * @return 파싱된 Map 객체
     * @throws Exception 파싱 실패 시
     */
    @SuppressWarnings("unchecked")
    private Map<String, Object> parseJsonResponse(String jsonResponse) throws Exception {
        try {
            com.fasterxml.jackson.databind.ObjectMapper objectMapper = new com.fasterxml.jackson.databind.ObjectMapper();
            return objectMapper.readValue(jsonResponse, Map.class);
        } catch (Exception e) {
            logger.error("JSON 응답 파싱 실패: {}", jsonResponse, e);
            throw new Exception("JSON 응답 파싱 실패: " + e.getMessage());
        }
    }

    /**
     * 세션 파일 상태 조회 요청 데이터 검증
     * 
     * @param requestDto 세션 파일 상태 조회 요청 DTO
     * @throws IllegalArgumentException 검증 실패 시
     */
    private void validateSessionFileStatusRequest(SessionFileStatusRequestDto requestDto) {
        if (requestDto == null) {
            throw new IllegalArgumentException("요청 데이터가 null입니다.");
        }
        if (requestDto.getFileUid() == null || requestDto.getFileUid().trim().isEmpty()) {
            throw new IllegalArgumentException("파일 아이디는 필수입니다.");
        }
        
        // 파일 ID 형식 검증 (UUID 형태)
        String fileUid = requestDto.getFileUid().trim();
        if (!fileUid.matches("^[a-zA-Z0-9_-]+$")) {
            throw new IllegalArgumentException("유효하지 않은 파일 아이디 형식입니다.");
        }
    }

    /**
     * 파일 상태가 완료 상태인지 확인
     * 
     * @param status 파일 상태
     * @return 완료 여부
     */
    public boolean isFileReady(String status) {
        return "ready".equals(status);
    }

    /**
     * 파일 상태가 오류 상태인지 확인
     * 
     * @param status 파일 상태
     * @return 오류 여부
     */
    public boolean isFileError(String status) {
        return "error".equals(status);
    }

    /**
     * 파일 상태가 처리 중인지 확인
     * 
     * @param status 파일 상태
     * @return 처리 중 여부
     */
    public boolean isFileProcessing(String status) {
        return "uploaded".equals(status) || "parsed".equals(status) || "processed".equals(status);
    }
}
