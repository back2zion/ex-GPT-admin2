package com.datastreams.gpt.file.mapper;

import com.datastreams.gpt.file.dto.AllFileDeleteInfoRequestDto;
import com.datastreams.gpt.file.dto.AllFileDeleteInfoResponseDto;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface AllFileDeleteInfoMapper {

    /**
     * L-021: 전체 파일 삭제 정보 갱신
     * 특정 세션의 모든 파일 삭제 상태를 DB에 업데이트
     * 
     * @param requestDto 전체 파일 삭제 정보 갱신 요청 DTO
     * @return 전체 파일 삭제 정보 갱신 응답 DTO
     */
    AllFileDeleteInfoResponseDto updateAllFileDeleteInfo(AllFileDeleteInfoRequestDto requestDto);

    /**
     * L-021: 세션별 파일 개수 조회
     * 특정 세션에 속한 파일 개수를 조회
     * 
     * @param cnvsIdtId 대화 식별 아이디
     * @return 파일 개수
     */
    Integer countFilesBySession(@Param("cnvsIdtId") String cnvsIdtId);

    /**
     * L-021: 세션별 삭제된 파일 개수 조회
     * 특정 세션에서 삭제된 파일 개수를 조회
     * 
     * @param cnvsIdtId 대화 식별 아이디
     * @return 삭제된 파일 개수
     */
    Integer countDeletedFilesBySession(@Param("cnvsIdtId") String cnvsIdtId);
}
