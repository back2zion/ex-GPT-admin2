/**
 * react-admin Auth Provider
 * 테스트 환경: X-Test-Auth 헤더 사용 (authToken 사용 안 함)
 */

export const authProvider = {
  // 로그인
  login: async ({ username, password }) => {
    try {
      // 테스트 환경: 간단한 로그인 (실제 API 호출 없이 진행)
      // 프로덕션에서는 실제 API 호출로 변경 필요

      // 사용자 정보 저장 (authToken은 저장하지 않음)
      localStorage.setItem('user', JSON.stringify({
        id: 1,
        username: username,
        full_name: username,
        is_superuser: true
      }));
      localStorage.setItem('lastLogin', new Date().toISOString());

      return Promise.resolve();
    } catch (error) {
      console.error('Auth error:', error);
      return Promise.reject(error);
    }
  },

  // 로그아웃
  logout: () => {
    localStorage.removeItem('user');
    localStorage.removeItem('lastLogin');
    // authToken 제거하지 않음 (사용하지 않으므로)
    return Promise.resolve();
  },

  // 인증 확인 (테스트 환경: 항상 허용)
  checkAuth: () => {
    const user = localStorage.getItem('user');
    return user ? Promise.resolve() : Promise.reject();
  },

  // 에러 처리
  checkError: (error) => {
    const status = error.status;
    if (status === 401 || status === 403) {
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
