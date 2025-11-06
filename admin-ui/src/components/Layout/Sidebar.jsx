/**
 * Sidebar - 최소 기능 버전 (TDD)
 * 일단 기본 구조만 구현하고 작동 확인 후 고도화
 */

import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import PropTypes from 'prop-types';
import { menuConfig } from '@/config/menuConfig';
import '@/styles/templates/Menu/Menu.css';

export default function Sidebar({ collapsed, onToggle }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [openMenus, setOpenMenus] = useState({});

  const handleMenuClick = (item) => {
    if (item.children) {
      setOpenMenus(prev => ({
        ...prev,
        [item.id]: !prev[item.id],
      }));
    } else if (item.path) {
      navigate(item.path);
    }
  };

  return (
    <aside style={{
      width: collapsed ? '60px' : '250px',
      transition: 'width 0.3s',
      height: '100%',
      overflowY: 'auto',
      flexShrink: 0,
    }}>
      {/* 로고 */}
      <h1 className="logo-area">
        <a href="/" className="logo">
          <span className="sr-only">한국도로공사 ex-GPT</span>
        </a>
      </h1>

      {/* 메뉴 영역 */}
      <div className="menu-area">
        <div className="menu-header">
          {!collapsed && <div className="menu-header-title">관리자 대시보드</div>}
          <button
            className="menu-header-toggle"
            onClick={onToggle}
            type="button"
            aria-label="메뉴 접기/펼치기"
          />
        </div>

        {/* 메뉴 리스트 */}
        <div className="menus">
          {menuConfig.map(item => (
            <div
              key={item.id}
              className={`menu ${item.root ? 'root' : ''} ${item.children ? 'hasChildren' : ''} ${openMenus[item.id] ? 'open' : ''}`}
              id={item.id}
            >
              <div className="menu-content" onClick={() => handleMenuClick(item)}>
                <div className="menu-icon" />
                {!collapsed && <div className="menu-text">{item.label}</div>}
                {item.children && !collapsed && (
                  <div className="menu-arrow">
                    <svg width="5" height="7" viewBox="0 0 5 7" fill="none">
                      <path fillRule="evenodd" clipRule="evenodd" d="M4.80476 3.94161L1.74103 6.81678C1.48072 7.06107 1.06021 7.06107 0.799889 6.81678C0.539572 6.57248 0.539572 6.17785 0.799889 5.93356L3.38971 3.49687L0.799889 1.06644C0.539572 0.822148 0.539572 0.427517 0.799889 0.183222C1.06021 -0.0610736 1.48072 -0.0610736 1.74103 0.183222L4.80476 3.05839C5.06508 3.29642 5.06508 3.69732 4.80476 3.94161Z" fill="#7192D5"/>
                    </svg>
                  </div>
                )}
              </div>

              {/* 하위 메뉴 - 항상 렌더링, CSS로 높이 제어 */}
              {item.children && (
                <div className="menu-children">
                  {item.children.map(child => (
                    <div
                      key={child.id}
                      className="menu"
                      onClick={() => handleMenuClick(child)}
                    >
                      <div className="menu-content">
                        <div className="menu-icon" />
                        <div className="menu-text">{child.label}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}

Sidebar.propTypes = {
  collapsed: PropTypes.bool.isRequired,
  onToggle: PropTypes.func.isRequired,
};
