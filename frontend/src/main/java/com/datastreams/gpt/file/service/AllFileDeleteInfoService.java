package com.datastreams.gpt.file.service;

import com.datastreams.gpt.file.dto.AllFileDeleteInfoRequestDto;
import com.datastreams.gpt.file.dto.AllFileDeleteInfoResponseDto;
import com.datastreams.gpt.file.mapper.AllFileDeleteInfoMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Objects;

@Service
@Transactional
public class AllFileDeleteInfoService {

    private static final Logger logger = LoggerFactory.getLogger(AllFileDeleteInfoService.class);

    @Autowired
    private AllFileDeleteInfoMapper allFileDeleteInfoMapper;

    /**
     * L-021: 전체 파일 삭제 정보 갱신
     * 특정 세션의 모든 파일 삭제 상태를 DB에 업데이트
     * 
     * @param requestDto 전체 파일 삭제 정보 갱신 요청 DTO
     * @return 전체 파일 삭제 정보 갱신 응답 DTO
     * @throws IllegalArgumentException 필수 파라미터 누락 시 발생
     * @throws RuntimeException DB 업데이트 오류 시 발생
     */
    public AllFileDeleteInfoResponseDto updateAllFileDeleteInfo(AllFileDeleteInfoRequestDto requestDto) {
        logger.info("L-021 전체 파일 삭제 정보 갱신 서비스 호출. cnvsIdtId: {}, sucYn: {}", 
                   requestDto.getCnvsIdtId(), requestDto.getSucYn());

        long startTime = System.currentTimeMillis();

        try {
            // 1. 입력 값 검증
            validateAllFileDeleteInfoRequest(requestDto);

            // 2. 세션별 파일 개수 조회 (업데이트 전)
            Integer totalFileCount = allFileDeleteInfoMapper.countFilesBySession(requestDto.getCnvsIdtId());
            logger.info("L-021 세션별 파일 개수 조회 완료. cnvsIdtId: {}, totalFileCount: {}", 
                       requestDto.getCnvsIdtId(), totalFileCount);

            if (totalFileCount == 0) {
                logger.warn("L-021 해당 세션에 파일이 없습니다. cnvsIdtId: {}", requestDto.getCnvsIdtId());
                throw new IllegalArgumentException("해당 세션에 파일이 없습니다.");
            }

            // 3. 전체 파일 삭제 정보 갱신 실행
            AllFileDeleteInfoResponseDto responseDto = allFileDeleteInfoMapper.updateAllFileDeleteInfo(requestDto);
            
            // 4. 응답 DTO 설정
            if (responseDto == null) {
                responseDto = new AllFileDeleteInfoResponseDto();
            }
            
            responseDto.setCnvsIdtId(requestDto.getCnvsIdtId());
            responseDto.setTxnNm("UPD_USR_UPLD_DOC_MNG");
            responseDto.setStatus("success");
            responseDto.setProcessingTime(System.currentTimeMillis() - startTime);
            responseDto.setUpdatedFileCount(responseDto.getCnt());
            responseDto.setSucYn(requestDto.getSucYn());

            // 5. 업데이트 후 삭제된 파일 개수 조회
            Integer deletedFileCount = allFileDeleteInfoMapper.countDeletedFilesBySession(requestDto.getCnvsIdtId());
            logger.info("L-021 삭제된 파일 개수 조회 완료. cnvsIdtId: {}, deletedFileCount: {}", 
                       requestDto.getCnvsIdtId(), deletedFileCount);

            logger.info("L-021 전체 파일 삭제 정보 갱신 성공. cnvsIdtId: {}, updatedCount: {}, processingTime: {}ms", 
                       requestDto.getCnvsIdtId(), responseDto.getCnt(), responseDto.getProcessingTime());

            return responseDto;

        } catch (IllegalArgumentException e) {
            logger.warn("L-021 전체 파일 삭제 정보 갱신 실패 (잘못된 요청): {}", e.getMessage());
            throw e;
        } catch (Exception e) {
            logger.error("L-021 전체 파일 삭제 정보 갱신 중 오류 발생: {}", e.getMessage(), e);
            throw new RuntimeException("전체 파일 삭제 정보 갱신 중 오류가 발생했습니다: " + e.getMessage(), e);
        }
    }

    /**
     * L-021: 세션별 파일 개수 조회
     * 
     * @param cnvsIdtId 대화 식별 아이디
     * @return 파일 개수
     */
    public Integer getFileCountBySession(String cnvsIdtId) {
        logger.info("L-021 세션별 파일 개수 조회. cnvsIdtId: {}", cnvsIdtId);
        
        if (Objects.isNull(cnvsIdtId) || cnvsIdtId.trim().isEmpty()) {
            throw new IllegalArgumentException("대화 식별 아이디는 필수입니다.");
        }
        
        return allFileDeleteInfoMapper.countFilesBySession(cnvsIdtId);
    }

    /**
     * L-021: 세션별 삭제된 파일 개수 조회
     * 
     * @param cnvsIdtId 대화 식별 아이디
     * @return 삭제된 파일 개수
     */
    public Integer getDeletedFileCountBySession(String cnvsIdtId) {
        logger.info("L-021 세션별 삭제된 파일 개수 조회. cnvsIdtId: {}", cnvsIdtId);
        
        if (Objects.isNull(cnvsIdtId) || cnvsIdtId.trim().isEmpty()) {
            throw new IllegalArgumentException("대화 식별 아이디는 필수입니다.");
        }
        
        return allFileDeleteInfoMapper.countDeletedFilesBySession(cnvsIdtId);
    }

    /**
     * 전체 파일 삭제 정보 갱신 요청 데이터 검증
     * 
     * @param requestDto 전체 파일 삭제 정보 갱신 요청 DTO
     * @throws IllegalArgumentException 검증 실패 시
     */
    private void validateAllFileDeleteInfoRequest(AllFileDeleteInfoRequestDto requestDto) {
        if (requestDto == null) {
            throw new IllegalArgumentException("요청 데이터가 null입니다.");
        }
        
        if (Objects.isNull(requestDto.getCnvsIdtId()) || requestDto.getCnvsIdtId().trim().isEmpty()) {
            throw new IllegalArgumentException("대화 식별 아이디는 필수입니다.");
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
    }
}
