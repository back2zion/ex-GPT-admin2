# ex-GPT User App

Java Spring Boot 기반 사용자 UI 백엔드

## 🛠 기술 스택

- Java 17
- Spring Boot 3.2
- MyBatis
- PostgreSQL
- Thymeleaf

## 📁 프로젝트 구조

```
user-app/
├── src/main/
│   ├── java/com/datastreams/gpt/
│   │   ├── chat/          # 채팅 컨트롤러/서비스
│   │   ├── login/         # SSO 인증
│   │   ├── file/          # 파일 업로드
│   │   ├── notice/        # 공지사항
│   │   └── survey/        # 만족도 조사
│   └── resources/
│       ├── mappers/       # MyBatis XML
│       └── application.yml
├── new-exgpt-ui/          # 사용자 UI 프론트엔드
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── assets/
│   └── package.json
├── pom.xml
└── mvnw
```

## 🚀 시작하기

### 백엔드 실행
```bash
./mvnw spring-boot:run
```
→ http://localhost:8080

### 프론트엔드 개발
```bash
cd new-exgpt-ui
npm install
npm run dev
```

## 📋 주요 기능

- SSO 기반 인증 (SimpleSSOTestController)
- 채팅 인터페이스
- 파일 업로드/다운로드
- 대화 히스토리
- 공지사항
- 만족도 조사

## 🔧 설정

### application.yml
```yaml
server:
  port: 8080

spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/admin_db
```

## 🔗 배포 URL
https://ui.datastreams.co.kr:20443
