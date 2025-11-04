package com.datastreams.gpt.file.mapper;

import com.datastreams.gpt.file.dto.SingleFileDeleteInfoRequestDto;
import com.datastreams.gpt.file.dto.SingleFileDeleteInfoResponseDto;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface SingleFileDeleteInfoMapper {

    /**
     * L-039: 단일 파일 삭제 정보 갱신
     * 특정 세션의 특정 파일 삭제 상태를 DB에 업데이트
     * 
     * @param requestDto 단일 파일 삭제 정보 갱신 요청 DTO
     * @return 단일 파일 삭제 정보 갱신 응답 DTO
     */
    SingleFileDeleteInfoResponseDto updateSingleFileDeleteInfo(SingleFileDeleteInfoRequestDto requestDto);

    /**
     * L-039: 특정 파일 존재 여부 조회
     * 특정 세션의 특정 파일이 존재하는지 조회
     * 
     * @param cnvsIdtId 대화 식별 아이디
     * @param fileUid 파일 아이디
     * @return 파일 존재 여부 (1: 존재, 0: 없음)
     */
    Integer checkFileExists(@Param("cnvsIdtId") String cnvsIdtId, @Param("fileUid") String fileUid);

    /**
     * L-039: 특정 파일 삭제 상태 조회
     * 특정 세션의 특정 파일 삭제 상태를 조회
     * 
     * @param cnvsIdtId 대화 식별 아이디
     * @param fileUid 파일 아이디
     * @return 삭제 상태 (Y: 삭제됨, N: 삭제 안됨)
     */
    String getFileDeleteStatus(@Param("cnvsIdtId") String cnvsIdtId, @Param("fileUid") String fileUid);
}
