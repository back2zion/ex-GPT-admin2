import { create } from "zustand";

export const useFileStore = create(set => ({
  attachedFiles: [],

  addFiles: files =>
    set(state => ({
      attachedFiles: [...state.attachedFiles, ...files],
    })),

  removeFile: file =>
    set(state => ({
      attachedFiles: file === null ? [] : state.attachedFiles.filter(f => f !== file),
    })),

  resetFiles: () => set({ attachedFiles: [] }),
}));
