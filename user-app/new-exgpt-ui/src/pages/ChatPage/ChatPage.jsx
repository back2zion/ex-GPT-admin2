import { useState, useEffect, useRef } from "react";
import { useMessageStore } from "@store/messageStore";
import { useToastStore } from "@store/toastStore";
import { useRoomId } from "@store/roomIdStore";
import { sendChatWithSSE } from "@api/chat_updated";
import { generateConversationTitle } from "@api/title";

// 기존 Content에서 사용하던 컴포넌트
import Intro from "@content/Intro/Intro";
import Suggests from "@content/Suggests/Suggests";
import MessageArea from "@content/Messages/MessageArea";
import Form from "@content/Form/Form";

import "./chatPage.scss";

const ChatPage = ({ mode }) => {
  const textareaRef = useRef(null);
  const [hasText, setHasText] = useState(false);
  const [textareaValue, setTextareaValue] = useState("");
  const roomId = useRoomId(state => state.roomId);
  const titleGeneratedRef = useRef(false); // 제목 생성 여부 (ref로 즉시 업데이트)

  // document.title 설정
  useEffect(() => {
    document.title = "한국도로공사 ex-GPT";
  }, []);

  const addUserMessage = useMessageStore(state => state.addUserMessage);
  const addAssistantMessage = useMessageStore(state => state.addAssistantMessage);

  const messages = useMessageStore(state => state.messages);
  const lastMessageRef = useRef(null);

  const addToast = useToastStore(state => state.addToast);

  // 새 대화 시작 시 제목 생성 플래그 초기화
  useEffect(() => {
    if (messages.length === 0) {
      titleGeneratedRef.current = false;
    }
  }, [messages.length]);

  const handleInput = e => {
    const value = e.target.value;  // trim() 제거 - 입력 중에는 공백 허용
    const textarea = textareaRef.current;
    setTextareaValue(value);

    // 자동 높이 조절
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${textarea.scrollHeight}px`;
    }

    // 텍스트 여부 상태 업데이트 (trim된 값으로 체크)
    setHasText(value.trim().length > 0);

    // 패딩 조절
    if (textarea) {
      textarea.style.paddingLeft = value.trim().length > 0 ? "0.4em" : "2.2em";
    }
  };

  const handleSuggestClick = text => {
    setTextareaValue(text.trim());
    setHasText(text.trim().length > 0);

    // textarea 높이 및 패딩 조절
    if (textareaRef.current) {
      textareaRef.current.value = text.trim();
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
      textareaRef.current.style.paddingLeft = text.trim() ? "0.4em" : "2.2em";
    }
  };

  const handleSubmit = async () => {
    if (!textareaValue.trim()) return;

    const userText = textareaValue.trim();

    if (userText.length > 2000) {
      addToast({ message: "메시지는 최대 2000자까지 입력할 수 있습니다.", type: "fail" });
      return;
    }
    if (userText.length < 2) {
      addToast({ message: "메시지는 최소 2자 이상 입력해야 합니다.", type: "fail" });
      return;
    }

    addUserMessage(userText);
    setTextareaValue("");
    setHasText(false);

    if (textareaRef.current) {
      textareaRef.current.value = "";
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.paddingLeft = "2.2em";
    }

    // 질의 메시지를 화면 상단에 위치시키기 (즉시 스크롤)
    setTimeout(() => {
      const userMessages = document.querySelectorAll('.message--user');
      const lastUserMessage = userMessages[userMessages.length - 1];
      if (lastUserMessage) {
        lastUserMessage.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }, 0);

    // Session ID 생성 (새 대화 시작)
    let currentSessionId = roomId;
    if (!currentSessionId || messages.length === 0) {
      // 새 대화 시작 또는 첫 메시지인 경우 항상 새 session_id 생성
      const userId = localStorage.getItem('user_id') || 'react_user';
      // userId가 이미 timestamp를 포함하는 경우 정리
      const cleanUserId = userId.includes('_') ? userId.split('_')[0] : userId;
      currentSessionId = `${cleanUserId}_${Date.now()}`;
      useRoomId.getState().setCurrentRoomId(currentSessionId);
      console.log('🆕 New session created:', currentSessionId);
    }

    // 임시 응답 메시지 추가 (스트리밍으로 업데이트됨)
    addAssistantMessage({
      think: "",
      response: "",
      sources: [],
      metadata: {}
    });

    // tempMessageIndex는 addAssistantMessage 호출 후에 계산
    const tempMessageIndex = messages.length + 1;  // +1: user 메시지 추가 후이므로

    // 서버에 메시지 전송 (SSE 스트리밍)
    try {
      let fullResponse = "";
      let fullThinkText = "";
      let isInThinkMode = false;
      let receivedSources = [];
      let receivedMetadata = {};

      // 대화 이력 생성 (multiturn 지원)
      const chatHistory = messages.map(msg => {
        if (msg.role === "user") {
          return { role: "user", content: msg.content };
        } else if (msg.role === "assistant") {
          // assistant는 response만 전달
          const response = typeof msg.content === 'string'
            ? msg.content
            : (msg.content?.response || "");
          return { role: "assistant", content: response };
        }
        return null;
      }).filter(Boolean);

      // 디버깅: 전송할 데이터 확인
      console.log('📤 Chat Request:', {
        message: userText,
        session_id: currentSessionId,
        history_length: chatHistory.length,
        history: chatHistory
      });

      await sendChatWithSSE(
        [], // files
        userText, // message
        currentSessionId, // session_id
        {
          onToken: (token) => {
            // think 모드 감지
            if (token.includes("<think>")) {
              isInThinkMode = true;
              token = token.replace("<think>", "");
            }
            if (token.includes("</think>")) {
              isInThinkMode = false;
              token = token.replace("</think>", "");
            }

            // 토큰을 받을 때마다 응답 업데이트
            if (isInThinkMode) {
              fullThinkText += token;
            } else {
              fullResponse += token;
            }

            const updateMessage = useMessageStore.getState().updateMessage;
            updateMessage(tempMessageIndex, {
              think: fullThinkText,
              response: fullResponse,
              sources: receivedSources,  // 기존 sources 유지
              metadata: receivedMetadata  // 기존 metadata 유지
            });
          },
          onMetadata: (metadata) => {
            // 메타데이터 업데이트 (sources 포함)
            console.log("Metadata received:", metadata);

            if (metadata.sources) {
              receivedSources = metadata.sources;
            }

            receivedMetadata = { ...receivedMetadata, ...metadata };

            const updateMessage = useMessageStore.getState().updateMessage;
            const currentMessages = useMessageStore.getState().messages;
            const currentContent = currentMessages[tempMessageIndex]?.content || {};
            updateMessage(tempMessageIndex, {
              ...currentContent,
              sources: receivedSources,
              metadata: receivedMetadata
            });
          },
          onComplete: async () => {
            // 완료 시 스크롤 이동
            setTimeout(() => {
              if (lastMessageRef.current) {
                lastMessageRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
              }
            }, 0);

            // 대화 주제 자동 생성 (layout.html 로직)
            // - 2턴 (2개 메시지): 총 길이 50자 이상
            // - 4턴 (4개 메시지): 무조건 생성
            const currentMessages = useMessageStore.getState().messages;
            if (!titleGeneratedRef.current && currentMessages.length >= 2) {
              // 전체 대화 내용의 총 길이 계산 (layout.html 방식)
              const totalLength = currentMessages.reduce((sum, msg) => {
                const content = msg.role === 'user'
                  ? msg.content
                  : (typeof msg.content === 'string' ? msg.content : msg.content?.response || '');
                return sum + content.length;
              }, 0);

              const shouldGenerate =
                (currentMessages.length === 2 && totalLength > 50) ||
                currentMessages.length === 4;

              if (shouldGenerate) {
                titleGeneratedRef.current = true; // ref는 즉시 업데이트되어 중복 방지
                console.log(`✅ ${currentMessages.length}턴 제목 생성 시작 (총 길이: ${totalLength}자)`);

                // 제목 생성을 비동기로 실행 (UI 블로킹 방지)
                setTimeout(async () => {
                  try {
                    // 간단한 형식으로 변환: { role, content }
                    const simpleMessages = currentMessages.map(msg => ({
                      role: msg.role,
                      content: msg.role === 'user'
                        ? msg.content
                        : (typeof msg.content === 'string' ? msg.content : msg.content?.response || '')
                    }));

                    await generateConversationTitle(simpleMessages, currentSessionId);
                  } catch (err) {
                    console.error('제목 생성 실패:', err);
                  }
                }, 1000);
              }
            }
          },
          onError: (err) => {
            console.error("채팅 응답 실패:", err);
            addToast({ message: "채팅 응답 중 오류가 발생했습니다.", type: "fail" });
          }
        },
        chatHistory  // 대화 이력 전달 (multiturn 지원)
      );
    } catch (err) {
      console.error("채팅 전송 실패:", err);
      addToast({ message: "메시지 전송에 실패했습니다.", type: "fail" });
    }
  };

  return (
    <div className="content content--layout">
      <div className="top--scrollable">
        <Intro />
        <Suggests onSuggestClick={handleSuggestClick} />
        <div className="content__messages_wrapper">
          <div className="content__inner">
            {messages.map((msg, idx) => (
              <MessageArea
                key={idx}
                message={msg}
                ref={idx === messages.length - 1 ? lastMessageRef : null}
              />
            ))}
          </div>
        </div>
      </div>
      <Form
        hasText={hasText}
        textareaRef={textareaRef}
        handleInput={handleInput}
        handleSubmit={handleSubmit}
        textareaValue={textareaValue}
      />
    </div>
  );
};

export default ChatPage;
