/**
 * Enhanced File Store with Security and Validation
 *
 * Features:
 * - File type validation
 * - File size limits
 * - Duplicate prevention
 * - Memory management
 *
 * Security:
 * - Path traversal prevention
 * - File type whitelist
 * - Size limits
 */

import { create } from 'zustand';

// Constants
const ALLOWED_FILE_TYPES = [
  // PDF
  'application/pdf',

  // MS Word
  'application/msword',                                                        // .doc
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  // .docx

  // MS Excel
  'application/vnd.ms-excel',                                                  // .xls
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',       // .xlsx

  // MS PowerPoint
  'application/vnd.ms-powerpoint',                                            // .ppt
  'application/vnd.openxmlformats-officedocument.presentationml.presentation', // .pptx

  // 한글 (Hangul)
  'application/x-hwp',                                                        // .hwp
  'application/haansofthwp',                                                  // .hwp (alternative MIME)
  'application/vnd.hancom.hwp',                                               // .hwp (another variant)
  'application/vnd.hancom.hwpx',                                              // .hwpx

  // Text
  'text/plain',

  // Images
  'image/png',
  'image/jpeg',
  'image/jpg'
];

const ALLOWED_EXTENSIONS = [
  // Documents
  '.pdf',
  '.doc', '.docx',   // MS Word
  '.xls', '.xlsx',   // MS Excel
  '.ppt', '.pptx',   // MS PowerPoint
  '.hwp', '.hwpx',   // Hangul
  '.txt',            // Text

  // Images
  '.png', '.jpg', '.jpeg'
];

const MAX_FILE_SIZE = 100 * 1024 * 1024;  // 100MB
const MAX_FILES = 10;  // Max 10 files at once

/**
 * Validate file object
 */
function validateFile(file) {
  if (!file || !(file instanceof File)) {
    console.warn('Invalid file object');
    return { valid: false, error: 'Invalid file object' };
  }

  // File size check
  if (file.size > MAX_FILE_SIZE) {
    const sizeMB = (file.size / 1024 / 1024).toFixed(2);
    return {
      valid: false,
      error: `File too large: ${sizeMB}MB (max 100MB)`
    };
  }

  // File type check
  if (!ALLOWED_FILE_TYPES.includes(file.type)) {
    return {
      valid: false,
      error: `File type not allowed: ${file.type}`
    };
  }

  // Extension check
  const extension = '.' + file.name.split('.').pop().toLowerCase();
  if (!ALLOWED_EXTENSIONS.includes(extension)) {
    return {
      valid: false,
      error: `File extension not allowed: ${extension}`
    };
  }

  // Filename check (prevent path traversal)
  if (file.name.includes('..') || file.name.includes('/') || file.name.includes('\\')) {
    return {
      valid: false,
      error: 'Invalid filename (path traversal detected)'
    };
  }

  // Null byte check
  if (file.name.includes('\0')) {
    return {
      valid: false,
      error: 'Invalid filename (null byte detected)'
    };
  }

  return { valid: true };
}

/**
 * Sanitize filename
 */
function sanitizeFilename(filename) {
  if (!filename || typeof filename !== 'string') {
    return 'unnamed';
  }

  // Remove path separators
  let sanitized = filename.replace(/[/\\]/g, '_');

  // Remove null bytes
  sanitized = sanitized.replace(/\0/g, '');

  // Remove special characters except dot, dash, underscore
  sanitized = sanitized.replace(/[^a-zA-Z0-9._-]/g, '_');

  // Limit length
  if (sanitized.length > 255) {
    const ext = sanitized.split('.').pop();
    sanitized = sanitized.substring(0, 250) + '.' + ext;
  }

  return sanitized;
}

/**
 * Enhanced File Store
 */
export const useFileStore = create((set, get) => ({
  // State
  attachedFiles: [],
  uploadErrors: [],

  /**
   * Add files with validation
   *
   * @param {FileList|Array<File>} files - Files to add
   * @returns {Object} - { success: Array, failed: Array }
   */
  addFiles: (files) => {
    const fileArray = Array.from(files);
    const success = [];
    const failed = [];

    // Check total file count
    const currentCount = get().attachedFiles.length;
    if (currentCount + fileArray.length > MAX_FILES) {
      const error = `Too many files (max ${MAX_FILES})`;
      console.warn(error);
      return {
        success: [],
        failed: fileArray.map(f => ({ file: f, error }))
      };
    }

    // Validate each file
    fileArray.forEach(file => {
      const validation = validateFile(file);

      if (validation.valid) {
        // Check for duplicates (by name and size)
        const isDuplicate = get().attachedFiles.some(
          f => f.name === file.name && f.size === file.size
        );

        if (isDuplicate) {
          failed.push({ file, error: 'Duplicate file' });
        } else {
          success.push(file);
        }
      } else {
        failed.push({ file, error: validation.error });
      }
    });

    // Update state
    if (success.length > 0) {
      set(state => ({
        attachedFiles: [...state.attachedFiles, ...success],
        uploadErrors: [...state.uploadErrors, ...failed]
      }));
    } else if (failed.length > 0) {
      set(state => ({
        uploadErrors: [...state.uploadErrors, ...failed]
      }));
    }

    return { success, failed };
  },

  /**
   * Remove file
   *
   * @param {File|string|null} file - File object or filename, or null to clear all
   */
  removeFile: (file) => {
    if (file === null) {
      set({ attachedFiles: [] });
      return;
    }

    set(state => ({
      attachedFiles: state.attachedFiles.filter(f => {
        if (typeof file === 'string') {
          return f.name !== file;
        }
        return f !== file;
      })
    }));
  },

  /**
   * Reset all files
   */
  resetFiles: () => {
    set({ attachedFiles: [], uploadErrors: [] });
  },

  /**
   * Get file by name
   */
  getFileByName: (filename) => {
    return get().attachedFiles.find(f => f.name === filename);
  },

  /**
   * Get total file size
   */
  getTotalSize: () => {
    return get().attachedFiles.reduce((sum, file) => sum + file.size, 0);
  },

  /**
   * Get formatted total size
   */
  getFormattedTotalSize: () => {
    const bytes = get().getTotalSize();
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / 1024 / 1024).toFixed(2) + ' MB';
  },

  /**
   * Check if file limit reached
   */
  isLimitReached: () => {
    return get().attachedFiles.length >= MAX_FILES;
  },

  /**
   * Get upload errors
   */
  getUploadErrors: () => {
    return get().uploadErrors;
  },

  /**
   * Clear upload errors
   */
  clearUploadErrors: () => {
    set({ uploadErrors: [] });
  },

  /**
   * Validate files (for debugging)
   */
  validateFiles: () => {
    const files = get().attachedFiles;
    return files.map(file => ({
      name: file.name,
      size: file.size,
      type: file.type,
      validation: validateFile(file)
    }));
  },
}));
