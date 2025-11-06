/**
 * Header - 상단 헤더 컴포넌트
 * 한국도로공사 Templates 디자인 시스템 적용
 *
 * @description
 * - 높이: 40px 고정
 * - 사용자 정보 표시
 * - 로그아웃 버튼
 * - TDD: Header.test.jsx에서 테스트
 * - 시큐어 코딩:
 *   - XSS 방지: React가 자동으로 escape 처리
 *   - 사용자 정보는 authProvider를 통해 검증된 데이터만 표시
 */

import { useLogout, useGetIdentity } from 'react-admin';
import PropTypes from 'prop-types';
import '@/styles/templates/Header/Header.css';
import '@/styles/templates/Button/Button.css';

/**
 * Header 컴포넌트
 * @returns {JSX.Element}
 */
export default function Header() {
  const logout = useLogout();
  const { data: identity, isLoading } = useGetIdentity();

  /**
   * 로그아웃 핸들러
   * @security
   * - useLogout hook은 authProvider.logout() 호출
   * - 토큰 삭제 및 세션 정리
   */
  const handleLogout = () => {
    logout();
  };

  // 로딩 중일 때 기본 정보 표시
  const userName = identity?.full_name || '관리자';
  const userDept = identity?.department || '시스템관리팀';

  return (
    <header>
      <div className="user">
        <div className="user-info">
          {/* 사용자 아이콘 SVG */}
          <svg width="23" height="23" viewBox="0 0 23 23" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M11.5 22C17.299 22 22 17.299 22 11.5C22 5.70101 17.299 1 11.5 1C5.70101 1 1 5.70101 1 11.5C1 17.299 5.70101 22 11.5 22Z" fill="#BDBDBD" stroke="#E6E6E6" strokeWidth="0.125524" strokeLinecap="round" strokeLinejoin="round"/>
            <mask id="mask0_0_1" style={{maskType:'alpha'}} maskUnits="userSpaceOnUse" x="0" y="0" width="23" height="23">
              <path d="M11.5 22C17.299 22 22 17.299 22 11.5C22 5.70101 17.299 1 11.5 1C5.70101 1 1 5.70101 1 11.5C1 17.299 5.70101 22 11.5 22Z" fill="#0071CE" stroke="#D9D9D9" strokeWidth="0.125524" strokeLinecap="round" strokeLinejoin="round"/>
            </mask>
            <g mask="url(#mask0_0_1)">
              <path d="M11.6805 13.7673C13.8801 13.7673 15.6633 11.9841 15.6633 9.78449C15.6633 7.58488 13.8801 5.80173 11.6805 5.80173C9.4809 5.80173 7.69775 7.58488 7.69775 9.78449C7.69775 11.9841 9.4809 13.7673 11.6805 13.7673Z" fill="white"/>
              <path d="M11.5902 24.3699C16.4394 24.3699 20.3704 25.2186 20.3704 21.3334C20.3704 17.4481 16.4394 15.0345 11.5902 15.0345C6.74107 15.0345 2.81006 17.4481 2.81006 21.3334C2.81006 25.2186 6.74107 24.3699 11.5902 24.3699Z" fill="white"/>
            </g>
          </svg>
          <div>
            {/* XSS 방지: React가 자동으로 escape */}
            {isLoading ? '로딩 중...' : `${userName}/${userDept}`}
          </div>
        </div>
        <button
          className="ds-button logout btn-size-xs secondary"
          onClick={handleLogout}
          type="button"
          aria-label="로그아웃"
        >
          <p className="button-inner">
            <span className="button-label">로그아웃</span>
          </p>
        </button>
      </div>
    </header>
  );
}

Header.propTypes = {};
