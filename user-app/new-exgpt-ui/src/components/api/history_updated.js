/**
 * History API Client - FastAPI 통합 버전
 *
 * Features:
 * - 대화 목록 조회 (페이지네이션)
 * - 대화 상세 히스토리 조회
 * - 자동 인증 (Session cookie)
 *
 * Security:
 * - HTTP Session 기반 인증
 * - 본인 데이터만 조회 가능
 * - SQL Injection 방지 (백엔드 처리)
 */

const API_BASE = '/api/v1';

/**
 * 대화 목록 조회 (페이지네이션)
 *
 * @param {number} page - 페이지 번호 (1부터 시작)
 * @param {number} page_size - 페이지당 항목 수 (기본 10)
 *
 * @returns {Promise<Object>} 대화 목록 응답
 *   - items: Array<{cnvs_idt_id, cnvs_smry_txt, reg_dt, mod_dt}>
 *   - total: number (전체 대화 수)
 *   - page: number (현재 페이지)
 *   - page_size: number
 *   - total_pages: number
 *
 * @example
 * const result = await getHistoryList(1, 10);
 * console.log(result.items); // 대화 목록
 * console.log(result.total); // 전체 개수
 */
export const getHistoryList = async (page = 1, page_size = 10) => {
  try {
    const response = await fetch(`${API_BASE}/history/list`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include', // Session cookie
      body: JSON.stringify({
        page: page,
        page_size: page_size
      })
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('인증이 필요합니다');
      }
      const errorData = await response.json();
      throw new Error(errorData.detail || '대화 목록 조회 실패');
    }

    return await response.json();
  } catch (err) {
    console.error('Get history list error:', err);
    throw err;
  }
};


/**
 * 대화 상세 히스토리 조회
 *
 * @param {string} room_id - 대화방 ID (CNVS_IDT_ID)
 *
 * @returns {Promise<Object>} 대화 상세 응답
 *   - cnvs_idt_id: string
 *   - cnvs_smry_txt: string (대화 요약)
 *   - messages: Array<{cnvs_id, ques_txt, ans_txt, reg_dt, ...}>
 *   - total_messages: number
 *
 * @example
 * const detail = await getDetailHistory('user123_20251022104412345678');
 * console.log(detail.messages); // 질문/답변 목록
 */
export const getDetailHistory = async (room_id) => {
  try {
    const response = await fetch(`${API_BASE}/history/${room_id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include' // Session cookie
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('인증이 필요합니다');
      }
      if (response.status === 403) {
        throw new Error('접근 권한이 없습니다');
      }
      if (response.status === 404) {
        throw new Error('대화를 찾을 수 없습니다');
      }
      const errorData = await response.json();
      throw new Error(errorData.detail || '히스토리 조회 실패');
    }

    return await response.json();
  } catch (err) {
    console.error('Get detail history error:', err);
    throw err;
  }
};


/**
 * 대화방 이름 수정
 *
 * @param {string} room_id - 대화방 ID
 * @param {string} new_name - 새로운 이름
 *
 * @returns {Promise<Object>} 수정 결과
 *
 * @example
 * await updateRoomName('user123_20251022104412345678', '새 대화방 이름');
 */
export const updateRoomName = async (room_id, new_name) => {
  try {
    const response = await fetch(`${API_BASE}/rooms/${room_id}/name`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({
        cnvs_smry_txt: new_name
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || '이름 수정 실패');
    }

    return await response.json();
  } catch (err) {
    console.error('Update room name error:', err);
    throw err;
  }
};


/**
 * 대화방 삭제 (Soft Delete)
 *
 * @param {string} room_id - 대화방 ID
 *
 * @returns {Promise<Object>} 삭제 결과
 *
 * @example
 * await deleteRoom('user123_20251022104412345678');
 */
export const deleteRoom = async (room_id) => {
  try {
    const response = await fetch(`${API_BASE}/rooms/${room_id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include'
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || '대화 삭제 실패');
    }

    return await response.json();
  } catch (err) {
    console.error('Delete room error:', err);
    throw err;
  }
};
