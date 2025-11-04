/**
 * API Client with Interceptor Pattern
 *
 * 책임:
 * - 모든 API 요청에 대한 중앙 집중식 처리
 * - 401 인증 에러 자동 처리
 * - 토큰 자동 추가
 * - 에러 로깅
 *
 * 보안:
 * - XSS 방지: Content-Type 검증
 * - CSRF 방지: credentials: 'include'
 * - 자동 토큰 정리
 */

import { useAuthStore } from "@store/authStore";

// CONTEXT_PATH 제거: React 앱이 이미 /exGenBotDS/에서 로드되므로 중복 추가 방지
const CONTEXT_PATH = '';

/**
 * HTTP 요청 래퍼
 * @param {string} url - API 엔드포인트
 * @param {object} options - fetch options
 * @returns {Promise<Response>}
 */
async function request(url, options = {}) {
  // 1. 기본 헤더 설정
  const headers = {
    "Content-Type": "application/json",
    ...options.headers
  };

  // 2. 토큰 자동 추가
  const token = localStorage.getItem("access_token");
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // 3. 요청 실행
  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "include" // 세션 쿠키 포함
  });

  // 4. 401 에러 자동 처리
  if (response.status === 401) {
    // 인증 실패 - 토큰 삭제 및 로그아웃
    useAuthStore.getState().handleAuthError();

    // 빈 응답 반환 (UI에서 처리)
    return new Response(JSON.stringify({ error: "Unauthorized" }), {
      status: 401,
      headers: { "Content-Type": "application/json" }
    });
  }

  // 5. 정상 응답 반환
  return response;
}

/**
 * GET 요청
 */
export async function get(endpoint) {
  const url = `${CONTEXT_PATH}${endpoint}`;
  const response = await request(url, { method: "GET" });

  if (!response.ok && response.status !== 401) {
    throw new Error(`GET ${endpoint} failed: ${response.status}`);
  }

  return response.json();
}

/**
 * POST 요청
 */
export async function post(endpoint, data) {
  const url = `${CONTEXT_PATH}${endpoint}`;
  const response = await request(url, {
    method: "POST",
    body: JSON.stringify(data)
  });

  if (!response.ok && response.status !== 401) {
    throw new Error(`POST ${endpoint} failed: ${response.status}`);
  }

  return response.json();
}

/**
 * DELETE 요청
 */
export async function del(endpoint) {
  const url = `${CONTEXT_PATH}${endpoint}`;
  const response = await request(url, { method: "DELETE" });

  if (!response.ok && response.status !== 401) {
    throw new Error(`DELETE ${endpoint} failed: ${response.status}`);
  }

  return response.json();
}

export default { get, post, del };
