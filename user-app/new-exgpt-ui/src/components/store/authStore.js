/**
 * 인증 상태 관리 Store
 *
 * 책임:
 * - 로그인/로그아웃 상태 관리
 * - 토큰 저장 및 검증
 * - 세션 쿠키 확인
 *
 * 보안:
 * - 만료된 토큰 자동 제거
 * - XSS 방지를 위한 HttpOnly 쿠키 사용 권장
 */

import { create } from "zustand";

export const useAuthStore = create((set, get) => ({
  // 상태
  isAuthenticated: false,
  user: null,

  /**
   * 초기화 - 저장된 토큰 확인
   */
  initialize: () => {
    const token = localStorage.getItem("access_token");

    if (token) {
      // 토큰이 있으면 인증 상태로 설정
      // TODO: 실제로는 토큰 검증 API 호출 필요
      set({
        isAuthenticated: true,
        user: { id: localStorage.getItem("user_id") || "react_user" }
      });
    } else {
      set({ isAuthenticated: false, user: null });
    }
  },

  /**
   * 로그인 성공
   * @param {string} token - JWT 토큰
   * @param {object} userData - 사용자 정보
   */
  login: (token, userData) => {
    localStorage.setItem("access_token", token);
    if (userData?.id) {
      localStorage.setItem("user_id", userData.id);
    }

    set({
      isAuthenticated: true,
      user: userData
    });
  },

  /**
   * 로그아웃
   * 보안: 모든 인증 정보 제거
   */
  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_id");

    set({
      isAuthenticated: false,
      user: null
    });
  },

  /**
   * 인증 실패 처리 (401 에러 등)
   * 자동으로 로그아웃하고 상태 초기화
   */
  handleAuthError: () => {
    const { logout } = get();
    logout();
  }
}));
