package com.datastreams.gpt.file.service;

import com.datastreams.gpt.file.dto.SessionFileUploadRequestDto;
import com.datastreams.gpt.file.dto.SessionFileUploadResponseDto;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.InputStreamResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;

@Service
@Transactional
public class SessionFileUploadService {

    private static final Logger logger = LoggerFactory.getLogger(SessionFileUploadService.class);

    @Value("${ds.ai.server.url}")
    private String fastApiBaseUrl;

    @Value("${ds.ai.api.key}")
    private String apiKey;

    @Value("${file.upload.streaming.enabled:false}")
    private boolean useStreamingUpload;

    private final RestTemplate restTemplate;

    public SessionFileUploadService(@Qualifier("fileUploadRestTemplate") RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    /**
     * L-017: 세션 파일 업로드
     * FastAPI 세션 API를 통해 파일을 업로드하고 파일 ID를 반환
     * 
     * @param requestDto 세션 파일 업로드 요청 DTO
     * @return 세션 파일 업로드 응답 DTO
     * @throws Exception 업로드 실패 시
     */
    public SessionFileUploadResponseDto uploadSessionFile(SessionFileUploadRequestDto requestDto) throws Exception {
        long startTime = System.currentTimeMillis();
        
        logger.info("세션 파일 업로드 시작 - 세션: {}, 사용자: {}, 파일: {}", 
                   requestDto.getCnvsIdtId(), requestDto.getUserId(), 
                   requestDto.getFile().getOriginalFilename());

        try {
            // 입력 파라미터 검증
            validateSessionFileUploadRequest(requestDto);

            // FastAPI 세션 파일 업로드
            String fileId = uploadToFastApiSession(requestDto);

            // 응답 DTO 생성
            SessionFileUploadResponseDto responseDto = new SessionFileUploadResponseDto();
            responseDto.setCnvsIdtId(requestDto.getCnvsIdtId());
            responseDto.setFileUid(fileId);
            responseDto.setFileName(requestDto.getFile().getOriginalFilename());
            responseDto.setFileSize(requestDto.getFile().getSize());
            responseDto.setStatus(requestDto.isWait() ? "completed" : "processing");
            responseDto.setProcessingTime(System.currentTimeMillis() - startTime);

            logger.info("세션 파일 업로드 완료 - 세션: {}, 파일 ID: {}, 처리시간: {}ms", 
                       requestDto.getCnvsIdtId(), fileId, responseDto.getProcessingTime());

            return responseDto;

        } catch (IllegalArgumentException e) {
            logger.warn("세션 파일 업로드 요청 데이터 오류: {}", e.getMessage());
            throw e;
        } catch (Exception e) {
            logger.error("세션 파일 업로드 중 오류 발생", e);
            throw new Exception("세션 파일 업로드 중 오류가 발생했습니다: " + e.getMessage());
        }
    }

    /**
     * FastAPI 세션에 파일 업로드
     * 
     * @param requestDto 세션 파일 업로드 요청 DTO
     * @return 파일 ID
     * @throws Exception 업로드 실패 시
     */
    private String uploadToFastApiSession(SessionFileUploadRequestDto requestDto) throws Exception {
        String apiUrl = fastApiBaseUrl + "/v1/session/" + requestDto.getCnvsIdtId() + 
                       "/file?user_id=" + requestDto.getUserId() + "&wait=" + requestDto.isWait();
        
        logger.info("FastAPI 세션 파일 업로드 요청: {}", apiUrl);

        try {
            // 멀티파트 요청 구성
            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            
            // 파일을 InputStreamResource로 변환 (스트리밍)
            InputStreamResource fileResource = new InputStreamResource(requestDto.getFile().getInputStream()) {
                @Override
                public String getFilename() {
                    return requestDto.getFile().getOriginalFilename();
                }
                
                @Override
                public long contentLength() {
                    return requestDto.getFile().getSize();
                }
            };
            body.add("file", fileResource);

            // 헤더 설정
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);
            headers.set("X-API-Key", apiKey);

            HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

            // FastAPI 호출
            ResponseEntity<String> response = restTemplate.exchange(
                apiUrl, 
                HttpMethod.POST, 
                requestEntity, 
                String.class
            );

            if (response.getStatusCode().is2xxSuccessful()) {
                // JSON 응답에서 file_id 추출
                Map<String, Object> responseMap = parseJsonResponse(response.getBody());
                String fileId = (String) responseMap.get("file_id");
                
                if (fileId != null) {
                    logger.info("FastAPI 세션 파일 업로드 성공 - file_id: {}", fileId);
                    return fileId;
                } else {
                    throw new Exception("FastAPI 응답에 file_id가 없습니다: " + response.getBody());
                }
            } else {
                throw new Exception("FastAPI 세션 파일 업로드 실패 - 상태코드: " + response.getStatusCode());
            }

        } catch (Exception e) {
            logger.error("FastAPI 세션 파일 업로드 중 오류 발생", e);
            throw new Exception("FastAPI 세션 파일 업로드 실패: " + e.getMessage(), e);
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
     * 세션 파일 업로드 요청 데이터 검증
     * 
     * @param requestDto 세션 파일 업로드 요청 DTO
     * @throws IllegalArgumentException 검증 실패 시
     */
    private void validateSessionFileUploadRequest(SessionFileUploadRequestDto requestDto) {
        if (requestDto == null) {
            throw new IllegalArgumentException("요청 데이터가 null입니다.");
        }
        if (requestDto.getCnvsIdtId() == null || requestDto.getCnvsIdtId().trim().isEmpty()) {
            throw new IllegalArgumentException("대화 식별 아이디는 필수입니다.");
        }
        if (requestDto.getUserId() == null || requestDto.getUserId().trim().isEmpty()) {
            throw new IllegalArgumentException("사용자 아이디는 필수입니다.");
        }
        if (requestDto.getFile() == null || requestDto.getFile().isEmpty()) {
            throw new IllegalArgumentException("업로드할 파일이 없습니다.");
        }
        
        // 파일 크기 검증 (200MB 제한)
        long maxFileSize = 200 * 1024 * 1024; // 200MB
        if (requestDto.getFile().getSize() > maxFileSize) {
            throw new IllegalArgumentException("파일 크기가 너무 큽니다. 최대 200MB까지 업로드 가능합니다.");
        }
        
        // 파일 확장자 검증
        String originalFilename = requestDto.getFile().getOriginalFilename();
        if (originalFilename == null || !originalFilename.contains(".")) {
            throw new IllegalArgumentException("유효하지 않은 파일명입니다.");
        }
        
        String fileExtension = originalFilename.substring(originalFilename.lastIndexOf(".") + 1).toLowerCase();
        String[] allowedExtensions = {"pdf", "hwp", "hwpx", "doc", "docx", "ppt", "pptx", "txt", "xls", "xlsx"};
        
        boolean isValidExtension = false;
        for (String allowedExt : allowedExtensions) {
            if (allowedExt.equals(fileExtension)) {
                isValidExtension = true;
                break;
            }
        }
        
        if (!isValidExtension) {
            throw new IllegalArgumentException("지원하지 않는 파일 형식입니다. 허용 형식: " + String.join(", ", allowedExtensions));
        }
    }
}
