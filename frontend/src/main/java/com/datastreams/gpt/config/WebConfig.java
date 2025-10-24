package com.datastreams.gpt.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.Resource;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.resource.PathResourceResolver;

import java.io.IOException;

/**
 * Spring MVC 설정
 * React Router 지원을 위한 설정 포함
 */
@Configuration
public class WebConfig implements WebMvcConfigurer {

    /**
     * React Router를 위한 리소스 핸들러 설정
     * 모든 경로를 index.html로 포워딩 (SPA 지원)
     */
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        registry.addResourceHandler("/**")
            .addResourceLocations("classpath:/static/")
            .resourceChain(true)
            .addResolver(new PathResourceResolver() {
                @Override
                protected Resource getResource(String resourcePath, Resource location) throws IOException {
                    Resource requestedResource = location.createRelative(resourcePath);
                    
                    // 실제 파일이 존재하면 그대로 반환
                    if (requestedResource.exists() && requestedResource.isReadable()) {
                        return requestedResource;
                    }
                    
                    // 파일이 없으면 index.html로 포워딩 (React Router 경로)
                    return new ClassPathResource("/static/index.html");
                }
            });
    }
}

