/**
 * File API Client - FastAPI 통합 버전
 *
 * Features:
 * - 파일 업로드 (MinIO + PostgreSQL)
 * - 파일 타입 검증
 * - 크기 제한 (100MB)
 *
 * Security:
 * - HTTP Session 기반 인증
 * - Path Traversal 방지
 * - 파일 타입 화이트리스트
 * - Room ID 소유권 검증
 */

const API_BASE = '/api/v1';

// 허용된 파일 확장자
const ALLOWED_EXTENSIONS = [
  // Documents
  '.pdf',
  '.doc', '.docx',   // MS Word
  '.xls', '.xlsx',   // MS Excel
  '.ppt', '.pptx',   // MS PowerPoint
  '.hwp', '.hwpx',   // Hangul (한글)
  '.txt',            // Text
  // Images
  '.png', '.jpg', '.jpeg'
];

// 파일 크기 제한 (100MB)
const MAX_FILE_SIZE = 100 * 1024 * 1024;


/**
 * 파일 업로드 (FormData)
 *
 * @param {File} file - 업로드할 파일 객체
 * @param {string} room_id - 대화방 ID
 *
 * @returns {Promise<Object>} 업로드 결과
 *   - file_id: number
 *   - cnvs_idt_id: string
 *   - file_name: string
 *   - file_path: string (MinIO)
 *   - file_size: number
 *   - upload_dt: string
 *
 * @throws {Error} 파일 크기/타입 제한 초과, 업로드 실패
 *
 * @example
 * const file = document.getElementById('fileInput').files[0];
 * const result = await uploadFile(file, 'user123_20251022104412345678');
 * console.log(result.file_id); // 파일 ID
 */
export const uploadFile = async (file, room_id) => {
  try {
    // 1. 파일 크기 검증 (클라이언트 사이드)
    if (file.size > MAX_FILE_SIZE) {
      throw new Error(`파일 크기가 100MB를 초과합니다 (${(file.size / 1024 / 1024).toFixed(2)}MB)`);
    }

    // 2. 파일 확장자 검증 (클라이언트 사이드)
    const extension = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      throw new Error(`지원하지 않는 파일 형식입니다: ${extension}\n허용된 형식: ${ALLOWED_EXTENSIONS.join(', ')}`);
    }

    // 3. FormData 생성
    const formData = new FormData();
    formData.append('file', file);
    formData.append('room_id', room_id);

    // 4. 파일 업로드
    const response = await fetch(`${API_BASE}/files/upload`, {
      method: 'POST',
      credentials: 'include', // Session cookie
      body: formData // FormData는 Content-Type 자동 설정
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('인증이 필요합니다');
      }
      if (response.status === 403) {
        throw new Error('파일 업로드 권한이 없습니다');
      }
      if (response.status === 413) {
        throw new Error('파일 크기가 너무 큽니다');
      }
      const errorData = await response.json();
      throw new Error(errorData.detail || '파일 업로드 실패');
    }

    return await response.json();
  } catch (err) {
    console.error('Upload file error:', err);
    throw err;
  }
};


/**
 * 다중 파일 업로드
 *
 * @param {FileList|Array<File>} files - 업로드할 파일 목록
 * @param {string} room_id - 대화방 ID
 *
 * @returns {Promise<Array<Object>>} 업로드 결과 배열
 *   - 각 파일의 업로드 결과 객체
 *
 * @example
 * const files = document.getElementById('fileInput').files;
 * const results = await uploadMultipleFiles(files, 'user123_20251022104412345678');
 * console.log(results); // [{file_id: 1, ...}, {file_id: 2, ...}]
 */
export const uploadMultipleFiles = async (files, room_id) => {
  try {
    const uploadPromises = Array.from(files).map(file =>
      uploadFile(file, room_id)
    );

    // 모든 파일 병렬 업로드
    const results = await Promise.allSettled(uploadPromises);

    // 결과 분리
    const succeeded = results
      .filter(r => r.status === 'fulfilled')
      .map(r => r.value);

    const failed = results
      .filter(r => r.status === 'rejected')
      .map(r => r.reason);

    if (failed.length > 0) {
      console.warn(`${failed.length}개 파일 업로드 실패:`, failed);
    }

    return succeeded;
  } catch (err) {
    console.error('Upload multiple files error:', err);
    throw err;
  }
};


/**
 * 파일 삭제
 *
 * @param {number} file_id - 파일 ID
 *
 * @returns {Promise<Object>} 삭제 결과
 *
 * @example
 * await deleteFile(123);
 */
export const deleteFile = async (file_id) => {
  try {
    const response = await fetch(`${API_BASE}/files/${file_id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include'
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || '파일 삭제 실패');
    }

    return await response.json();
  } catch (err) {
    console.error('Delete file error:', err);
    throw err;
  }
};


/**
 * 대화방의 모든 파일 조회
 *
 * @param {string} room_id - 대화방 ID
 *
 * @returns {Promise<Array<Object>>} 파일 목록
 *
 * @example
 * const files = await getRoomFiles('user123_20251022104412345678');
 * console.log(files); // [{file_id: 1, file_name: 'doc.pdf', ...}]
 */
export const getRoomFiles = async (room_id) => {
  try {
    const response = await fetch(`${API_BASE}/files/room/${room_id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include'
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || '파일 목록 조회 실패');
    }

    return await response.json();
  } catch (err) {
    console.error('Get room files error:', err);
    throw err;
  }
};


/**
 * 파일 다운로드 URL 생성
 *
 * @param {number} file_id - 파일 ID
 *
 * @returns {string} 다운로드 URL
 *
 * @example
 * const downloadUrl = getFileDownloadUrl(123);
 * window.open(downloadUrl, '_blank');
 */
export const getFileDownloadUrl = (file_id) => {
  return `${API_BASE}/files/${file_id}/download`;
};
