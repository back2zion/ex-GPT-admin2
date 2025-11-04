package com.datastreams.gpt.file.mapper;

import com.datastreams.gpt.file.dto.FileUploadHistoryUpdateRequestDto;
import com.datastreams.gpt.file.dto.FileUploadHistoryUpdateResponseDto;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface FileUploadHistoryUpdateMapper {
    
    /**
     * L-018: 파일 업로드 이력 갱신
     * 
     * @param requestDto 파일 업로드 이력 갱신 요청 DTO
     * @return 파일 업로드 이력 갱신 응답 DTO
     */
    FileUploadHistoryUpdateResponseDto updateFileUploadHistory(FileUploadHistoryUpdateRequestDto requestDto);
}
