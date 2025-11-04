package com.datastreams.gpt.file.service;

import com.datastreams.gpt.file.dto.SingleFileDeleteRequestDto;
import com.datastreams.gpt.file.dto.SingleFileDeleteResponseDto;
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
public class SingleFileDeleteService {

    private static final Logger logger = LoggerFactory.getLogger(SingleFileDeleteService.class);

    @Value("${ds.ai.server.url}")
    private String fastApiBaseUrl;

    @Value("${ds.ai.api.key}")
    private String apiKey;

    private final RestTemplate restTemplate;

    public SingleFileDeleteService(@Qualifier("fileUploadRestTemplate") RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    /**
     * L-020: 단일 파일 삭제
     * FastAPI에서 지정된 파일을 삭제
     * 
     * @param requestDto 단일 파일 삭제 요청 DTO
     * @return 단일 파일 삭제 응답 DTO
     * @throws Exception 삭제 실패 시
     */
    public SingleFileDeleteResponseDto deleteSingleFile(SingleFileDeleteRequestDto requestDto) throws Exception {
        long startTime = System.currentTimeMillis();
        logger.info("L-020 단일 파일 삭제 서비스 호출. cnvsIdtId: {}, fileUid: {}", 
                   requestDto.getCnvsIdtId(), requestDto.getFileUid());

        try {
            // 1. 입력 값 검증
            validateSingleFileDeleteRequest(requestDto);

            // 2. FastAPI 단일 파일 삭제
            String deleteResult = deleteFileFromFastApi(requestDto.getFileUid());

            // 3. 응답 DTO 생성
            SingleFileDeleteResponseDto responseDto = new SingleFileDeleteResponseDto();
            responseDto.setCnvsIdtId(requestDto.getCnvsIdtId());
            responseDto.setFileUid(requestDto.getFileUid());
            responseDto.setStatus("success");
            responseDto.setDeletedAt(Instant.now().toString());
            responseDto.setProcessingTime(System.currentTimeMillis() - startTime);
            responseDto.setFileSize(parseFileSize(deleteResult));
            responseDto.setFileName(parseFileName(deleteResult));

            logger.info("L-020 단일 파일 삭제 성공. cnvsIdtId: {}, fileUid: {}, processingTime: {}ms", 
                       requestDto.getCnvsIdtId(), requestDto.getFileUid(), responseDto.getProcessingTime());

            return responseDto;

        } catch (IllegalArgumentException e) {
            logger.warn("L-020 단일 파일 삭제 요청 데이터 오류: {}", e.getMessage());
            throw e;
        } catch (Exception e) {
            logger.error("L-020 단일 파일 삭제 중 오류 발생", e);
            throw new Exception("단일 파일 삭제 중 오류가 발생했습니다: " + e.getMessage());
        }
    }

    /**
     * FastAPI에서 단일 파일 삭제
     * 
     * @param fileUid 파일 아이디
     * @return 삭제 결과
     * @throws Exception 삭제 실패 시
     */
    private String deleteFileFromFastApi(String fileUid) throws Exception {
        String apiUrl = fastApiBaseUrl + "/v1/file/" + fileUid;
        
        logger.info("FastAPI 단일 파일 삭제 요청: {}", apiUrl);

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
                logger.info("FastAPI 단일 파일 삭제 성공 - fileUid: {}, result: {}", fileUid, result);
                return result;
            } else {
                throw new Exception("FastAPI 단일 파일 삭제 실패 - 상태코드: " + response.getStatusCode());
            }

        } catch (Exception e) {
            logger.error("FastAPI 단일 파일 삭제 중 오류 발생", e);
            throw new Exception("FastAPI 단일 파일 삭제 실패: " + e.getMessage(), e);
        }
    }

    /**
     * 파일 크기 파싱
     * 
     * @param deleteResult 삭제 결과 문자열
     * @return 파일 크기
     */
    private Long parseFileSize(String deleteResult) {
        try {
            // FastAPI 응답에서 파일 크기 추출 (예: "File deleted: 1024000 bytes")
            if (deleteResult.contains("bytes") || deleteResult.contains("size")) {
                String[] parts = deleteResult.split("\\s+");
                for (String part : parts) {
                    if (part.matches("\\d+")) {
                        return Long.parseLong(part);
                    }
                }
            }
            // JSON 형태의 응답인 경우 (예: {"file_size": 1024000})
            if (deleteResult.contains("file_size")) {
                String[] parts = deleteResult.split("\"file_size\"\\s*:\\s*");
                if (parts.length > 1) {
                    String sizeStr = parts[1].split("[,\\}]")[0].trim();
                    return Long.parseLong(sizeStr);
                }
            }
            return 0L; // 기본값
        } catch (Exception e) {
            logger.warn("파일 크기 파싱 실패: {}", deleteResult, e);
            return 0L;
        }
    }

    /**
     * 파일명 파싱
     * 
     * @param deleteResult 삭제 결과 문자열
     * @return 파일명
     */
    private String parseFileName(String deleteResult) {
        try {
            // FastAPI 응답에서 파일명 추출 (예: "File 'document.pdf' deleted")
            if (deleteResult.contains("File") && deleteResult.contains("deleted")) {
                String[] parts = deleteResult.split("'");
                if (parts.length > 1) {
                    return parts[1];
                }
            }
            // JSON 형태의 응답인 경우 (예: {"file_name": "document.pdf"})
            if (deleteResult.contains("file_name")) {
                String[] parts = deleteResult.split("\"file_name\"\\s*:\\s*\"");
                if (parts.length > 1) {
                    String nameStr = parts[1].split("\"")[0];
                    return nameStr;
                }
            }
            return "unknown"; // 기본값
        } catch (Exception e) {
            logger.warn("파일명 파싱 실패: {}", deleteResult, e);
            return "unknown";
        }
    }

    /**
     * 단일 파일 삭제 요청 데이터 검증
     * 
     * @param requestDto 단일 파일 삭제 요청 DTO
     * @throws IllegalArgumentException 검증 실패 시
     */
    private void validateSingleFileDeleteRequest(SingleFileDeleteRequestDto requestDto) {
        if (requestDto == null) {
            throw new IllegalArgumentException("요청 데이터가 null입니다.");
        }
        if (Objects.isNull(requestDto.getCnvsIdtId()) || requestDto.getCnvsIdtId().trim().isEmpty()) {
            throw new IllegalArgumentException("대화 식별 아이디는 필수입니다.");
        }
        if (Objects.isNull(requestDto.getFileUid()) || requestDto.getFileUid().trim().isEmpty()) {
            throw new IllegalArgumentException("파일 아이디는 필수입니다.");
        }
        
        // 대화 식별 아이디 형식 검증
        String cnvsIdtId = requestDto.getCnvsIdtId().trim();
        if (!cnvsIdtId.matches("^[a-zA-Z0-9_-]+$")) {
            throw new IllegalArgumentException("유효하지 않은 대화 식별 아이디 형식입니다.");
        }
        
        // 파일 아이디 형식 검증
        String fileUid = requestDto.getFileUid().trim();
        if (!fileUid.matches("^[a-zA-Z0-9_-]+$")) {
            throw new IllegalArgumentException("유효하지 않은 파일 아이디 형식입니다.");
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
