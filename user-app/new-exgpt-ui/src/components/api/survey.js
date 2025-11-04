//만족도조사
export const setSurvey = async (usrId, ractTxt, ractLevelVal) => {
  const res = await fetch(`${CONTEXT_PATH}/api/survey/setSurvey`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      usrId: usrId,
      ractTxt: ractTxt,
      ractLevelVal: ractLevelVal,
    }),
  });

  if (!res.ok) throw new Error("Failed to fetch Notice List");
  return await res.json();
};
