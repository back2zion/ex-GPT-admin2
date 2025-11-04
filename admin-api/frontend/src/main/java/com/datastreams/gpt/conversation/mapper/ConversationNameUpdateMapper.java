package com.datastreams.gpt.conversation.mapper;

import java.util.List;
import java.util.Map;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import com.datastreams.gpt.conversation.dto.ConversationNameUpdateRequestDto;

/**
 * L-025: 대화 대표 명 변경 Mapper
 * 대화 대표 명 및 사용 여부를 업데이트하기 위한 데이터베이스 접근 인터페이스
 */
@Mapper
public interface ConversationNameUpdateMapper {
    
    /**
     * 대화 대표 명 및 사용 여부 업데이트
     * @param requestDto 요청 데이터
     * @return 업데이트 결과 (트랜잭션명, 건수)
     */
    List<Map<String, Object>> updateConversationName(ConversationNameUpdateRequestDto requestDto);
    
    /**
     * 업데이트된 대화 정보 조회
     * @param cnvsIdtId 대화 식별 ID
     * @return 업데이트된 대화 정보
     */
    Map<String, Object> selectUpdatedConversationInfo(@Param("cnvsIdtId") String cnvsIdtId);
}
