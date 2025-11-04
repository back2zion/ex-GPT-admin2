package com.datastreams.gpt.file.service;

import com.datastreams.gpt.file.dto.SingleFileDeleteInfoRequestDto;
import com.datastreams.gpt.file.dto.SingleFileDeleteInfoResponseDto;
import com.datastreams.gpt.file.mapper.SingleFileDeleteInfoMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Objects;

@Service
@Transactional
public class SingleFileDeleteInfoService {

    private static final Logger logger = LoggerFactory.getLogger(SingleFileDeleteInfoService.class);

    @Autowired
    private SingleFileDeleteInfoMapper singleFileDeleteInfoMapper;

    /**
     * L-039: 단일 파일 삭제 정보 갱신
     * 특정 세션의 특정 파일 삭제 상태를 DB에 업데이트
     * 
     * @param requestDto 단일 파일 삭제 정보 갱신 요청 DTO
     * @return 단일 파일 삭제 정보 갱신 응답 DTO
     * @throws IllegalArgumentException 필수 파라미터 누락 시 발생
     * @throws RuntimeException DB 업데이트 오류 시 발생
     */
    public SingleFileDeleteInfoResponseDto updateSingleFileDeleteInfo(SingleFileDeleteInfoRequestDto requestDto) {
        logger.info("L-039 단일 파일 삭제 정보 갱신 서비스 호출. cnvsIdtId: {}, fileUid: {}, sucYn: {}", 
                   requestDto.getCnvsIdtId(), requestDto.getFileUid(), requestDto.getSucYn());

        long startTime = System.currentTimeMillis();

        try {
            // 1. 입력 값 검증
            validateSingleFileDeleteInfoRequest(requestDto);

            // 2. 특정 파일 존재 여부 조회
            Integer fileExists = singleFileDeleteInfoMapper.checkFileExists(
                requestDto.getCnvsIdtId(), requestDto.getFileUid());
            logger.info("L-039 특정 파일 존재 여부 조회 완료. cnvsIdtId: {}, fileUid: {}, exists: {}", 
                       requestDto.getCnvsIdtId(), requestDto.getFileUid(), fileExists);

            if (fileExists == 0) {
                logger.warn("L-039 해당 파일이 존재하지 않습니다. cnvsIdtId: {}, fileUid: {}", 
                           requestDto.getCnvsIdtId(), requestDto.getFileUid());
                throw new IllegalArgumentException("해당 파일이 존재하지 않습니다.");
            }

            // 3. 단일 파일 삭제 정보 갱신 실행
            SingleFileDeleteInfoResponseDto responseDto = singleFileDeleteInfoMapper.updateSingleFileDeleteInfo(requestDto);
            
            // 4. 응답 DTO 설정
            if (responseDto == null) {
                responseDto = new SingleFileDeleteInfoResponseDto();
            }
            
            responseDto.setCnvsIdtId(requestDto.getCnvsIdtId());
            responseDto.setFileUid(requestDto.getFileUid());
            responseDto.setTxnNm("UPD_USR_UPLD_DOC_MNG");
            responseDto.setStatus("success");
            responseDto.setProcessingTime(System.currentTimeMillis() - startTime);
            responseDto.setUpdatedFileCount(responseDto.getCnt());
            responseDto.setSucYn(requestDto.getSucYn());

            // 5. 업데이트 후 삭제 상태 조회
            String deleteStatus = singleFileDeleteInfoMapper.getFileDeleteStatus(
                requestDto.getCnvsIdtId(), requestDto.getFileUid());
            logger.info("L-039 삭제 상태 조회 완료. cnvsIdtId: {}, fileUid: {}, deleteStatus: {}", 
                       requestDto.getCnvsIdtId(), requestDto.getFileUid(), deleteStatus);

            logger.info("L-039 단일 파일 삭제 정보 갱신 성공. cnvsIdtId: {}, fileUid: {}, updatedCount: {}, processingTime: {}ms", 
                       requestDto.getCnvsIdtId(), requestDto.getFileUid(), responseDto.getCnt(), responseDto.getProcessingTime());

            return responseDto;

        } catch (IllegalArgumentException e) {
            logger.warn("L-039 단일 파일 삭제 정보 갱신 실패 (잘못된 요청): {}", e.getMessage());
            throw e;
        } catch (Exception e) {
            logger.error("L-039 단일 파일 삭제 정보 갱신 중 오류 발생: {}", e.getMessage(), e);
            throw new RuntimeException("단일 파일 삭제 정보 갱신 중 오류가 발생했습니다: " + e.getMessage(), e);
        }
    }

    /**
     * L-039: 특정 파일 존재 여부 조회
     * 
     * @param cnvsIdtId 대화 식별 아이디
     * @param fileUid 파일 아이디
     * @return 파일 존재 여부
     */
    public boolean checkFileExists(String cnvsIdtId, String fileUid) {
        logger.info("L-039 특정 파일 존재 여부 조회. cnvsIdtId: {}, fileUid: {}", cnvsIdtId, fileUid);
        
        if (Objects.isNull(cnvsIdtId) || cnvsIdtId.trim().isEmpty()) {
            throw new IllegalArgumentException("대화 식별 아이디는 필수입니다.");
        }
        
        if (Objects.isNull(fileUid) || fileUid.trim().isEmpty()) {
            throw new IllegalArgumentException("파일 아이디는 필수입니다.");
        }
        
        Integer count = singleFileDeleteInfoMapper.checkFileExists(cnvsIdtId, fileUid);
        return count > 0;
    }

    /**
     * L-039: 특정 파일 삭제 상태 조회
     * 
     * @param cnvsIdtId 대화 식별 아이디
     * @param fileUid 파일 아이디
     * @return 삭제 상태
     */
    public String getFileDeleteStatus(String cnvsIdtId, String fileUid) {
        logger.info("L-039 특정 파일 삭제 상태 조회. cnvsIdtId: {}, fileUid: {}", cnvsIdtId, fileUid);
        
        if (Objects.isNull(cnvsIdtId) || cnvsIdtId.trim().isEmpty()) {
            throw new IllegalArgumentException("대화 식별 아이디는 필수입니다.");
        }
        
        if (Objects.isNull(fileUid) || fileUid.trim().isEmpty()) {
            throw new IllegalArgumentException("파일 아이디는 필수입니다.");
        }
        
        return singleFileDeleteInfoMapper.getFileDeleteStatus(cnvsIdtId, fileUid);
    }

    /**
     * 단일 파일 삭제 정보 갱신 요청 데이터 검증
     * 
     * @param requestDto 단일 파일 삭제 정보 갱신 요청 DTO
     * @throws IllegalArgumentException 검증 실패 시
     */
    private void validateSingleFileDeleteInfoRequest(SingleFileDeleteInfoRequestDto requestDto) {
        if (requestDto == null) {
            throw new IllegalArgumentException("요청 데이터가 null입니다.");
        }
        
        if (Objects.isNull(requestDto.getCnvsIdtId()) || requestDto.getCnvsIdtId().trim().isEmpty()) {
            throw new IllegalArgumentException("대화 식별 아이디는 필수입니다.");
        }
        
        if (Objects.isNull(requestDto.getFileUid()) || requestDto.getFileUid().trim().isEmpty()) {
            throw new IllegalArgumentException("파일 아이디는 필수입니다.");
        }
        
        if (Objects.isNull(requestDto.getLogCont()) || requestDto.getLogCont().trim().isEmpty()) {
            throw new IllegalArgumentException("로그 내용은 필수입니다.");
        }
        
        if (Objects.isNull(requestDto.getSucYn()) || requestDto.getSucYn().trim().isEmpty()) {
            throw new IllegalArgumentException("성공 여부는 필수입니다.");
        }
        
        if (!"Y".equals(requestDto.getSucYn()) && !"N".equals(requestDto.getSucYn())) {
            throw new IllegalArgumentException("성공 여부는 Y 또는 N이어야 합니다.");
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
}
