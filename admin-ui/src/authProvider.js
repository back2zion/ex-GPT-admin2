/**
 * react-admin Auth Provider
 * JWT 기반 인증
 */

export const authProvider = {
  // 로그인
  login: async ({ username, password }) => {
    try {
      // Use relative path (requires Apache proxy configuration)
      // ProxyPass /api/v1/auth http://localhost:8010/api/v1/auth
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
        credentials: 'include',
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Login failed:', response.status, errorText);
        throw new Error('로그인에 실패했습니다. 아이디와 비밀번호를 확인하세요.');
      }

      const data = await response.json();

      // Store token
      localStorage.setItem('authToken', data.access_token);

      // Fetch user info
      const userResponse = await fetch('/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${data.access_token}`
        }
      });

      if (userResponse.ok) {
        const userData = await userResponse.json();
        localStorage.setItem('user', JSON.stringify(userData));
        localStorage.setItem('lastLogin', new Date().toISOString());
      }

      return Promise.resolve();
    } catch (error) {
      console.error('Auth error:', error);
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
