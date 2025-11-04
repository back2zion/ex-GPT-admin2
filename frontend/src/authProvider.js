/**
 * react-admin authProvider
 * Spring Session 기반 인증
 */

const API_URL = '/api/v1/admin';

const authProvider = {
    // 로그인
    login: async ({ username, password }) => {
        try {
            const response = await fetch(`${API_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '로그인 실패');
            }

            const data = await response.json();

            // 토큰 저장
            if (data.access_token) {
                localStorage.setItem('authToken', data.access_token);
            }

            // 사용자 정보 저장
            if (data.user) {
                localStorage.setItem('user', JSON.stringify(data.user));
            }

            // 마지막 로그인 시간 저장
            localStorage.setItem('lastLogin', new Date().toISOString());

            return Promise.resolve();
        } catch (error) {
            return Promise.reject(error);
        }
    },

    // 로그아웃
    logout: async () => {
        // 토큰 및 사용자 정보 삭제
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        localStorage.removeItem('lastLogin');

        return Promise.resolve();
    },

    // 인증 체크
    checkAuth: async () => {
        const token = localStorage.getItem('authToken');

        if (!token) {
            return Promise.reject({ message: '인증 필요' });
        }

        // 토큰 유효성 검증 (선택사항)
        try {
            const response = await fetch(`${API_URL}/auth/me`, {
                headers: { 'Authorization': `Bearer ${token}` },
            });

            if (!response.ok) {
                localStorage.removeItem('authToken');
                localStorage.removeItem('user');
                return Promise.reject({ message: '인증 만료' });
            }

            return Promise.resolve();
        } catch (error) {
            // 네트워크 오류 시에도 토큰이 있으면 인증된 것으로 간주
            return Promise.resolve();
        }
    },

    // 에러 체크
    checkError: async (error) => {
        const status = error.status || error.response?.status;

        if (status === 401 || status === 403) {
            localStorage.removeItem('authToken');
            localStorage.removeItem('user');
            return Promise.reject();
        }

        return Promise.resolve();
    },

    // 권한 체크
    getPermissions: async () => {
        const user = localStorage.getItem('user');

        if (user) {
            const userData = JSON.parse(user);
            return Promise.resolve(userData.role || 'user');
        }

        return Promise.resolve('user');
    },

    // 사용자 정보 가져오기
    getIdentity: async () => {
        const user = localStorage.getItem('user');

        if (user) {
            const userData = JSON.parse(user);
            return Promise.resolve({
                id: userData.id,
                fullName: userData.username || '관리자',
                avatar: null,
            });
        }

        return Promise.reject();
    },
};

export default authProvider;
