export function loginApi(userId, password) {
  // FastAPI 로그인 엔드포인트는 application/x-www-form-urlencoded 형식을 사용합니다
  const formData = new URLSearchParams();
  formData.append('username', userId);
  formData.append('password', password);

  return fetch(`${CONTEXT_PATH}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    credentials: "include",
    body: formData.toString(),
  }).then(async res => {
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: '로그인 실패' }));
      throw new Error(error.detail || '로그인 실패');
    }
    return res.json();
  });
}
