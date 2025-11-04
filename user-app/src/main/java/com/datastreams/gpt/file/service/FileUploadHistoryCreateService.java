package com.datastreams.gpt.file.service;

import com.datastreams.gpt.file.dto.FileUploadHistoryCreateRequestDto;
import com.datastreams.gpt.file.dto.FileUploadHistoryCreateResponseDto;
import com.datastreams.gpt.file.mapper.FileUploadHistoryCreateMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class FileUploadHistoryCreateService {

    private static final Logger logger = LoggerFactory.getLogger(FileUploadHistoryCreateService.class);

    @Autowired
    private FileUploadHistoryCreateMapper fileUploadHistoryCreateMapper;

    /**
     * L-016: 파일 업로드 이력 생성
     * @param requestDto 파일 업로드 이력 생성 요청 DTO
     * @return 파일 업로드 이력 생성 응답 DTO
     * @throws Exception 처리 중 오류 발생 시
     */
    public FileUploadHistoryCreateResponseDto createFileUploadHistory(FileUploadHistoryCreateRequestDto requestDto) throws Exception {
        logger.info("파일 업로드 이력 생성 시작 - 사용자: {}, 세션: {}, 파일: {}", 
                   requestDto.getUsrId(), requestDto.getSesnId(), requestDto.getFileNm());

        try {
            // 입력 파라미터 검증
            validateFileUploadHistoryRequest(requestDto);

            // 파일 업로드 이력 생성
            FileUploadHistoryCreateResponseDto responseDto = fileUploadHistoryCreateMapper.createFileUploadHistory(requestDto);

            logger.info("파일 업로드 이력 생성 완료 - TXN: {}, CNT: {}, CNVS_IDT_ID: {}, FILE_UPLD_SEQ: {}", 
                       responseDto.getTxnNm(), responseDto.getCnt(), responseDto.getCnvsIdtId(), responseDto.getFileUpldSeq());

            return responseDto;

        } catch (IllegalArgumentException e) {
            logger.warn("파일 업로드 이력 생성 요청 데이터 오류: {}", e.getMessage());
            throw e;
        } catch (Exception e) {
            logger.error("파일 업로드 이력 생성 중 오류 발생", e);
            throw new Exception("파일 업로드 이력 생성 중 오류가 발생했습니다: " + e.getMessage());
        }
    }

    /**
     * 파일 업로드 이력 생성 요청 데이터 검증
     * @param requestDto 파일 업로드 이력 생성 요청 DTO
     * @throws IllegalArgumentException 검증 실패 시
     */
    private void validateFileUploadHistoryRequest(FileUploadHistoryCreateRequestDto requestDto) {
        if (requestDto == null) {
            throw new IllegalArgumentException("요청 데이터가 null입니다.");
        }
        if (requestDto.getUsrId() == null || requestDto.getUsrId().trim().isEmpty()) {
            throw new IllegalArgumentException("사용자 아이디는 필수입니다.");
        }
        if (requestDto.getSesnId() == null || requestDto.getSesnId().trim().isEmpty()) {
            throw new IllegalArgumentException("세션 아이디는 필수입니다.");
        }
        if (requestDto.getFileNm() == null || requestDto.getFileNm().trim().isEmpty()) {
            throw new IllegalArgumentException("파일명은 필수입니다.");
        }
        if (requestDto.getMenuIdtId() == null || requestDto.getMenuIdtId().trim().isEmpty()) {
            throw new IllegalArgumentException("메뉴 식별 아이디는 필수입니다.");
        }
    }
}
