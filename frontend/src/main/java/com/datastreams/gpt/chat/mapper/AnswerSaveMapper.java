package com.datastreams.gpt.chat.mapper;

import com.datastreams.gpt.chat.dto.AnswerSaveRequestDto;
import com.datastreams.gpt.chat.dto.AnswerSaveResponseDto;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface AnswerSaveMapper {
    
    /**
     * L-034: 답변 저장
     * @param requestDto 답변 저장 요청 DTO
     * @return 답변 저장 응답 DTO 리스트
     */
    List<AnswerSaveResponseDto> insertAnswerSave(AnswerSaveRequestDto requestDto);
}
