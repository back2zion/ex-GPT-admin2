const CONTEXT_PATH = '/exGenBotDS';

export const suggestionList = async () => {
  const res = await fetch(`${CONTEXT_PATH}/api/menu/recommended-questions/1`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("추천질문 목록 가져오기 실패");
  return await res.json();
};
