/**
 * 메뉴 구조 설정
 * 한국도로공사 ex-GPT 관리자 대시보드
 *
 * @description
 * - 계층적 메뉴 구조 정의 (기존 CoreUIMenu.jsx 구조 기반)
 * - root: true인 메뉴는 최상위 메뉴
 * - children: 하위 메뉴 배열
 *
 * @security
 * - 권한 체크는 authProvider와 React Admin의 권한 시스템 사용
 * - 메뉴는 UI 레벨 제어, 실제 API 접근은 백엔드에서 검증
 */

export const menuConfig = [
  // 1. 대시보드
  {
    id: 'dashboard',
    label: '대시보드',
    path: '/',
    root: true,
  },

  // 2. 대화내역
  {
    id: 'conversations',
    label: '대화내역',
    path: '/conversations',
    root: true,
  },

  // 3. 학습데이터 관리 (확장)
  {
    id: 'learning-data',
    label: '학습데이터 관리',
    root: true,
    children: [
      {
        id: 'vector-documents',
        label: '대상 문서관리',
        path: '/vector-data/documents',
      },
      {
        id: 'dictionaries',
        label: '사전관리',
        path: '/dictionaries',
      },
    ],
  },

  // 4. 권한 관리 (확장)
  {
    id: 'permissions',
    label: '권한 관리',
    root: true,
    children: [
      {
        id: 'users',
        label: '사용자 관리',
        path: '/users',
      },
      {
        id: 'document-permissions',
        label: '문서 권한',
        path: '/document-permissions',
      },
      {
        id: 'approval-lines',
        label: '결재라인',
        path: '/approval-lines',
      },
    ],
  },

  // 5. 부가서비스 관리 (확장)
  {
    id: 'services',
    label: '부가서비스 관리',
    root: true,
    children: [
      {
        id: 'version',
        label: '버전관리',
        path: '/services/version',
      },
      {
        id: 'notices',
        label: '공지사항',
        path: '/notices',
      },
      {
        id: 'error-reports',
        label: '오류신고관리',
        path: '/error_reports',
      },
      {
        id: 'recommended-questions',
        label: '추천질문관리',
        path: '/recommended_questions',
      },
      {
        id: 'satisfaction',
        label: '만족도조사',
        path: '/satisfaction',
      },
    ],
  },

  // 6. 배포관리 (확장)
  {
    id: 'deployment',
    label: '배포관리',
    root: true,
    children: [
      {
        id: 'deployment-models',
        label: '모델 레지스트리',
        path: '/deployment/models',
      },
      {
        id: 'deployment-services',
        label: '모델 서비스 관리',
        path: '/deployment/services',
      },
      {
        id: 'deployment-status',
        label: '시스템 배포 현황',
        path: '/deployment/status',
      },
    ],
  },

  // 7. STT 음성 전사
  {
    id: 'stt',
    label: 'STT 음성 전사',
    path: '/stt-batches',
    root: true,
  },
];
