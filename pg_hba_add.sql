-- pg_hba.conf에 추가할 내용을 생성하는 스크립트
-- 관리자가 수동으로 추가해야 합니다

-- /var/lib/edb/as14/data/pg_hba.conf 파일에 아래 라인을 추가:
-- host    all             all             172.31.0.0/16           md5

-- 추가 후 실행할 명령어:
-- sudo systemctl reload edb-as-14
