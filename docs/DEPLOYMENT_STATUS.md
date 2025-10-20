# AI Streams 관리도구 배포 상태

## 배포 완료 ✅

### 실행 중인 서비스

```bash
$ docker-compose ps
```

| 서비스 | 상태 | 포트 | 설명 |
|--------|------|------|------|
| admin-api | Running | 8010 | FastAPI 백엔드 서버 |
| postgres | Running | 5432 | PostgreSQL 데이터베이스 |
| redis | Running | 6379 | Redis 캐시 |
| cerbos | Running | 3592, 3593 | Cerbos 권한 관리 서버 |

### 접속 URL

- **API 문서 (Swagger)**: http://localhost:8010/docs
- **API 문서 (ReDoc)**: http://localhost:8010/redoc
- **Health Check**: http://localhost:8010/health
- **관리자 대시보드**: http://localhost/admin/index.html

### API 엔드포인트

#### 인증
- `POST /api/v1/auth/login` - 로그인
- `POST /api/v1/auth/logout` - 로그아웃
- `GET /api/v1/auth/me` - 현재 사용자 정보

#### 문서 관리
- `GET /api/v1/documents/` - 문서 목록
- `GET /api/v1/documents/{document_id}` - 문서 상세
- `GET /api/v1/documents/changes` - 문서 변경 이력
- `POST /api/v1/documents/sync` - 레거시 시스템 동기화
- `POST /api/v1/documents/{document_id}/approve` - 문서 변경 승인

#### 사용 이력
- `GET /api/v1/usage/history` - 사용 이력 조회
- `GET /api/v1/usage/statistics` - 사용 통계
- `GET /api/v1/usage/export` - 사용 이력 내보내기

#### 권한 관리
- `GET /api/v1/permissions/roles` - 역할 목록
- `GET /api/v1/permissions/departments` - 부서 목록
- `POST /api/v1/permissions/document-access` - 문서 접근 권한 설정
- `GET /api/v1/permissions/user/{user_id}/permissions` - 사용자 권한 조회
- `POST /api/v1/permissions/check` - 권한 확인

#### 공지사항
- `GET /api/v1/notices/` - 공지사항 목록
- `POST /api/v1/notices/` - 공지사항 생성
- `PUT /api/v1/notices/{notice_id}` - 공지사항 수정
- `DELETE /api/v1/notices/{notice_id}` - 공지사항 삭제
- `GET /api/v1/notices/active` - 활성 공지사항

#### 만족도 조사
- `POST /api/v1/satisfaction/submit` - 만족도 제출
- `GET /api/v1/satisfaction/results` - 만족도 결과
- `GET /api/v1/satisfaction/export` - 만족도 데이터 내보내기

## 데이터베이스 초기화

현재 데이터베이스 스키마는 정의되었지만, 마이그레이션이 아직 실행되지 않았습니다.

```bash
# 마이그레이션 실행
docker-compose exec admin-api poetry run alembic upgrade head

# 초기 데이터 생성 (TODO)
docker-compose exec admin-api python scripts/seed_data.py
```

## 다음 단계

### 1. 데이터베이스 마이그레이션 실행
SQLAlchemy 모델을 기반으로 데이터베이스 테이블 생성

### 2. 초기 데이터 시드
- 기본 역할 (admin, manager, user, viewer)
- 기본 권한
- 샘플 부서
- 테스트 사용자

### 3. 레거시 시스템 연계 구현
- 레거시 DB 연결 설정
- 문서 동기화 스케줄러
- 변경 감지 알고리즘

### 4. 프론트엔드 기능 구현
- 실제 API 연동
- 데이터 시각화
- 사용자 인터페이스 개선

### 5. Cerbos 정책 테스트
- 권한 정책 검증
- 통합 테스트

## 로그 확인

```bash
# 전체 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f admin-api
docker-compose logs -f postgres
docker-compose logs -f cerbos
```

## 서비스 중지

```bash
# 서비스 중지
docker-compose down

# 데이터 포함 완전 삭제
docker-compose down -v
```

## 환경 변수 설정

`.env` 파일에서 다음 설정을 확인하세요:

- `DATABASE_URL`: PostgreSQL 연결 문자열
- `SECRET_KEY`: JWT 시크릿 키 (프로덕션에서 반드시 변경)
- `CERBOS_HOST`: Cerbos 서버 호스트
- `LEGACY_DB_URL`: 레거시 시스템 DB 연결

## 보안 체크리스트

- [ ] SECRET_KEY를 강력한 값으로 변경
- [ ] 프로덕션 데이터베이스 비밀번호 변경
- [ ] CORS 설정을 실제 도메인으로 제한
- [ ] HTTPS 설정 (프로덕션)
- [ ] 방화벽 규칙 설정
- [ ] 백업 정책 수립

## 성능 모니터링

```bash
# 컨테이너 리소스 사용량
docker stats

# API 응답 시간 테스트
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8010/health
```

## 문제 해결

### API가 시작되지 않을 때

```bash
docker-compose logs admin-api
```

### 데이터베이스 연결 오류

```bash
docker-compose exec postgres psql -U postgres -d admin_db
```

### Cerbos 정책 오류

```bash
docker-compose logs cerbos
docker-compose exec cerbos cerbos validate /policies
```

---

**마지막 업데이트**: 2025-10-18
**상태**: 정상 작동 중 ✅
