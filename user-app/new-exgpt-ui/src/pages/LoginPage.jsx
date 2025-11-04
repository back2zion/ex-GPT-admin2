import { useState } from "react";
import ToastContainer from "@common/Toast/ToastContainer";
import { useToastStore } from "@store/toastStore";
import { loginApi } from "@api/login";

const LoginPage = () => {
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const addToast = useToastStore(state => state.addToast);

  function getInputVal(type) {
    return function (e) {
      const value = e.target.value;
      if (type === "userId") {
        setUserId(value);
      } else if (type === "password") {
        setPassword(value);
      }
    };
  }

  function login() {
    loginApi(userId, password)
      .then(data => {
        // FastAPI는 {access_token: "...", token_type: "bearer"} 형식으로 응답합니다
        if (data.access_token) {
          console.log("로그인 성공:", data);
          // JWT 토큰을 localStorage에 저장
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("token_type", data.token_type);
          sessionStorage.setItem("user", userId);
          // AI 채팅 페이지로 이동
          window.location.href = CONTEXT_PATH + `/ai`;
        } else {
          addToast({ message: "로그인 실패: 아이디 또는 비밀번호를 확인하세요.", type: "fail" });
        }
      })
      .catch(err => {
        console.error("로그인 오류:", err);
        const errorMsg = err.message || "로그인 오류가 발생했습니다. 관리자에게 문의해 주세요";
        addToast({ message: errorMsg, type: "fail" });
      });
  }
  return (
    <div
      style={{
        height: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <form
        style={{
          display: "flex",
          flexDirection: "column",
        }}
        onSubmit={e => {
          e.preventDefault();
          login();
        }}
      >
        <input value={userId} onChange={getInputVal("userId")} />
        <input type="current-password" value={password} onChange={getInputVal("password")} />
        <button type="submit">로그인</button>
      </form>
      <ToastContainer />
    </div>
  );
};
export default LoginPage;
