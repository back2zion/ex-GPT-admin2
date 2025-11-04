import { useEffect } from "react";
import { Routes, Route } from "react-router-dom";

// header
import { Header } from "@layout/Header/Header";
import { Aside } from "@layout/Aside/Aside";

// content
import ToastContainer from "@common/Toast/ToastContainer";
import ModalManager from "@modals/ModalManager";
import ChatPage from "@pages/ChatPage/ChatPage";
import LoginPage from "@pages/LoginPage";
import NotFoundPage from "@pages/NotFoundPage";

// store
import { useAuthStore } from "@store/authStore";

function App() {
  // 앱 시작 시 인증 상태 및 user_id 초기화
  useEffect(() => {
    // user_id 초기화 (없으면 생성)
    if (!localStorage.getItem('user_id')) {
      const userId = `user_${Date.now()}`;
      localStorage.setItem('user_id', userId);
      console.log('✅ user_id 초기화:', userId);
    }

    // 인증 상태 초기화
    useAuthStore.getState().initialize();
  }, []);
  // 페이지 렌더링 공통 구조
  const renderPage = mode => (
    <>
      <Header mode={mode} />
      <div className="app-container">
        <Aside mode={mode} />
        <ChatPage mode={mode} />
      </div>
      <ToastContainer />
      <ModalManager />
    </>
  );

  return (
    <>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/ai" element={renderPage("default")} />
        <Route path="/govAi" element={renderPage("gov")} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </>
  );
}

export default App;
