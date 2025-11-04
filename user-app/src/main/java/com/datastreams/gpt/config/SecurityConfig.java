package com.datastreams.gpt.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import java.util.Arrays;

/**
 * 애플리케이션의 보안 설정 클래스
 * Spring Security 사용
 */
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            // CSRF 설정 (담에 SSO 할 때,  이 라인을 삭제하면 됨!!!)
            .csrf(csrf -> csrf.disable())
            // CORS 설정 활성화 (프론트엔드 통신을 위해 필요)
            .cors(cors -> cors.configurationSource(corsConfigurationSource()))
            // 아래부터 세션 설정
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.ALWAYS)
                    // 세션 생성 정책 설정 -> 항상 만듬
                .maximumSessions(1)
                    // 세션 당 사용자수 설정 -> 이거 옵션화해서 admin은 중복 로그인 가능하게 만들어도 좋아요 20250929
                .maxSessionsPreventsLogin(false)
                    // 중복 로그인을 하면 기존 로그인 로그아웃 시키는 옵션
            )

            // HTTP 요청에 대한 접근 권한 설정 -> 여기 중요함 !! 이거 옵션으로 빼도 좋을거같아요 (20250929)
            .authorizeHttpRequests(auth -> auth
                // 프론트에서 필요한 정적 파일은 모두 접근이 가능해야해서 허용시킨 리스트 (당연히 필요 시, 추가 가능.. 그럴 때가 곧 올것임)
                .requestMatchers(
                    "/", "/index.html", "/static/**", "/images/**", "/*.jsx", "/*.scss",
                    "/*.js", "/*.css", "/*.ico", "/*.png", "/*.json", "/*.svg", "/hello.html", "/login",
                    "/assets/**",     // [수정됨] React 빌드 파일 경로 - 2025-10-01 추가
                    "/ai", "/ai/**",  // [수정됨] AI 채팅 페이지 허용 - 2025-10-01 추가
                    "/govAi", "/govAi/**"  // [수정됨] 국정감사 AI 페이지 허용 - 2025-10-01 추가
                ).permitAll()
                // 인증이 없어도 가능해야하는 api 경로 아래에 적으면 됩니다. 로그인, 로그아웃, 헬스 체크 등등등등
                .requestMatchers(
                    "/api/auth/login",        // 로그인 API  -> 이거 수정해야함 20250929
                    "/api/auth/logout",       // 로그아웃 API  -> 이거도 수정해야함 20250929
                    "/api/auth/status",       // [수정됨] 로그인 상태 확인 API - 2025-09-30 추가
                    "/api/auth/sso/**",       // [수정됨] SSO 로그인 및 테스트 API - 2025-10-15 추가
                    "/api/sso/**",            // [수정됨] 간단한 SSO 테스트 API - 2025-10-15 추가
                    "/api/auth/session/validate",  // [수정됨] 세션 유효성 체크 API - 2025-10-01 추가
                    "/api/auth/user/**",      // [수정됨] 사용자 정보 조회 API - 2025-10-01 추가
                    "/api/user/**",           // [수정됨] 사용자 설정 API (setUserInfo 등) - 2025-10-13 추가
                    "/api/user/setUserInfo",  // [수정됨] setUserInfo API 직접 허용 - 2025-10-13 추가
                    "/api/menu/**",           // [수정됨] 메뉴 조회 API - 2025-10-02 추가
                    "/api/suggestionList",    // [수정됨] 제안 목록 API - 2025-10-13 추가
                    "/api/notice/**",         // [수정됨] 공지사항 API - 2025-10-14 추가
                    "/api/survey/**",         // [수정됨] 만족도 저장 API - 2025-10-14 추가
                    "/api/chat/**",           // [수정됨] Chat API - 2025-10-16 추가
                    "/v1/health",       // 애플리케이션 상태 체크
                    "/ws/**",                 // WebSocket 연결 경로
                    "/v1/chat/respond/**",     // AI 채팅 답변 스트리밍 경로 (SSE)
                    "/swagger-ui/**",         // [수정됨] Swagger UI 경로 - 2025-09-30 추가 (Swagger 접근 허용)
                    "/swagger-ui.html",       // [수정됨] Swagger UI 메인 페이지 - 2025-09-30 추가
                    "/v3/api-docs/**",        // [수정됨] OpenAPI 문서 경로 - 2025-09-30 추가
                    "/swagger-resources/**",  // [수정됨] Swagger 리소스 - 2025-09-30 추가
                    "/webjars/**"             // [수정됨] Swagger 의존성 리소스 - 2025-09-30 추가
                ).permitAll()

                .anyRequest().authenticated() // 여기에서 인증 필요한 요청들을 적어주시면 됩니다.
            )

            .formLogin(form -> form.disable())        // 기본 로그인 폼 비활성화
            .logout(logout -> logout.disable())       // 기본 로그아웃 비활성화
            .httpBasic(basic -> basic.disable());     // HTTP Basic 인증 비활성화
            // Spring Security의 기본 로그인 기능 화면(?) 꺼버림. 프론트 양주임님꺼 받은ㄱ ㅓ 쓸거임

        return http.build();
        // 위의 설정들로 SecurityFilterChain 객체 생성 후 리턴
    }

    /**
     * CORS 설정
     * 프론트엔드와 백엔드 간 통신을 위한 CORS 설정
     */
    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        
        // 허용할 Origin 설정
        configuration.setAllowedOriginPatterns(Arrays.asList("*"));
        
        // 허용할 HTTP 메서드 설정
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE", "OPTIONS"));
        
        // 허용할 헤더 설정
        configuration.setAllowedHeaders(Arrays.asList("*"));
        
        // 쿠키/인증 정보 포함 허용
        configuration.setAllowCredentials(true);
        
        // preflight 요청 캐시 시간 설정
        configuration.setMaxAge(3600L);
        
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        
        return source;
    }
}