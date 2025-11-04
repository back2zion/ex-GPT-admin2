/**
 * Chat History API
 *
 * 책임:
 * - 대화 이력 조회
 * - 대화 상세 조회
 * - 대화 삭제
 *
 * 보안:
 * - API 클라이언트를 통한 자동 인증 처리
 * - 401 에러 자동 처리
 */

import apiClient from "./apiClient";

/**
 * 대화 목록 조회 (chat_proxy.py의 /api/chat/sessions 사용)
 * @param {number} page - 페이지 번호 (미사용 - chat_proxy는 전체 반환)
 * @param {number} page_size - 페이지 크기 (미사용)
 * @returns {Promise<{conversations: Array, total: number}>}
 */
export async function getHistoryList(page = 1, page_size = 10) {
  try {
    const user_id = localStorage.getItem('user_id') || 'react_user';

    const data = await apiClient.get(`/api/chat/sessions?user_id=${user_id}`);

    // 401 에러는 apiClient에서 처리되어 빈 응답 반환
    if (data.error === "Unauthorized" || !data.sessions) {
      return { conversations: [], total: 0 };
    }

    // chat_proxy 형식을 history 형식으로 변환
    const conversations = data.sessions.map(session => ({
      cnvs_idt_id: session.session_id,
      cnvs_smry_txt: session.title,
      reg_dt: session.latest_time
    }));

    return { conversations, total: conversations.length };
  } catch (error) {
    console.error("Failed to fetch history list:", error);
    return { conversations: [], total: 0 };
  }
}

/**
 * 대화 상세 조회
 * @param {string} room_id - 대화방 ID
 * @returns {Promise<{messages: Array, total_messages: number}>}
 */
export async function getDetailHistory(room_id) {
  try {
    const data = await apiClient.get(`/api/v1/history/${room_id}`);

    // 401 에러는 apiClient에서 처리되어 빈 응답 반환
    if (data.error === "Unauthorized") {
      return { messages: [], total_messages: 0 };
    }

    return data;
  } catch (error) {
    console.error("Failed to fetch detail history:", error);
    return { messages: [], total_messages: 0 };
  }
}

/**
 * 대화 삭제 (소프트 딜리트)
 * @param {string} session_id - 세션 ID
 * @returns {Promise<boolean>} 성공 여부
 */
export async function deleteHistory(session_id) {
  try {
    await apiClient.del(`/api/chat/sessions/${session_id}`);
    console.log(`✅ 대화 삭제 완료: ${session_id}`);
    return true;
  } catch (error) {
    console.error("Failed to delete history:", error);
    return false;
  }
}
