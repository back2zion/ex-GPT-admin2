package com.datastreams.gpt.file.mapper;

import com.datastreams.gpt.file.dto.FileUploadHistoryRequestDto;
import com.datastreams.gpt.file.dto.FileUploadHistoryResponseDto;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * 파일 업로드 관련 Mapper 인터페이스
 */
@Mapper
public interface FileUploadMapper {
    
    /**
     * L-016: 파일 업로드 이력 생성 (Insert)
     * 
     * @param requestDto 파일 업로드 이력 생성 요청 데이터
     * @return 파일 업로드 이력 생성 응답 데이터
     */
    FileUploadHistoryResponseDto insertFileUploadHistory(FileUploadHistoryRequestDto requestDto);
    
    /**
     * 파일 업로드 순번으로 파일 정보 조회
     * 
     * @param fileUpldSeq 파일 업로드 순번
     * @return 파일 업로드 정보
     */
    FileUploadHistoryRequestDto selectFileUploadBySeq(@Param("fileUpldSeq") Long fileUpldSeq);
    
    /**
     * 대화 식별 ID로 파일 업로드 목록 조회
     * 
     * @param cnvsIdtId 대화 식별 ID
     * @return 파일 업로드 목록
     */
    java.util.List<FileUploadHistoryRequestDto> selectFileUploadListByConversation(@Param("cnvsIdtId") String cnvsIdtId);
}
