import Button from "../../common/Button/Button";
import { ClipIcon } from "../../../assets/components/file/ClipIcon";
import { DocumentIcon } from "../../../assets/components/file/DocumentIcon";
import { FileDeleteIcon } from "../../../assets/components/file/FileDeleteIcon";

const AttachedFileItem = ({ file, onRemove }) => {
  function formatFileSize(bytes) {
    const sizes = ["Bytes", "KB", "MB", "GB"];
    if (bytes === 0) return "0 Bytes";
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + " " + sizes[i];
  }

  return (
    <div className="attached-file-item">
      <div className="attached-file-info">
        <span className="attached-file-icon">
          {/* 파일유형에 따라 아이콘 렌더링 다르게, ClipIcon: txt, DocumentIcon:ppt - 아이콘 추가..필요해보임, 디폴트는 ClipIcon */}
          {/* <DocumentIcon /> */}
          <ClipIcon />
        </span>
        <span className="attached-file-name">{file.name}</span>
        <span className="attached-file-size">{formatFileSize(file.size)}</span>
      </div>
      <Button
        className="attached-file-remove"
        iconComponent={<FileDeleteIcon />}
        onClick={onRemove}
      />
    </div>
  );
};

export default AttachedFileItem;
