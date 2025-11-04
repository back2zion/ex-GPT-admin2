/**
 * Enhanced Message Store with Optional Persistence and Security
 *
 * Features:
 * - Optional localStorage persistence
 * - Message limit (prevent memory issues)
 * - XSS prevention
 * - Message validation
 *
 * Security:
 * - HTML sanitization
 * - Length limits
 * - Type validation
 */

import { create } from 'zustand';

// Constants
const STORAGE_KEY = 'exGpt-messages';
const MAX_MESSAGES = 100;  // Keep last 100 messages
const MAX_MESSAGE_LENGTH = 50000;  // 50KB per message

/**
 * Sanitize HTML/XSS from message content
 */
function sanitizeMessage(content) {
  if (!content || typeof content !== 'string') {
    return '';
  }

  // Remove script tags
  let sanitized = content.replace(/<script[^>]*>.*?<\/script>/gi, '');

  // Remove dangerous event handlers
  sanitized = sanitized.replace(/on\w+\s*=\s*["'][^"']*["']/gi, '');

  // Remove iframe tags
  sanitized = sanitized.replace(/<iframe[^>]*>.*?<\/iframe>/gi, '');

  // Truncate if too long
  if (sanitized.length > MAX_MESSAGE_LENGTH) {
    sanitized = sanitized.substring(0, MAX_MESSAGE_LENGTH) + '... (truncated)';
  }

  return sanitized;
}

/**
 * Validate message object
 */
function validateMessage(message) {
  if (!message || typeof message !== 'object') {
    return false;
  }

  if (!message.role || !['user', 'assistant'].includes(message.role)) {
    return false;
  }

  if (!message.content || typeof message.content !== 'string') {
    return false;
  }

  return true;
}

/**
 * Load messages from localStorage
 */
function loadMessagesFromStorage() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      return [];
    }

    const parsed = JSON.parse(stored);
    if (!Array.isArray(parsed)) {
      return [];
    }

    // Validate and sanitize each message
    return parsed
      .filter(validateMessage)
      .map(msg => ({
        ...msg,
        content: sanitizeMessage(msg.content)
      }))
      .slice(-MAX_MESSAGES);  // Keep last MAX_MESSAGES
  } catch (err) {
    console.error('Failed to load messages from localStorage:', err);
    return [];
  }
}

/**
 * Save messages to localStorage
 */
function saveMessagesToStorage(messages) {
  try {
    const toSave = messages.slice(-MAX_MESSAGES);  // Keep last MAX_MESSAGES
    localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
  } catch (err) {
    if (err.name === 'QuotaExceededError') {
      console.error('localStorage quota exceeded, clearing old messages...');
      try {
        localStorage.removeItem(STORAGE_KEY);
        // Save only last 50 messages
        const reduced = messages.slice(-50);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(reduced));
      } catch (retryErr) {
        console.error('Failed to save messages even after clearing');
      }
    } else {
      console.error('Failed to save messages to localStorage:', err);
    }
  }
}

/**
 * Enhanced Message Store
 */
export const useMessageStore = create((set, get) => ({
  // State
  messages: [],
  persistenceEnabled: false,

  /**
   * Initialize messages from localStorage (if persistence enabled)
   */
  initMessages: () => {
    if (get().persistenceEnabled) {
      const messages = loadMessagesFromStorage();
      set({ messages });
    }
  },

  /**
   * Enable/disable persistence
   */
  enablePersistence: (enabled) => {
    set({ persistenceEnabled: enabled });
    if (enabled) {
      get().initMessages();
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  },

  /**
   * Add user message
   *
   * @param {string} content - Message content
   */
  addUserMessage: (content) => {
    // Validate
    if (!content || typeof content !== 'string' || content.trim() === '') {
      console.warn('Empty or invalid message, skipping');
      return;
    }

    // Sanitize
    const sanitized = sanitizeMessage(content);

    // Create message object
    const message = {
      role: 'user',
      content: sanitized,
      timestamp: Date.now()
    };

    // Update state
    set(state => {
      const newMessages = [...state.messages, message];

      // Enforce message limit
      const limited = newMessages.slice(-MAX_MESSAGES);

      // Persist if enabled
      if (state.persistenceEnabled) {
        saveMessagesToStorage(limited);
      }

      return { messages: limited };
    });
  },

  /**
   * Add assistant message
   *
   * @param {Object} chatData - Chat response data
   */
  addAssistantMessage: (chatData) => {
    // Validate
    if (!chatData || !chatData.content || !chatData.content.response) {
      console.warn('Invalid chat data, skipping');
      return;
    }

    // Sanitize content
    const sanitized = sanitizeMessage(chatData.content.response);

    // Create message object
    const message = {
      role: 'assistant',
      content: sanitized,
      raw: chatData,  // Preserve original data
      timestamp: Date.now()
    };

    // Update state
    set(state => {
      const newMessages = [...state.messages, message];

      // Enforce message limit
      const limited = newMessages.slice(-MAX_MESSAGES);

      // Persist if enabled
      if (state.persistenceEnabled) {
        // Don't persist raw data (too large)
        const toSave = limited.map(msg => ({
          role: msg.role,
          content: msg.content,
          timestamp: msg.timestamp
        }));
        saveMessagesToStorage(toSave);
      }

      return { messages: limited };
    });
  },

  /**
   * Update last assistant message (for streaming)
   *
   * @param {string} content - Updated content
   */
  updateLastAssistantMessage: (content) => {
    set(state => {
      const messages = [...state.messages];
      const lastIndex = messages.length - 1;

      if (lastIndex >= 0 && messages[lastIndex].role === 'assistant') {
        messages[lastIndex] = {
          ...messages[lastIndex],
          content: sanitizeMessage(content)
        };
      }

      return { messages };
    });
  },

  /**
   * Clear all messages
   */
  clearMessages: () => {
    set({ messages: [] });
    localStorage.removeItem(STORAGE_KEY);
  },

  /**
   * Get messages count
   */
  getMessagesCount: () => {
    return get().messages.length;
  },

  /**
   * Get last N messages
   */
  getRecentMessages: (count = 10) => {
    const messages = get().messages;
    return messages.slice(-count);
  },

  /**
   * Export messages as JSON
   */
  exportMessages: () => {
    return JSON.stringify(get().messages, null, 2);
  },

  /**
   * Import messages from JSON
   */
  importMessages: (jsonString) => {
    try {
      const imported = JSON.parse(jsonString);
      if (!Array.isArray(imported)) {
        throw new Error('Invalid format');
      }

      const validated = imported
        .filter(validateMessage)
        .map(msg => ({
          ...msg,
          content: sanitizeMessage(msg.content)
        }));

      set({ messages: validated });

      if (get().persistenceEnabled) {
        saveMessagesToStorage(validated);
      }

      return true;
    } catch (err) {
      console.error('Failed to import messages:', err);
      return false;
    }
  },
}));
