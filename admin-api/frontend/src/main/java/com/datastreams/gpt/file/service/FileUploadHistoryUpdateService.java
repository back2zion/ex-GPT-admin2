package com.datastreams.gpt.file.service;

import com.datastreams.gpt.file.dto.FileUploadHistoryUpdateRequestDto;
import com.datastreams.gpt.file.dto.FileUploadHistoryUpdateResponseDto;
import com.datastreams.gpt.file.mapper.FileUploadHistoryUpdateMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.Objects;

@Service
@Transactional
public class FileUploadHistoryUpdateService {

    private static final Logger logger = LoggerFactory.getLogger(FileUploadHistoryUpdateService.class);

    @Autowired
    private FileUploadHistoryUpdateMapper fileUploadHistoryUpdateMapper;

    /**
     * L-018: 파일 업로드 이력 갱신
     * L-017에서 업로드한 파일의 상태를 DB에 갱신하고 로그를 기록
     * 
     * @param requestDto 파일 업로드 이력 갱신 요청 DTO
     * @return 파일 업로드 이력 갱신 응답 DTO
     * @throws IllegalArgumentException 필수 파라미터 누락 시 발생
     */
    public FileUploadHistoryUpdateResponseDto updateFileUploadHistory(FileUploadHistoryUpdateRequestDto requestDto) {
        // 1. 입력 값 검증
        validateFileUploadHistoryUpdateRequest(requestDto);

        logger.info("L-018 파일 업로드 이력 갱신 서비스 호출. 요청: {}", requestDto);

        try {
            // 2. Mapper 호출하여 DB 작업 수행
            FileUploadHistoryUpdateResponseDto response = fileUploadHistoryUpdateMapper.updateFileUploadHistory(requestDto);

            if (Objects.isNull(response) || Objects.isNull(response.getCnt()) || response.getCnt() == 0) {
                logger.error("L-018 파일 업로드 이력 갱신 실패: 해당 파일 업로드 순번이 존재하지 않습니다. fileUpldSeq: {}", requestDto.getFileUpldSeq());
                throw new RuntimeException("해당 파일 업로드 순번이 존재하지 않습니다.");
            }

            // 3. 응답 데이터 보완
            response.setFileUpldSeq(requestDto.getFileUpldSeq());
            response.setFileUid(requestDto.getFileUid());
            response.setUpdatedAt(Instant.now().toString());

            logger.info("L-018 파일 업로드 이력 갱신 성공. 응답: {}", response);
            return response;

        } catch (Exception e) {
            logger.error("L-018 파일 업로드 이력 갱신 중 오류 발생: {}", e.getMessage(), e);
            throw new RuntimeException("파일 업로드 이력 갱신 중 오류가 발생했습니다: " + e.getMessage());
        }
    }

    /**
     * 파일 업로드 이력 갱신 요청 데이터 검증
     * 
     * @param requestDto 파일 업로드 이력 갱신 요청 DTO
     * @throws IllegalArgumentException 검증 실패 시
     */
    private void validateFileUploadHistoryUpdateRequest(FileUploadHistoryUpdateRequestDto requestDto) {
        if (Objects.isNull(requestDto)) {
            throw new IllegalArgumentException("요청 데이터가 null입니다.");
        }
        if (Objects.isNull(requestDto.getFileUpldSeq()) || requestDto.getFileUpldSeq() <= 0) {
            throw new IllegalArgumentException("파일 업로드 순번은 필수이며 0보다 커야 합니다.");
        }
        if (Objects.isNull(requestDto.getFileUid()) || requestDto.getFileUid().trim().isEmpty()) {
            throw new IllegalArgumentException("파일 아이디는 필수입니다.");
        }
        if (Objects.isNull(requestDto.getLogCont()) || requestDto.getLogCont().trim().isEmpty()) {
            throw new IllegalArgumentException("로그 내용은 필수입니다.");
        }
        
        // 파일 ID 형식 검증 (UUID 형태)
        String fileUid = requestDto.getFileUid().trim();
        if (!fileUid.matches("^[a-zA-Z0-9_-]+$")) {
            throw new IllegalArgumentException("유효하지 않은 파일 아이디 형식입니다.");
        }
        
        // 로그 내용 길이 검증
        String logCont = requestDto.getLogCont().trim();
        if (logCont.length() > 1000) {
            throw new IllegalArgumentException("로그 내용이 너무 깁니다. 최대 1000자까지 입력 가능합니다.");
        }
    }

    /**
     * 파일 업로드 이력 존재 여부 확인
     * 
     * @param fileUpldSeq 파일 업로드 순번
     * @return 존재 여부
     */
    public boolean existsFileUploadHistory(Long fileUpldSeq) {
        try {
            FileUploadHistoryUpdateRequestDto requestDto = new FileUploadHistoryUpdateRequestDto();
            requestDto.setFileUpldSeq(fileUpldSeq);
            requestDto.setFileUid("check");
            requestDto.setLogCont("check");
            
            FileUploadHistoryUpdateResponseDto response = fileUploadHistoryUpdateMapper.updateFileUploadHistory(requestDto);
            return Objects.nonNull(response) && Objects.nonNull(response.getCnt()) && response.getCnt() > 0;
        } catch (Exception e) {
            logger.warn("파일 업로드 이력 존재 여부 확인 중 오류 발생: {}", e.getMessage());
            return false;
        }
    }
}
