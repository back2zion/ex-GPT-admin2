/**
 * Chat API Client - FastAPI 통합 버전
 *
 * Features:
 * - SSE (Server-Sent Events) 스트리밍
 * - Room ID 자동 생성 처리
 * - Token-by-token 응답 처리
 * - 에러 핸들링
 *
 * Security:
 * - HTTP Session 기반 인증 (withCredentials)
 * - CSRF 토큰 자동 추가
 * - XSS 방지
 */

// FastAPI chat_proxy 엔드포인트 → /v1/chat/ 프록시 (RAG 검색 + usage_history 저장)
const CHAT_API = '/api/chat_stream';

/**
 * SSE 스트리밍으로 채팅 메시지 전송
 *
 * @param {Array} files - 파일 ID 배열
 * @param {string} message - 사용자 메시지
 * @param {string} cnvs_idt_id - 세션 ID (클라이언트에서 생성)
 * @param {Object} callbacks - 콜백 함수들
 * @param {Function} callbacks.onToken - 토큰 수신 시 호출 (token)
 * @param {Function} callbacks.onMetadata - 메타데이터 수신 시 호출 (metadata)
 * @param {Function} callbacks.onComplete - 완료 시 호출 ()
 * @param {Function} callbacks.onError - 에러 발생 시 호출 (error)
 *
 * @returns {Function} abort 함수 (스트리밍 중단용)
 *
 * @example
 * const sessionId = `react_user_${Date.now()}`;
 * const abort = await sendChatWithSSE(
 *   [],
 *   "안녕하세요",
 *   sessionId,
 *   {
 *     onToken: (token) => appendMessage(token),
 *     onComplete: () => setLoading(false),
 *     onError: (err) => showError(err)
 *   }
 * );
 */
export const sendChatWithSSE = async (
  files,
  message,
  cnvs_idt_id = null,
  callbacks = {},
  history = []  // 대화 이력 파라미터 추가
) => {
  const {
    onToken = () => {},
    onMetadata = () => {},
    onComplete = () => {},
    onError = () => {}
  } = callbacks;

  try {
    // Request payload (Spring Boot /v1/chat/ 형식 - aichat.html과 동일)
    const payload = {
      message: message,
      session_id: cnvs_idt_id || "",  // 빈 스트링 = 새 대화
      user_id: localStorage.getItem('user_id') || 'react_user',
      think_mode: true,  // 추론 모드 활성화
      file_ids: files || [],  // 파일 ID 배열
      history: history,  // 대화 이력 [{ role, content }]
      temperature: 0.0
    };

    // Fetch with SSE streaming
    const response = await fetch(CHAT_API, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-API-Key': 'z3JE1M8huXmNux6y'  // Spring Boot API Key
      },
      credentials: 'include', // Session cookie
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || '채팅 전송 실패');
    }

    // Read SSE stream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    const readStream = async () => {
      try {
        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            onComplete();
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (!line.trim() || line.startsWith(':')) continue;

            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim();

              // [DONE] 신호
              if (data === '[DONE]') {
                onComplete();
                break;
              }

              try {
                const parsed = JSON.parse(data);

                // Spring Boot /v1/chat/ 응답 형식 (aichat.html과 동일)
                // 1. token 이벤트
                if (parsed.type === 'token' && parsed.content) {
                  onToken(parsed.content);
                }
                // 2. final 이벤트 (sources, metadata 포함)
                else if (parsed.type === 'final' && parsed.content) {
                  if (parsed.content.sources) {
                    onMetadata({ sources: parsed.content.sources });
                  }
                  if (parsed.content.metadata) {
                    onMetadata(parsed.content.metadata);
                  }
                }
                // 3. sources 이벤트
                else if (parsed.type === 'sources' && parsed.sources) {
                  onMetadata({ sources: parsed.sources });
                }
                // 4. metadata 이벤트
                else if (parsed.type === 'end' && parsed.metadata) {
                  onMetadata(parsed.metadata);
                }
                // 5. error 이벤트
                else if (parsed.type === 'error') {
                  onError(new Error(parsed.content || 'Stream error'));
                }
              } catch (parseErr) {
                console.warn('SSE parse error:', parseErr, data);
              }
            }
          }
        }
      } catch (streamErr) {
        console.error('Stream read error:', streamErr);
        onError(streamErr);
      }
    };

    readStream();

    // Return abort function
    return () => {
      reader.cancel();
    };

  } catch (err) {
    console.error('Send chat error:', err);
    onError(err);
    throw err;
  }
};


/**
 * 일반 JSON 응답으로 채팅 메시지 전송 (폴백용)
 *
 * @param {Array} files - 파일 ID 배열
 * @param {string} message - 사용자 메시지
 * @param {string} cnvs_idt_id - 대화 ID
 *
 * @returns {Promise<Object>} 채팅 응답
 */
export const sendChatJSON = async (files, message, cnvs_idt_id = null) => {
  try {
    const payload = {
      message: message,
      session_id: cnvs_idt_id || "",
      user_id: "react_user",
      think_mode: true,
      file_ids: files || [],
      history: [],
      temperature: 0.0
    };

    const response = await fetch(CHAT_API, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || '채팅 전송 실패');
    }

    return await response.json();
  } catch (err) {
    console.error('Send chat JSON error:', err);
    throw err;
  }
};
