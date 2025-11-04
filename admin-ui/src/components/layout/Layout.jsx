/**
 * Layout 컴포넌트
 * Sidebar + Main Content 구조
 */

import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import './Layout.css';

/**
 * 메인 레이아웃 컴포넌트
 * @returns {JSX.Element}
 */
export default function Layout() {
  return (
    <div className="layout-container">
      <Sidebar />
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
