import { useState, useEffect } from "react";
import { useUserSettingsStore } from "../../store/userSettingsStore";

import Modal from "../../common/Modal/Modal";
import Button from "../../common/Button/Button";

import "./fontSizeModal.scss";

const FontSizeModal = ({ closeModal }) => {
  const fontSizeIndex = useUserSettingsStore(state => state.fontSizeIndex);
  const updateFontSize = useUserSettingsStore(state => state.updateFontSize);
  const [selectedSize, setSelectedSize] = useState(fontSizeIndex);

  useEffect(() => {
    const localSize = Number(localStorage.getItem("exGpt-font-size"));
    if (!isNaN(localSize)) {
      setSelectedSize(localSize);
    } else {
      setSelectedSize(fontSizeIndex);
    }
  }, [fontSizeIndex]);

  const handleConfirm = async () => {
    await updateFontSize(selectedSize);
    closeModal();
  };

  // --ds-font-size-base: 1em; // 20px -> 2px 씩 늘리기
  const sizes = ["가", "가", "가", "가", "가"];

  return (
    <Modal
      className="font-size-modal"
      title="글자 크기 선택"
      onCancel={closeModal}
      footerButtons={[
        { className: "secondary", label: "닫기", onClick: closeModal },
        { className: "primary", label: "확인", onClick: handleConfirm },
      ]}
    >
      {sizes.map((label, idx) => (
        <Button
          key={idx}
          defaultClass="font-size-button"
          className={selectedSize === idx ? "active" : ""}
          onClick={() => setSelectedSize(idx)}
        >
          {label}
        </Button>
      ))}
      {/* <div className="font-size-options">
      </div> */}
    </Modal>
  );
};

export default FontSizeModal;
