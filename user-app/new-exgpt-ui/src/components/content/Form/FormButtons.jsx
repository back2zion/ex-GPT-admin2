import { useRef } from "react";

import SubmitIcon from "../../../assets/icons/form/submitIcon.svg?react";
import Button from "../../common/Button/Button";

const FormButtons = ({ hasText, onFileChange, handleSubmit }) => {
  const fileInputRef = useRef(null);

  const handleLabelKeyDown = e => {
    console.log(e);
    // Enter(13) or Space(32) 키를 눌렀을 때 파일 선택창 열기
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      fileInputRef.current?.click();
    }
  };

  return (
    <div className="content__form_btn">
      {/* 파일첨부 */}
      <label
        htmlFor="file-upload"
        className="content__form-file-label"
        tabIndex={0}
        onKeyDown={handleLabelKeyDown}
      >
        <input
          type="file"
          id="file-upload"
          className="sr-only"
          onChange={onFileChange}
          ref={fileInputRef}
          tabIndex={-1}
          multiple
          aria-label="파일첨부 (최대 5개, 각 파일 100MB 까지)"
        />
        {/* div로도 테스트 */}
        <span className="tooltip">파일첨부 (최대 5개, 각 파일 100MB 까지)</span>
      </label>
      {/* 전송 */}
      <Button
        label="전송"
        className={`content__form-submit ${hasText ? "active" : ""}`}
        iconComponent={SubmitIcon}
        onClick={handleSubmit}
        aria-label="메시지 전송"
      ></Button>
    </div>
  );
};

export default FormButtons;
