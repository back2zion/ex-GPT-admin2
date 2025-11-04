package com.datastreams.gpt.chat.mapper;

import com.datastreams.gpt.chat.dto.QuerySaveRequestDto;
import com.datastreams.gpt.chat.dto.QuerySaveResponseDto;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface QuerySaveMapper {
    
    /**
     * L-033: 질의 저장
     * @param requestDto 질의 저장 요청 DTO
     * @return 질의 저장 응답 DTO
     */
    QuerySaveResponseDto insertQuerySave(QuerySaveRequestDto requestDto);
}
