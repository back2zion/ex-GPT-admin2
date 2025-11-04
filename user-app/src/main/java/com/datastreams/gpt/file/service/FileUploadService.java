package com.datastreams.gpt.file.service;

import com.datastreams.gpt.file.dto.FileUploadHistoryRequestDto;
import com.datastreams.gpt.file.dto.FileUploadHistoryResponseDto;
import com.datastreams.gpt.file.mapper.FileUploadMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 파일 업로드 관련 서비스 클래스
 */
@Service
@Transactional
public class FileUploadService {
    
    private static final Logger logger = LoggerFactory.getLogger(FileUploadService.class);
    
    @Autowired
    private FileUploadMapper fileUploadMapper;
    
    /**
     * L-016: 파일 업로드 이력 생성 (Insert)
     * 
     * @param requestDto 파일 업로드 이력 생성 요청 데이터
     * @return 파일 업로드 이력 생성 응답 데이터
     * @throws Exception 처리 중 오류 발생 시
     */
    public FileUploadHistoryResponseDto createFileUploadHistory(FileUploadHistoryRequestDto requestDto) throws Exception {
        logger.info("파일 업로드 이력 생성 시작 - 사용자: {}, 파일명: {}", 
                   requestDto.getUsrId(), requestDto.getFileNm());
        
        try {
            // 입력 파라미터 검증
            validateFileUploadHistoryRequest(requestDto);
            
            // 파일 업로드 이력 생성
            FileUploadHistoryResponseDto responseDto = fileUploadMapper.insertFileUploadHistory(requestDto);
            
            if (responseDto == null) {
                throw new Exception("파일 업로드 이력 생성 실패");
            }
            
            logger.info("파일 업로드 이력 생성 완료 - 대화ID: {}, 파일순번: {}, 실행건수: {}", 
                       responseDto.getCnvsIdtId(), responseDto.getFileUpldSeq(), responseDto.getCnt());
            
            return responseDto;
            
        } catch (Exception e) {
            logger.error("파일 업로드 이력 생성 중 오류 발생", e);
            throw new Exception("파일 업로드 이력 생성 중 오류가 발생했습니다: " + e.getMessage());
        }
    }
    
    /**
     * 파일 업로드 순번으로 파일 정보 조회
     * 
     * @param fileUpldSeq 파일 업로드 순번
     * @return 파일 업로드 정보
     * @throws Exception 처리 중 오류 발생 시
     */
    public FileUploadHistoryRequestDto getFileUploadBySeq(Long fileUpldSeq) throws Exception {
        logger.info("파일 업로드 정보 조회 - 순번: {}", fileUpldSeq);
        
        if (fileUpldSeq == null) {
            throw new IllegalArgumentException("파일 업로드 순번은 필수입니다.");
        }
        
        try {
            FileUploadHistoryRequestDto fileUpload = fileUploadMapper.selectFileUploadBySeq(fileUpldSeq);
            
            if (fileUpload == null) {
                throw new Exception("해당 파일 업로드 정보를 찾을 수 없습니다.");
            }
            
            logger.info("파일 업로드 정보 조회 완료 - 파일명: {}", fileUpload.getFileNm());
            return fileUpload;
            
        } catch (Exception e) {
            logger.error("파일 업로드 정보 조회 중 오류 발생", e);
            throw new Exception("파일 업로드 정보 조회 중 오류가 발생했습니다: " + e.getMessage());
        }
    }
    
    /**
     * 대화 식별 ID로 파일 업로드 목록 조회
     * 
     * @param cnvsIdtId 대화 식별 ID
     * @return 파일 업로드 목록
     * @throws Exception 처리 중 오류 발생 시
     */
    public List<FileUploadHistoryRequestDto> getFileUploadListByConversation(String cnvsIdtId) throws Exception {
        logger.info("대화별 파일 업로드 목록 조회 - 대화ID: {}", cnvsIdtId);
        
        if (cnvsIdtId == null || cnvsIdtId.trim().isEmpty()) {
            throw new IllegalArgumentException("대화 식별 ID는 필수입니다.");
        }
        
        try {
            List<FileUploadHistoryRequestDto> fileUploadList = fileUploadMapper.selectFileUploadListByConversation(cnvsIdtId);
            
            logger.info("대화별 파일 업로드 목록 조회 완료 - 건수: {}", fileUploadList.size());
            return fileUploadList;
            
        } catch (Exception e) {
            logger.error("대화별 파일 업로드 목록 조회 중 오류 발생", e);
            throw new Exception("대화별 파일 업로드 목록 조회 중 오류가 발생했습니다: " + e.getMessage());
        }
    }
    
    /**
     * 파일 업로드 이력 생성 요청 데이터 검증
     * 
     * @param requestDto 검증할 요청 데이터
     * @throws IllegalArgumentException 검증 실패 시
     */
    private void validateFileUploadHistoryRequest(FileUploadHistoryRequestDto requestDto) {
        if (requestDto == null) {
            throw new IllegalArgumentException("요청 데이터는 필수입니다.");
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
        
        // CNVS_IDT_ID는 첫 업로드 시 빈 값이 허용됨
        // null 체크는 하되, 빈 문자열은 허용
    }
}
