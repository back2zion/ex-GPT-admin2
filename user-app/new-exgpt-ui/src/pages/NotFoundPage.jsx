import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

function NotFoundPage() {
  const navigate = useNavigate();

  useEffect(() => {
    setTimeout(() => {
      navigate("/login");
    }, 3000); // 3초 후 홈으로 이동
  }, [navigate]);

  return (
    <div style={{ textAlign: "center", marginTop: "100px" }}>
      <h1>존재하지 않는 페이지</h1>
      <p>페이지를 찾을 수 없습니다. 초기 화면으로 이동합니다.</p>
    </div>
  );
}

export default NotFoundPage;
