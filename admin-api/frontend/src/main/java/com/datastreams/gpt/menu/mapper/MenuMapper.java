package com.datastreams.gpt.menu.mapper;

import com.datastreams.gpt.menu.dto.MenuInfoDto;
import com.datastreams.gpt.menu.dto.RecommendedQuestionDto;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface MenuMapper {
    
    /**
     * L-007: 사용자별 메뉴 목록 조회
     * @param usrId 사용자 ID
     * @return 메뉴 목록
     */
    List<MenuInfoDto> selectUserMenus(@Param("usrId") String usrId);
    
    /**
     * L-007: 사용자별 메뉴 목록 조회 (getUserMenus)
     * @param usrId 사용자 ID
     * @return 메뉴 목록
     */
    List<MenuInfoDto> getUserMenus(@Param("usrId") String usrId);
    
    /**
     * L-013: 메뉴별 추천 질의 조회
     * @param menuId 메뉴 ID
     * @return 추천 질의 목록
     */
    List<RecommendedQuestionDto> selectRecommendedQuestions(@Param("menuId") Long menuId);
}