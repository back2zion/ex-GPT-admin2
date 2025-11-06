/**
 * 로그인 페이지 (templates 디자인 적용)
 * /templates/html/login/login.html 구조 적용
 * react-admin 통합 버전
 *
 * 리팩토링: 인라인 스타일 사용으로 CSS 충돌 방지
 * - React Admin과 완전 독립적
 * - 유지보수 용이성: 모든 스타일이 한 파일에
 * - 디버깅 용이: 스타일 우선순위 명확
 */

import { useState, useEffect } from 'react';
import { useLogin, useNotify } from 'react-admin';
import { isValidUserId } from '../utils/security';

/**
 * 로그인 페이지 전용 스타일 정의
 * CSS 충돌 방지를 위해 인라인 스타일 사용
 */
const styles = {
  // 최상위 래퍼: 전체 화면 고정
  pageWrapper: {
    position: 'fixed',
    top: 0,
    left: 0,
    width: '100vw',
    height: '100vh',
    margin: 0,
    padding: 0,
    backgroundColor: '#0F3353',
    zIndex: 9999,
    overflow: 'hidden',
  },
  // 센터링 컨테이너: flexbox 센터링
  centerContainer: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    width: '100%',
    height: '100%',
    gap: '20px',
  },
  // 폼 영역
  formPane: {
    padding: '0 60px',
    display: 'flex',
    alignItems: 'center',
  },
  // 폼 래퍼
  formWrap: {
    display: 'inline-flex',
    justifyContent: 'center',
    margin: '0 auto',
    alignItems: 'center',
  },
  // 폼 내부
  formWrapper: {
    display: 'flex',
    boxSizing: 'border-box',
    flexDirection: 'column',
    background: '#ffffff',
    borderRadius: '23px 0 0 23px',
    padding: '46px 40px 67px',
    minWidth: '392px',
    flexShrink: 0,
  },
  // 로고 영역
  logo: {
    display: 'flex',
    alignItems: 'end',
    gap: '7px',
    color: '#5E5C5C',
    fontWeight: '300',
    fontSize: '15px',
    marginBottom: '51px',
  },
  logoText: {
    margin: 0,
  },
  // 입력 필드 공통
  inputContainer: {
    position: 'relative',
    marginBottom: '31px',
  },
  inputContainerPassword: {
    position: 'relative',
  },
  input: {
    border: 'none',
    outline: 'none',
    boxShadow: 'none',
    backgroundColor: 'transparent',
    borderBottom: '1px solid #E0E0E0',
    fontSize: '14px',
    boxSizing: 'border-box',
    borderRadius: 0,
    color: '#222222',
    position: 'relative',
    lineHeight: '32px',
    height: '32px',
    caretColor: '#006DCD',
    width: '100%',
    paddingLeft: '32px',
    paddingRight: '32px',
  },
  inputIcon: {
    position: 'absolute',
    top: '50%',
    left: 0,
    transform: 'translateY(-50%)',
    width: '21px',
    height: '21px',
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundRepeat: 'no-repeat',
  },
  showIcon: {
    border: 'none',
    position: 'absolute',
    top: '50%',
    right: 0,
    transform: 'translateY(-50%)',
    width: '24px',
    height: '24px',
    background: 'transparent',
    cursor: 'pointer',
    padding: 0,
  },
  // 체크박스
  rememberWrapper: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    marginTop: '12px',
    position: 'relative',
  },
  checkbox: {
    margin: 0,
    appearance: 'none',
    width: '21px',
    height: '21px',
    border: '1px solid #D3D3D3',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  checkboxLabel: {
    fontSize: '13px',
    color: '#222222',
    fontWeight: '400',
    cursor: 'pointer',
  },
  // 에러 메시지
  errorMessage: {
    marginTop: '10px',
    fontSize: '14px',
    color: 'red',
    fontWeight: '500',
    overflowWrap: 'break-word',
    marginBottom: '8px',
  },
  // 로그인 버튼
  loginButtonContainer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: '30px',
  },
  loginButton: {
    minWidth: '239px',
    height: '44px',
    lineHeight: '44px',
    border: 'none',
    borderRadius: '44px',
    backgroundColor: '#0044A2',
    boxShadow: '0px 6.9px 6.04px 0px #3939391C',
    color: 'white',
    fontWeight: '700',
    fontSize: '14px',
    cursor: 'pointer',
    transition: '0.1s',
  },
  loginButtonHover: {
    backgroundColor: '#1461CD',
  },
  // 우측 배경
  desc: {
    background: 'url(/admin/img/login/login_bg.svg) center / cover no-repeat',
    width: '219px',
    borderRadius: '0 23px 23px 0',
    paddingTop: '37px',
    flexShrink: 0,
    alignSelf: 'normal',
  },
  // 하단 크레딧
  creditBottom: {
    marginTop: 0,
    color: '#A4B3C7AB',
    fontSize: '14px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  creditSpan: {
    position: 'relative',
    paddingLeft: '12px',
  },
  bottomCredit: {
    background: 'url(/admin/img/login/ex_gpt_bottom_logo.svg) center / cover no-repeat',
    width: '128px',
    height: '15px',
    order: -1,
    marginRight: '12px',
  },
};

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
  const [showPassword, setShowPassword] = useState(false);

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

  return (
    <div style={styles.pageWrapper}>
      <div style={styles.centerContainer}>
        <div style={styles.formPane}>
          <div style={styles.formWrap}>
            <div style={styles.formWrapper}>
              <div style={styles.logo}>
                <img src="/admin/img/login/ex_gpt_logo.svg" alt="ex-GPT Logo" />
                <p style={styles.logoText}>관리자 대시보드</p>
              </div>
            <form onSubmit={handleSubmit}>
              <div style={styles.inputContainer}>
                <input
                  type="text"
                  id="usrId"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  placeholder="아이디"
                  disabled={isLoading}
                  autoComplete="off"
                  maxLength="80"
                  style={styles.input}
                />
                <span
                  style={{
                    ...styles.inputIcon,
                    backgroundImage: 'url(/admin/img/login/id_icon.svg)',
                  }}
                  aria-hidden="true"
                ></span>
              </div>

              <div style={styles.inputContainerPassword}>
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="pswd"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="비밀번호"
                  disabled={isLoading}
                  autoComplete="off"
                  maxLength="80"
                  style={styles.input}
                />
                <span
                  style={{
                    ...styles.inputIcon,
                    backgroundImage: 'url(/admin/img/login/pswd_icon.svg)',
                  }}
                  aria-hidden="true"
                ></span>
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? '비밀번호 숨기기' : '비밀번호 보기'}
                  style={styles.showIcon}
                >
                  <img
                    src={showPassword ? '/admin/img/login/eye_off_icon.svg' : '/admin/img/login/eye_icon.svg'}
                    alt=""
                    style={{ width: '24px', height: '24px' }}
                  />
                </button>
              </div>

              <div style={styles.rememberWrapper}>
                <input
                  type="checkbox"
                  id="remember-id"
                  name="rememberMe"
                  checked={formData.rememberMe}
                  onChange={handleChange}
                  style={styles.checkbox}
                />
                <label htmlFor="remember-id" style={styles.checkboxLabel}>
                  아이디저장
                </label>
              </div>

              {/* 에러 메시지 */}
              {(errors.username || errors.password) && (
                <div style={styles.errorMessage}>
                  {errors.username || errors.password}
                </div>
              )}

              <div style={styles.loginButtonContainer}>
                <button
                  type="submit"
                  disabled={isLoading}
                  style={styles.loginButton}
                  onMouseEnter={(e) => e.target.style.backgroundColor = styles.loginButtonHover.backgroundColor}
                  onMouseLeave={(e) => e.target.style.backgroundColor = styles.loginButton.backgroundColor}
                >
                  {isLoading ? '로그인 중...' : '로그인'}
                </button>
              </div>
            </form>
            </div>
            <div style={styles.desc}></div>
          </div>
        </div>
        <div style={styles.creditBottom}>
          <span style={styles.creditSpan}>Korea Expressway Corporation Service Co., Ltd. All Rights Reserved.</span>
          <div style={styles.bottomCredit}></div>
        </div>
      </div>
    </div>
  );
}
