package com.datastreams.gpt.notice.service;

import com.datastreams.gpt.notice.dto.NoticeDto;
import com.datastreams.gpt.notice.dto.NoticeDetailDto;
import com.datastreams.gpt.notice.dto.NoticeTodayDto;
import com.datastreams.gpt.notice.mapper.NoticeMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 공지사항 관리 서비스
 * L-011: 공지사항 조회/상세보기 기능정의서 기준
 */
@Service
public class NoticeService {

    private static final Logger log = LoggerFactory.getLogger(NoticeService.class);
    
    @Autowired
    private NoticeMapper noticeMapper;

    /**
     * 공지사항 목록 조회
     * L-011: 공지사항 조회 기능정의서 쿼리 실행
     * 
     * @return 공지사항 목록
     */
    public List<NoticeDto> getNoticeList() {
        try {
            log.info("[L-011 공지사항 조회] 공지사항 목록 조회 시작");
            
            List<NoticeDto> noticeList = noticeMapper.getNoticeList();
            
            log.info("[L-011 공지사항 조회] 조회 완료 - 총 {}건", noticeList.size());
            
            return noticeList;
            
        } catch (Exception e) {
            log.error("[L-011 공지사항 조회] 오류 발생: {}", e.getMessage(), e);
            throw new RuntimeException("공지사항 목록 조회 중 오류가 발생했습니다: " + e.getMessage());
        }
    }

    /**
     * 공지사항 상세보기
     * L-011: 공지사항 상세보기 기능정의서 쿼리 실행
     * 
     * @param brdId 게시판 아이디
     * @param pstId 게시글 아이디
     * @return 공지사항 상세 정보
     */
    public NoticeDetailDto getNoticeDetail(Long brdId, Long pstId) {
        try {
            log.info("[L-011 공지사항 상세보기] 조회 시작 - BRD_ID: {}, PST_ID: {}", brdId, pstId);
            
            if (brdId == null || pstId == null) {
                throw new IllegalArgumentException("게시판 ID와 게시글 ID는 필수입니다.");
            }
            
            NoticeDetailDto noticeDetail = noticeMapper.getNoticeDetail(brdId, pstId);
            
            if (noticeDetail == null) {
                log.warn("[L-011 공지사항 상세보기] 공지사항을 찾을 수 없습니다 - BRD_ID: {}, PST_ID: {}", brdId, pstId);
                throw new RuntimeException("해당 공지사항을 찾을 수 없습니다.");
            }
            
            log.info("[L-011 공지사항 상세보기] 조회 완료 - 제목: {}", noticeDetail.getTitleNm());
            
            return noticeDetail;
            
        } catch (IllegalArgumentException e) {
            log.error("[L-011 공지사항 상세보기] 잘못된 파라미터: {}", e.getMessage());
            throw e;
        } catch (Exception e) {
            log.error("[L-011 공지사항 상세보기] 오류 발생: {}", e.getMessage(), e);
            throw new RuntimeException("공지사항 상세보기 조회 중 오류가 발생했습니다: " + e.getMessage());
        }
    }

    /**
     * 오늘 기준 팝업 게시글 조회
     * L-011: 오늘 기준 팝업 게시글 조회 기능정의서 쿼리 실행
     * 
     * @return 오늘 기준 팝업 게시글 목록
     */
    public List<NoticeTodayDto> getNoticeToday() {
        try {
            log.info("[L-011 오늘 기준 팝업 게시글 조회] 조회 시작");
            
            List<NoticeTodayDto> noticeTodayList = noticeMapper.getNoticeToday();
            
            log.info("[L-011 오늘 기준 팝업 게시글 조회] 조회 완료 - 총 {}건", noticeTodayList.size());
            
            return noticeTodayList;
            
        } catch (Exception e) {
            log.error("[L-011 오늘 기준 팝업 게시글 조회] 오류 발생: {}", e.getMessage(), e);
            throw new RuntimeException("오늘 기준 팝업 게시글 조회 중 오류가 발생했습니다: " + e.getMessage());
        }
    }
}
