package com.datastreams.gpt.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;

/**
 * RestTemplate 설정
 * HTTP 클라이언트 설정을 위한 Configuration 클래스
 * 
 * @Version: 1.0
 * @Author: create by TeamS
 * @Desc: RestTemplate Configuration
 */
@Configuration
public class RestTemplateConfig {
    
    /**
     * RestTemplate Bean 생성
     * 
     * @return RestTemplate 인스턴스
     */
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}
