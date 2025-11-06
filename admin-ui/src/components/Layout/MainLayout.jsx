/**
 * MainLayout - 메인 레이아웃 컴포넌트
 * 한국도로공사 Templates 디자인 시스템 적용
 *
 * @description
 * - Header + Sidebar + Content 구조
 * - 모든 관리자 페이지에 공통 적용 (로그인 제외)
 * - TDD: MainLayout.test.jsx에서 테스트
 * - 시큐어 코딩: 권한 체크는 authProvider에서 처리
 */

import { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import PropTypes from 'prop-types';
import Header from './Header';
import Sidebar from './Sidebar';
import BreadCrumbs from './BreadCrumbs';

// Templates CSS import
import '@/styles/templates/Header/Header.css';
import '@/styles/templates/Menu/Menu.css';
import '@/styles/templates/PageLayout/PageLayout.css';
import '@/styles/templates/BreadCrumbs/BreadCrumbs.css';

/**
 * MainLayout 컴포넌트
 * @param {Object} props
 * @param {React.ReactNode} props.children - 자식 컴포넌트 (Outlet 사용 시 불필요)
 * @returns {JSX.Element}
 */
export default function MainLayout({ children }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const location = useLocation();

  /**
   * 사이드바 토글 핸들러
   * @security 클라이언트 사이드 상태이므로 보안 이슈 없음
   */
  const handleSidebarToggle = () => {
    setSidebarCollapsed(prev => !prev);
  };

  return (
    <div className="main-layout">
      {/* Header: 사용자 정보, 로그아웃 */}
      <Header />

      {/* Main Container: Sidebar + Content */}
      <main style={{ display: 'flex', height: 'calc(100vh - 40px)' }}>
        {/* Sidebar: 메뉴 네비게이션 */}
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggle={handleSidebarToggle}
        />

        {/* Content Area */}
        <div
          className="content-area"
          style={{
            flex: 1,
            marginLeft: sidebarCollapsed ? '60px' : '0',
            transition: 'margin-left 0.3s ease',
            overflowY: 'auto',
            height: 'calc(100vh - 40px)', // 헤더 높이 제외
          }}
        >
          {/* BreadCrumbs: 현재 경로 */}
          <BreadCrumbs pathname={location.pathname} />

          {/* Page Content */}
          <div className="page-content" style={{ padding: '20px' }}>
            {children || <Outlet />}
          </div>
        </div>
      </main>
    </div>
  );
}

MainLayout.propTypes = {
  children: PropTypes.node,
};

MainLayout.defaultProps = {
  children: null,
};
