import { create } from "zustand";

export const useToastStore = create(set => ({
  toasts: [],

  addToast: toast => {
    const id = Date.now() + Math.random();
    set(state => ({
      toasts: [...state.toasts, { ...toast, id }],
    }));
  },

  removeToast: id => {
    set(state => ({
      toasts: state.toasts.filter(t => t.id !== id),
    }));
  },

  clearToasts: () => {
    set({ toasts: [] });
  },
}));
