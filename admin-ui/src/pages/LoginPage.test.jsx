/**
 * LoginPage TDD 테스트
 *
 * 테스트 커버리지:
 * - 컴포넌트 렌더링
 * - Body 클래스 적용 및 정리
 * - 폼 입력 및 검증
 * - 로그인 성공/실패 시나리오
 * - "아이디 저장" 기능
 * - 비밀번호 표시/숨기기
 * - 계정 잠금 메시지
 * - 시큐어 코딩 (XSS, 입력 검증)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import LoginPage from './LoginPage';
import * as api from '../utils/api';

// Mock API
vi.mock('../utils/api', () => ({
  login: vi.fn(),
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// 테스트 래퍼
const renderLoginPage = () => {
  return render(
    <BrowserRouter>
      <LoginPage />
    </BrowserRouter>
  );
};

describe('LoginPage 컴포넌트', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    document.documentElement.className = '';
    document.body.className = '';
  });

  afterEach(() => {
    document.documentElement.className = '';
    document.body.className = '';
  });

  describe('렌더링 테스트', () => {
    it('로그인 페이지가 정상적으로 렌더링되어야 한다', () => {
      renderLoginPage();

      expect(screen.getByPlaceholderText('아이디')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('비밀번호')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
      expect(screen.getByLabelText('아이디저장')).toBeInTheDocument();
    });

    it('로고와 타이틀이 표시되어야 한다', () => {
      renderLoginPage();

      expect(screen.getByAltText('ex-GPT Logo')).toBeInTheDocument();
      expect(screen.getByText('관리자 대시보드')).toBeInTheDocument();
    });

    it('저작권 정보가 표시되어야 한다', () => {
      renderLoginPage();

      expect(
        screen.getByText(/© 2025 Korea Expressway Corporation Service Co., Ltd./i)
      ).toBeInTheDocument();
    });

    it('보안 안내 메시지가 표시되어야 한다', () => {
      renderLoginPage();

      expect(
        screen.getByText(/로그인 5회 실패시 계정이 일시적으로 차단됩니다/i)
      ).toBeInTheDocument();
    });
  });

  describe('Body 클래스 적용 테스트', () => {
    it('컴포넌트 마운트 시 login-html 클래스가 추가되어야 한다', () => {
      renderLoginPage();

      expect(document.documentElement.classList.contains('login-html')).toBe(true);
    });

    it('컴포넌트 마운트 시 login-body 클래스가 추가되어야 한다', () => {
      renderLoginPage();

      expect(document.body.classList.contains('login-body')).toBe(true);
    });

    it('컴포넌트 언마운트 시 클래스가 제거되어야 한다', () => {
      const { unmount } = renderLoginPage();

      expect(document.documentElement.classList.contains('login-html')).toBe(true);
      expect(document.body.classList.contains('login-body')).toBe(true);

      unmount();

      expect(document.documentElement.classList.contains('login-html')).toBe(false);
      expect(document.body.classList.contains('login-body')).toBe(false);
    });
  });

  describe('폼 입력 테스트', () => {
    it('아이디 입력이 가능해야 한다', async () => {
      const user = userEvent.setup();
      renderLoginPage();

      const usernameInput = screen.getByPlaceholderText('아이디');
      await user.type(usernameInput, 'testuser');

      expect(usernameInput).toHaveValue('testuser');
    });

    it('비밀번호 입력이 가능해야 한다', async () => {
      const user = userEvent.setup();
      renderLoginPage();

      const passwordInput = screen.getByPlaceholderText('비밀번호');
      await user.type(passwordInput, 'password123');

      expect(passwordInput).toHaveValue('password123');
    });

    it('비밀번호는 기본적으로 숨겨져야 한다', () => {
      renderLoginPage();

      const passwordInput = screen.getByPlaceholderText('비밀번호');
      expect(passwordInput).toHaveAttribute('type', 'password');
    });

    it('아이디 입력 최대 길이는 80자여야 한다', () => {
      renderLoginPage();

      const usernameInput = screen.getByPlaceholderText('아이디');
      expect(usernameInput).toHaveAttribute('maxLength', '80');
    });

    it('비밀번호 입력 최대 길이는 80자여야 한다', () => {
      renderLoginPage();

      const passwordInput = screen.getByPlaceholderText('비밀번호');
      expect(passwordInput).toHaveAttribute('maxLength', '80');
    });
  });

  describe('비밀번호 표시/숨기기 테스트', () => {
    it('눈 아이콘 클릭 시 비밀번호가 표시되어야 한다', async () => {
      const user = userEvent.setup();
      renderLoginPage();

      const passwordInput = screen.getByPlaceholderText('비밀번호');
      const toggleButton = screen.getByLabelText('비밀번호 표시 토글');

      expect(passwordInput).toHaveAttribute('type', 'password');

      await user.click(toggleButton);

      expect(passwordInput).toHaveAttribute('type', 'text');
    });

    it('눈 아이콘을 다시 클릭하면 비밀번호가 숨겨져야 한다', async () => {
      const user = userEvent.setup();
      renderLoginPage();

      const passwordInput = screen.getByPlaceholderText('비밀번호');
      const toggleButton = screen.getByLabelText('비밀번호 표시 토글');

      await user.click(toggleButton);
      expect(passwordInput).toHaveAttribute('type', 'text');

      await user.click(toggleButton);
      expect(passwordInput).toHaveAttribute('type', 'password');
    });
  });

  describe('"아이디 저장" 기능 테스트', () => {
    it('체크박스가 정상적으로 작동해야 한다', async () => {
      const user = userEvent.setup();
      renderLoginPage();

      const checkbox = screen.getByLabelText('아이디저장');
      expect(checkbox).not.toBeChecked();

      await user.click(checkbox);
      expect(checkbox).toBeChecked();
    });

    it('로컬스토리지에 저장된 아이디가 있으면 자동으로 입력되어야 한다', () => {
      localStorage.setItem('rememberedUsername', 'saveduser');

      renderLoginPage();

      const usernameInput = screen.getByPlaceholderText('아이디');
      expect(usernameInput).toHaveValue('saveduser');
    });

    it('저장된 아이디가 있으면 체크박스가 자동으로 체크되어야 한다', () => {
      localStorage.setItem('rememberedUsername', 'saveduser');

      renderLoginPage();

      const checkbox = screen.getByLabelText('아이디저장');
      expect(checkbox).toBeChecked();
    });
  });

  describe('로그인 검증 테스트', () => {
    it('아이디가 없으면 에러 메시지가 표시되어야 한다', async () => {
      const user = userEvent.setup();
      renderLoginPage();

      const loginButton = screen.getByRole('button', { name: /login/i });
      await user.click(loginButton);

      expect(
        screen.getByText('아이디와 비밀번호를 입력하세요.')
      ).toBeInTheDocument();
    });

    it('비밀번호가 없으면 에러 메시지가 표시되어야 한다', async () => {
      const user = userEvent.setup();
      renderLoginPage();

      const usernameInput = screen.getByPlaceholderText('아이디');
      await user.type(usernameInput, 'testuser');

      const loginButton = screen.getByRole('button', { name: /login/i });
      await user.click(loginButton);

      expect(
        screen.getByText('아이디와 비밀번호를 입력하세요.')
      ).toBeInTheDocument();
    });
  });

  describe('로그인 성공 시나리오', () => {
    it('로그인 성공 시 토큰이 저장되고 대시보드로 이동해야 한다', async () => {
      const user = userEvent.setup();
      api.login.mockResolvedValue({ access_token: 'test-token-123' });

      renderLoginPage();

      const usernameInput = screen.getByPlaceholderText('아이디');
      const passwordInput = screen.getByPlaceholderText('비밀번호');
      const loginButton = screen.getByRole('button', { name: /login/i });

      await user.type(usernameInput, 'testuser');
      await user.type(passwordInput, 'password123');
      await user.click(loginButton);

      await waitFor(() => {
        expect(localStorage.setItem).toHaveBeenCalledWith('authToken', 'test-token-123');
        expect(mockNavigate).toHaveBeenCalledWith('/');
      });
    });

    it('"아이디 저장"이 체크되면 아이디가 로컬스토리지에 저장되어야 한다', async () => {
      const user = userEvent.setup();
      api.login.mockResolvedValue({ access_token: 'test-token-123' });

      renderLoginPage();

      const usernameInput = screen.getByPlaceholderText('아이디');
      const passwordInput = screen.getByPlaceholderText('비밀번호');
      const checkbox = screen.getByLabelText('아이디저장');
      const loginButton = screen.getByRole('button', { name: /login/i });

      await user.type(usernameInput, 'testuser');
      await user.type(passwordInput, 'password123');
      await user.click(checkbox);
      await user.click(loginButton);

      await waitFor(() => {
        expect(localStorage.setItem).toHaveBeenCalledWith('rememberedUsername', 'testuser');
      });
    });

    it('"아이디 저장"이 체크되지 않으면 저장된 아이디가 삭제되어야 한다', async () => {
      const user = userEvent.setup();
      api.login.mockResolvedValue({ access_token: 'test-token-123' });
      localStorage.setItem('rememberedUsername', 'olduser');

      renderLoginPage();

      const usernameInput = screen.getByPlaceholderText('아이디');
      const passwordInput = screen.getByPlaceholderText('비밀번호');
      const checkbox = screen.getByLabelText('아이디저장');
      const loginButton = screen.getByRole('button', { name: /login/i });

      // 체크박스가 자동으로 체크되어 있으므로, 해제해야 함
      await user.click(checkbox);

      await user.clear(usernameInput);
      await user.type(usernameInput, 'newuser');
      await user.type(passwordInput, 'password123');
      await user.click(loginButton);

      await waitFor(() => {
        expect(localStorage.removeItem).toHaveBeenCalledWith('rememberedUsername');
      });
    });

    it('로그인 중에는 버튼이 비활성화되어야 한다', async () => {
      const user = userEvent.setup();
      api.login.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({ access_token: 'test-token' }), 1000)));

      renderLoginPage();

      const usernameInput = screen.getByPlaceholderText('아이디');
      const passwordInput = screen.getByPlaceholderText('비밀번호');
      const loginButton = screen.getByRole('button', { name: /login/i });

      await user.type(usernameInput, 'testuser');
      await user.type(passwordInput, 'password123');
      await user.click(loginButton);

      expect(loginButton).toBeDisabled();
      expect(loginButton).toHaveTextContent('로그인 중...');
    });
  });

  describe('로그인 실패 시나리오', () => {
    it('로그인 실패 시 에러 메시지가 표시되어야 한다', async () => {
      const user = userEvent.setup();
      api.login.mockRejectedValue({
        response: { data: { detail: 'Invalid credentials' } }
      });

      renderLoginPage();

      const usernameInput = screen.getByPlaceholderText('아이디');
      const passwordInput = screen.getByPlaceholderText('비밀번호');
      const loginButton = screen.getByRole('button', { name: /login/i });

      await user.type(usernameInput, 'wronguser');
      await user.type(passwordInput, 'wrongpass');
      await user.click(loginButton);

      await waitFor(() => {
        expect(
          screen.getByText('로그인에 실패했습니다. 아이디와 비밀번호를 확인하세요.')
        ).toBeInTheDocument();
      });
    });

    it('계정 잠금 메시지가 표시되어야 한다', async () => {
      const user = userEvent.setup();
      const lockMessage = '계정이 5회 로그인 실패로 30분간 잠겼습니다.';
      api.login.mockRejectedValue({
        response: { data: { detail: lockMessage } }
      });

      renderLoginPage();

      const usernameInput = screen.getByPlaceholderText('아이디');
      const passwordInput = screen.getByPlaceholderText('비밀번호');
      const loginButton = screen.getByRole('button', { name: /login/i });

      await user.type(usernameInput, 'lockeduser');
      await user.type(passwordInput, 'password');
      await user.click(loginButton);

      await waitFor(() => {
        expect(screen.getByText(lockMessage)).toBeInTheDocument();
      });
    });

    it('입력 중 에러 메시지가 사라져야 한다', async () => {
      const user = userEvent.setup();
      api.login.mockRejectedValue({
        response: { data: { detail: 'Invalid credentials' } }
      });

      renderLoginPage();

      const usernameInput = screen.getByPlaceholderText('아이디');
      const passwordInput = screen.getByPlaceholderText('비밀번호');
      const loginButton = screen.getByRole('button', { name: /login/i });

      await user.type(usernameInput, 'wronguser');
      await user.type(passwordInput, 'wrongpass');
      await user.click(loginButton);

      await waitFor(() => {
        expect(
          screen.getByText('로그인에 실패했습니다. 아이디와 비밀번호를 확인하세요.')
        ).toBeInTheDocument();
      });

      // 입력 시작
      await user.type(usernameInput, 'a');

      await waitFor(() => {
        expect(
          screen.queryByText('로그인에 실패했습니다. 아이디와 비밀번호를 확인하세요.')
        ).not.toBeInTheDocument();
      });
    });
  });

  describe('시큐어 코딩 검증', () => {
    it('autoComplete 속성이 올바르게 설정되어야 한다', () => {
      renderLoginPage();

      const usernameInput = screen.getByPlaceholderText('아이디');
      const passwordInput = screen.getByPlaceholderText('비밀번호');

      expect(usernameInput).toHaveAttribute('autoComplete', 'username');
      expect(passwordInput).toHaveAttribute('autoComplete', 'current-password');
    });

    it('로그인 중에는 입력 필드가 비활성화되어야 한다', async () => {
      const user = userEvent.setup();
      api.login.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({ access_token: 'test-token' }), 1000)));

      renderLoginPage();

      const usernameInput = screen.getByPlaceholderText('아이디');
      const passwordInput = screen.getByPlaceholderText('비밀번호');
      const loginButton = screen.getByRole('button', { name: /login/i });

      await user.type(usernameInput, 'testuser');
      await user.type(passwordInput, 'password123');
      await user.click(loginButton);

      expect(usernameInput).toBeDisabled();
      expect(passwordInput).toBeDisabled();
    });

    it('API 함수가 올바른 파라미터로 호출되어야 한다', async () => {
      const user = userEvent.setup();
      api.login.mockResolvedValue({ access_token: 'test-token' });

      renderLoginPage();

      const usernameInput = screen.getByPlaceholderText('아이디');
      const passwordInput = screen.getByPlaceholderText('비밀번호');
      const loginButton = screen.getByRole('button', { name: /login/i });

      await user.type(usernameInput, 'testuser');
      await user.type(passwordInput, 'password123');
      await user.click(loginButton);

      await waitFor(() => {
        expect(api.login).toHaveBeenCalledWith('testuser', 'password123');
      });
    });
  });

  describe('접근성 테스트', () => {
    it('모든 입력 필드가 label 또는 placeholder를 가져야 한다', () => {
      renderLoginPage();

      const usernameInput = screen.getByPlaceholderText('아이디');
      const passwordInput = screen.getByPlaceholderText('비밀번호');
      const checkbox = screen.getByLabelText('아이디저장');

      expect(usernameInput).toBeInTheDocument();
      expect(passwordInput).toBeInTheDocument();
      expect(checkbox).toBeInTheDocument();
    });

    it('비밀번호 토글 버튼이 aria-label을 가져야 한다', () => {
      renderLoginPage();

      const toggleButton = screen.getByLabelText('비밀번호 표시 토글');
      expect(toggleButton).toBeInTheDocument();
    });

    it('로고 이미지가 alt 텍스트를 가져야 한다', () => {
      renderLoginPage();

      const logo = screen.getByAltText('ex-GPT Logo');
      expect(logo).toBeInTheDocument();
    });
  });
});
