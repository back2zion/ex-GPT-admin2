package com.datastreams.gpt.file.service;

import com.datastreams.gpt.file.dto.SessionFileDeleteRequestDto;
import com.datastreams.gpt.file.dto.SessionFileDeleteResponseDto;
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
import java.util.Objects;

@Service
@Transactional
public class SessionFileDeleteService {

    private static final Logger logger = LoggerFactory.getLogger(SessionFileDeleteService.class);

    @Value("${ds.ai.server.url}")
    private String fastApiBaseUrl;

    @Value("${ds.ai.api.key}")
    private String apiKey;

    private final RestTemplate restTemplate;

    public SessionFileDeleteService(@Qualifier("fileUploadRestTemplate") RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    /**
     * L-019: 세션 파일 삭제
     * FastAPI에서 지정된 세션의 모든 파일을 삭제
     * 
     * @param requestDto 세션 파일 삭제 요청 DTO
     * @return 세션 파일 삭제 응답 DTO
     * @throws Exception 삭제 실패 시
     */
    public SessionFileDeleteResponseDto deleteSessionFiles(SessionFileDeleteRequestDto requestDto) throws Exception {
        long startTime = System.currentTimeMillis();
        logger.info("L-019 세션 파일 삭제 서비스 호출. cnvsIdtId: {}", requestDto.getCnvsIdtId());

        try {
            // 1. 입력 값 검증
            validateSessionFileDeleteRequest(requestDto);

            // 2. FastAPI 세션 파일 삭제
            String deleteResult = deleteSessionFilesFromFastApi(requestDto.getCnvsIdtId());

            // 3. 응답 DTO 생성
            SessionFileDeleteResponseDto responseDto = new SessionFileDeleteResponseDto();
            responseDto.setCnvsIdtId(requestDto.getCnvsIdtId());
            responseDto.setStatus("success");
            responseDto.setDeletedFileCount(parseDeletedFileCount(deleteResult));
            responseDto.setDeletedFiles(parseDeletedFiles(deleteResult));
            responseDto.setDeletedAt(Instant.now().toString());
            responseDto.setProcessingTime(System.currentTimeMillis() - startTime);

            logger.info("L-019 세션 파일 삭제 성공. cnvsIdtId: {}, deletedCount: {}, processingTime: {}ms", 
                       requestDto.getCnvsIdtId(), responseDto.getDeletedFileCount(), responseDto.getProcessingTime());

            return responseDto;

        } catch (IllegalArgumentException e) {
            logger.warn("L-019 세션 파일 삭제 요청 데이터 오류: {}", e.getMessage());
            throw e;
        } catch (Exception e) {
            logger.error("L-019 세션 파일 삭제 중 오류 발생", e);
            throw new Exception("세션 파일 삭제 중 오류가 발생했습니다: " + e.getMessage());
        }
    }

    /**
     * FastAPI에서 세션 파일 삭제
     * 
     * @param cnvsIdtId 대화 식별 아이디
     * @return 삭제 결과
     * @throws Exception 삭제 실패 시
     */
    private String deleteSessionFilesFromFastApi(String cnvsIdtId) throws Exception {
        String apiUrl = fastApiBaseUrl + "/v1/session/" + cnvsIdtId;
        
        logger.info("FastAPI 세션 파일 삭제 요청: {}", apiUrl);

        try {
            // 헤더 설정
            HttpHeaders headers = new HttpHeaders();
            headers.set("X-API-Key", apiKey);

            HttpEntity<Void> requestEntity = new HttpEntity<>(headers);

            // FastAPI 호출
            ResponseEntity<String> response = restTemplate.exchange(
                apiUrl, 
                HttpMethod.DELETE, 
                requestEntity, 
                String.class
            );

            if (response.getStatusCode().is2xxSuccessful()) {
                String result = response.getBody() != null ? response.getBody() : "success";
                logger.info("FastAPI 세션 파일 삭제 성공 - cnvsIdtId: {}, result: {}", cnvsIdtId, result);
                return result;
            } else {
                throw new Exception("FastAPI 세션 파일 삭제 실패 - 상태코드: " + response.getStatusCode());
            }

        } catch (Exception e) {
            logger.error("FastAPI 세션 파일 삭제 중 오류 발생", e);
            throw new Exception("FastAPI 세션 파일 삭제 실패: " + e.getMessage(), e);
        }
    }

    /**
     * 삭제된 파일 개수 파싱
     * 
     * @param deleteResult 삭제 결과 문자열
     * @return 삭제된 파일 개수
     */
    private Integer parseDeletedFileCount(String deleteResult) {
        try {
            // FastAPI 응답에서 파일 개수 추출 (예: "3 files deleted" 또는 JSON 형태)
            if (deleteResult.contains("files deleted") || deleteResult.contains("deleted")) {
                String[] parts = deleteResult.split("\\s+");
                for (String part : parts) {
                    if (part.matches("\\d+")) {
                        return Integer.parseInt(part);
                    }
                }
            }
            // JSON 형태의 응답인 경우 (예: {"deleted_count": 3})
            if (deleteResult.contains("deleted_count")) {
                String[] parts = deleteResult.split("\"deleted_count\"\\s*:\\s*");
                if (parts.length > 1) {
                    String countStr = parts[1].split("[,\\}]")[0].trim();
                    return Integer.parseInt(countStr);
                }
            }
            return 0; // 기본값
        } catch (Exception e) {
            logger.warn("삭제된 파일 개수 파싱 실패: {}", deleteResult, e);
            return 0;
        }
    }

    /**
     * 삭제된 파일 목록 파싱
     * 
     * @param deleteResult 삭제 결과 문자열
     * @return 삭제된 파일 목록
     */
    private String[] parseDeletedFiles(String deleteResult) {
        try {
            // JSON 형태의 응답에서 파일 목록 추출
            if (deleteResult.contains("deleted_files") || deleteResult.contains("files")) {
                // 간단한 파싱 (실제 구현에서는 JSON 파서 사용 권장)
                if (deleteResult.contains("[")) {
                    String filesPart = deleteResult.substring(deleteResult.indexOf("[") + 1, deleteResult.lastIndexOf("]"));
                    return filesPart.split(",");
                }
            }
            return new String[0]; // 기본값
        } catch (Exception e) {
            logger.warn("삭제된 파일 목록 파싱 실패: {}", deleteResult, e);
            return new String[0];
        }
    }

    /**
     * 세션 파일 삭제 요청 데이터 검증
     * 
     * @param requestDto 세션 파일 삭제 요청 DTO
     * @throws IllegalArgumentException 검증 실패 시
     */
    private void validateSessionFileDeleteRequest(SessionFileDeleteRequestDto requestDto) {
        if (requestDto == null) {
            throw new IllegalArgumentException("요청 데이터가 null입니다.");
        }
        if (Objects.isNull(requestDto.getCnvsIdtId()) || requestDto.getCnvsIdtId().trim().isEmpty()) {
            throw new IllegalArgumentException("대화 식별 아이디는 필수입니다.");
        }
        
        // 대화 식별 아이디 형식 검증
        String cnvsIdtId = requestDto.getCnvsIdtId().trim();
        if (!cnvsIdtId.matches("^[a-zA-Z0-9_-]+$")) {
            throw new IllegalArgumentException("유효하지 않은 대화 식별 아이디 형식입니다.");
        }
    }

    /**
     * FastAPI 헬스체크
     *
     * @return FastAPI 서버가 정상 작동하는지 여부
     */
    public boolean checkFastApiHealth() {
        String healthUrl = String.format("%s/v1/file/stats", fastApiBaseUrl);
        try {
            ResponseEntity<String> response = restTemplate.getForEntity(healthUrl, String.class);
            return response.getStatusCode().is2xxSuccessful();
        } catch (Exception e) {
            logger.error("FastAPI 헬스체크 실패: {}", e.getMessage());
            return false;
        }
    }
}
