/**
 * BreadCrumbs - 최소 기능 버전 (TDD)
 * 현재 경로만 표시하는 간단한 버전
 */

import PropTypes from 'prop-types';
import '@/styles/templates/BreadCrumbs/BreadCrumbs.css';

export default function BreadCrumbs({ pathname }) {
  // 경로를 breadcrumb로 변환하는 간단한 로직
  const paths = pathname.split('/').filter(Boolean);

  const getBreadcrumbLabel = (path) => {
    // 간단한 매핑 (나중에 menuConfig와 연동 가능)
    const labels = {
      'vector-data': '벡터 데이터 관리',
      'dictionary': '사전 관리',
      'users': '사용자 목록',
      'conversations': '대화 이력',
      'stats': '통계',
      'deployment': '시스템 관리',
    };
    return labels[path] || path;
  };

  return (
    <div className="breadcrumbs" style={{ padding: '16px 24px', background: '#f9f9f9' }}>
      <span>홈</span>
      {paths.map((path, index) => (
        <span key={index}>
          {' > '}
          <span>{getBreadcrumbLabel(path)}</span>
        </span>
      ))}
    </div>
  );
}

BreadCrumbs.propTypes = {
  pathname: PropTypes.string.isRequired,
};
