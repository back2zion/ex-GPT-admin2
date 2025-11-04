/**
 * 대화 주제 자동 생성 API
 * layout.html의 generateSessionTitle 로직을 React에 구현
 */

const CHAT_API = '/api/chat_stream'; // Spring Boot proxy endpoint

/**
 * 대화 내용을 기반으로 제목 생성
 * @param {Array} messages - 대화 이력 [{ role, content }]
 * @param {string} sessionId - 현재 세션 ID
 * @returns {Promise<string>} 생성된 제목
 */
export async function generateConversationTitle(messages, sessionId) {
  try {
    // 최근 4개 메시지만 사용
    const recentMessages = messages.slice(0, 4).map(msg =>
      `${msg.role === 'user' ? '사용자' : 'AI'}: ${msg.content.substring(0, 200)}`
    ).join('\n');

    const titlePrompt = `아래 대화의 내용을 가장 잘 요약하는 5단어 이내의 간결한 제목을 한국어로 만들어줘. 제목만 출력하고 다른 말은 하지 마.

대화 내용:
${recentMessages}

제목:`;

    const response = await fetch(CHAT_API, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'z3JE1M8huXmNux6y'
      },
      body: JSON.stringify({
        message: titlePrompt,
        user_id: localStorage.getItem('user_id') || 'react_user',
        session_id: `title_gen_${Date.now()}`, // 제목 생성용 임시 세션
        think_mode: false,
        temperature: 0.3
      })
    });

    if (!response.ok) {
      throw new Error('Title generation failed');
    }

    // SSE 스트리밍 응답 파싱
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let titleText = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const eventData = line.slice(6);
          if (eventData === '[DONE]') break;

          try {
            const data = JSON.parse(eventData);
            if (data.type === 'token' && data.content) {
              titleText += data.content;
            }
          } catch (e) {
            // 파싱 실패는 무시
          }
        }
      }
    }

    // <think> 태그 제거 및 정리
    let cleanTitle = titleText.trim();
    cleanTitle = cleanTitle.replace(/<think>[\s\S]*?<\/think>/g, '').trim();
    cleanTitle = cleanTitle.replace(/^["']|["']$/g, '');
    const generatedTitle = cleanTitle.substring(0, 50);

    console.log('✅ 제목 생성 완료:', generatedTitle);

    // localStorage에 저장
    if (generatedTitle && generatedTitle.length > 0) {
      const storageKey = `session_title_${sessionId}`;
      localStorage.setItem(storageKey, generatedTitle);

      // DB에도 저장 시도 (chat_proxy.py의 PATCH /api/chat/sessions/{session_id}/title)
      try {
        await fetch(`/api/chat/sessions/${sessionId}/title`, {
          method: 'PATCH',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            session_id: sessionId,
            title: generatedTitle
          })
        });
        console.log('✅ 제목 DB 저장 완료');

        // 즉시 사이드바 업데이트 (layout.html 방식)
        console.log('🔄 사이드바 즉시 업데이트 시도');
        window.dispatchEvent(new CustomEvent('refreshChatHistory'));
      } catch (dbErr) {
        console.warn('⚠️ 제목 DB 저장 실패 (localStorage에는 저장됨):', dbErr);
      }
    }

    return generatedTitle;
  } catch (error) {
    console.error('❌ 제목 생성 실패:', error);
    return '';
  }
}
