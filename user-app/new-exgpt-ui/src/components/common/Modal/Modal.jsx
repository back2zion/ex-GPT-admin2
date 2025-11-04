import { useEffect, useCallback, useRef, useState } from "react";
import Button from "../Button/Button";
import { ModalCloseIcon } from "../../../assets/components/modal/ModalCloseIcon";
import { useModalStore } from "../../store/modalStore";

import "./modal.scss";

const Modal = ({ className, title, children, onCancel, footerButtons = [], type }) => {
  const modalRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [modalPosition, setModalPosition] = useState(null); // null이면 중앙 정렬
  const { getOpenModalCount, getNextZIndex } = useModalStore.getState();
  const [zIndex, setZIndex] = useState(1000);

  // 초기 위치 및 z-index 설정
  useEffect(() => {
    const index = getOpenModalCount() - 1;

    const nextZ = getNextZIndex();
    setZIndex(nextZ); // z-index 상태 추가

    if (index === 0) {
      setModalPosition(null);
    } else {
      const offsetX = 50 * index;
      const offsetY = 20 * index;
      const baseX = window.innerWidth / 2 - 295;
      const baseY = window.innerHeight / 2 - 200;
      setModalPosition({ x: baseX + offsetX, y: baseY + offsetY });
    }
  }, []);

  // overlay 배경 클릭 닫기
  const handleOverlayClick = e => {
    if (e.target.classList.contains("modal")) {
      //onCancel?.();
    }
  };

  // 드래그 시작
  const handleMouseDown = e => {
    if (e.target.closest(".modal-header")) {
      setIsDragging(true);
      const rect = modalRef.current.getBoundingClientRect();
      setDragStart({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      });
    }
  };

  // 드래그 중
  const handleMouseMove = e => {
    if (isDragging) {
      const newX = e.clientX - dragStart.x;
      const newY = e.clientY - dragStart.y;
      setModalPosition({ x: newX, y: newY });
    }
  };

  // 드래그 종료
  const handleMouseUp = () => {
    setIsDragging(false);
  };

  useEffect(() => {
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging, dragStart]);

  return (
    <div className={`modal ${className}`} onMouseDown={handleOverlayClick}>
      <div
        role="dialog"
        className="modal-box"
        aria-label="title"
        aria-modal="true"
        ref={modalRef}
        onMouseDown={handleMouseDown}
        style={{
          position: "fixed",
          left: modalPosition ? modalPosition.x : "50%",
          top: modalPosition ? modalPosition.y : "50%",
          transform: modalPosition ? "none" : "translate(-50%, -50%)",
          zIndex: zIndex,
        }}
      >
        <button className="modal-close" onClick={onCancel} tabIndex={0} aria-label="모달창 닫기">
          <ModalCloseIcon />
        </button>

        {title && (
          <div className="modal-header">
            <p className="modal-header-title">{title}</p>
          </div>
        )}

        <div className="modal-content">
          <div className="modal-content-inn">{children}</div>
        </div>

        {footerButtons.length > 0 && (
          <div className="modal-footer">
            <div className="flex-end">
              {footerButtons.map((btn, idx) => (
                <Button
                  key={idx}
                  className={btn.className || ""}
                  onClick={btn.onClick}
                  label={btn.label}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Modal;
