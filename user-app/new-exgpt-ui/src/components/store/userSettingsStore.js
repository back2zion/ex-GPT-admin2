import { create } from "zustand";
import { applyFontSize } from "@utils/fontSize";
import { applyTheme } from "@utils/theme";
import { getUserInfo, saveUserFontSize, saveUserTheme } from "@api/userSettings";

export const useUserSettingsStore = create(set => ({
  initSettings: async () => {
    try {
      const user = sessionStorage.getItem("user");
      const userSetting = await getUserInfo({ usrId: user });
      console.log(userSetting.data);
      const fontSizeIndex = userSetting.data.fntSizeCd === undefined || userSetting.data.fntSizeCd === null  ? 2 : Number(userSetting.data.fntSizeCd);
      const theme = userSetting.data.uiThmCd || "light";
      applyFontSize(fontSizeIndex);
      applyTheme(theme);
      set({ fontSizeIndex, theme });
      localStorage.setItem("exGpt-font-size", fontSizeIndex);
      localStorage.setItem("exGpt-theme", theme);
    } catch {
      const fontSizeIndex = Number(localStorage.getItem("exGpt-font-size")) || 2;
      const theme = localStorage.getItem("exGpt-theme") || "light";
      applyFontSize(fontSizeIndex);
      applyTheme(theme);
      set({ fontSizeIndex, theme });
    }
  },

  updateFontSize: async index => {
    const user = sessionStorage.getItem("user");
    applyFontSize(index);
    localStorage.setItem("exGpt-font-size", index);
    set({ fontSizeIndex: index });
    await saveUserFontSize({ usrId: String(user), fntSizeCd: String(index) });
  },

  updateTheme: async theme => {
    const user = sessionStorage.getItem("user");
    applyTheme(theme);
    localStorage.setItem("exGpt-theme", theme);
    set({ theme });
    await saveUserTheme({ usrId: String(user), uiThmCd: String(theme) });
  },
}));
