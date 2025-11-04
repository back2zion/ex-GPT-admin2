import Modal from "@common/Modal/Modal";
import Button from "@common/Button/Button";

import { FileDeleteIcon } from "@assets/components/file/FileDeleteIcon";
import { DocumentIcon } from "@assets/components/file/DocumentIcon";
import { ClipIcon } from "@assets/components/file/ClipIcon";

import "./fileUploadModal.scss";

const FileUploadModal = ({ isOpen, onCancel, onConfirm }) => {
  return (
    <Modal
      className="file-upload-modal"
      isOpen={isOpen}
      title="파일업로드"
      footerButtons={[
        { className: "secondary", label: "취소", onClick: onCancel },
        { className: "primary", label: "학습하기", onClick: onConfirm },
      ]}
    >
      <div className="file-upload-modal-area">
        <div className="file-upload-modal-set">
          <div className="file-upload-modal__icon">
            <ClipIcon />
          </div>
          <div className="file-upload-modal-file">
            <div className="file-upload-modal-file__name">ex-GPT_화면기능 정의서 _v.0.txt</div>
            <div className="file-upload-modal-file__size">2.83MB</div>
          </div>
          <Button iconComponent={<FileDeleteIcon />} className="file-upload-modal__delete"></Button>
        </div>
        <div className="file-upload-modal-set">
          <div className="file-upload-modal__icon">
            <DocumentIcon />
          </div>
          <div className="file-upload-modal-file">
            <div className="file-upload-modal-file__name">ex-GPT_화면기능 정의서 _v.0.ppt</div>
            <div className="file-upload-modal-file__size">2.83MB</div>
          </div>
          <Button iconComponent={<FileDeleteIcon />} className="file-upload-modal__delete"></Button>
        </div>
      </div>
      <div className="file-upload-modal-info">
        선택한 파일들을 AI가 학습하여
        <br />
        문서 내용에 대한 질문에 답변 할 수 있습니다.
      </div>
    </Modal>
  );
};

export default FileUploadModal;
