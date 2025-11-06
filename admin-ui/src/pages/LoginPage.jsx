/**
 * 로그인 페이지
 * TDD + 시큐어 코딩
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../utils/api';
import { isValidUserId, escapeHtml } from '../utils/security';
import './LoginPage.css';

/**
 * 로그인 페이지 컴포넌트
 */
export default function LoginPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    rememberMe: false,
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

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
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  /**
   * 폼 검증 (TDD - 시큐어 코딩)
   */
  const validateForm = () => {
    const newErrors = {};

    // 사용자 ID 검증
    if (!formData.username) {
      newErrors.username = '아이디를 입력하세요.';
    } else if (!isValidUserId(formData.username)) {
      newErrors.username = '아이디 형식이 올바르지 않습니다. (영문, 숫자, -, _ 만 허용)';
    }

    // 비밀번호 검증
    if (!formData.password) {
      newErrors.password = '비밀번호를 입력하세요.';
    } else if (formData.password.length < 4) {
      newErrors.password = '비밀번호는 최소 4자 이상이어야 합니다.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * 로그인 제출 핸들러
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    // 폼 검증
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      // API 호출
      const response = await login(formData.username, formData.password);

      // 토큰 저장 (FastAPI는 access_token 필드로 반환)
      if (response.access_token) {
        localStorage.setItem('authToken', response.access_token);

        // "아이디 기억하기" 처리
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
      setErrorMessage(
        error.response?.data?.detail || '로그인에 실패했습니다. 아이디와 비밀번호를 확인하세요.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  // 컴포넌트 마운트 시 "아이디 기억하기" 불러오기
  useState(() => {
    const rememberedUsername = localStorage.getItem('rememberedUsername');
    if (rememberedUsername) {
      setFormData(prev => ({
        ...prev,
        username: rememberedUsername,
        rememberMe: true,
      }));
    }
  }, []);

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-card card">
          <div className="login-header">
            <div className="logo-container">
              <div className="logo-icon">🛣️</div>
              <h1>한국도로공사</h1>
            </div>
            <h2>ex-GPT 관리자 시스템</h2>
          </div>

          <form onSubmit={handleSubmit}>
            {errorMessage && (
              <div className="alert alert-danger" role="alert">
                {escapeHtml(errorMessage)}
              </div>
            )}

            <div className="form-group">
              <label htmlFor="username">아이디</label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleChange}
                placeholder="아이디를 입력하세요"
                disabled={isLoading}
                aria-invalid={errors.username ? 'true' : 'false'}
                aria-describedby={errors.username ? 'username-error' : null}
              />
              {errors.username && (
                <span id="username-error" className="error-text" role="alert">
                  {errors.username}
                </span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="password">비밀번호</label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="비밀번호를 입력하세요"
                disabled={isLoading}
                aria-invalid={errors.password ? 'true' : 'false'}
                aria-describedby={errors.password ? 'password-error' : null}
              />
              {errors.password && (
                <span id="password-error" className="error-text" role="alert">
                  {errors.password}
                </span>
              )}
            </div>

            <div className="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  name="rememberMe"
                  checked={formData.rememberMe}
                  onChange={handleChange}
                  disabled={isLoading}
                />
                <span>아이디 기억하기</span>
              </label>
            </div>

            <button
              type="submit"
              className="btn-primary btn-login"
              disabled={isLoading}
            >
              {isLoading ? '로그인 중...' : '로그인'}
            </button>

            <div className="login-notice">
              <p className="notice-text">
                ⚠️ 로그인 5회 실패시 계정이 일시적으로 차단됩니다.<br />
                계정 관련 문의는 시스템 담당자에게 연락해주세요.
              </p>
            </div>
          </form>
        </div>

        <div className="login-footer">
          <p>© 2025 DataStreams. Co.Ltd. All Rights Reserved.</p>
        </div>
      </div>
    </div>
  );
}
