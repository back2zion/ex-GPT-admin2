import { useState } from "react";
import { useToastStore } from "../../store/toastStore";
import { useFileStore } from "../../store/fileStore";
import { validateFiles } from "../../utils/validateFiles";

import AttachedFiles from "./AttachedFiles";
import FormTextarea from "./FormTextarea";
import FormButtons from "./FormButtons";

import { FilePlusIcon } from "../../../assets/components/form/FilePlusIcon";

import "./form.scss";

const Form = ({ hasText, textareaRef, handleInput, handleSubmit, textareaValue }) => {
  const attachedFiles = useFileStore(state => state.attachedFiles);
  const addFiles = useFileStore(state => state.addFiles);
  const [dragCounter, setDragCounter] = useState(0);
  const removeFile = useFileStore(state => state.removeFile);

  const addToast = useToastStore(state => state.addToast);

  //첨부파일 관리
  const handleFiles = incomingFiles => {
    const files = Array.from(incomingFiles);

    if (attachedFiles.length + files.length > 5) {
      addToast({ message: "파일은 최대 5개까지 첨부할 수 있습니다.", type: "fail" });
      return;
    }

    const validFiles = validateFiles(files, attachedFiles, addToast);

    if (validFiles.length > 0) {
      addFiles(validFiles);
    }
  };

  const handleRemoveFile = file => {
    removeFile(file);
  };

  return (
    <div className="content__form_wrapper">
      <div className="content__inner">
        <div
          className={`content__form_section ${hasText ? "active" : ""} ${dragCounter > 0 ? "dragging" : ""}`}
          onDragEnter={e => {
            e.preventDefault();
            setDragCounter(prev => prev + 1);
          }}
          onDragLeave={e => {
            e.preventDefault();
            setDragCounter(prev => prev - 1);
          }}
          onDragOver={e => e.preventDefault()}
          onDrop={e => {
            e.preventDefault();
            setDragCounter(0);
            handleFiles(e.dataTransfer.files);
          }}
        >
          <div className="form-backdrop">
            <FilePlusIcon />
            <span>여기에 파일 업로드해 주세요</span>
          </div>
          <AttachedFiles files={attachedFiles} onRemoveFile={handleRemoveFile} />
          <form className="content__form">
            <FormTextarea
              hasText={hasText}
              textareaRef={textareaRef}
              handleInput={handleInput}
              handleSubmit={handleSubmit}
              textareaValue={textareaValue}
            />
            <FormButtons
              hasText={hasText}
              attachedFiles={attachedFiles}
              handleSubmit={handleSubmit}
              onFileChange={e => handleFiles(e.target.files)}
            />
          </form>
        </div>
      </div>
    </div>
  );
};

export default Form;
