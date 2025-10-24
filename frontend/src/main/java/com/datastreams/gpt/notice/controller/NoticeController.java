package com.datastreams.gpt.notice.controller;

import com.datastreams.gpt.common.dto.ApiResponseDto;
import com.datastreams.gpt.notice.dto.NoticeDto;
import com.datastreams.gpt.notice.dto.NoticeDetailDto;
import com.datastreams.gpt.notice.dto.NoticeTodayDto;
import com.datastreams.gpt.notice.service.NoticeService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 공지사항 관련 API 컨트롤러
 * L-011: 공지사항 조회/상세보기 기능정의서 기준
 */
@RestController
@RequestMapping("/api/notice")
@CrossOrigin(origins = "*")
@Tag(name = "공지사항 API", description = "공지사항 조회 및 상세보기 API")
public class NoticeController {

    private static final Logger log = LoggerFactory.getLogger(NoticeController.class);
    
    @Autowired
    private NoticeService noticeService;

    /**
     * 공지사항 목록 조회 API
     * L-011: 공지사항 조회 기능정의서 기준
     * 
     * @return 공지사항 목록
     */
    @GetMapping("/notices")
    @Operation(summary = "공지사항 목록 조회", description = "공지사항 목록을 조회합니다.")
    public ResponseEntity<ApiResponseDto<List<NoticeDto>>> getNoticeList() {
        
        log.info("[공지사항 목록 조회 API] 호출됨");
        
        try {
            List<NoticeDto> noticeList = noticeService.getNoticeList();
            
            if (noticeList != null && !noticeList.isEmpty()) {
                return ResponseEntity.ok(ApiResponseDto.<List<NoticeDto>>success(
                    "공지사항 목록을 성공적으로 조회했습니다.",
                    noticeList
                ));
            } else {
                return ResponseEntity.ok(ApiResponseDto.<List<NoticeDto>>success(
                    "조회된 공지사항이 없습니다.",
                    noticeList
                ));
            }
            
        } catch (Exception e) {
            log.error("[공지사항 목록 조회 API] 오류 발생: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(ApiResponseDto.error(
                "공지사항 목록 조회 중 오류가 발생했습니다: " + e.getMessage()
            ));
        }
    }

    /**
     * 공지사항 상세보기 API
     * L-011: 공지사항 상세보기 기능정의서 기준
     * 
     * @param brdId 게시판 아이디
     * @param pstId 게시글 아이디
     * @return 공지사항 상세 정보
     */
    @GetMapping("/notices/detail")
    @Operation(summary = "공지사항 상세보기", description = "특정 공지사항의 상세 내용을 조회합니다.")
    public ResponseEntity<ApiResponseDto<NoticeDetailDto>> getNoticeDetail(
            @Parameter(description = "게시판 아이디") @RequestParam Long brdId,
            @Parameter(description = "게시글 아이디") @RequestParam Long pstId) {
        
        log.info("[공지사항 상세보기 API] 호출됨 - BRD_ID: {}, PST_ID: {}", brdId, pstId);
        
        try {
            NoticeDetailDto noticeDetail = noticeService.getNoticeDetail(brdId, pstId);
            
            return ResponseEntity.ok(ApiResponseDto.success(
                "공지사항 상세보기를 성공적으로 조회했습니다.",
                noticeDetail
            ));
            
        } catch (IllegalArgumentException e) {
            log.error("[공지사항 상세보기 API] 잘못된 파라미터: {}", e.getMessage());
            return ResponseEntity.badRequest().body(ApiResponseDto.error(
                "잘못된 요청입니다: " + e.getMessage()
            ));
        } catch (Exception e) {
            log.error("[공지사항 상세보기 API] 오류 발생: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(ApiResponseDto.error(
                "공지사항 상세보기 조회 중 오류가 발생했습니다: " + e.getMessage()
            ));
        }
    }

    /**
     * 오늘 기준 팝업 게시글 조회 API
     * L-011: 오늘 기준 팝업 게시글 조회 기능정의서 기준
     * 
     * @return 오늘 기준 팝업 게시글 목록
     */
    @GetMapping("/notices/today")
    @Operation(summary = "오늘 기준 팝업 게시글 조회", description = "오늘 기준으로 표시할 팝업 게시글 목록을 조회합니다.")
    public ResponseEntity<ApiResponseDto<List<NoticeTodayDto>>> getNoticeToday() {
        
        log.info("[오늘 기준 팝업 게시글 조회 API] 호출됨");
        
        try {
            List<NoticeTodayDto> noticeTodayList = noticeService.getNoticeToday();
            
            if (noticeTodayList != null && !noticeTodayList.isEmpty()) {
                return ResponseEntity.ok(ApiResponseDto.<List<NoticeTodayDto>>success(
                    "오늘 기준 팝업 게시글을 성공적으로 조회했습니다.",
                    noticeTodayList
                ));
            } else {
                return ResponseEntity.ok(ApiResponseDto.<List<NoticeTodayDto>>success(
                    "조회된 팝업 게시글이 없습니다.",
                    noticeTodayList
                ));
            }
            
        } catch (Exception e) {
            log.error("[오늘 기준 팝업 게시글 조회 API] 오류 발생: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(ApiResponseDto.error(
                "오늘 기준 팝업 게시글 조회 중 오류가 발생했습니다: " + e.getMessage()
            ));
        }
    }

    /**
     * 간단한 테스트 API
     */
    @GetMapping("/health")
    @Operation(summary = "API 테스트", description = "공지사항 API가 정상 작동하는지 확인합니다.")
    public ResponseEntity<ApiResponseDto<String>> test() {
        log.info("[공지사항 테스트 API] 호출됨");
        return ResponseEntity.ok(ApiResponseDto.success(
            "공지사항 API가 정상 작동합니다.",
            "OK"
        ));
    }
}
