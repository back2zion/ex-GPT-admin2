package com.datastreams.gpt.file.mapper;

import com.datastreams.gpt.file.dto.FileUploadHistoryCreateRequestDto;
import com.datastreams.gpt.file.dto.FileUploadHistoryCreateResponseDto;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface FileUploadHistoryCreateMapper {

    /**
     * L-016: 파일 업로드 이력 생성
     * @param requestDto 파일 업로드 이력 생성 요청 DTO
     * @return 파일 업로드 이력 생성 응답 DTO
     */
    FileUploadHistoryCreateResponseDto createFileUploadHistory(FileUploadHistoryCreateRequestDto requestDto);
}
