package com.datastreams.gpt.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.filter.CorsFilter;

/**
 * CORS 설정 클래스
 * 프론트엔드와 백엔드 포트가 다를 때 필요
 */
@Configuration
public class CorsConfig {

    @Bean
    public CorsFilter corsFilter() {
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        CorsConfiguration config = new CorsConfiguration();
        
        // 자격 증명 허용 (쿠키, 세션 등)
        config.setAllowCredentials(true);
        
        // 허용할 Origin (프론트엔드 주소)
        config.addAllowedOrigin("http://localhost:4173");
        config.addAllowedOrigin("http://localhost:4174");
        config.addAllowedOrigin("http://localhost:4175");
        config.addAllowedOrigin("http://localhost:5173");
        
        // 모든 헤더 허용
        config.addAllowedHeader("*");
        
        // 모든 HTTP 메서드 허용
        config.addAllowedMethod("*");
        
        source.registerCorsConfiguration("/**", config);
        return new CorsFilter(source);
    }
}

