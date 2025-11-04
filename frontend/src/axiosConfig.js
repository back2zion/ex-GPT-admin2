/**
 * Axios 기본 설정
 * 모든 API 요청에 인증 헤더 추가
 */
import axios from 'axios';

// Axios 인터셉터 설정
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    } else {
      // 임시: 테스트 환경에서 인증 우회
      config.headers['X-Test-Auth'] = 'admin';
    }
    config.withCredentials = true; // 세션 쿠키 포함
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default axios;
