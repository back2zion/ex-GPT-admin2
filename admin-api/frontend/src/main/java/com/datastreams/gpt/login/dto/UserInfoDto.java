package com.datastreams.gpt.login.dto;

/**
 * 사용자 정보 DTO
 * L-005: 사용자 조회 결과 데이터 (기술정의서 기준)
 */
public class UserInfoDto {
    
    private String usrId;           // 사용자 ID
    private String usrNm;           // 사용자 명
    private String deptCd;          // 부서 코드
    private String deptNm;          // 부서 명
    private String jikjongCd;       // 직종 코드
    private String jikjongNm;       // 직종 명
    private String jikwiCd;         // 직위 코드
    private String jikwiNm;         // 직위 명
    private String jikgeupCd;       // 직급 코드
    private String jikgeupNm;       // 직급 명
    private String email;           // 이메일
    private String telNo;           // 전화번호
    private String useYn;           // 사용 여부
    private String sysAccsYn;       // 시스템 접근 여부
    private String mgrAuthYn;       // 관리자 권한 여부
    private String vceMdlUseYn;     // 음성 모델 사용 여부
    private String imgMdlUseYn;     // 이미지 모델 사용 여부
    private String fntSizeCd;       // 폰트 크기 코드
    private String uiThmCd;         // 테마 코드
    
    // 기존 호환성을 위한 필드들 (deprecated)
    @Deprecated
    private String srtNm;           // 직종명 (jikjongNm으로 대체)
    @Deprecated
    private String grdNm;           // 직위명 (jikwiNm으로 대체)
    @Deprecated
    private String posNm;           // 직급명 (jikgeupNm으로 대체)
    @Deprecated
    private String stgubun;         // 상태코드 (useYn으로 대체)
    
    // 기본 생성자
    public UserInfoDto() {}
    
    // Getter/Setter 메서드들
    public String getUsrId() {
        return usrId;
    }
    
    public void setUsrId(String usrId) {
        this.usrId = usrId;
    }
    
    public String getUsrNm() {
        return usrNm;
    }
    
    public void setUsrNm(String usrNm) {
        this.usrNm = usrNm;
    }
    
    public String getDeptCd() {
        return deptCd;
    }
    
    public void setDeptCd(String deptCd) {
        this.deptCd = deptCd;
    }
    
    public String getDeptNm() {
        return deptNm;
    }
    
    public void setDeptNm(String deptNm) {
        this.deptNm = deptNm;
    }
    
    public String getSrtNm() {
        return srtNm;
    }
    
    public void setSrtNm(String srtNm) {
        this.srtNm = srtNm;
    }
    
    public String getGrdNm() {
        return grdNm;
    }
    
    public void setGrdNm(String grdNm) {
        this.grdNm = grdNm;
    }
    
    public String getPosNm() {
        return posNm;
    }
    
    public void setPosNm(String posNm) {
        this.posNm = posNm;
    }
    
    public String getStgubun() {
        return stgubun;
    }
    
    public void setStgubun(String stgubun) {
        this.stgubun = stgubun;
    }
    
    public String getFntSizeCd() {
        return fntSizeCd;
    }
    
    public void setFntSizeCd(String fntSizeCd) {
        this.fntSizeCd = fntSizeCd;
    }
    
    public String getUiThmCd() {
        return uiThmCd;
    }
    
    public void setUiThmCd(String uiThmCd) {
        this.uiThmCd = uiThmCd;
    }
    
    public String getSysAccsYn() {
        return sysAccsYn;
    }
    
    public void setSysAccsYn(String sysAccsYn) {
        this.sysAccsYn = sysAccsYn;
    }
    
    public String getMgrAuthYn() {
        return mgrAuthYn;
    }
    
    public void setMgrAuthYn(String mgrAuthYn) {
        this.mgrAuthYn = mgrAuthYn;
    }
    
    public String getVceMdlUseYn() {
        return vceMdlUseYn;
    }
    
    public void setVceMdlUseYn(String vceMdlUseYn) {
        this.vceMdlUseYn = vceMdlUseYn;
    }
    
    public String getImgMdlUseYn() {
        return imgMdlUseYn;
    }
    
    public void setImgMdlUseYn(String imgMdlUseYn) {
        this.imgMdlUseYn = imgMdlUseYn;
    }
    
    // 새로운 필드들의 Getter/Setter
    public String getJikjongCd() {
        return jikjongCd;
    }
    
    public void setJikjongCd(String jikjongCd) {
        this.jikjongCd = jikjongCd;
    }
    
    public String getJikjongNm() {
        return jikjongNm;
    }
    
    public void setJikjongNm(String jikjongNm) {
        this.jikjongNm = jikjongNm;
    }
    
    public String getJikwiCd() {
        return jikwiCd;
    }
    
    public void setJikwiCd(String jikwiCd) {
        this.jikwiCd = jikwiCd;
    }
    
    public String getJikwiNm() {
        return jikwiNm;
    }
    
    public void setJikwiNm(String jikwiNm) {
        this.jikwiNm = jikwiNm;
    }
    
    public String getJikgeupCd() {
        return jikgeupCd;
    }
    
    public void setJikgeupCd(String jikgeupCd) {
        this.jikgeupCd = jikgeupCd;
    }
    
    public String getJikgeupNm() {
        return jikgeupNm;
    }
    
    public void setJikgeupNm(String jikgeupNm) {
        this.jikgeupNm = jikgeupNm;
    }
    
    public String getEmail() {
        return email;
    }
    
    public void setEmail(String email) {
        this.email = email;
    }
    
    public String getTelNo() {
        return telNo;
    }
    
    public void setTelNo(String telNo) {
        this.telNo = telNo;
    }
    
    public String getUseYn() {
        return useYn;
    }
    
    public void setUseYn(String useYn) {
        this.useYn = useYn;
    }
}
