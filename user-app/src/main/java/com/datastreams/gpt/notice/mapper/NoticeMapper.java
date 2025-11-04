package com.datastreams.gpt.notice.mapper;

import com.datastreams.gpt.notice.dto.NoticeDto;
import com.datastreams.gpt.notice.dto.NoticeDetailDto;
import com.datastreams.gpt.notice.dto.NoticeTodayDto;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 공지사항 MyBatis 매퍼 인터페이스
 * L-011: 공지사항 조회/상세보기 기능정의서 기준
 */
@Mapper
public interface NoticeMapper {

    /**
     * 공지사항 목록 조회
     * L-011: 공지사항 조회 기능정의서 쿼리
     * 
     * @return 공지사항 목록
     */
    List<NoticeDto> getNoticeList();

    /**
     * 공지사항 상세보기
     * L-011: 공지사항 상세보기 기능정의서 쿼리
     * 
     * @param brdId 게시판 아이디
     * @param pstId 게시글 아이디
     * @return 공지사항 상세 정보
     */
    NoticeDetailDto getNoticeDetail(@Param("brdId") Long brdId, @Param("pstId") Long pstId);

    /**
     * 오늘 기준 팝업 게시글 조회
     * L-011: 오늘 기준 팝업 게시글 조회 기능정의서 쿼리
     * 
     * @return 오늘 기준 팝업 게시글 목록
     */
    List<NoticeTodayDto> getNoticeToday();
}
