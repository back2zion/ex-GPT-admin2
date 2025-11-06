/**
 * react-admin Auth Provider
 * JWT 기반 인증
 */

export const authProvider = {
  // 로그인
  login: async ({ username, password }) => {
    const { login } = await import('./utils/api');
    try {
      const response = await login(username, password);
      // api.js의 login 함수가 이미 localStorage에 토큰 저장
      return Promise.resolve();
    } catch (error) {
      return Promise.reject(error);
    }
  },

  // 로그아웃
  logout: () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    localStorage.removeItem('lastLogin');
    return Promise.resolve();
  },

  // 인증 확인
  checkAuth: () => {
    const token = localStorage.getItem('authToken');
    return token ? Promise.resolve() : Promise.reject();
  },

  // 에러 처리
  checkError: (error) => {
    const status = error.status;
    if (status === 401 || status === 403) {
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      localStorage.removeItem('lastLogin');
      return Promise.reject();
    }
    return Promise.resolve();
  },

  // 권한 확인
  getPermissions: () => {
    // 향후 구현: 사용자 역할 기반 권한
    return Promise.resolve();
  },

  // 사용자 정보 조회
  getIdentity: () => {
    const user = localStorage.getItem('user');
    if (user) {
      try {
        const userData = JSON.parse(user);
        return Promise.resolve({
          id: userData.id,
          fullName: userData.full_name || userData.username,
          avatar: null,
        });
      } catch (e) {
        return Promise.reject();
      }
    }
    return Promise.reject();
  },
};

export default authProvider;
