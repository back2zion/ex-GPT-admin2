/**
 * 로그인 페이지 (Templates 기반)
 * 한국도로공사 공식 디자인 시스템 적용
 */

import { useState, useEffect } from 'react';
import { useLogin, useNotify } from 'react-admin';
import '../styles/templates/Login/Login.css';

export default function LoginPage() {
  const login = useLogin();
  const notify = useNotify();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    rememberMe: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // 컴포넌트 마운트 시 body 클래스 적용 및 "아이디 저장" 불러오기
  useEffect(() => {
    // 로그인 페이지 전용 body 클래스 추가
    document.documentElement.classList.add('login-html');
    document.body.classList.add('login-body');

    // "아이디 저장" 불러오기
    const rememberedUsername = localStorage.getItem('rememberedUsername');
    if (rememberedUsername) {
      setFormData(prev => ({
        ...prev,
        username: rememberedUsername,
        rememberMe: true,
      }));
    }

    // Cleanup: 언마운트 시 클래스 제거
    return () => {
      document.documentElement.classList.remove('login-html');
      document.body.classList.remove('login-body');
    };
  }, []);

  /**
   * 입력 변경 핸들러
   */
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    // 에러 메시지 초기화
    if (errorMessage) {
      setErrorMessage('');
    }
  };

  /**
   * 비밀번호 보기/숨기기 토글
   */
  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  /**
   * 로그인 제출
   */
  const handleSubmit = async (e) => {
    e.preventDefault();

    // 기본 검증
    if (!formData.username || !formData.password) {
      setErrorMessage('아이디와 비밀번호를 입력하세요.');
      return;
    }

    setIsLoading(true);
    setErrorMessage('');

    try {
      // React Admin의 useLogin hook 사용 (authProvider.login 호출)
      await login({
        username: formData.username,
        password: formData.password,
      });

      // "아이디 저장" 처리
      if (formData.rememberMe) {
        localStorage.setItem('rememberedUsername', formData.username);
      } else {
        localStorage.removeItem('rememberedUsername');
      }

      // React Admin이 자동으로 dashboard로 리다이렉트 (hash routing)
    } catch (error) {
      console.error('Login error:', error);
      setErrorMessage('로그인에 실패했습니다. 아이디와 비밀번호를 확인하세요.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="locator">
      <div className="form-pane">
        <div className="form-wrap">
          <div className="form-wrapper">
            <div className="logo">
              <img src="/admin/templates/img/login/ex_gpt_logo.svg" alt="ex-GPT Logo" />
              <p>관리자 대시보드</p>
            </div>

            <form className="signin" onSubmit={handleSubmit}>
              {/* 아이디 입력 */}
              <div className="id_input_container">
                <div className="placeholding-input">
                  <input
                    type="text"
                    id="usrId"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    maxLength="80"
                    placeholder="아이디"
                    disabled={isLoading}
                    autoComplete="username"
                  />
                </div>
                <span className="input_icon" aria-hidden="true"></span>
              </div>

              {/* 비밀번호 입력 */}
              <div className="pswd_input_container">
                <div className="placeholding-input">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    id="pswd"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    maxLength="80"
                    placeholder="비밀번호"
                    disabled={isLoading}
                    autoComplete="current-password"
                  />
                </div>
                <span className="input_icon" aria-hidden="true"></span>
                <button
                  type="button"
                  className={`show_icon ${showPassword ? 'on' : ''}`}
                  onClick={togglePasswordVisibility}
                  disabled={isLoading}
                  aria-label="비밀번호 표시 토글"
                ></button>
              </div>

              {/* 아이디 저장 체크박스 */}
              <div className="remember-id-wrapper">
                <input
                  type="checkbox"
                  id="remember-id"
                  name="rememberMe"
                  checked={formData.rememberMe}
                  onChange={handleChange}
                  disabled={isLoading}
                />
                <label htmlFor="remember-id">
                  <span className="remember-id-text">아이디저장</span>
                </label>
              </div>

              {/* 로그인 버튼 */}
              <div className="login-button-container">
                <button
                  type="submit"
                  className="submit"
                  disabled={isLoading}
                >
                  {isLoading ? '로그인 중...' : 'Login'}
                </button>
              </div>

              {/* 에러 메시지 - form 내부에서 조건부 표시 */}
              {errorMessage && (
                <div className="error-message">{errorMessage}</div>
              )}
            </form>
          </div>
          <div className="desc"></div>
        </div>
      </div>

      {/* 저작권 표시 */}
      <div className="credit-bottom">
        <span>© 2025 Korea Expressway Corporation Service Co., Ltd. All Rights Reserved.</span>
        <div className="bottom-credit"></div>
      </div>
    </div>
  );
}
