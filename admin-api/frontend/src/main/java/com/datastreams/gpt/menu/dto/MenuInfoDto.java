package com.datastreams.gpt.menu.dto;

/**
 * 메뉴 정보 DTO
 * L-007: 메뉴 조회 결과 데이터
 */
public class MenuInfoDto {
    
    private String menuId;              // 메뉴 아이디 (PK)
    private String menuIdtId;           // 메뉴 식별 아이디
    private String menuNm;              // 메뉴 명
    private String menuDesc;            // 메뉴 설명
    private String upperMenuId;         // 상위 메뉴 아이디 (계층구조)
    private String callUrl;             // 호출 URL
    private Integer menuSeq;            // 메뉴 순번
    private String mainMenuUseYn;       // 메인 메뉴 사용 여부
    private String menuTypCd;           // UI 메뉴 유형 코드
    private String useYn;               // 사용 여부
    private String authYn;              // 사용자별 메뉴 권한 여부
    
    // 기본 생성자
    public MenuInfoDto() {}
    
    // Getter/Setter 메서드들
    public String getMenuId() {
        return menuId;
    }
    
    public void setMenuId(String menuId) {
        this.menuId = menuId;
    }
    
    public String getMenuIdtId() {
        return menuIdtId;
    }
    
    public void setMenuIdtId(String menuIdtId) {
        this.menuIdtId = menuIdtId;
    }
    
    public String getMenuNm() {
        return menuNm;
    }
    
    public void setMenuNm(String menuNm) {
        this.menuNm = menuNm;
    }
    
    public String getMenuDesc() {
        return menuDesc;
    }
    
    public void setMenuDesc(String menuDesc) {
        this.menuDesc = menuDesc;
    }
    
    public String getUpperMenuId() {
        return upperMenuId;
    }
    
    public void setUpperMenuId(String upperMenuId) {
        this.upperMenuId = upperMenuId;
    }
    
    public String getCallUrl() {
        return callUrl;
    }
    
    public void setCallUrl(String callUrl) {
        this.callUrl = callUrl;
    }
    
    public Integer getMenuSeq() {
        return menuSeq;
    }
    
    public void setMenuSeq(Integer menuSeq) {
        this.menuSeq = menuSeq;
    }
    
    public String getMainMenuUseYn() {
        return mainMenuUseYn;
    }
    
    public void setMainMenuUseYn(String mainMenuUseYn) {
        this.mainMenuUseYn = mainMenuUseYn;
    }
    
    public String getMenuTypCd() {
        return menuTypCd;
    }
    
    public void setMenuTypCd(String menuTypCd) {
        this.menuTypCd = menuTypCd;
    }
    
    public String getUseYn() {
        return useYn;
    }
    
    public void setUseYn(String useYn) {
        this.useYn = useYn;
    }
    
    public String getAuthYn() {
        return authYn;
    }
    
    public void setAuthYn(String authYn) {
        this.authYn = authYn;
    }
}
