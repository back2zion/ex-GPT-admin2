/**
 * Chat History Component
 *
 * 책임:
 * - 대화 이력 표시
 * - 대화 선택 및 로드
 *
 * 동작:
 * - 로그인 상태에서만 히스토리 로드
 * - 401 에러는 자동으로 처리됨 (apiClient)
 */

import { useState, useEffect } from "react";
import { Virtuoso } from "react-virtuoso";

import { useRoomId } from "@store/roomIdStore";
import { useMessageStore } from "@store/messageStore";
import { useAuthStore } from "@store/authStore";

import { getHistoryList, deleteHistory } from "@api/history";

const ChatHistory = () => {
  const roomId = useRoomId(state => state.roomId);
  const setCurrentRoomId = useRoomId(state => state.setCurrentRoomId);
  const clearMessages = useMessageStore(state => state.clearMessages);

  const isAuthenticated = useAuthStore(state => state.isAuthenticated);

  const [chatHistoryList, setChatHistoryList] = useState([]);

  useEffect(() => {
    // 히스토리 로드 함수
    const loadHistory = async () => {
      const userId = localStorage.getItem('user_id');
      if (!userId) {
        console.log('⚠️ user_id 없음, 히스토리 로드 건너뜀');
        setChatHistoryList([]);
        return;
      }

      console.log('🔄 loadHistory 호출됨');
      const data = await getHistoryList(1, 50);
      setChatHistoryList(data.conversations || []);
    };

    // 초기 로드
    loadHistory();

    // 제목 생성 시 히스토리 갱신을 위한 polling (5초마다)
    const intervalId = setInterval(() => {
      loadHistory();
    }, 5000);

    // 커스텀 이벤트 리스너: 제목 생성 직후 즉시 갱신 (layout.html 방식)
    const handleRefresh = () => {
      console.log('🔄 refreshChatHistory 이벤트 받음 - 즉시 갱신');
      loadHistory();
    };
    window.addEventListener('refreshChatHistory', handleRefresh);

    return () => {
      clearInterval(intervalId);
      window.removeEventListener('refreshChatHistory', handleRefresh);
    };
  }, []); // 한 번만 실행, 이벤트 리스너는 항상 등록

  // 대화 삭제 핸들러
  const handleDelete = async (e, sessionId) => {
    e.stopPropagation(); // 클릭 이벤트 전파 중지

    if (!confirm('이 대화를 삭제하시겠습니까?')) {
      return;
    }

    const success = await deleteHistory(sessionId);
    if (success) {
      // 삭제 후 목록 새로고침
      const userId = localStorage.getItem('user_id');
      if (userId) {
        const data = await getHistoryList(1, 50);
        setChatHistoryList(data.conversations || []);
      }

      // 현재 선택된 대화가 삭제된 경우 초기화
      if (sessionId === roomId) {
        clearMessages();
        setCurrentRoomId("");
      }
    }
  };

  function renderHistoryDom() {
    if (chatHistoryList.length === 0) {
      return (
        <div className="history-item" style={{ cursor: "default" }}>
          대화내역이 없습니다
        </div>
      );
    }

    return (
      <Virtuoso
        increaseViewportBy={30}
        totalCount={chatHistoryList.length}
        itemContent={(index) => {
          const item = chatHistoryList[index];
          const isActive = item.cnvs_idt_id === roomId;

          return (
            <div
              className={`history-item ${isActive ? "active" : ""}`}
              key={item.cnvs_idt_id}
              onClick={() => {
                clearMessages();
                setCurrentRoomId(item.cnvs_idt_id);
              }}
            >
              <span className="history-title">{item.cnvs_smry_txt || item.cnvs_idt_id}</span>
              <button
                className="delete-button"
                onClick={(e) => handleDelete(e, item.cnvs_idt_id)}
                title="삭제"
              >
                🗑️
              </button>
            </div>
          );
        }}
      />
    );
  }

  return (
    <div className="history-list">
      <div className="history-title">이전 대화</div>
      {renderHistoryDom()}
    </div>
  );
};

export default ChatHistory;
