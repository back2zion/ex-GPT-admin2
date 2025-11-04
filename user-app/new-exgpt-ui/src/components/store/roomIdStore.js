import { create } from "zustand";

export const useRoomId = create(set => ({
  roomId: '',

  setCurrentRoomId: id => {
    set({ roomId: id });
  },

  clearRoomId: () => {
    set({ roomId: '' });
  }
}));
