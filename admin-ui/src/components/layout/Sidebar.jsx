/**
 * Sidebar 컴포넌트
 * 8개 메인 메뉴, 23개 서브메뉴
 * 한국도로공사 브랜딩 (#0a2986, #e64701)
 */

import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Sidebar.css';

/**
 * 메뉴 구조 정의
 */
const menuStructure = [
  {
    id: 'login',
    title: '🔐 로그인',
    items: [
      { id: 'login', title: '로그인', path: '/login' }
    ]
  },
  // 통계는 메인 대시보드(/)에서 확인
  // {
  //   id: 'stats',
  //   title: '📊 통계',
  //   items: [
  //     { id: 'stats-exgpt', title: 'ex-GPT 통계', path: '/stats/exgpt' },
  //     { id: 'stats-server', title: '서버현황 통계', path: '/stats/server' }
  //   ]
  // },
  {
    id: 'conversations',
    title: '💬 대화내역 조회',
    items: [
      { id: 'conversation-list', title: '대화내역 목록', path: '/conversations' }
    ]
  },
  {
    id: 'permissions',
    title: '🔑 권한관리',
    items: [
      { id: 'gpt-user-mgmt', title: 'ex-GPT 접근권한 - 사용자관리', path: '/permissions/users' },
      { id: 'gpt-approval-mgmt', title: 'ex-GPT 접근권한 - 접근승인관리', path: '/permissions/approvals' },
      { id: 'doc-permissions', title: '국정자료 권한관리', path: '/permissions/documents' }
    ]
  },
  {
    id: 'learning-data',
    title: '📚 학습데이터관리',
    items: [
      { id: 'doc-mgmt', title: '대상문서 관리', path: '/learning-data/documents' },
      { id: 'dict-mgmt', title: '사전 관리', path: '/learning-data/dictionary' }
    ]
  },
  {
    id: 'services',
    title: '🎯 부가서비스관리',
    items: [
      { id: 'greeting-mgmt', title: '인사말 관리', path: '/services/greetings' },
      { id: 'notices', title: '공지사항', path: '/services/notices' },
      { id: 'error-reports', title: '오류사항신고 관리', path: '/services/error-reports' },
      { id: 'recommended-questions', title: '추천질문 관리', path: '/services/recommended-questions' },
      { id: 'satisfaction', title: '만족도조사 조회', path: '/services/satisfaction' }
    ]
  },
  {
    id: 'deployment',
    title: '🚀 배포관리',
    items: [
      { id: 'model-mgmt', title: '모델 레지스트리', path: '/deployment/models' },
      { id: 'service-mgmt', title: '모델 서비스 관리', path: '/deployment/services' },
      { id: 'system-status', title: '시스템 배포 현황', path: '/deployment/status' }
    ]
  },
  {
    id: 'settings',
    title: '⚙️ 설정',
    items: [
      { id: 'admin-mgmt', title: '관리자관리', path: '/settings/admins' },
      { id: 'user-info', title: '사용자정보 변경', path: '/settings/profile' }
    ]
  }
];

/**
 * MenuSection 컴포넌트
 */
function MenuSection({ section, collapsed, onToggle }) {
  const location = useLocation();

  return (
    <div className={`menu-section ${collapsed ? 'collapsed' : ''}`}>
      <div className="menu-section-title" onClick={onToggle}>
        <span>{section.title}</span>
        <span className="icon">▼</span>
      </div>
      <div className="submenu">
        {section.items.map(item => (
          <Link
            key={item.id}
            to={item.path}
            className={`menu-item ${location.pathname === item.path ? 'active' : ''}`}
          >
            {item.title}
          </Link>
        ))}
      </div>
    </div>
  );
}

/**
 * Sidebar 메인 컴포넌트
 */
export default function Sidebar() {
  // 각 섹션의 collapse 상태 관리
  const [collapsedSections, setCollapsedSections] = useState({});

  /**
   * 섹션 토글 핸들러
   */
  const handleToggle = (sectionId) => {
    setCollapsedSections(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId]
    }));
  };

  return (
    <aside className="sidebar">
      <div className="logo">
        <img src="/admin/images/bg_logo_r.svg" alt="한국도로공사" className="logo-image" />
        <p>한국도로공사 관리도구</p>
      </div>

      {menuStructure.map(section => (
        <MenuSection
          key={section.id}
          section={section}
          collapsed={collapsedSections[section.id]}
          onToggle={() => handleToggle(section.id)}
        />
      ))}
    </aside>
  );
}
