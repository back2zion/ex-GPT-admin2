import { useEffect, useRef, useState } from "react";

import { SuccessToastIcon } from "../../../assets/components/toast/SuccessToastIcon";
import { FailToastIcon } from "../../../assets/components/toast/FailToastIcon";
import { WarningToastIcon } from "../../../assets/components/toast/WarningToastIcon";

import "./toast.scss";

const Toast = ({ type = "success", message, timer = 4000, onClose }) => {
  const [visible, setVisible] = useState(true);
  const fadeTimeoutRef = useRef();
  const removeTimeoutRef = useRef();

  const startTimers = () => {
    setVisible(true);
    fadeTimeoutRef.current = setTimeout(() => setVisible(false), timer - 2000);
    removeTimeoutRef.current = setTimeout(onClose, timer);
  };

  const clearTimers = () => {
    clearTimeout(fadeTimeoutRef.current);
    clearTimeout(removeTimeoutRef.current);
  };

  useEffect(() => {
    startTimers();
    return clearTimers;
  }, []);

  const handleMouseEnter = () => {
    clearTimers();
    setVisible(true);
  };

  const handleMouseLeave = () => {
    startTimers();
  };

  const renderIcon = () => {
    switch (type) {
      case "success":
        return <SuccessToastIcon />;
      case "fail":
        return <FailToastIcon />;
      case "warning":
        return <WarningToastIcon />;
      default:
        return null;
    }
  };

  return (
    <div
      role="alert"
      className={`toast show ${type} ${!visible ? "hide" : ""}`}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div className="toast-content">
        <div className="toast-icon">{renderIcon()}</div>
        <div className="toast-message">{message}</div>
      </div>
    </div>
  );
};

export default Toast;
