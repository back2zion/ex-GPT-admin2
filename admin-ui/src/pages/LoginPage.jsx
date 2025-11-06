/**
 * 로그인 페이지 (Templates 기반)
 * 한국도로공사 공식 디자인 시스템 적용
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../utils/api';
import '../styles/templates/Login/Login.css';

export default function LoginPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    rememberMe: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // 컴포넌트 마운트 시 "아이디 저장" 불러오기
  useEffect(() => {
    const rememberedUsername = localStorage.getItem('rememberedUsername');
    if (rememberedUsername) {
      setFormData(prev => ({
        ...prev,
        username: rememberedUsername,
        rememberMe: true,
      }));
    }
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
      // API 호출
      const response = await login(formData.username, formData.password);

      // 토큰 저장
      if (response.access_token) {
        localStorage.setItem('authToken', response.access_token);

        // "아이디 저장" 처리
        if (formData.rememberMe) {
          localStorage.setItem('rememberedUsername', formData.username);
        } else {
          localStorage.removeItem('rememberedUsername');
        }

        // Dashboard로 이동
        navigate('/');
      }
    } catch (error) {
      console.error('Login error:', error);
      const detail = error.response?.data?.detail;

      // 계정 잠금 메시지 처리
      if (detail && detail.includes('잠겼습니다')) {
        setErrorMessage(detail);
      } else {
        setErrorMessage('로그인에 실패했습니다. 아이디와 비밀번호를 확인하세요.');
      }
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
              <img src="/templates/img/login/ex_gpt_logo.svg" alt="ex-GPT Logo" />
              <p>관리자 대시보드</p>
            </div>

            <form className="signin" onSubmit={handleSubmit}>
              {/* 에러 메시지 */}
              {errorMessage && (
                <div className="error-message">{errorMessage}</div>
              )}

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
                  className="remember-id"
                  id="remember-id"
                  name="rememberMe"
                  checked={formData.rememberMe}
                  onChange={handleChange}
                  disabled={isLoading}
                />
                <label className="remember-id" htmlFor="remember-id">
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
            </form>

            {/* 하단 메시지 (보안 안내) */}
            <div className="bottom-message">
              <p style={{ fontSize: '13px', color: '#666', marginTop: '20px', lineHeight: '1.6' }}>
                ⚠️ 로그인 5회 실패시 계정이 일시적으로 차단됩니다.<br />
                계정 관련 문의는 시스템 담당자에게 연락해주세요.
              </p>
            </div>
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
