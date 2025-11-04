/**
 * 로그인 페이지
 * react-admin 통합 버전
 */

import { useState } from 'react';
import { useLogin, useNotify } from 'react-admin';
import { isValidUserId, escapeHtml } from '../utils/security';
import './LoginPage.css';

/**
 * 로그인 페이지 컴포넌트
 */
export default function LoginPage() {
  const login = useLogin();
  const notify = useNotify();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    rememberMe: false,
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);

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

    // 폼 검증
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      // authProvider.login 호출
      await login({
        username: formData.username,
        password: formData.password,
      });

      // "아이디 기억하기" 처리
      if (formData.rememberMe) {
        localStorage.setItem('rememberedUsername', formData.username);
      } else {
        localStorage.removeItem('rememberedUsername');
      }

      // react-admin이 자동으로 리다이렉트
    } catch (error) {
      console.error('Login error:', error);
      notify(
        error?.message || '로그인에 실패했습니다. 아이디와 비밀번호를 확인하세요.',
        { type: 'error' }
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
      <div className="login-card card">
        <div className="login-header">
          <h1>ex-GPT</h1>
          <p>한국도로공사 관리도구</p>
        </div>

        <form onSubmit={handleSubmit}>
          <h2>관리자 로그인</h2>

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

          {/* 보안 안내 */}
          <div className="security-notice">
            <p>로그인 5회 실패 시 계정이 일시적으로 차단됩니다.</p>
            <p>계정 관련 문의는 시스템 담당자에게 연락해주세요.</p>
          </div>
        </form>

        {/* 저작권 */}
        <div className="copyright">
          © 2025 DataStreams Co., Ltd. All Rights Reserved.
        </div>
      </div>
    </div>
  );
}
