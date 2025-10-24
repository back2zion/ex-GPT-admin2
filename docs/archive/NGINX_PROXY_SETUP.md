# nginx 프록시 설정 가이드 (포트 20443)

## 문제 상황

`https://ui.datastreams.co.kr:20443/api/v1/usage/log` 호출 시 **404 Not Found** 발생

## 원인

포트 20443에서 실행 중인 웹서버(nginx/리버스 프록시)에 `/api/v1/usage/` 경로에 대한 프록시 설정이 없음

## 해결 방법

### 1. nginx 설정 파일 찾기

포트 20443을 처리하는 nginx 설정 파일을 찾습니다:

```bash
# 방법 1: 포트로 검색
sudo netstat -tlnp | grep 20443

# 방법 2: 설정 파일 검색
sudo find /etc -name "*.conf" | xargs grep -l "20443"
sudo find /var/opt -name "*.conf" | xargs grep -l "20443"
sudo find /opt -name "*.conf" | xargs grep -l "20443"

# 방법 3: GitLab nginx인 경우
sudo ls -la /var/opt/gitlab/nginx/conf/
```

### 2. 프록시 설정 추가

찾은 설정 파일에 다음 내용을 추가합니다:

#### 옵션 A: /api/v1/usage/ 경로 추가 (권장)

```nginx
# https://ui.datastreams.co.kr:20443을 처리하는 server 블록 내부에 추가

# admin-api 사용 이력 로깅
location /api/v1/usage/ {
    proxy_pass http://localhost:8010/api/v1/usage/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 30s;
    proxy_read_timeout 30s;
    proxy_send_timeout 30s;
}

# admin-api 문서 관리
location /api/v1/documents/ {
    proxy_pass http://localhost:8010/api/v1/documents/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 30s;
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
    client_max_body_size 100M;
}
```

#### 옵션 B: /admin-api/ 전체 프록시 (모든 경로 한 번에)

```nginx
# admin-api 전체
location /api/v1/ {
    # 기존 /api/v1/ 처리가 있다면 순서 주의!
    # /api/v1/documents/, /api/v1/usage/ 등을 먼저 처리하고
    # 나머지를 기존 백엔드로 프록시

    # admin-api로 먼저 시도
    proxy_pass http://localhost:8010/api/v1/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### 3. nginx 설정 테스트 및 재시작

```bash
# 설정 파일 문법 검사
sudo nginx -t

# GitLab nginx인 경우
sudo /opt/gitlab/embedded/sbin/nginx -t -c /var/opt/gitlab/nginx/conf/nginx.conf

# nginx 재시작
sudo systemctl reload nginx
# 또는 GitLab nginx
sudo gitlab-ctl restart nginx
```

### 4. 테스트

```bash
# 브라우저에서 접속
https://ui.datastreams.co.kr:20443/test_usage_log.html

# 또는 curl로 테스트
curl -X POST "https://ui.datastreams.co.kr:20443/api/v1/usage/log" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"테스트","answer":"답변","response_time":500}'
```

---

## 설정 예시 전체

### GitLab nginx 설정 예시

**파일**: `/var/opt/gitlab/nginx/conf/nginx-status.conf` 또는 `/var/opt/gitlab/nginx/conf/gitlab-http.conf`

```nginx
server {
    listen 20443 ssl http2;
    server_name ui.datastreams.co.kr;

    # SSL 설정 (생략)

    # 기존 location 블록들...

    # admin-api 추가 ⭐
    location /api/v1/usage/ {
        proxy_pass http://localhost:8010/api/v1/usage/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_connect_timeout 30s;
        proxy_read_timeout 30s;
    }

    location /api/v1/documents/ {
        proxy_pass http://localhost:8010/api/v1/documents/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_connect_timeout 30s;
        proxy_read_timeout 300s;
        client_max_body_size 100M;
    }
}
```

---

## 문제 해결

### nginx 설정 파일을 찾을 수 없는 경우

```bash
# nginx 프로세스 확인
ps aux | grep nginx

# 설정 파일 위치 확인
sudo nginx -V 2>&1 | grep "configure arguments"

# GitLab nginx 설정 위치
ls -la /var/opt/gitlab/nginx/conf/
```

### 권한 문제

```bash
# root 권한으로 전환
sudo su -

# 또는 관리자에게 요청
```

### 재시작 후에도 404가 계속 나오는 경우

1. **브라우저 캐시 클리어**: Ctrl + Shift + Delete
2. **nginx 로그 확인**:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   sudo tail -f /var/opt/gitlab/nginx/gitlab_error.log
   ```
3. **프록시 순서 확인**: location 블록이 위에서 아래로 처리되므로 순서가 중요

---

## 완료 체크리스트

- [ ] nginx 설정 파일 위치 확인
- [ ] `/api/v1/usage/` 프록시 설정 추가
- [ ] `/api/v1/documents/` 프록시 설정 추가
- [ ] `nginx -t` 문법 검사 통과
- [ ] nginx 재시작
- [ ] 브라우저 캐시 클리어
- [ ] https://ui.datastreams.co.kr:20443/test_usage_log.html 테스트 성공
- [ ] layout.html에서 실제 질문 → 관리 도구에서 확인

---

## 연락처

설정 파일 위치를 찾기 어려우면 서버 관리자에게 다음을 요청하세요:

> "포트 20443을 처리하는 nginx 설정 파일에 `/api/v1/usage/`와 `/api/v1/documents/` 경로를 `http://localhost:8010`로 프록시하는 설정을 추가해주세요."

또는 이 파일을 첨부하여 전달하세요.
