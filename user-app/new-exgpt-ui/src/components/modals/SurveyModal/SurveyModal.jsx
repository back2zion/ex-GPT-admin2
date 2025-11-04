import { useState } from "react";
import Modal from "../../common/Modal/Modal";
import Button from "../../common/Button/Button";

import { useToastStore } from "@store/toastStore";
import { setSurvey } from "@api/survey";
import { SurveyStarIcon } from "@assets/components/modal/SurveyModal/SurveyStarIcon";

import "./surveyModal.scss";

const SurveyModal = ({ closeModal }) => {
  const [activeIndex, setActiveIndex] = useState(-1);
  const [feedbackText, setFeedbackText] = useState("");

  const addToast = useToastStore(state => state.addToast);
  
  const surveyButtons = Array.from({ length: 5 }, (_, idx) => ({
    defaultClass: "survey-modal-star-button",
    onClick: () => setActiveIndex(idx),
  }));

  const submitSurvey = async () => {
    if( activeIndex === -1 ) {
      addToast({ message: "별점을 선택해주세요.", type: "fail" });
      return;
    }
    if(feedbackText.trim() === "") {
      addToast({ message: "의견을 입력해주세요.", type: "fail" });
      return;
    }
    try {
      await setSurvey(sessionStorage.getItem('user'), feedbackText, activeIndex);
      addToast({ message: "소중한 의견 감사합니다.", type: "success" });
      closeModal();
    } catch (error) {
      console.error("설문 제출 실패:", error);
      addToast({ message: "제출 중 오류가 발생했습니다.", type: "fail" });
    }
  };


  return (
    <Modal
      className="survey-modal"
      title="만족도 조사"
      onCancel={closeModal}
      footerButtons={[
        { className: "secondary", label: "취소", onClick: closeModal },
        { className: "primary", label: "제출", onClick: submitSurvey },
      ]}
    >
      <div className="survey-modal-area">
        <div className="survey-modal-title">서비스 만족도를 평가해주세요!</div>
        <div className="survey-modal-buttons">
          {surveyButtons.map((btn, idx) => (
            <Button
              key={idx}
              className={`${btn.defaultClass} ${idx <= activeIndex ? "active" : ""}`}
              onClick={btn.onClick}
            >
              <SurveyStarIcon
                fill={idx <= activeIndex ? "#FFD900" : "#DBDAD6"}
                stroke={idx <= activeIndex ? "#F4D000" : "#BFBFBF"}
              />
            </Button>
          ))}
        </div>
        <textarea
          className="survey-modal-textarea"
          placeholder="개선사항이나 의견을 입력해주세요."
          rows="5"
          value={feedbackText}
          onChange={(e) => setFeedbackText(e.target.value)}
        ></textarea>
      </div>
    </Modal>
  );
};

export default SurveyModal;
