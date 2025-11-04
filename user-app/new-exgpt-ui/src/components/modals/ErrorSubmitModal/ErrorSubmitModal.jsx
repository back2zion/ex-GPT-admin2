import { useState } from "react";
import Modal from "../../common/Modal/Modal";
import { CheckIcon } from "../../../assets/components/modal/ErrorSubmitModal/CheckIcon";
import "./errorSubmitModal.scss";

const ErrorSubmitModal = ({ isOpen, closeModal }) => {
  const [selectedOptions, setSelectedOptions] = useState([]);

  const options = [
    { title: "부정확함" },
    { title: "날짜가 지남" },
    { title: "너무 짧음" },
    { title: "너무 길어요" },
    { title: "해롭거나 불쾌함" },
    { title: "잘못된 소스" },
  ];

  const toggleOption = idx => {
    setSelectedOptions(prev => (prev.includes(idx) ? prev.filter(i => i !== idx) : [...prev, idx]));
  };

  return (
    <Modal
      className="error-submit-modal"
      isOpen={isOpen}
      title="오류사항신고"
      onCancel={closeModal}
      footerButtons={[
        { className: "secondary", label: "취소", onClick: closeModal },
        { className: "primary", label: "제출", onClick: closeModal },
      ]}
    >
      <div className="error-submit-modal-title">ex-GPT를 개선시키는 데 도움을 주세요.</div>
      <div className="error-submit-modal-info">
        <p className="error-submit-modal-info__feedback">
          이 답변에 대해 추가 피드백을 제공해 주세요.
        </p>
        <p className="error-submit-modal-info__choice">해당하는 모든 항목을 선택해주세요. </p>
      </div>
      <div className="error-submit-modal-select">
        {options.map((option, idx) => (
          <div
            className={`error-submit-modal-select__option ${selectedOptions.includes(idx) ? "active" : ""}`}
            key={idx}
            onClick={() => toggleOption(idx)}
          >
            {option.title}
            {selectedOptions.includes(idx) && <CheckIcon />}
          </div>
        ))}
      </div>
      <div className="error-submit-modal-question">응답을 어떻게 개선할수 있을까요?</div>
      <textarea
        name=""
        id=""
        rows="6"
        placeholder="추가의견"
        className="error-submit-modal-textarea"
      ></textarea>
    </Modal>
  );
};

export default ErrorSubmitModal;
