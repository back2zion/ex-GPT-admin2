/**
 * API 유틸리티
 * Axios 기반 + 시큐어 코딩
 */

import axios from 'axios';
import { getCsrfToken } from './security';

// API Base URL
const API_BASE = '/api/v1';

/**
 * Axios 인스턴스 생성 (시큐어 코딩 적용)
 */
const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // CSRF 방어를 위해 쿠키 전송
});

/**
 * 요청 인터셉터 (CSRF 토큰 추가)
 */
apiClient.interceptors.request.use(
  (config) => {
    // GET 요청이 아닐 때 CSRF 토큰 추가
    if (config.method !== 'get') {
      const csrfToken = getCsrfToken();
      if (csrfToken) {
        config.headers['X-CSRF-Token'] = csrfToken;
      }
    }

    // Authorization 토큰 추가 (로그인 후)
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * 응답 인터셉터 (에러 처리)
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // 401 Unauthorized - 로그인 페이지로 리다이렉트
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/admin/';
    }

    // 403 Forbidden - 권한 없음
    if (error.response?.status === 403) {
      console.error('권한이 없습니다.');
    }

    return Promise.reject(error);
  }
);

// ==================== API 함수들 ====================

/**
 * 사용 이력 조회 (대화내역)
 * @param {Object} params - 쿼리 파라미터 (start_date, end_date, user_id, limit)
 * @returns {Promise<Array>}
 */
export async function getUsageHistory(params = {}) {
  const response = await apiClient.get('/usage', { params });
  return response.data;
}

/**
 * 사용 이력 상세 조회
 * @param {number} id - 사용 이력 ID
 * @returns {Promise<Object>}
 */
export async function getUsageDetail(id) {
  const response = await apiClient.get(`/usage/${id}`);
  return response.data;
}

/**
 * 통계 요약 조회
 * @param {Object} params - 쿼리 파라미터 (start_date, end_date)
 * @returns {Promise<Object>}
 */
export async function getStatisticsSummary(params = {}) {
  const response = await apiClient.get('/admin/statistics/summary', { params });
  return response.data;
}

/**
 * 일별 통계 조회
 * @param {string} start_date - 시작 날짜 (YYYY-MM-DD)
 * @param {string} end_date - 종료 날짜 (YYYY-MM-DD)
 * @returns {Promise<Array>}
 */
export async function getDailyStatistics(start_date, end_date) {
  const response = await apiClient.get('/admin/statistics/daily', {
    params: { start_date, end_date }
  });
  return response.data;
}

/**
 * 시간별 통계 조회
 * @param {string} start_date - 시작 날짜 (YYYY-MM-DD)
 * @param {string} end_date - 종료 날짜 (YYYY-MM-DD)
 * @returns {Promise<Array>}
 */
export async function getHourlyStatistics(start_date, end_date) {
  const response = await apiClient.get('/admin/statistics/hourly', {
    params: { start_date, end_date }
  });
  return response.data;
}

/**
 * 주별 통계 조회
 * @param {number} weeks - 조회할 주 수
 * @returns {Promise<Array>}
 */
export async function getWeeklyStatistics(weeks = 4) {
  const response = await apiClient.get('/admin/statistics/weekly', {
    params: { weeks }
  });
  return response.data;
}

/**
 * 월별 통계 조회
 * @param {number} months - 조회할 월 수
 * @returns {Promise<Array>}
 */
export async function getMonthlyStatistics(months = 12) {
  const response = await apiClient.get('/admin/statistics/monthly', {
    params: { months }
  });
  return response.data;
}

/**
 * 부서별 통계 조회
 * @param {Object} params - 쿼리 파라미터 (start_date, end_date)
 * @returns {Promise<Array>}
 */
export async function getStatisticsByDepartment(params = {}) {
  const response = await apiClient.get('/admin/statistics/by-department', { params });
  return response.data;
}

/**
 * 모델별 통계 조회
 * @param {Object} params - 쿼리 파라미터 (start_date, end_date)
 * @returns {Promise<Array>}
 */
export async function getStatisticsByModel(params = {}) {
  const response = await apiClient.get('/admin/statistics/by-model', { params });
  return response.data;
}

/**
 * 서버 요약 정보 조회
 * @returns {Promise<Object>}
 */
export async function getServerSummary() {
  const response = await apiClient.get('/admin/stats/server/summary');
  return response.data;
}

/**
 * 시간별 CPU 사용량 조회
 * @returns {Promise<Array>}
 */
export async function getHistoricalCpuUsage() {
  const response = await apiClient.get('/admin/stats/server/cpu-history');
  return response.data;
}

/**
 * 시간별 메모리 사용량 조회
 * @returns {Promise<Array>}
 */
export async function getHistoricalMemoryUsage() {
  const response = await apiClient.get('/admin/stats/server/memory-history');
  return response.data;
}

/**
 * 디스크 사용량 조회
 * @returns {Promise<Array>}
 */
export async function getDiskUsage() {
  const response = await apiClient.get('/admin/stats/server/disk');
  return response.data;
}

/**
 * GPU 사용량 조회
 * @returns {Promise<Object>}
 */
export async function getGpuUsage() {
  const response = await apiClient.get('/admin/stats/server/gpu');
  return response.data;
}

/**
 * Docker 컨테이너 정보 조회
 * @returns {Promise<Object>}
 */
export async function getDockerInfo() {
  const response = await apiClient.get('/admin/stats/server/docker');
  return response.data;
}

/**
 * 로그인
 * @param {string} username - 사용자 ID
 * @param {string} password - 비밀번호
 * @returns {Promise<Object>}
 */
export async function login(username, password) {
  // OAuth2PasswordRequestForm은 application/x-www-form-urlencoded 필요
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await apiClient.post('/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  return response.data;
}

/**
 * 로그아웃
 * @returns {Promise<void>}
 */
export async function logout() {
  await apiClient.post('/auth/logout');
  localStorage.removeItem('authToken');
}

/**
 * 공지사항 목록 조회
 * @param {Object} params - 쿼리 파라미터
 * @returns {Promise<Array>}
 */
export async function getNotices(params = {}) {
  const response = await apiClient.get('/notices', { params });
  return response.data;
}

/**
 * 공지사항 생성
 * @param {Object} data - 공지사항 데이터
 * @returns {Promise<Object>}
 */
export async function createNotice(data) {
  const response = await apiClient.post('/notices', data);
  return response.data;
}

/**
 * 만족도 조사 결과 조회
 * @param {Object} params - 쿼리 파라미터
 * @returns {Promise<Object>}
 */
export async function getSatisfactionResults(params = {}) {
  const response = await apiClient.get('/satisfaction', { params });
  return response.data;
}

/**
 * 문서 권한 목록 조회
 * @param {Object} params - 쿼리 파라미터
 * @returns {Promise<Array>}
 */
export async function getDocumentPermissions(params = {}) {
  const response = await apiClient.get('/document-permissions', { params });
  return response.data;
}

/**
 * 문서 권한 부여
 * @param {Object} data - 권한 데이터
 * @returns {Promise<Object>}
 */
export async function grantDocumentPermission(data) {
  const response = await apiClient.post('/document-permissions', data);
  return response.data;
}

/**
 * 대화내역 목록 조회
 * @param {Object} params - 쿼리 파라미터 (start, end, main_category, sub_category, page, limit)
 * @returns {Promise<Object>} - { items, total, page, limit, total_pages }
 */
export async function getConversations(params = {}) {
  console.log('[API] getConversations 호출:', params);
  console.log('[API] 요청 URL:', apiClient.defaults.baseURL + '/admin/conversations/simple');

  try {
    const response = await apiClient.get('/admin/conversations/simple', { params });
    console.log('[API] getConversations 응답:', response.data);
    return response.data;
  } catch (error) {
    console.error('[API] getConversations 실패:', error);
    throw error;
  }
}

/**
 * 대화내역 상세 조회
 * @param {number} id - 대화내역 ID
 * @returns {Promise<Object>}
 */
export async function getConversationDetail(id) {
  const response = await apiClient.get(`/admin/conversations/simple/${id}`);
  return response.data;
}

/**
 * 세션 내 모든 대화 조회
 * @param {string} sessionId - 세션 ID
 * @returns {Promise<Array>} - 세션 내 모든 대화 (시간순)
 */
export async function getSessionConversations(sessionId) {
  console.log('[API] getSessionConversations 호출:', sessionId);
  try {
    const response = await apiClient.get(`/admin/conversations/session/${sessionId}`);
    console.log('[API] getSessionConversations 응답:', response.data.length, '개 대화');
    return response.data;
  } catch (error) {
    console.error('[API] getSessionConversations 실패:', error);
    throw error;
  }
}

/**
 * 일별 오류 신고 수 조회
 * @param {string} start_date - 시작 날짜 (YYYY-MM-DD)
 * @param {string} end_date - 종료 날짜 (YYYY-MM-DD)
 * @returns {Promise<Array>}
 */
export async function getErrorReportsDaily(start_date, end_date) {
  const params = {};
  if (start_date) params.start_date = start_date;
  if (end_date) params.end_date = end_date;

  const response = await apiClient.get('/admin/statistics/error-reports-daily', { params });
  return response.data;
}

/**
 * 카테고리별 문서 등록 현황 조회
 * @returns {Promise<Object>}
 */
export async function getDocumentsByCategory() {
  const response = await apiClient.get('/admin/statistics/documents-by-category');
  return response.data;
}

/**
 * 분야별 질문 수 조회 (경영/기술/기타)
 * @param {Object} params - 쿼리 파라미터 (start_date, end_date)
 * @returns {Promise<Object>}
 */
export async function getQuestionsByField(params = {}) {
  const response = await apiClient.get('/admin/statistics/questions-by-field', { params });
  return response.data;
}

export default apiClient;
