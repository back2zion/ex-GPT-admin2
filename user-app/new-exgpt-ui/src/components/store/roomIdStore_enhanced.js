/**
 * Enhanced Room ID Store with Persistence and Security
 *
 * Features:
 * - localStorage persistence (survives page refresh)
 * - Room ID format validation
 * - XSS prevention
 * - Quota exceeded handling
 *
 * Security:
 * - Input validation (regex pattern)
 * - Length limits (max 200 chars)
 * - HTML/script tag filtering
 * - Path traversal prevention
 */

import { create } from 'zustand';

// Constants
const STORAGE_KEY = 'exGpt-room-id';
const MAX_ROOM_ID_LENGTH = 200;

// Room ID format: {user_id}_{timestamp}{microseconds}
// Example: "user123_20251022104412345678"
const ROOM_ID_PATTERN = /^[a-zA-Z0-9_-]{1,200}$/;

// Dangerous patterns to reject
const DANGEROUS_PATTERNS = [
  /<script/i,
  /<iframe/i,
  /javascript:/i,
  /on\w+\s*=/i,  // onload=, onclick=, etc.
  /\.\.\//,       // Path traversal
  /\0/,           // Null byte
];

/**
 * Validate room ID format
 */
function validateRoomId(roomId) {
  if (!roomId || typeof roomId !== 'string') {
    return false;
  }

  // Length check
  if (roomId.length > MAX_ROOM_ID_LENGTH) {
    console.warn(`Room ID too long: ${roomId.length} chars`);
    return false;
  }

  // Format check
  if (!ROOM_ID_PATTERN.test(roomId)) {
    console.warn(`Invalid room ID format: ${roomId}`);
    return false;
  }

  // Security check - dangerous patterns
  for (const pattern of DANGEROUS_PATTERNS) {
    if (pattern.test(roomId)) {
      console.error(`Dangerous pattern detected in room ID: ${roomId}`);
      return false;
    }
  }

  return true;
}

/**
 * Sanitize HTML tags from string
 */
function sanitizeString(str) {
  if (!str || typeof str !== 'string') {
    return '';
  }

  // Remove HTML tags
  return str
    .replace(/<script[^>]*>.*?<\/script>/gi, '')
    .replace(/<[^>]+>/g, '')
    .trim();
}

/**
 * Load room ID from localStorage with validation
 */
function loadRoomIdFromStorage() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      return '';
    }

    // Validate before using
    if (validateRoomId(stored)) {
      return stored;
    } else {
      console.warn('Invalid room ID in localStorage, clearing...');
      localStorage.removeItem(STORAGE_KEY);
      return '';
    }
  } catch (err) {
    console.error('Failed to load room ID from localStorage:', err);
    return '';
  }
}

/**
 * Save room ID to localStorage with error handling
 */
function saveRoomIdToStorage(roomId) {
  try {
    if (roomId) {
      localStorage.setItem(STORAGE_KEY, roomId);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  } catch (err) {
    if (err.name === 'QuotaExceededError') {
      console.error('localStorage quota exceeded');
      // Clear old data and retry
      try {
        localStorage.removeItem(STORAGE_KEY);
        localStorage.setItem(STORAGE_KEY, roomId);
      } catch (retryErr) {
        console.error('Failed to save room ID even after clearing');
      }
    } else {
      console.error('Failed to save room ID to localStorage:', err);
    }
  }
}

/**
 * Enhanced Room ID Store
 */
export const useRoomId = create((set, get) => ({
  // State
  roomId: '',

  /**
   * Initialize room ID from localStorage
   */
  initRoomId: () => {
    const roomId = loadRoomIdFromStorage();
    set({ roomId });
  },

  /**
   * Set current room ID with validation
   *
   * @param {string} id - Room ID to set
   * @returns {boolean} - true if successful, false if invalid
   */
  setCurrentRoomId: (id) => {
    // Sanitize input
    const sanitized = sanitizeString(id);

    // Validate
    if (!validateRoomId(sanitized)) {
      return false;
    }

    // Update state
    set({ roomId: sanitized });

    // Persist to localStorage
    saveRoomIdToStorage(sanitized);

    return true;
  },

  /**
   * Clear room ID
   */
  clearRoomId: () => {
    set({ roomId: '' });
    saveRoomIdToStorage('');
  },

  /**
   * Get current room ID
   *
   * @returns {string} - Current room ID
   */
  getCurrentRoomId: () => {
    return get().roomId;
  },

  /**
   * Check if room ID is set
   *
   * @returns {boolean} - true if room ID exists
   */
  hasRoomId: () => {
    return !!get().roomId;
  },
}));

// Initialize on module load
if (typeof window !== 'undefined') {
  useRoomId.getState().initRoomId();
}
