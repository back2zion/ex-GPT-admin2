/**
 * 메뉴 구조 설정
 * 한국도로공사 ex-GPT 관리자 대시보드
 *
 * @description
 * - 계층적 메뉴 구조 정의
 * - icon: Templates/img/menu/ 의 아이콘 ID와 매핑
 * - root: true인 메뉴는 최상위 메뉴
 * - children: 하위 메뉴 배열
 *
 * @security
 * - 권한 체크는 authProvider와 React Admin의 권한 시스템 사용
 * - 메뉴는 UI 레벨 제어, 실제 API 접근은 백엔드에서 검증
 */

export const menuConfig = [
  {
    id: 'dashboard',
    label: '대시보드',
    icon: 'dashboard',
    path: '/',
    root: true,
  },
  {
    id: 'data',
    label: '데이터 관리',
    icon: 'data',
    root: true,
    children: [
      {
        id: 'vector',
        label: '벡터 데이터 관리',
        path: '/vector-data',
      },
      {
        id: 'dictionary',
        label: '사전 관리',
        path: '/dictionary',
      },
      {
        id: 'questions',
        label: '추천 질문 관리',
        path: '/recommended-questions',
      },
      {
        id: 'error-reports',
        label: '오류 리포트',
        path: '/error-reports',
      },
    ],
  },
  {
    id: 'users',
    label: '사용자 관리',
    icon: 'users',
    root: true,
    children: [
      {
        id: 'user-list',
        label: '사용자 목록',
        path: '/users',
      },
      {
        id: 'conversations',
        label: '대화 이력',
        path: '/conversations',
      },
    ],
  },
  {
    id: 'stats',
    label: '통계 및 모니터링',
    icon: 'stats',
    root: true,
    children: [
      {
        id: 'stats-dashboard',
        label: '통계 대시보드',
        path: '/stats/dashboard',
      },
      {
        id: 'exgpt-stats',
        label: 'ex-GPT 통계',
        path: '/stats/exgpt',
      },
      {
        id: 'server-stats',
        label: '서버 통계',
        path: '/stats/server',
      },
    ],
  },
  {
    id: 'system',
    label: '시스템 관리',
    icon: 'system',
    root: true,
    children: [
      {
        id: 'model',
        label: '모델 관리',
        path: '/deployment/model',
      },
      {
        id: 'service',
        label: '서비스 관리',
        path: '/deployment/service',
      },
      {
        id: 'system-status',
        label: '시스템 상태',
        path: '/deployment/status',
      },
      {
        id: 'version',
        label: '버전 관리',
        path: '/version',
      },
      {
        id: 'notifications',
        label: '알림 관리',
        path: '/notifications',
      },
    ],
  },
];
