import { useCallback } from "react";

import AttachedFileItem from "./AttachedFileItem";
import Button from "../../common/Button/Button";

const AttachedFiles = ({ files, onRemoveFile }) => {
  const handleRemoveAll = useCallback(() => {
    if (onRemoveFile) onRemoveFile(null); // null이면 전체 삭제
  }, [onRemoveFile]);

  if (!files || files.length === 0) return null;

  return (
    <div className="attached-files">
      <div className="attached-file-header">
        <span className="attached-file-header-title">첨부파일</span>
        <Button className="attached-file-header-remove-all" onClick={handleRemoveAll}>
          모두 삭제
        </Button>
      </div>
      <div className="attached-file-list">
        {files.map((file, idx) => (
          <AttachedFileItem key={idx} file={file} onRemove={() => onRemoveFile(file)} />
        ))}
      </div>
    </div>
  );
};

export default AttachedFiles;
