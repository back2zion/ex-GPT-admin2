package com.datastreams.gpt.menu.service;

import com.datastreams.gpt.menu.dto.MenuInfoDto;
import com.datastreams.gpt.menu.dto.RecommendedQuestionDto;
import com.datastreams.gpt.menu.mapper.MenuMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 메뉴 정보 관리 서비스
 * L-007: 메뉴 조회 기능
 */
@Service
public class MenuService {
    
    private static final Logger log = LoggerFactory.getLogger(MenuService.class);
    
    @Autowired
    private MenuMapper menuMapper;
    
    /**
     * 사용자별 메뉴 목록 조회 (L-007)
     * @param usrId 사용자 ID
     * @return 메뉴 목록
     */
    public List<MenuInfoDto> getUserMenus(String usrId) {
        try {
            List<MenuInfoDto> menuList = menuMapper.getUserMenus(usrId);
            
            if (menuList != null && !menuList.isEmpty()) {
                log.info("[L-007] 메뉴 조회 성공 - 사용자: {}, 메뉴 수: {}", usrId, menuList.size());
                
                // 메뉴 목록 로깅 (디버깅용)
                for (MenuInfoDto menu : menuList) {
                    log.debug("[L-007] 메뉴 정보 - ID: {}, 이름: {}, URL: {}, 순번: {}", 
                        menu.getMenuId(), menu.getMenuNm(), menu.getCallUrl(), menu.getMenuSeq());
                }
            } else {
                log.warn("[L-007] 메뉴 없음 - 사용자: {}", usrId);
            }
            
            return menuList;
        } catch (Exception e) {
            log.error("[L-007] 메뉴 조회 실패 - 사용자: {}, 에러: {}", usrId, e.getMessage());
            throw new RuntimeException("메뉴 조회 실패", e);
        }
    }

    /**
     * L-013: 메뉴별 추천 질의 조회
     * @param menuId 메뉴 ID
     * @return 추천 질의 목록
     */
    public List<RecommendedQuestionDto> getRecommendedQuestions(Long menuId) {
        log.info("[L-013] 메뉴별 추천 질의 조회 시작 - 메뉴 ID: {}", menuId);
        
        try {
            List<RecommendedQuestionDto> questionList = menuMapper.selectRecommendedQuestions(menuId);
            log.info("[L-013] 메뉴별 추천 질의 조회 완료 - 메뉴 ID: {}, 질의 수: {}", menuId, questionList.size());
            return questionList;
        } catch (Exception e) {
            log.error("[L-013] 메뉴별 추천 질의 조회 중 오류 발생 - 메뉴 ID: {}, 에러: {}", menuId, e.getMessage(), e);
            throw new RuntimeException("추천 질의 조회 중 오류가 발생했습니다: " + e.getMessage());
        }
    }
}
