/**
 * App 컴포넌트 - react-admin 기반 + CoreUI 스타일
 * 한국도로공사 ex-GPT 관리자 도구
 */

import { Admin, Resource, CustomRoutes } from 'react-admin';
import { Route } from 'react-router-dom';
import { createContext, useState, useEffect } from 'react';
import dataProvider from './dataProvider';
import { lightTheme, darkTheme } from './theme';
import i18nProvider from './i18nProvider';

// Theme Context
export const ThemeContext = createContext();
import { ConversationList, ConversationShow } from './resources/conversations';
import { NoticeList, NoticeShow, NoticeEdit, NoticeCreate } from './resources/notices';
import { SatisfactionList, SatisfactionShow } from './resources/satisfaction';
import { DocumentPermissionList, DocumentPermissionShow, DocumentPermissionEdit, DocumentPermissionCreate } from './resources/document_permissions';
import { ApprovalLineList, ApprovalLineShow, ApprovalLineEdit, ApprovalLineCreate } from './resources/approval_lines';
import { UserList, UserShow, UserEdit, UserCreate } from './resources/users';
import { STTBatchList, STTBatchShow, STTBatchCreate } from './resources/stt_batches';
import { ErrorReportList, ErrorReportShow } from './resources/error_reports';
import { RecommendedQuestionList, RecommendedQuestionShow, RecommendedQuestionEdit, RecommendedQuestionCreate } from './resources/recommended_questions';

// MLOps 리소스
import { TrainingDatasetList, TrainingDatasetShow, TrainingDatasetCreate } from './resources/training_datasets_simple';
import { FinetuningJobList, FinetuningJobShow, FinetuningJobCreate } from './resources/finetuning_jobs_simple';
import { ModelRegistryList, ModelRegistryShow } from './resources/model_registry_simple';

// CoreUI 스타일 레이아웃
import CoreUILayout from './layout/CoreUILayout';

// 기존 페이지들 (react-admin 외부)
import LoginPage from './pages/LoginPage';
import ExGPTStatsPage from './pages/ExGPTStatsPage';
import ServerStatsPage from './pages/ServerStatsPage';
import StatsDashboard from './pages/StatsDashboard';
import VectorDataManagementPage from './pages/VectorDataManagementPage';
import DictionaryManagementPage from './pages/DictionaryManagementPage';
import VersionManagementPage from './pages/VersionManagementPage';
import ErrorReportManagementPage from './pages/ErrorReportManagementPage';
import RecommendedQuestionsPage from './pages/RecommendedQuestionsPage';

// 새로운 대화내역 페이지
import ConversationsPage from './pages/ConversationsPage';
import ConversationDetailPage from './pages/ConversationDetailPage';

// 새로운 사용자 관리 페이지
import UsersPage from './pages/UsersPage';

// 사전 관리 페이지
import DictionaryDetailPage from './pages/DictionaryDetailPage';

// TDD 기반 통계 대시보드 (메인 페이지)
import Dashboard from './pages/Dashboard';

// 배포관리 페이지
import ModelManagement from './pages/Deployment/ModelManagement';
import ServiceManagement from './pages/Deployment/ServiceManagement';
import SystemStatus from './pages/Deployment/SystemStatus';

/**
 * Placeholder 페이지 컴포넌트
 */
function PlaceholderPage({ title }) {
  return (
    <div className="card" style={{ padding: '20px', margin: '20px' }}>
      <h2>{title}</h2>
      <p>구현 예정입니다.</p>
    </div>
  );
}

/**
 * App 컴포넌트
 */
export default function App() {
  // 다크 모드 상태 (localStorage에서 가져오기)
  const [darkMode, setDarkMode] = useState(() => {
    const savedMode = localStorage.getItem('darkMode');
    return savedMode === 'true';
  });

  // 다크 모드 토글
  const toggleDarkMode = () => {
    setDarkMode(prev => {
      const newMode = !prev;
      localStorage.setItem('darkMode', newMode);
      return newMode;
    });
  };

  // 초기 로딩 시 lastLogin 설정
  useEffect(() => {
    if (!localStorage.getItem('lastLogin')) {
      localStorage.setItem('lastLogin', new Date().toISOString());
    }
  }, []);

  return (
    <ThemeContext.Provider value={{ darkMode, toggleDarkMode }}>
      <Admin
        dataProvider={dataProvider}
        theme={darkMode ? darkTheme : lightTheme}
        i18nProvider={i18nProvider}
        title="ex-GPT 관리도구"
        loginPage={LoginPage}
        requireAuth={false} // 인증 미구현 시 false
        dashboard={Dashboard} // TDD 기반 통계 대시보드 (메인 페이지)
        layout={CoreUILayout} // CoreUI 스타일 레이아웃
      >
      {/* react-admin Resources */}
      {/* 대화내역, 학습데이터는 CustomRoutes로 처리 */}

      {/* 부가서비스 관리 */}
      <Resource
        name="notices"
        list={NoticeList}
        show={NoticeShow}
        edit={NoticeEdit}
        create={NoticeCreate}
        options={{ label: '📢 공지사항' }}
      />

      <Resource
        name="error_reports"
        list={ErrorReportList}
        show={ErrorReportShow}
        options={{ label: '⚠️ 오류사항신고' }}
      />

      <Resource
        name="recommended_questions"
        list={RecommendedQuestionList}
        show={RecommendedQuestionShow}
        edit={RecommendedQuestionEdit}
        create={RecommendedQuestionCreate}
        options={{ label: '❓ 추천질문' }}
      />

      <Resource
        name="satisfaction"
        list={SatisfactionList}
        show={SatisfactionShow}
        options={{ label: '⭐ 만족도 조사' }}
      />

      {/* 권한 관리 리소스 (PRD P0) */}
      <Resource
        name="document-permissions"
        list={DocumentPermissionList}
        show={DocumentPermissionShow}
        edit={DocumentPermissionEdit}
        create={DocumentPermissionCreate}
        options={{ label: '🔐 문서 권한 관리' }}
      />

      <Resource
        name="approval-lines"
        list={ApprovalLineList}
        show={ApprovalLineShow}
        edit={ApprovalLineEdit}
        create={ApprovalLineCreate}
        options={{ label: '📋 결재라인 관리' }}
      />

      {/* 사용자 관리는 CustomRoutes로 처리 */}

      {/* STT 음성 전사 시스템 */}
      <Resource
        name="stt-batches"
        list={STTBatchList}
        show={STTBatchShow}
        create={STTBatchCreate}
        options={{ label: '🎙️ STT 음성 전사' }}
      />

      {/* ========================================
          MLOps - Fine-tuning 시스템
          ======================================== */}

      {/* 학습 데이터셋 관리 */}
      <Resource
        name="training_datasets"
        list={TrainingDatasetList}
        show={TrainingDatasetShow}
        create={TrainingDatasetCreate}
        options={{ label: '📊 학습 데이터셋' }}
      />

      {/* Fine-tuning 작업 */}
      <Resource
        name="finetuning_jobs"
        list={FinetuningJobList}
        show={FinetuningJobShow}
        create={FinetuningJobCreate}
        options={{ label: '🔧 Fine-tuning 작업' }}
      />

      {/* 모델 레지스트리 */}
      <Resource
        name="model_registry"
        list={ModelRegistryList}
        show={ModelRegistryShow}
        options={{ label: '📦 모델 레지스트리' }}
      />

      {/* 향후 추가할 리소스들 */}
      {/* <Resource name="documents" options={{ label: '📄 문서 관리' }} /> */}

      {/* 기존 Custom Routes (react-admin 외부 페이지) */}
      <CustomRoutes>
        {/* 대화내역 (완전 개편) */}
        <Route path="/conversations" element={<ConversationsPage />} />
        <Route path="/conversations/:id" element={<ConversationDetailPage />} />

        {/* 사용자 관리 (완전 개편) */}
        <Route path="/users" element={<UsersPage />} />

        {/* 사용 안 함: MUI 의존성 문제로 제거 */}
        {/* <Route path="/dashboard" element={<StatsDashboard />} /> */}
        {/* <Route path="/stats/exgpt" element={<ExGPTStatsPage />} /> */}
        {/* <Route path="/stats/server" element={<ServerStatsPage />} /> */}

        {/* 학습데이터 관리 */}
        <Route path="/vector-data/documents" element={<VectorDataManagementPage />} />
        <Route path="/vector-data/dictionaries" element={<DictionaryManagementPage />} />
        <Route path="/vector-data/dictionaries/:dictId" element={<DictionaryDetailPage />} />
        <Route path="/dictionaries" element={<DictionaryManagementPage />} />
        <Route path="/dictionaries/:dictId" element={<DictionaryDetailPage />} />

        {/* 부가서비스 관리 */}
        <Route path="/services/version" element={<VersionManagementPage />} />
        <Route path="/services/error-reports" element={<ErrorReportManagementPage />} />
        <Route path="/services/recommended-questions" element={<RecommendedQuestionsPage />} />

        {/* Placeholder 페이지들 */}
        <Route path="/permissions/users" element={<PlaceholderPage title="🔑 ex-GPT 접근권한 - 사용자관리" />} />
        <Route path="/permissions/approvals" element={<PlaceholderPage title="✅ ex-GPT 접근권한 - 접근승인관리" />} />
        <Route path="/permissions/documents" element={<PlaceholderPage title="📄 국정자료 권한관리" />} />

        <Route path="/learning-data/documents" element={<PlaceholderPage title="📚 대상문서 관리" />} />
        <Route path="/learning-data/dictionary" element={<PlaceholderPage title="📖 사전 관리" />} />

        <Route path="/services/greetings" element={<PlaceholderPage title="👋 인사말 관리" />} />
        <Route path="/services/notices" element={<PlaceholderPage title="📢 공지사항" />} />
        <Route path="/services/error-reports" element={<PlaceholderPage title="⚠️ 오류사항신고 관리" />} />
        <Route path="/services/recommended-questions" element={<PlaceholderPage title="❓ 추천질문 관리" />} />
        <Route path="/services/satisfaction" element={<PlaceholderPage title="⭐ 만족도조사 조회" />} />

        <Route path="/deployment/models" element={<ModelManagement />} />
        <Route path="/deployment/services" element={<ServiceManagement />} />
        <Route path="/deployment/status" element={<SystemStatus />} />

        <Route path="/settings/admins" element={<PlaceholderPage title="👥 관리자관리" />} />
        <Route path="/settings/profile" element={<PlaceholderPage title="👤 사용자정보 변경" />} />
      </CustomRoutes>
    </Admin>
    </ThemeContext.Provider>
  );
}
