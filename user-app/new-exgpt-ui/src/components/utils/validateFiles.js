export const validateFiles = (files, attachedFiles, addToast) => {
  const allowedExtensions = [
    "pdf",
    "hwp",
    "hwpx",
    "doc",
    "docx",
    "ppt",
    "pptx",
    "txt",
    "xls",
    "xlsx",
  ];
  const validFiles = [];

  for (const file of files) {
    const ext = file.name.split(".").pop().toLowerCase();
    const isDuplicate = attachedFiles.some(f => f.name === file.name && f.size === file.size);

    if (file.size > 100 * 1024 * 1024) {
      addToast({ message: `${file.name} 파일이 100MB를 초과합니다.`, type: "fail" });
      continue;
    }

    if (!allowedExtensions.includes(ext)) {
      addToast({ message: `${file.name} 파일 형식이 지원되지 않습니다.`, type: "fail" });
      continue;
    }

    if (isDuplicate) {
      addToast({ message: `${file.name} 파일이 이미 첨부되어 있습니다.`, type: "fail" });
      continue;
    }

    validFiles.push(file);
  }

  return validFiles;
};
