const fontSizes = [14, 16, 18, 20, 22];
export const applyFontSize = index => {
  const px = fontSizes[index] || 18;
  document.documentElement.style.setProperty("--ds-font-size-base", `${px}px`);
};
