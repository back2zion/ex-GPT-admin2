export const getUserInfo = async ({ usrId }) => {
  const res = await fetch(`${CONTEXT_PATH}/api/auth/user/${encodeURIComponent(usrId)}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Failed to fetch settings");
  return await res.json();
};

export const saveUserFontSize = async ({ usrId, fntSizeCd }) => {
  const res = await fetch(`${CONTEXT_PATH}/api/user/setUserInfo`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      userId: usrId,
      fntSizeCd: fntSizeCd,
    }),
  });
  if (!res.ok) throw new Error("Failed to save font settings");
  return await res.json();
};

export const saveUserTheme = async ({ usrId, uiThmCd }) => {
  console.log(usrId, uiThmCd);
  const res = await fetch(`${CONTEXT_PATH}/api/user/setUserInfo`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      userId: usrId,
      uiThmCd: uiThmCd,
    }),
  });
  if (!res.ok) throw new Error("Failed to save theme settings");
  return await res.json();
};
