package com.datastreams.gpt.file.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

@Configuration
public class FileUploadRestTemplateConfig {

    @Bean("fileUploadRestTemplate")
    public RestTemplate fileUploadRestTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        
        // 타임아웃 설정 (파일 업로드용)
        factory.setConnectTimeout(30000); // 30초 연결 타임아웃
        factory.setReadTimeout(300000);   // 5분 읽기 타임아웃 (대용량 파일 업로드 고려)
        
        return new RestTemplate(factory);
    }
}
