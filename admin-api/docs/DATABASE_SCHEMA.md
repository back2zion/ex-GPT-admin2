# 데이터베이스 스키마 문서

## 개요

ex-GPT 관리 시스템의 데이터베이스 스키마입니다. PostgreSQL을 사용하며, SQLAlchemy ORM을 통해 관리됩니다.

이 문서는 전체 데이터베이스 스키마의 **정식 참조 문서**입니다. 코드 작성 시 반드시 이 문서를 참고하세요.

---

## 테이블 분류 및 목록

### 1. 공통 코드 관리 (Common Code Management)

#### COM_CD_LV1 (공통 코드 레벨1)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| LEVEL_N1_SEQ | 레벨 1번 순번 | INTEGER | - | N | N | Y | - | 시퀀스 |
| LEVEL_N1_CD | 레벨 1번 코드 | VARCHAR | 50 | Y | N | Y | - | 코드 |
| LEVEL_N1_NM | 레벨 1번 명 | VARCHAR | 500 | N | N | Y | - | 코드명 |
| LEVEL_N1_DESC | 레벨 1번 설명 | VARCHAR | 2000 | N | N | N | - | 설명 |
| CD_SEQ | 코드 순번 | INTEGER | - | N | N | N | - | 정렬 순서 |
| USE_YN | 사용 여부 | VARCHAR | 1 | N | N | Y | - | Y/N |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | - | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

#### COM_CD_LV2 (공통 코드 레벨2)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| LEVEL_N2_SEQ | 레벨 2번 순번 | INTEGER | - | N | N | Y | - | 시퀀스 |
| LEVEL_N2_CD | 레벨 2번 코드 | VARCHAR | 50 | Y | N | Y | - | 코드 |
| LEVEL_N1_CD | 레벨 1번 코드 | VARCHAR | 50 | Y | Y | Y | - | 상위코드 FK |
| LEVEL_N2_NM | 레벨 2번 명 | VARCHAR | 500 | N | N | Y | - | 코드명 |
| LEVEL_N2_DESC | 레벨 2번 설명 | VARCHAR | 2000 | N | N | N | - | 설명 |
| CD_SEQ | 코드 순번 | INTEGER | - | N | N | N | - | 정렬 순서 |
| USE_YN | 사용 여부 | VARCHAR | 1 | N | N | Y | - | Y/N |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | - | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

**관계**: COM_CD_LV2.LEVEL_N1_CD → COM_CD_LV1.LEVEL_N1_CD

#### COM_CD_LV3 (공통 코드 레벨3)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| LEVEL_N3_SEQ | 레벨 3번 순번 | INTEGER | - | N | N | Y | - | 시퀀스 |
| LEVEL_N3_CD | 레벨 3번 코드 | VARCHAR | 50 | Y | N | Y | - | 코드 |
| LEVEL_N1_CD | 레벨 1번 코드 | VARCHAR | 50 | Y | Y | Y | - | 상위코드1 FK |
| LEVEL_N2_CD | 레벨 2번 코드 | VARCHAR | 50 | Y | Y | Y | - | 상위코드2 FK |
| LEVEL_N3_NM | 레벨 3번 명 | VARCHAR | 500 | N | N | Y | - | 코드명 |
| LEVEL_N3_DESC | 레벨 3번 설명 | VARCHAR | 2000 | N | N | N | - | 설명 |
| CD_SEQ | 코드 순번 | INTEGER | - | N | N | N | - | 정렬 순서 |
| USE_YN | 사용 여부 | VARCHAR | 1 | N | N | Y | - | Y/N |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | - | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

**복합키**: (LEVEL_N3_CD, LEVEL_N1_CD, LEVEL_N2_CD)

#### COM_CD_LV4, COM_CD_LV5
레벨3과 동일한 구조로 계층이 깊어짐 (상세 컬럼은 위 패턴 참조)

---

### 2. 조직 및 사용자 관리 (Organization & User Management)

#### DEPT_INFO (부서정보)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| DEPT_ID | 부서 아이디 | VARCHAR | 50 | Y | N | Y | - | 부서 고유 ID |
| DEPT_NM | 부서 명 | VARCHAR | 500 | N | N | Y | - | 부서명 |
| UPPER_DEPT_ID | 상위 부서 아이디 | VARCHAR | 50 | N | N | N | - | 상위 부서 (자기참조) |
| USE_YN | 사용 여부 | VARCHAR | 1 | N | N | Y | - | Y/N |
| EFF_STRT_DT | 유효 시작 일시 | TIMESTAMP | - | N | N | N | - | 유효기간 시작 |
| EFF_END_DT | 유효 종료 일시 | TIMESTAMP | - | N | N | Y | - | 유효기간 종료 |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | - | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

**자기참조**: DEPT_INFO.UPPER_DEPT_ID → DEPT_INFO.DEPT_ID

#### USR_INFO (사용자 정보)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| USR_ID | 사용자 아이디 | VARCHAR | 50 | Y | N | Y | - | 사용자 고유 ID |
| USR_NM | 사용자 명 | VARCHAR | 50 | N | N | Y | - | 사용자명 |
| DEPT_ID | 부서 아이디 | VARCHAR | 50 | N | N | Y | - | 소속 부서 |
| USR_POS_CD | 사용자 직급 코드 | VARCHAR | 50 | N | N | N | - | 직급 코드 |
| USR_SRT_CD | 사용자 직종 코드 | VARCHAR | 50 | N | N | N | - | 직종 코드 |
| USR_REP_CD | 사용자 직책 코드 | VARCHAR | 50 | N | N | N | - | 직책 코드 |
| USR_STAT_CLS_CD | 사용자 상태 구분코드 | VARCHAR | 50 | N | N | N | - | 상태 (재직/퇴사 등) |
| USE_YN | 사용 여부 | VARCHAR | 1 | N | N | Y | - | Y/N |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | - | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

#### USR_PRV_CONF (사용자 개인 설정)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| PRV_CONF_ID | 개인 설정 아이디 | BIGINT | - | Y | N | Y | - | 설정 고유 ID |
| USR_ID | 사용자 아이디 | VARCHAR | 50 | N | Y | Y | - | 사용자 FK |
| FNT_SIZE_CD | 폰트 크기 코드 | VARCHAR | 50 | N | N | N | - | 폰트 설정 |
| UI_THM_CD | UI 테마 코드 | VARCHAR | 50 | N | N | N | - | 테마 설정 |
| SYS_ACCS_YN | 시스템 접근 여부 | VARCHAR | 1 | N | N | N | N | 접근 허용 |
| MGR_AUTH_YN | 관리자 권한 여부 | VARCHAR | 1 | N | N | N | N | 관리자 권한 |
| VCE_MDL_USE_YN | 음성 모델 사용 여부 | VARCHAR | 1 | N | N | N | N | 음성 기능 |
| IMG_MDL_USE_YN | 이미지 모델 사용 여부 | VARCHAR | 1 | N | N | N | N | 이미지 기능 |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | CURRENT_TIMESTAMP | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

#### USR_CONN_LST (사용자 접속 목록)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| CONN_SEQ | 접속 순번 | BIGINT | - | Y | N | Y | - | 접속 고유 ID |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | Y | N | - | 사용자 FK |
| IP_INFO | IP 정보 | VARCHAR | 2000 | N | N | Y | - | 접속 IP |
| SESN_ID | 세션 아이디 | VARCHAR | 500 | N | N | N | - | 세션 ID |
| SESN_EXPR_DT | 세션 만료 일시 | TIMESTAMP | - | N | N | N | - | 세션 만료시간 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | CURRENT_TIMESTAMP | 접속일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

---

### 3. 메뉴 및 권한 관리 (Menu & Authorization)

#### MENU (메뉴)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| MENU_ID | 메뉴 아이디 | BIGINT | - | Y | N | Y | - | 메뉴 고유 ID |
| MENU_IDT_ID | 메뉴 식별 아이디 | VARCHAR | 50 | N | N | Y | - | 메뉴 식별자 |
| MENU_NM | 메뉴 명 | VARCHAR | 500 | N | N | Y | - | 메뉴명 |
| MENU_DESC | 메뉴 설명 | VARCHAR | 2000 | N | N | N | - | 설명 |
| UPPER_MENU_ID | 상위 메뉴 아이디 | VARCHAR | 50 | N | N | N | - | 상위 메뉴 (자기참조) |
| MENU_TYP_CD | 메뉴 유형 코드 | VARCHAR | 50 | N | N | Y | M | 메뉴 타입 |
| MENU_SEQ | 메뉴 순번 | INTEGER | - | N | N | N | - | 정렬 순서 |
| CALL_URL | 호출 URL | VARCHAR | 2000 | N | N | N | - | 메뉴 URL |
| USE_YN | 사용 여부 | VARCHAR | 1 | N | N | Y | Y | Y/N |
| MAIN_MENU_USE_YN | 메인 메뉴 사용 여부 | VARCHAR | 1 | N | N | Y | N | 메인 노출 여부 |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | CURRENT_TIMESTAMP | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

#### MENU_AUTH (메뉴 권한)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| MENU_ID | 메뉴 아이디 | BIGINT | - | Y | Y | Y | - | 메뉴 FK |
| ALW_AUTH_TGT_TYP_CD | 허용 권한 대상 유형 코드 | VARCHAR | 50 | Y | N | Y | - | 권한 타입 (USER/DEPT/ROLE) |
| ALW_AUTH_TGT_ID | 허용 권한 대상 아이디 | VARCHAR | 50 | Y | N | Y | - | 대상 ID |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | - | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

**복합키**: (MENU_ID, ALW_AUTH_TGT_TYP_CD, ALW_AUTH_TGT_ID)

#### MENU_RCM_QUES (메뉴 추천 질의)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| MENU_RCM_QUES_ID | 메뉴 추천 질의 아이디 | BIGINT | - | Y | N | Y | - | 추천질의 고유 ID |
| MENU_ID | 메뉴 아이디 | VARCHAR | 50 | N | Y | N | - | 메뉴 FK |
| RCM_QUES_SEQ | 추천 질의 순번 | INTEGER | - | N | N | N | - | 정렬 순서 |
| RCM_QUES_NM | 추천 질의 명 | VARCHAR | 500 | N | N | N | - | 추천 질의 내용 |
| USE_YN | 사용 여부 | VARCHAR | 1 | N | N | Y | Y | Y/N |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | CURRENT_TIMESTAMP | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

---

### 4. 문서 관리 (Document Management)

#### DOC_BAS_INFO (문서 기본 정보)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| DOC_ID | 문서 아이디 | BIGINT | - | Y | N | Y | - | 문서 고유 ID |
| DOC_CAT_CD | 문서 분류 코드 | VARCHAR | 50 | N | Y | Y | - | 문서 분류 FK |
| DOC_DET_LEVEL_N1_CD | 문서 상세 레벨 1번 | VARCHAR | 50 | N | Y | Y | - | 분류 레벨1 FK |
| DOC_DET_LEVEL_N2_CD | 문서 상세 레벨 2번 | VARCHAR | 50 | N | Y | Y | - | 분류 레벨2 FK |
| DOC_DET_LEVEL_N3_CD | 문서 상세 레벨 3번 | VARCHAR | 50 | N | Y | N | - | 분류 레벨3 FK |
| DOC_DET_LEVEL_N4_CD | 문서 상세 레벨 4번 | VARCHAR | 50 | N | Y | N | - | 분류 레벨4 FK |
| DOC_DET_LEVEL_N5_CD | 문서 상세 레벨 5번 | VARCHAR | 50 | N | N | N | - | 분류 레벨5 |
| DOC_REP_TITLE_NM | 문서 대표 제목 | VARCHAR | 2000 | N | N | N | - | 대표 제목 |
| DOC_TITLE_NM | 문서 제목 명 | VARCHAR | 2000 | N | N | N | - | 제목 |
| DOC_TXT | 문서 텍스트 | TEXT | - | N | N | N | - | 문서 내용 |
| DOC_SHAR_LVL_CD | 문서 공유 수준 코드 | VARCHAR | 50 | N | N | N | ALL | 공유 수준 |
| DOC_DOWN_ALW_YN | 문서 다운로드 허용 여부 | VARCHAR | 1 | N | N | N | Y | 다운로드 허용 |
| FILE_ATT_YN | 파일 첨부 여부 | VARCHAR | 1 | N | N | N | Y | 첨부파일 존재 |
| FILE_ATT_CNT | 파일 첨부 개수 | INTEGER | - | N | N | N | 0 | 첨부파일 수 |
| AUTH_OWNR_TYP_CD | 권한 소유자 유형 코드 | VARCHAR | 50 | N | N | N | - | 소유자 타입 |
| AUTH_OWNR_ID | 권한 소유자 아이디 | VARCHAR | 50 | N | N | N | - | 소유자 ID |
| INTG_SYS_CD | 연계 시스템 코드 | VARCHAR | 50 | N | N | N | - | 연계 시스템 |
| INTG_SYS_DOC_CAT_CD | 연계 시스템 문서 분류 코드 | VARCHAR | 50 | N | N | N | - | 연계 시스템 분류 |
| ORIG_SYS_IDT_ID | 원천 시스템 식별 아이디 | VARCHAR | 50 | N | N | N | - | 원천 ID |
| ORIG_SYS_IDT_CNO | 원천 시스템 식별 문자번호 | VARCHAR | 50 | N | N | N | - | 원천 번호 |
| ORIG_SYS_MNG_ID | 원천 시스템 관리 아이디 | VARCHAR | 50 | N | N | N | - | 원천 관리 ID |
| ORIG_SYS_MNG_CNO | 원천 시스템 관리 문자번호 | VARCHAR | 50 | N | N | N | - | 원천 관리 번호 |
| ORIG_SYS_CREATE_YMD | 원천 시스템 생성 년월일 | VARCHAR | 8 | N | N | N | - | 원천 생성일 (YYYYMMDD) |
| ORIG_SYS_PIC_ID | 원천 시스템 담당자 아이디 | VARCHAR | 500 | N | N | N | - | 원천 담당자 ID |
| ORIG_SYS_PIC_NM | 원천 시스템 담당자 명 | VARCHAR | 1000 | N | N | N | - | 원천 담당자명 |
| ORIG_SYS_DEPT_ID | 원천 시스템 부서 아이디 | VARCHAR | 500 | N | N | N | - | 원천 부서 ID |
| ORIG_SYS_DEPT_NM | 원천 시스템 부서 명 | VARCHAR | 1000 | N | N | N | - | 원천 부서명 |
| ORIG_SYS_PIC_INFO | 원천 시스템 담당자 정보 | VARCHAR | 2000 | N | N | N | - | 담당자 상세 정보 |
| DOC_STAT_CD | 문서 상태 코드 | VARCHAR | 50 | N | N | N | - | 문서 상태 |
| DOC_STAT_MOD_DT | 문서 상태 변경 일시 | TIMESTAMP | - | N | N | N | - | 상태 변경일시 |
| RAG_CLS_CD | RAG 구분코드 | VARCHAR | 50 | N | N | N | - | RAG 분류 |
| LAST_MOD_YMD | 최종 변경 일자 | VARCHAR | 8 | N | N | N | - | 최종 변경일 (YYYYMMDD) |
| USE_YN | 사용 여부 | VARCHAR | 1 | N | N | Y | Y | Y/N |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | CURRENT_TIMESTAMP | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

#### DOC_DET_INFO (문서 상세 정보)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| DOC_DET_ID | 문서 상세 아이디 | BIGINT | - | Y | N | Y | - | 문서상세 고유 ID |
| DOC_ID | 문서 아이디 | BIGINT | - | N | Y | Y | - | 문서 FK |
| DOC_DET_TITLE_NM | 문서 상세 제목 명 | VARCHAR | 2000 | N | N | N | - | 상세 제목 |
| DOC_REP_DET_TITLE_NM | 문서 대표 상세 제목 명 | VARCHAR | 2000 | N | N | N | - | 대표 상세 제목 |
| DOC_DET_TXT | 문서 상세 텍스트 | TEXT | - | N | N | N | - | 상세 내용 |
| SOC_DET_SMRY_TXT | 문서 상세 요약 텍스트 | TEXT | - | N | N | N | - | 요약 |
| DOC_CREATE_YMD | 문서 생성 년월일 | VARCHAR | 8 | N | N | N | - | 생성일 (YYYYMMDD) |
| DOC_PIC_ID | 문서 담당자 아이디 | VARCHAR | 500 | N | N | N | - | 담당자 ID |
| DOC_PIC_NM | 문서 담당자 명 | VARCHAR | 1000 | N | N | N | - | 담당자명 |
| DOC_RESP_DEPT_ID | 문서 담당 부서 아이디 | VARCHAR | 500 | N | N | N | - | 담당 부서 ID |
| DOC_RESP_DEPT_NM | 문서 담당 부서 명 | VARCHAR | 1000 | N | N | N | - | 담당 부서명 |
| DOC_PIC_INFO | 문서 담당자 정보 | VARCHAR | 2000 | N | N | N | - | 담당자 상세 정보 |
| ORIG_DOC_IDT_ID | 원천 문서 식별 아이디 | VARCHAR | 50 | N | N | N | - | 원천 ID |
| ORIG_DOC_IDT_CNO | 원천 문서 식별 번호 | VARCHAR | 50 | N | N | N | - | 원천 번호 |
| ORIG_DOC_IDT_DET_ID | 원천 문서 식별 상세 아이디 | VARCHAR | 50 | N | N | N | - | 원천 상세 ID |
| ORIG_DOC_MNG_ID | 원천 문서 관리 아이디 | VARCHAR | 50 | N | N | N | - | 원천 관리 ID |
| ORIG_DOC_MNG_CNO | 원천 문서 관리 문자번호 | VARCHAR | 50 | N | N | N | - | 원천 관리 번호 |
| AUTH_OWNR_TYP_CD | 권한 소유자 유형 코드 | VARCHAR | 50 | N | N | N | DPT | 소유자 타입 |
| AUTH_OWNR_ID | 권한 소유자 아이디 | VARCHAR | 50 | N | N | N | - | 소유자 ID |
| DOC_SHAR_LVL_CD | 문서 공유 수준 코드 | VARCHAR | 50 | N | N | N | 0 | 공유 수준 |
| DOC_DOWN_ALW_YN | 문서 다운로드 허용 여부 | VARCHAR | 1 | N | N | N | Y | 다운로드 허용 |
| FILE_ATT_YN | 파일 첨부 여부 | VARCHAR | 1 | N | N | N | Y | 첨부파일 존재 |
| FILE_ATT_CNT | 파일 첨부 개수 | INTEGER | - | N | N | N | 0 | 첨부파일 수 |
| ATT_FILE_EMB_YN | 첨부 파일 임베딩 여부 | VARCHAR | 1 | N | N | Y | N | 임베딩 완료 |
| DOC_STAT_CD | 문서 상태 코드 | VARCHAR | 50 | N | N | N | 0 | 문서 상태 |
| DOC_STAT_MOD_DT | 문서 상태 변경 일시 | TIMESTAMP | - | N | N | N | - | 상태 변경일시 |
| LAST_MOD_YMD | 최종 변경 일자 | VARCHAR | 8 | N | N | N | - | 최종 변경일 (YYYYMMDD) |
| USE_YN | 사용 여부 | VARCHAR | 1 | N | N | Y | Y | Y/N |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | - | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

**관계**: DOC_DET_INFO.DOC_ID → DOC_BAS_INFO.DOC_ID

#### DOC_CAT (문서 분류)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| DOC_CAT_SEQ | 문서 분류 순번 | INTEGER | - | N | N | Y | - | 정렬 순서 |
| DOC_CAT_CD | 문서 분류 코드 | VARCHAR | 50 | Y | N | Y | - | 분류 코드 |
| DOC_CAT_NM | 문서 분류 명 | VARCHAR | 500 | N | N | Y | - | 분류명 |
| USE_YN | 사용 여부 | VARCHAR | 1 | N | N | Y | - | Y/N |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | N | - | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

#### DOC_ALW_AUTH (문서 허용 권한)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| DOC_DET_ID | 문서 상세 아이디 | BIGINT | - | Y | Y | Y | - | 문서상세 FK |
| ALW_AUTH_TGT_TYP_CD | 허용 권한 대상 유형 코드 | VARCHAR | 50 | Y | N | Y | - | 권한 타입 (USER/DEPT/ROLE) |
| ALW_AUTH_TGT_ID | 허용 권한 대상 아이디 | VARCHAR | 50 | Y | N | Y | - | 대상 ID |
| DOC_DOWN_ALW_YN | 문서 다운로드 허용 여부 | VARCHAR | 1 | N | N | Y | - | 다운로드 허용 |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | - | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

**복합키**: (DOC_DET_ID, ALW_AUTH_TGT_TYP_CD, ALW_AUTH_TGT_ID)

#### DOC_FILE_ATT_LST (문서 파일 첨부 목록)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| ATT_FILE_ID | 첨부 파일 아이디 | BIGINT | - | Y | N | Y | - | 첨부파일 고유 ID |
| ATT_FILE_ORIG_ID | 첨부 파일 원천 아이디 | BIGINT | - | N | Y | N | - | 원본 파일 FK (버전 관리) |
| ORG_FILE_NM | 원본 파일 명 | VARCHAR | 500 | N | N | N | - | 원본 파일명 |
| SAV_FILE_NM | 저장 파일 명 | VARCHAR | 500 | N | N | N | - | 저장 파일명 |
| FILE_UID | 파일 UUID | VARCHAR | 100 | N | N | N | - | 파일 고유 UUID |
| FILE_EXT_NM | 파일 확장자 | VARCHAR | 500 | N | N | N | - | 확장자 |
| FILE_HASH_CVAL | 파일 해시 값 | VARCHAR | 250 | N | N | N | - | 파일 해시 (중복 체크용) |
| STRG_SAV_PTH_NM | 스토리지 저장 경로 명 | VARCHAR | 500 | N | N | N | - | 저장 경로 |
| DOC_TXT | 문서 텍스트 | TEXT | - | N | N | N | - | 추출된 텍스트 |
| SOC_SMRY_TXT | 문서 요약 텍스트 | TEXT | - | N | N | N | - | 요약 텍스트 |
| DOC_TYP_CD | 문서 유형 코드 | VARCHAR | 50 | N | N | Y | - | 문서 유형 |
| DOC_CLASS_CVAL | 문서 구분 값 | VARCHAR | 250 | N | N | N | - | 문서 구분 |
| DOC_VER_CVAL | 문서 버전 값 | VARCHAR | 250 | N | N | N | - | 버전 |
| FILE_REP_YN | 파일 대표 여부 | VARCHAR | 1 | N | N | N | - | 대표 파일 여부 |
| ATT_FILE_IDT_ID | 첨부 파일 식별 아이디 | VARCHAR | 50 | N | N | N | - | 파일 식별자 |
| ATT_FILE_IDT_CNO | 첨부 파일 식별 번호 | VARCHAR | 50 | N | N | N | - | 파일 식별 번호 |
| ATT_FILE_IDT_DET_ID | 첨부 파일 식별 상세 아이디 | VARCHAR | 50 | N | N | N | - | 파일 상세 식별자 |
| ATT_FILE_MNG_ID | 첨부 파일 관리 아이디 | VARCHAR | 50 | N | N | N | - | 파일 관리 ID |
| ATT_FILE_MNG_CNO | 첨부 파일 관리 문자번호 | VARCHAR | 50 | N | N | N | - | 파일 관리 번호 |
| DOC_DEAL_STAT_CD | 문서 처리 상태 코드 | VARCHAR | 50 | N | N | Y | 0 | 처리 상태 |
| DOC_DEAL_STAT_MOD_DT | 문서 처리 상태 변경 일시 | TIMESTAMP | - | N | N | N | - | 처리상태 변경일시 |
| DOC_STAT_CD | 문서 상태 코드 | VARCHAR | 50 | N | N | Y | 0 | 문서 상태 |
| DOC_STAT_MOD_DT | 문서 상태 변경 일시 | TIMESTAMP | - | N | N | N | - | 상태 변경일시 |
| DOC_ERR_YN | 문서 에러 여부 | VARCHAR | 1 | N | N | Y | N | 에러 발생 여부 |
| JOB_TGT_YN | 작업 대상 여부 | VARCHAR | 1 | N | N | Y | Y | 작업 대상 |
| JOB_RSLT_TXT | 작업 결과 텍스트 | TEXT | - | N | N | N | - | 작업 결과 메시지 |
| DEL_JOB_PRC_ID | 삭제 작업 프로세스 아이디 | VARCHAR | 50 | N | N | N | - | 삭제 작업 ID |
| DEL_JOB_STRT_DT | 삭제 작업 시작 일시 | TIMESTAMP | - | N | N | N | - | 삭제 시작일시 |
| DEL_JOB_END_DT | 삭제 작업 종료 일시 | TIMESTAMP | - | N | N | N | - | 삭제 종료일시 |
| DEL_JOB_RSLT_CD | 삭제 작업 결과 코드 | VARCHAR | 50 | N | N | N | - | 삭제 결과 |
| DEL_JOB_LOG | 삭제 작업 로그 | TEXT | - | N | N | N | - | 삭제 로그 |
| LAST_MOD_YMD | 최종 변경 일자 | VARCHAR | 8 | N | N | N | - | 최종 변경일 (YYYYMMDD) |
| USE_YN | 사용 여부 | VARCHAR | 1 | N | N | Y | Y | Y/N |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | - | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

**자기참조**: DOC_FILE_ATT_LST.ATT_FILE_ORIG_ID → DOC_FILE_ATT_LST.ATT_FILE_ID

#### DOC_ATT_HST (문서 첨부 이력)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| DOC_HST_ID | 문서 이력 아이디 | BIGINT | - | Y | N | Y | - | 이력 고유 ID |
| ATT_FILE_ID | 첨부 파일 아이디 | BIGINT | - | Y | Y | Y | - | 첨부파일 FK |
| STRG_SAV_PTH_NM | 스토리지 저장 경로 명 | VARCHAR | 500 | N | N | Y | - | 저장 경로 |
| ORG_FILE_NM | 원본 파일 명 | VARCHAR | 500 | N | N | Y | - | 원본 파일명 |
| FILE_UID | 파일 UUID | VARCHAR | 36 | N | N | Y | - | 파일 UUID |
| FILE_HASH_INFO | 파일 해시 정보 | TEXT | - | N | N | N | - | 해시 정보 |
| FILE_TXT | 파일 텍스트 | TEXT | - | N | N | N | - | 추출된 텍스트 |
| ORG_SAV_DT | 원본 저장 일시 | TIMESTAMP | - | N | N | N | - | 원본 저장일시 |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | - | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

**복합키**: (DOC_HST_ID, ATT_FILE_ID)

---

### 5. 문서 처리 작업 관리 (Document Processing Jobs)

#### DOC_UPLD_JOB_LST (문서 업로드 작업 목록)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| UPLD_JOB_ID | 업로드 작업 아이디 | BIGINT | - | Y | N | Y | - | 작업 고유 ID |
| ATT_FILE_ID | 첨부 파일 아이디 | BIGINT | - | Y | Y | Y | - | 첨부파일 FK |
| JOB_FLAG | 작업 여부 | VARCHAR | 1 | N | N | Y | N | 작업 진행 여부 |
| JOB_PRC_ID | 작업 프로세스 아이디 | VARCHAR | 50 | N | N | N | - | 작업 프로세스 ID |
| JOB_STRT_DT | 작업 시작 일시 | TIMESTAMP | - | N | N | N | - | 시작일시 |
| JOB_END_DT | 작업 종료 일시 | TIMESTAMP | - | N | N | N | - | 종료일시 |
| JOB_RSLT_CD | 작업 결과 코드 | VARCHAR | 50 | N | N | N | - | 결과 코드 |
| JOB_LOG | 작업 로그 | TEXT | - | N | N | N | - | 작업 로그 |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | - | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

**복합키**: (UPLD_JOB_ID, ATT_FILE_ID)

#### DOC_PARC_JOB_LST (문서 파싱 작업 목록)
동일한 구조 (작업 타입만 다름)

#### DOC_EMB_JOB_LST (문서 임베딩 작업 목록)
동일한 구조 (작업 타입만 다름)

#### DOC_DUP_CHK_JOB_LST (문서 중복 체크 작업 목록)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| DUP_DOC_JOB_ID | 중복 문서 작업 아이디 | BIGINT | - | Y | N | Y | - | 작업 고유 ID |
| ATT_FILE_ID | 첨부 파일 아이디 | BIGINT | - | Y | Y | Y | - | 첨부파일 FK |
| JOB_PRC_ID | 작업 프로세스 아이디 | VARCHAR | 50 | Y | N | Y | - | 작업 프로세스 ID |
| JOB_FLAG | 작업 여부 | VARCHAR | 1 | N | N | Y | N | 작업 진행 여부 |
| JOB_STRT_DT | 작업 시작 일시 | TIMESTAMP | - | N | N | N | - | 시작일시 |
| JOB_END_DT | 작업 종료 일시 | TIMESTAMP | - | N | N | N | - | 종료일시 |
| JOB_RSLT_CD | 작업 결과 코드 | VARCHAR | 50 | N | N | N | - | 결과 코드 |
| JOB_LOG | 작업 로그 | TEXT | - | N | N | N | - | 작업 로그 |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | - | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

**복합키**: (DUP_DOC_JOB_ID, ATT_FILE_ID, JOB_PRC_ID)

#### DOC_DUP_CHK_RSLT_LST (문서 중복 체크 결과 목록)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| DUP_DOC_CHK_RSLT_ID | 중복 문서 체크 결과 아이디 | BIGINT | - | Y | N | Y | - | 결과 고유 ID |
| DUP_DOC_JOB_ID | 중복 문서 작업 아이디 | BIGINT | - | Y | Y | Y | - | 작업 FK |
| ATT_FILE_ID | 첨부 파일 아이디 | BIGINT | - | Y | Y | Y | - | 첨부파일 FK |
| JOB_PRC_ID | 작업 프로세스 아이디 | VARCHAR | 50 | Y | Y | Y | - | 프로세스 FK |
| DUP_ATT_FILE_UID | 중복 첨부 파일 UUID | VARCHAR | 100 | N | N | Y | - | 중복 파일 UUID |
| DUP_IDT_ATT_FILE_ID | 중복 식별 첨부 파일 아이디 | BIGINT | - | N | N | Y | - | 중복 파일 ID |
| DUP_DEA_YN | 중복 처리 여부 | VARCHAR | 1 | N | N | Y | N | 처리 완료 여부 |
| DUP_DEA_DT | 중복 처리 일시 | TIMESTAMP | - | N | N | N | - | 처리일시 |
| DUP_DEA_USR_ID | 중복 처리 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 처리자 |
| DUP_DEA_CONT | 중복 처리 내용 | TEXT | - | N | N | N | - | 처리 내용 |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | - | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

**복합키**: (DUP_DOC_CHK_RSLT_ID, DUP_DOC_JOB_ID, ATT_FILE_ID, JOB_PRC_ID)

#### DOC_SMLT_CHK_JOB_LST (문서 유사도 체크 작업 목록)
중복 체크와 유사한 구조

#### DOC_SMLT_CHK_RSLT_LST (문서 유사도 체크 결과 목록)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | 소수점 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|--------|----|----|----------|--------|------|
| SMLT_DOC_CHK_RSLT_ID | 유사도 문서 체크 결과 아이디 | BIGINT | - | - | Y | N | Y | - | 결과 고유 ID |
| SMLT_DOC_JOB_ID | 유사도 문서 작업 아이디 | BIGINT | - | - | Y | Y | Y | - | 작업 FK |
| ATT_FILE_ID | 첨부 파일 아이디 | BIGINT | - | - | Y | Y | Y | - | 첨부파일 FK |
| JOB_PRC_ID | 작업 프로세스 아이디 | VARCHAR | 50 | - | Y | Y | Y | - | 프로세스 FK |
| SMLT_FILE_UID | 유사도 파일 UUID | VARCHAR | 36 | - | N | N | Y | - | 유사 파일 UUID |
| SMLT_IDT_ATT_FILE_ID | 유사도 식별 첨부 파일 아이디 | BIGINT | - | - | N | N | Y | - | 유사 파일 ID |
| SMLT_RTE | 유사도 율 | NUMERIC | 20 | 2 | N | N | Y | 0 | 유사도 점수 |
| SMLT_DEAL_YN | 유사도 처리 여부 | VARCHAR | 1 | - | N | N | Y | N | 처리 완료 여부 |
| SLMT_DEAL_DT | 유사도 처리 일시 | TIMESTAMP | - | - | N | N | N | - | 처리일시 |
| SMLT_DEAL_USR_ID | 유사도 처리 사용자 아이디 | VARCHAR | 50 | - | N | N | N | - | 처리자 |
| SMLT_DEAL_CONT | 유사도 처리 내용 | TEXT | - | - | N | N | N | - | 처리 내용 |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | - | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | - | N | N | Y | - | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | - | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | - | N | N | N | - | 수정일시 |

**복합키**: (SMLT_DOC_CHK_RSLT_ID, SMLT_DOC_JOB_ID, ATT_FILE_ID, JOB_PRC_ID)

#### DOC_PRV_INF_CHK_JOB_LST (문서 개인 정보 체크 작업 목록)
유사한 구조

#### DOC_PRV_INF_CHK_RSLT_LST (문서 개인 정보 체크 결과 목록)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| PRV_INF_CHK_RSLT_ID | 개인 정보 체크 결과 아이디 | BIGINT | - | Y | N | Y | - | 결과 고유 ID |
| PRV_INF_DOC_JOB_ID | 개인 정보 문서 작업 아이디 | BIGINT | - | Y | Y | Y | - | 작업 FK |
| ATT_FILE_ID | 첨부 파일 아이디 | BIGINT | - | Y | Y | Y | - | 첨부파일 FK |
| JOB_PRC_ID | 작업 프로세스 아이디 | VARCHAR | 50 | Y | Y | Y | - | 프로세스 FK |
| PRV_INF_FILE_UID | 개인 정보 파일 UUID | VARCHAR | 36 | N | N | Y | - | 파일 UUID |
| PRV_INF_TYP_CD | 개인 정보 유형 코드 | VARCHAR | 50 | N | N | Y | - | 개인정보 유형 |
| PRV_INF_TYP_CVAL | 개인 정보 유형 문자값 | VARCHAR | 2000 | N | N | Y | - | 검출된 개인정보 |
| PRV_INF_DEAL_YN | 개인 정보 처리 여부 | VARCHAR | 1 | N | N | Y | N | 처리 완료 여부 |
| PRV_INF_DEAL_DT | 개인 정보 처리 일시 | TIMESTAMP | - | N | N | N | - | 처리일시 |
| PRV_INF_DEAL_USR_ID | 개인 정보 처리 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 처리자 |
| PRV_INF_DEAL_CONT | 개인 정보 처리 내용 | TEXT | - | N | N | N | - | 처리 내용 |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | - | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

**복합키**: (PRV_INF_CHK_RSLT_ID, PRV_INF_DOC_JOB_ID, ATT_FILE_ID, JOB_PRC_ID)

---

### 6. 사전 관리 (Dictionary Management)

#### DIC_LST (사전 목록)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| DIC_ID | 사전 아이디 | BIGINT | - | Y | N | Y | - | 사전 고유 ID |
| DIC_SORT_CD | 사전 종류 코드 | VARCHAR | 50 | N | N | Y | - | 사전 종류 |
| DIC_USG_CD | 사전 용도 코드 | VARCHAR | 50 | N | N | Y | - | 사전 용도 |
| DIC_DESC | 사전 설명 | VARCHAR | 2000 | N | N | N | - | 설명 |
| USE_YN | 사용 여부 | VARCHAR | 1 | N | N | Y | Y | Y/N |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | CURRENT_TIMESTAMP | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

#### DIC_SYN_VOCA (사전 동의어 어휘)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| DIC_VOCA_ID | 사전 어휘 아이디 | BIGINT | - | Y | N | Y | - | 어휘 고유 ID |
| DIC_ID | 사전 아이디 | BIGINT | - | N | Y | N | - | 사전 FK |
| VOCA_NM | 어휘 명 | VARCHAR | 500 | N | N | Y | - | 표준 용어 |
| SYN_NM | 동의어 명 | VARCHAR | 500 | N | N | N | - | 동의어 |
| BLW_VOCA_NM | 하위 어휘 명 | VARCHAR | 500 | N | N | N | - | 하위 용어 |
| VOCA_EMB_YN | 어휘 임베딩 여부 | VARCHAR | 1 | N | N | Y | N | 임베딩 완료 |
| VOCA_EMB_ID | 어휘 임베딩 아이디 | VARCHAR | 100 | N | N | N | - | 임베딩 ID |
| VODA_EMB_DT | 어휘 임베딩 일시 | TIMESTAMP | - | N | N | N | - | 임베딩일시 |
| USE_YN | 사용 여부 | VARCHAR | 1 | N | N | Y | Y | Y/N |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | CURRENT_TIMESTAMP | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

---

### 7. 대화 관리 (Conversation Management)

#### USR_CNVS (사용자 대화)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| CNVS_ID | 대화 아이디 | BIGINT | - | Y | N | Y | - | 대화 고유 ID |
| CNVS_IDT_ID | 대화 식별 UUID | VARCHAR | 100 | N | Y | N | - | 세션별 대화 UUID |
| QUES_TXT | 질의 텍스트 | TEXT | - | N | N | N | - | 사용자 질문 |
| QUES_SMRY_TXT | 질의 요약 텍스트 | - | - | N | N | N | - | 질문 요약 |
| INFR_TXT | 추론 텍스트 | TEXT | - | N | N | N | - | 추론 과정 |
| ANS_TXT | 답변 텍스트 | TEXT | - | N | N | N | - | AI 답변 |
| ANS_SMRY_TXT | 답변 요약 텍스트 | TEXT | - | N | N | N | - | 답변 요약 |
| SESN_ID | 세션 아이디 | VARCHAR | 500 | N | N | N | - | 세션 ID |
| QROUT_TYP_CD | 쿼리라우팅 유형 코드 | VARCHAR | 50 | N | N | N | - | 라우팅 타입 |
| QUES_CAT_CD | 질의 분류 코드 | VARCHAR | 50 | N | N | N | - | 질문 분류 |
| DOC_CAT_SYS_CD | 문서 분류 체계 코드 | VARCHAR | 50 | N | N | N | - | 문서 체계 |
| SRCH_TIM_MS | 검색 시간 밀리초 | BIGINT | - | N | N | N | - | 검색 소요시간 (ms) |
| RSP_TIM_MS | 응답 시간 밀리초 | BIGINT | - | N | N | N | - | 응답 소요시간 (ms) |
| TKN_USE_CNT | 토큰 사용 개수 | INTEGER | - | N | N | N | - | 사용 토큰 수 |
| RCM_QUES_YN | 추천 질의 여부 | VARCHAR | 1 | N | N | Y | N | 추천질의 선택 |
| ANS_ABRT_YN | 답변 중지 여부 | VARCHAR | 1 | N | N | Y | N | 답변 중단 여부 |
| USE_YN | 사용 여부 | VARCHAR | 1 | N | N | Y | N | Y/N |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | CURRENT_TIMESTAMP | 질의일시 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

#### USR_CNVS_SMRY (사용자 대화 요약)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| CNVS_SMRY_ID | 대화 요약 아이디 | BIGINT | - | N | N | Y | - | 요약 고유 ID |
| CNVS_IDT_ID | 대화 식별 UUID | VARCHAR | 100 | Y | N | Y | - | 세션 UUID (PK) |
| USR_ID | 사용자 아이디 | VARCHAR | 50 | N | Y | N | - | 사용자 FK |
| MENU_IDT_ID | 메뉴 식별 아이디 | VARCHAR | 50 | N | N | N | - | 메뉴 |
| CNVS_SMRY_TXT | 대화 요약 텍스트 | TEXT | - | N | N | N | - | 대화 요약 |
| REP_CNVS_NM | 대표 대화 명 | VARCHAR | 2000 | N | N | N | - | 대화 제목 |
| USE_YN | 사용 여부 | VARCHAR | 1 | N | N | Y | Y | Y/N |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | CURRENT_TIMESTAMP | 생성일시 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

#### USR_CNVS_REF_DOC_LST (사용자 대화 참조 문서 목록)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | 소수점 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|--------|----|----|----------|--------|------|
| REF_DOC_ID | 참조 문서 아이디 | BIGINT | - | - | Y | N | Y | - | 참조 고유 ID |
| CNVS_ID | 대화 아이디 | BIGINT | - | - | N | Y | N | - | 대화 FK |
| REF_SEQ | 참조 순번 | INTEGER | - | - | N | N | Y | - | 참조 순서 |
| ATT_DOC_NM | 첨부 문서 명 | VARCHAR | 500 | - | N | N | N | - | 문서명 |
| ATT_DOC_ID | 첨부 문서 아이디 | VARCHAR | 500 | - | N | N | N | - | 문서 ID |
| FILE_UID | 파일 UUID | VARCHAR | 100 | - | N | N | N | - | 파일 UUID |
| FILE_DOWN_URL | 파일 다운로드 URL | VARCHAR | 2000 | - | N | N | N | - | 다운로드 URL |
| DOC_CHNK_NM | 문서 청크 명 | VARCHAR | 1000 | - | N | N | N | - | 청크 제목 |
| DOC_CHNK_TXT | 문서 청크 텍스트 | TEXT | - | - | N | N | N | - | 청크 내용 |
| DOC_TYP_CD | 문서 유형 코드 | VARCHAR | 50 | - | N | N | N | - | 문서 유형 |
| SMLT_RTE | 유사도 율 | NUMERIC | 20 | 5 | N | N | N | - | 유사도 점수 |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | - | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | - | N | N | Y | CURRENT_TIMESTAMP | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | - | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | - | N | N | N | - | 수정일시 |

#### USR_CNVS_ADD_QUES_LST (사용자 대화 추가 질의 목록)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| REF_HST_ID | 참조 이력 아이디 | BIGINT | - | Y | N | Y | - | 이력 고유 ID |
| CNVS_ID | 대화 아이디 | BIGINT | - | N | Y | N | - | 대화 FK |
| QUES_SEQ | 질의 순번 | INTEGER | - | N | N | Y | - | 순서 |
| QUES_TXT | 질의 텍스트 | TEXT | - | N | N | N | - | 추가 질문 |
| RAG_CLS_CD | RAG 구분코드 | VARCHAR | 50 | N | N | N | - | RAG 분류 |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | CURRENT_TIMESTAMP | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

#### USR_RACT (사용자 반응)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| RACT_ID | 반응 아이디 | BIGINT | - | Y | N | Y | - | 반응 고유 ID |
| CNVS_ID | 대화 아이디 | BIGINT | - | N | Y | N | - | 대화 FK |
| USR_RACT_CONF_CD | 사용자 반응 설정 코드 | VARCHAR | 50 | N | N | N | - | 반응 타입 |
| RACT_TXT | 반응 텍스트 | TEXT | - | N | N | N | - | 피드백 내용 |
| RACT_LEVEL_VAL | 반응 레벨 값 | NUMERIC | 18 | N | N | N | - | 평점 |
| SESN_ID | 세션 아이디 | VARCHAR | 500 | N | N | N | - | 세션 ID |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | CURRENT_TIMESTAMP | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

#### USR_ERR_RPT (사용자 오류 보고)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| ERR_RPT_ID | 오류 보고 아이디 | BIGINT | - | Y | N | Y | - | 보고 고유 ID |
| CNVS_ID | 대화 아이디 | BIGINT | - | N | Y | N | - | 대화 FK |
| ERR_RPT_TXT | 오류 보고 텍스트 | TEXT | - | N | N | N | - | 오류 내용 |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | CURRENT_TIMESTAMP | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

#### USR_ERR_RPT_SEL_LST (사용자 오류 보고 선택 목록)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| ERR_RPT_SEL_ID | 오류 보고 선택 아이디 | BIGINT | - | Y | N | Y | - | 선택 고유 ID |
| ERR_RPT_ID | 오류 보고 아이디 | BIGINT | - | N | Y | N | - | 오류보고 FK |
| ERR_RPT_CD | 오류 보고 코드 | VARCHAR | 50 | N | N | N | - | 오류 유형 코드 |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | CURRENT_TIMESTAMP | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

#### USR_UPD_DOC_MNG (사용자 업로드 문서 관리)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| FILE_UPLD_SEQ | 파일 업로드 순번 | BIGINT | - | Y | N | Y | - | 업로드 고유 ID |
| USR_ID | 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 사용자 ID |
| CNVS_IDT_ID | 대화 식별 UUID | VARCHAR | 100 | N | Y | N | - | 세션 UUID FK |
| UI_IDT_CVAL | UI 식별 값 | VARCHAR | 250 | N | N | Y | - | UI 컴포넌트 식별자 |
| FILE_NM | 파일 명 | VARCHAR | 1000 | N | N | Y | - | 파일명 |
| FILE_UID | 파일 UUID | VARCHAR | 100 | N | N | N | - | 파일 UUID |
| FILE_UPLD_DT | 파일 업로드 일시 | TIMESTAMP | - | N | N | N | - | 업로드일시 |
| UPLD_RSN_CLS_CD | 업로드 사유 구분 코드 | VARCHAR | 50 | N | N | Y | - | 업로드 사유 |
| PRSC_YN | 파싱 여부 | VARCHAR | 1 | N | N | Y | N | 파싱 완료 |
| PRSC_FIN_DT | 파싱 완료 일시 | TIMESTAMP | - | N | N | N | - | 파싱 완료일시 |
| PRC_YN | 프로세스 여부 | VARCHAR | 1 | N | N | Y | N | 처리 완료 |
| PRC_FIN_DT | 프로세스 완료 일시 | TIMESTAMP | - | N | N | N | - | 처리 완료일시 |
| DEL_YN | 삭제 여부 | VARCHAR | 1 | N | N | Y | N | 삭제 여부 |
| DEL_DT | 삭제 일시 | TIMESTAMP | - | N | N | N | - | 삭제일시 |
| LOG_CONT | 로그 내용 | VARCHAR | 4000 | N | N | N | - | 처리 로그 |
| LOG_SAV_DT | 로그 저장 일시 | TIMESTAMP | - | N | N | N | - | 로그 저장일시 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | CURRENT_TIMESTAMP | 등록일시 |

---

### 8. 게시판 관리 (Board Management)

#### INTR_BRD (교류 게시판)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| BRD_ID | 게시판 아이디 | BIGINT | - | Y | N | Y | - | 게시판 고유 ID |
| BRD_NM | 게시판 명 | VARCHAR | 500 | N | N | N | - | 게시판명 |
| BRD_CLS_CD | 게시판 구분 코드 | VARCHAR | 50 | N | N | N | - | 게시판 타입 |
| CALL_URL | 호출 URL | VARCHAR | 2000 | N | N | N | - | 게시판 URL |
| POP_USE_YN | 팝업 사용 여부 | VARCHAR | 1 | N | N | Y | N | 팝업 기능 |
| FILE_UPLD_YN | 파일 업로드 여부 | VARCHAR | 1 | N | N | Y | Y | 첨부 허용 |
| CMT_REG_YN | 댓글 등록 여부 | VARCHAR | 1 | N | N | Y | Y | 댓글 허용 |
| PGE_CNT | 페이지 건수 | INTEGER | - | N | N | N | - | 페이지당 수 |
| PGE_PST_CNT | 페이지 게시글 건수 | INTEGER | - | N | N | N | - | 게시글 수 |
| USE_YN | 사용 여부 | VARCHAR | 1 | N | N | Y | Y | Y/N |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | CURRENT_TIMESTAMP | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

#### INTR_PST (교류 게시글)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| PST_ID | 게시글 아이디 | BIGINT | - | Y | N | Y | - | 게시글 고유 ID |
| BRD_ID | 게시판 아이디 | BIGINT | - | N | Y | N | - | 게시판 FK |
| TITLE_NM | 제목 명 | VARCHAR | 500 | N | N | N | - | 제목 |
| PST_CONT | 게시글 내용 | VARCHAR | 4000 | N | N | N | - | 내용 |
| POP_PST_YN | 팝업 게시글 여부 | VARCHAR | 1 | N | N | Y | N | 팝업 공지 |
| POP_STRT_YMD | 팝업 시작 년월일 | VARCHAR | 8 | N | N | N | - | 팝업 시작일 (YYYYMMDD) |
| POP_END_YMD | 팝업 종료 년월일 | VARCHAR | 8 | N | N | N | - | 팝업 종료일 (YYYYMMDD) |
| USE_YN | 사용 여부 | VARCHAR | 1 | N | N | Y | Y | Y/N |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 작성자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | CURRENT_TIMESTAMP | 작성일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

#### INTR_PST_ATT_FILE (교류 게시글 첨부 파일)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| PST_ATT_FILE_ID | 게시글 첨부 파일 아이디 | BIGINT | - | Y | N | Y | - | 첨부파일 고유 ID |
| PST_ID | 게시글 아이디 | BIGINT | - | N | Y | N | - | 게시글 FK |
| FILE_NM | 파일 명 | VARCHAR | 500 | N | N | N | - | 파일명 |
| FILE_SAV_PTH_INFO | 파일 저장 경로 정보 | VARCHAR | 2000 | N | N | N | - | 저장 경로 |
| FILE_FILE | 파일 파일 | BYTEA | - | N | N | N | - | 파일 바이너리 |
| FILE_SIZE | 파일 크기 | BIGINT | - | N | N | N | - | 파일 크기 (bytes) |
| USE_YN | 사용 여부 | VARCHAR | 1 | N | N | Y | Y | Y/N |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | CURRENT_TIMESTAMP | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

#### INTR_PST_CMT (교류 게시글 댓글)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| PST_CMT_ID | 게시글 댓글 아이디 | BIGINT | - | Y | N | Y | - | 댓글 고유 ID |
| PST_ID | 게시글 아이디 | BIGINT | - | N | Y | N | - | 게시글 FK |
| CMT_RMK | 댓글 첨언 | VARCHAR | 2000 | N | N | N | - | 댓글 내용 |
| USE_YN | 사용 여부 | VARCHAR | 1 | N | N | Y | Y | Y/N |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 작성자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | CURRENT_TIMESTAMP | 작성일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

#### INTR_PST_CMT_ATT_FILE (교류 게시글 댓글 첨부 파일)
동일한 구조 (게시글 첨부 파일과 유사)

---

### 9. 스케쥴 및 시스템 관리 (Schedule & System Management)

#### SCHD_MNG (스케쥴 관리)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| SCHD_ID | 스케쥴 아이디 | BIGINT | - | Y | N | Y | - | 스케쥴 고유 ID |
| SCHD_IDT_ID | 스케쥴 식별 아이디 | VARCHAR | 500 | N | N | Y | - | 스케쥴 식별자 |
| SCHD_NM | 스케쥴 명 | VARCHAR | 500 | N | N | Y | - | 스케쥴명 |
| SCHD_DESC | 스케쥴 설명 | VARCHAR | 2000 | N | N | N | - | 설명 |
| SCHD_RUN_TYP_CD | 스케쥴 실행 유형 코드 | VARCHAR | 50 | N | N | Y | - | 실행 타입 |
| SCHD_USE_CYC_CD | 스케쥴 사용 주기 코드 | VARCHAR | 50 | N | N | Y | - | 실행 주기 |
| RUN_TGT_NM | 실행 대상 명 | VARCHAR | 500 | N | N | N | - | 실행 대상 |
| RUN_CYC_DESC | 실행 주기 설명 | VARCHAR | 2000 | N | N | N | - | 주기 설명 |
| CRNTB_CONF_CVAL | CRONTAB 설정 문자값 | VARCHAR | 50 | N | N | N | - | CRON 표현식 |
| CALL_URI | 호출 URI | VARCHAR | 2000 | N | N | N | - | API 엔드포인트 |
| PARM_INFO | 매개변수 정보 | VARCHAR | 2000 | N | N | N | - | 파라미터 |
| INST_CNT | 인스턴스 개수 | INTEGER | - | N | N | N | - | 동시 실행 수 |
| SCHD_STRT_YMD | 스케쥴 시작 문자일자 | VARCHAR | 8 | N | N | N | - | 시작일 (YYYYMMDD) |
| SCHD_END_YMD | 스케쥴 종료 문자일자 | VARCHAR | 8 | N | N | N | - | 종료일 (YYYYMMDD) |
| SCHD_STRT_TM | 스케쥴 시작 문자시간 | VARCHAR | 4 | N | N | N | - | 시작시간 (HHMM) |
| SCHD_END_TM | 스케쥴 종료 문자시간 | VARCHAR | 4 | N | N | N | - | 종료시간 (HHMM) |
| USE_YN | 사용 여부 | VARCHAR | 1 | N | N | Y | 'Y' | Y/N |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | CURRENT_TIMESTAMP | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

#### SCHD_LOG_HST (스케쥴 로그 이력)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| LOG_SEQ | 로그 순번 | BIGINT | - | Y | N | Y | - | 로그 고유 ID |
| SCHD_ID | 스케쥴 아이디 | BIGINT | - | Y | Y | Y | - | 스케쥴 FK |
| LOG_TYP_CD | 로그 유형 코드 | VARCHAR | 50 | N | N | Y | - | 로그 타입 |
| USR_IP_CVAL | 사용자 IP 문자값 | VARCHAR | 50 | N | N | N | - | IP 주소 |
| UI_NM | 화면 명 | VARCHAR | 2000 | N | N | N | - | 화면명 |
| CALL_URI | 호출 URI | VARCHAR | 2000 | N | N | N | - | API URI |
| FWIN_URL | 유입 URL | VARCHAR | 2000 | N | N | N | - | Referer URL |
| USR_ID | 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 사용자 ID |
| CALL_WAY_CVAL | 호출 방식 문자값 | VARCHAR | 50 | N | N | N | - | HTTP Method |
| PARM_INFO | 매개 변수 정보 | VARCHAR | 2000 | N | N | N | - | 파라미터 |
| INST_INFO | 인스턴스 정보 | VARCHAR | 2000 | N | N | N | - | 인스턴스 정보 |
| RSLT_CD | 결과 코드 | VARCHAR | 200 | N | N | N | - | 결과 코드 |
| RSLT_MSG | 결과 메시지 | VARCHAR | 4000 | N | N | N | - | 결과 메시지 |
| CREATE_DT | 생성 일시 | TIMESTAMP | - | N | N | Y | CURRENT_TIMESTAMP | 생성일시 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

**복합키**: (LOG_SEQ, SCHD_ID)

#### SYS_RSC (시스템 자원)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | 소수점 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|--------|----|----|----------|--------|------|
| LOG_SEQ | 로그 순번 | BIGINT | - | - | Y | N | Y | - | 로그 고유 ID |
| RSC_NM | 자원 명 | VARCHAR | 500 | - | Y | N | Y | - | 자원명 (CPU/Memory/Disk) |
| USE_RTE | 사용 율 | NUMERIC | 20 | 2 | N | N | Y | 0 | 사용률 (%) |
| REG_DT | 생성 일시 | TIMESTAMP | - | - | N | N | Y | CURRENT_TIMESTAMP | 수집일시 |

**복합키**: (LOG_SEQ, RSC_NM)

### 10. 서비스 관리 (Service Management)

#### RCM_QUES (추천 질문)
| 컬럼명 | 한글명 | 데이터타입 | 길이 | PK | FK | NOT NULL | 기본값 | 설명 |
|--------|--------|-----------|------|----|----|----------|--------|------|
| RCM_QUES_ID | 추천 질문 아이디 | BIGSERIAL | - | Y | N | Y | - | 추천 질문 고유 ID |
| QUES_TXT | 질문 텍스트 | VARCHAR | 500 | N | N | Y | - | 추천 질문 내용 |
| CAT_NM | 카테고리 명 | VARCHAR | 100 | N | N | N | - | 질문 카테고리 |
| DESC_TXT | 설명 텍스트 | TEXT | - | N | N | N | - | 질문 설명 |
| DISP_ORD | 표시 순서 | INTEGER | - | N | N | N | 999 | 화면 표시 순서 |
| USE_YN | 사용 여부 | VARCHAR | 1 | N | N | Y | 'Y' | Y/N |
| REG_USR_ID | 등록 사용자 아이디 | VARCHAR | 50 | N | N | Y | - | 등록자 |
| REG_DT | 등록 일시 | TIMESTAMP | - | N | N | Y | CURRENT_TIMESTAMP | 등록일시 |
| MOD_USR_ID | 수정 사용자 아이디 | VARCHAR | 50 | N | N | N | - | 수정자 |
| MOD_DT | 수정 일시 | TIMESTAMP | - | N | N | N | - | 수정일시 |

**설명**:
- 사용자 UI에 표시되는 추천 질문 관리
- DISP_ORD 순으로 정렬하여 화면에 표시
- USE_YN='Y'인 질문만 사용자에게 노출
- 최대 4개까지 화면에 표시 (UI 레이아웃 제약)

---

## 주요 관계도

### 1. 코드 계층 구조
```
COM_CD_LV1 (레벨1)
  ↓
COM_CD_LV2 (레벨2)
  ↓
COM_CD_LV3 (레벨3)
  ↓
COM_CD_LV4 (레벨4)
  ↓
COM_CD_LV5 (레벨5)
```

### 2. 조직 구조
```
DEPT_INFO (부서)
  ↓ (자기참조)
DEPT_INFO (하위부서)
  ↓
USR_INFO (사용자)
  ↓
USR_PRV_CONF (개인설정)
USR_CONN_LST (접속이력)
```

### 3. 문서 구조
```
DOC_BAS_INFO (기본정보)
  ↓
DOC_DET_INFO (상세정보)
  ↓
DOC_ALW_AUTH (권한)
  ↓
DOC_FILE_ATT_LST (첨부파일)
  ↓
DOC_ATT_HST (첨부이력)
```

### 4. 작업 처리 플로우
```
DOC_FILE_ATT_LST (첨부파일)
  ↓
DOC_UPLD_JOB_LST (업로드 작업)
  ↓
DOC_PARC_JOB_LST (파싱 작업)
  ↓
DOC_EMB_JOB_LST (임베딩 작업)
  ↓
DOC_DUP_CHK_JOB_LST → DOC_DUP_CHK_RSLT_LST (중복체크)
DOC_SMLT_CHK_JOB_LST → DOC_SMLT_CHK_RSLT_LST (유사도체크)
DOC_PRV_INF_CHK_JOB_LST → DOC_PRV_INF_CHK_RSLT_LST (개인정보체크)
```

### 5. 대화 구조
```
USR_CNVS_SMRY (대화요약)
  ↓
USR_CNVS (대화)
  ├→ USR_CNVS_REF_DOC_LST (참조문서)
  ├→ USR_CNVS_ADD_QUES_LST (추가질의)
  ├→ USR_RACT (사용자반응)
  └→ USR_ERR_RPT (오류보고)
       ↓
     USR_ERR_RPT_SEL_LST (오류선택)
```

### 6. 게시판 구조
```
INTR_BRD (게시판)
  ↓
INTR_PST (게시글)
  ├→ INTR_PST_ATT_FILE (첨부파일)
  └→ INTR_PST_CMT (댓글)
       ↓
     INTR_PST_CMT_ATT_FILE (댓글첨부)
```

### 7. 메뉴 및 권한
```
MENU (메뉴)
  ├→ MENU_AUTH (메뉴권한)
  └→ MENU_RCM_QUES (추천질의)

DOC_DET_INFO (문서상세)
  ↓
DOC_ALW_AUTH (문서권한)
```

---

## 인덱스 권장사항

### 성능 최적화를 위한 인덱스

```sql
-- 사용자 검색
CREATE INDEX idx_usr_info_dept ON USR_INFO(DEPT_ID);
CREATE INDEX idx_usr_conn_usr_dt ON USR_CONN_LST(REG_USR_ID, REG_DT);

-- 문서 검색
CREATE INDEX idx_doc_bas_cat ON DOC_BAS_INFO(DOC_CAT_CD);
CREATE INDEX idx_doc_bas_stat ON DOC_BAS_INFO(DOC_STAT_CD, USE_YN);
CREATE INDEX idx_doc_det_doc ON DOC_DET_INFO(DOC_ID);
CREATE INDEX idx_doc_file_uid ON DOC_FILE_ATT_LST(FILE_UID);
CREATE INDEX idx_doc_file_stat ON DOC_FILE_ATT_LST(DOC_STAT_CD, USE_YN);

-- 대화 검색
CREATE INDEX idx_cnvs_idt ON USR_CNVS_SMRY(CNVS_IDT_ID);
CREATE INDEX idx_cnvs_usr ON USR_CNVS_SMRY(USR_ID, REG_DT);
CREATE INDEX idx_cnvs_ref ON USR_CNVS_REF_DOC_LST(CNVS_ID);

-- 작업 처리
CREATE INDEX idx_upld_job_file ON DOC_UPLD_JOB_LST(ATT_FILE_ID);
CREATE INDEX idx_upld_job_flag ON DOC_UPLD_JOB_LST(JOB_FLAG, JOB_RSLT_CD);
CREATE INDEX idx_emb_job_file ON DOC_EMB_JOB_LST(ATT_FILE_ID);
CREATE INDEX idx_emb_job_flag ON DOC_EMB_JOB_LST(JOB_FLAG, JOB_RSLT_CD);

-- 스케쥴
CREATE INDEX idx_schd_idt ON SCHD_MNG(SCHD_IDT_ID);
CREATE INDEX idx_schd_log_dt ON SCHD_LOG_HST(SCHD_ID, CREATE_DT);
```

---

## 데이터 타입 및 제약사항

### 공통 패턴

| 용도 | 데이터타입 | 길이 | 설명 |
|------|-----------|------|------|
| 일련번호/ID | BIGINT | - | AUTO INCREMENT |
| 코드 | VARCHAR | 50 | 공통코드, 분류코드 |
| 명칭 | VARCHAR | 500 | 일반 이름 |
| 설명 | VARCHAR | 2000 | 간단한 설명 |
| 텍스트 | TEXT | - | 긴 내용 |
| Y/N 플래그 | VARCHAR | 1 | 'Y' 또는 'N' |
| 일자 | VARCHAR | 8 | YYYYMMDD 형식 |
| 시간 | VARCHAR | 4 | HHMM 형식 |
| 일시 | TIMESTAMP | - | 날짜+시간 |
| UUID | VARCHAR | 36-100 | 파일 식별자 |
| 비율 | NUMERIC | 20,2 | 백분율, 유사도 등 |

### 기본값 정책

- **USE_YN**: 기본값 'Y' 또는 'N' (테이블마다 다름)
- **REG_DT**: CURRENT_TIMESTAMP
- **REG_USR_ID**: NOT NULL
- **MOD_DT**: NULL 허용
- **MOD_USR_ID**: NULL 허용

---

## 마이그레이션

### Alembic 사용

```bash
# 마이그레이션 생성
alembic revision --autogenerate -m "description"

# 마이그레이션 적용
alembic upgrade head

# 마이그레이션 롤백
alembic downgrade -1

# 현재 버전 확인
alembic current

# 마이그레이션 이력
alembic history
```

### 마이그레이션 주의사항

1. **외래키 제약조건**: 반드시 참조 테이블이 먼저 생성되어야 함
2. **복합키**: 다수의 테이블이 복합키를 사용하므로 주의
3. **기본값**: TIMESTAMP 컬럼은 기본값 설정 확인
4. **인덱스**: 대용량 테이블은 인덱스 생성 시간 고려

---

## 데이터베이스 연결 정보

```python
# app/core/config.py
DATABASE_URL = "postgresql://user:password@localhost/dbname"
```

---

## 백업 및 복구

### 백업

```bash
# 전체 백업
pg_dump -h localhost -U postgres -d admin_db > backup.sql

# 스키마만 백업
pg_dump -h localhost -U postgres -d admin_db --schema-only > schema.sql

# 데이터만 백업
pg_dump -h localhost -U postgres -d admin_db --data-only > data.sql
```

### 복구

```bash
# 복구
psql -h localhost -U postgres -d admin_db < backup.sql
```

---

## 참고사항

1. **테이블명 규칙**: 대문자 + 언더스코어
2. **컬럼명 규칙**: 축약형 사용 (예: LEVEL_N1_CD, DOC_DET_ID)
3. **코드 관리**: 5단계 계층형 코드 체계
4. **이력 관리**: 주요 테이블은 이력 테이블 존재 (예: DOC_ATT_HST)
5. **작업 관리**: 작업 목록 + 결과 목록 분리 패턴
6. **원천 시스템 연계**: ORIG_SYS_* 컬럼으로 외부 시스템 연계

---

## 문의

데이터베이스 스키마 관련 문의사항은 개발팀에 문의하시기 바랍니다.

**최종 업데이트**: 2025-10-29
