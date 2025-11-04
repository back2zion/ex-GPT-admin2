import { create } from "zustand";

// 모달 상태 관리. 여닫기, 열린 모달 갯수, z-index 관리
export const useModalStore = create(set => ({
  modals: {
    fontSize: false,
    guide: false,
    notice: false,
    noticeDetail: false,
    survey: false,
    errorSubmit: false,
  },

  modalOrder: [], // 모달 렌더링 순서

  openModal: key =>
    set(state => ({
      modals: { ...state.modals, [key]: true },
      modalOrder: [...state.modalOrder.filter(k => k !== key), key], // 중복 제거 후 push
    })),

  closeModal: key =>
    set(state => ({
      modals: { ...state.modals, [key]: false },
      modalOrder: state.modalOrder.filter(k => k !== key),
    })),

  getOpenModalCount: () => Object.values(useModalStore.getState().modals).filter(Boolean).length,

  getNextZIndex: () => 1000 + useModalStore.getState().modalOrder.length,
}));
