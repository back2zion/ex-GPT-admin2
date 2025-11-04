package com.datastreams.gpt.error.mapper;

import java.util.List;
import java.util.Map;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import com.datastreams.gpt.error.dto.ErrorChoiceListRequestDto;

/**
 * L-022: 오류 선택지 목록 조회 Mapper
 * 공통코드 레벨2 조회를 위한 데이터베이스 접근 인터페이스
 */
@Mapper
public interface ErrorChoiceListMapper {
    
    /**
     * 오류 선택지 목록 조회
     * @param requestDto 요청 데이터
     * @return 오류 선택지 목록
     */
    List<Map<String, Object>> selectErrorChoiceList(ErrorChoiceListRequestDto requestDto);
    
    /**
     * 오류 선택지 총 개수 조회
     * @param levelN1Cd 레벨1 코드
     * @return 총 개수
     */
    Integer selectErrorChoiceCount(@Param("levelN1Cd") String levelN1Cd);
}
