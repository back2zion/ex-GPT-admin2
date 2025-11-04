import { useEffect } from "react";
import { useModalStore } from "@store/modalStore";
import FontSizeModal from "./FontSizeModal/FontSizeModal";
import GuideModal from "./GuideModal/GuideModal";
import ErrorSubmitModal from "./ErrorSubmitModal/ErrorSubmitModal";
import NoticeModal from "./NoticeModal/NoticeModal";
import SurveyModal from "./SurveyModal/SurveyModal";
import NoticeDetailModal from "./NoticeModal/NoticeDetailModal";
const modalMap = {
  fontSize: FontSizeModal,
  guide: GuideModal,
  notice: NoticeModal,
  noticeDetail: NoticeDetailModal,
  survey: SurveyModal,
  errorSubmit: ErrorSubmitModal,
};

// 모달 컴포넌트들이 불러지는 순서대로 렌더링 되게끔 수정.(모달 여러개일 때 div 순서때문에 z-index가 높아도 아래로 가는 오류 방지)
const ModalManager = () => {
  const { modals, modalOrder, closeModal } = useModalStore();

  useEffect(() => {
  const handleKeyDown = e => {
    if (e.key !== "Escape") return;
    // modalOrder의 마지막 키를 꺼내서 닫기
    const lastKey = modalOrder[modalOrder.length - 1];
    if (lastKey) closeModal(lastKey);
  };

  document.addEventListener("keydown", handleKeyDown);
  return () => document.removeEventListener("keydown", handleKeyDown);
 }, [modalOrder, closeModal]);

  return (
    <div className="modal-container">
      {modalOrder.map(key => {
        if (!modals[key]) return null;
        const ModalComponent = modalMap[key];
        return <ModalComponent key={key} closeModal={() => closeModal(key)} />;
      })}
    </div>
  );
};

export default ModalManager;
