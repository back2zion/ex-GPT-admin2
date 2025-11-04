import { create } from "zustand";
import { useToastStore } from "@store/toastStore";
import { useFileStore } from "@store/fileStore";
import { useRoomId } from "@store/roomIdStore";

export const useMessageStore = create(set => ({
  messages: [], // { role: "user" | "assistant", content: string, raw?: object }

  addUserMessage: msg => {
    set(state => ({
      messages: [...state.messages, { role: "user", content: msg }],
    }));
  },

  addAssistantMessage: chatData => {
    // chatData를 content 구조로 저장
    let content;
    if (typeof chatData === 'object' && chatData !== null) {
      // 이미 올바른 구조인 경우
      if (chatData.response !== undefined || chatData.think !== undefined || chatData.sources !== undefined) {
        content = chatData;
      } else if (chatData?.response?.data?.content) {
        // 기존 API 응답 구조
        content = chatData.response.data.content;
      } else {
        // 기본 구조
        content = {
          think: "",
          response: "",
          sources: [],
          metadata: {}
        };
      }
    } else {
      // 기본 구조
      content = {
        think: "",
        response: "",
        sources: [],
        metadata: {}
      };
    }

    set(state => ({
      messages: [
        ...state.messages,
        {
          role: "assistant",
          content: content,
          raw: chatData, // 원본 전체 저장
        },
      ],
    }));
  },

  updateMessage: (index, newContent) =>
    set(state => {
      const newMessages = [...state.messages];
      if (newMessages[index]) {
        newMessages[index] = {
          ...newMessages[index],
          content: newContent
        };
      }
      return { messages: newMessages };
    }),

  clearMessages: () => {
    const addToast = useToastStore.getState().addToast;
    const resetFiles = useFileStore.getState().resetFiles;
    const resetRoomId = useRoomId.getState().clearRoomId;
    addToast({ message: "새 대화를 시작합니다.", type: "success" });
    set({ messages: [] });
    resetFiles();
    resetRoomId();
  },
}));
