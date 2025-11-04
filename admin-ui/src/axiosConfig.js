/**
 * Axios 기본 설정
 * 모든 API 요청에 인증 헤더 추가
 */
import axios from 'axios';

// Axios 인터셉터 설정
axios.interceptors.request.use(
  (config) => {
    // 테스트 환경: 항상 X-Test-Auth 사용 (authToken 체크 제거)
    config.headers['X-Test-Auth'] = 'admin';

    // credentials 포함 (세션 쿠키 전송)
    config.withCredentials = true;

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default axios;
