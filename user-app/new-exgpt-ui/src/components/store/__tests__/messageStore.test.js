/**
 * Message Store Tests
 *
 * Test Coverage:
 * - 메시지 추가/삭제
 * - localStorage persistence (optional)
 * - XSS 방지
 * - 메모리 관리 (max messages)
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useMessageStore } from '../messageStore_enhanced';

// Mock localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: (key) => store[key] || null,
    setItem: (key, value) => { store[key] = value.toString(); },
    removeItem: (key) => { delete store[key]; },
    clear: () => { store = {}; }
  };
})();

global.localStorage = localStorageMock;

describe('MessageStore', () => {
  beforeEach(() => {
    localStorage.clear();
    useMessageStore.setState({ messages: [] });
  });

  describe('Basic Functionality', () => {
    it('should initialize with empty messages', () => {
      const { messages } = useMessageStore.getState();
      expect(messages).toEqual([]);
    });

    it('should add user message', () => {
      useMessageStore.getState().addUserMessage('Hello');

      const { messages } = useMessageStore.getState();
      expect(messages).toHaveLength(1);
      expect(messages[0]).toEqual({
        role: 'user',
        content: 'Hello'
      });
    });

    it('should add assistant message', () => {
      const chatData = {
        content: {
          response: 'Hi there!'
        },
        metadata: {
          tokens_used: 10
        }
      };

      useMessageStore.getState().addAssistantMessage(chatData);

      const { messages } = useMessageStore.getState();
      expect(messages).toHaveLength(1);
      expect(messages[0].role).toBe('assistant');
      expect(messages[0].content).toBe('Hi there!');
    });

    it('should clear all messages', () => {
      useMessageStore.getState().addUserMessage('Test 1');
      useMessageStore.getState().addUserMessage('Test 2');

      useMessageStore.getState().clearMessages();

      const { messages } = useMessageStore.getState();
      expect(messages).toEqual([]);
    });
  });

  describe('Message Ordering', () => {
    it('should maintain correct message order', () => {
      useMessageStore.getState().addUserMessage('Question 1');
      useMessageStore.getState().addAssistantMessage({ content: { response: 'Answer 1' } });
      useMessageStore.getState().addUserMessage('Question 2');
      useMessageStore.getState().addAssistantMessage({ content: { response: 'Answer 2' } });

      const { messages } = useMessageStore.getState();
      expect(messages).toHaveLength(4);
      expect(messages[0].content).toBe('Question 1');
      expect(messages[1].content).toBe('Answer 1');
      expect(messages[2].content).toBe('Question 2');
      expect(messages[3].content).toBe('Answer 2');
    });
  });

  describe('Persistence (Optional)', () => {
    it('should persist messages to localStorage when enabled', () => {
      useMessageStore.getState().enablePersistence(true);
      useMessageStore.getState().addUserMessage('Test message');

      const stored = localStorage.getItem('exGpt-messages');
      expect(stored).toBeDefined();

      const parsed = JSON.parse(stored);
      expect(parsed).toHaveLength(1);
      expect(parsed[0].content).toBe('Test message');
    });

    it('should load messages from localStorage when enabled', () => {
      const testMessages = [
        { role: 'user', content: 'Hello' },
        { role: 'assistant', content: 'Hi' }
      ];
      localStorage.setItem('exGpt-messages', JSON.stringify(testMessages));

      useMessageStore.getState().enablePersistence(true);
      useMessageStore.getState().initMessages();

      const { messages } = useMessageStore.getState();
      expect(messages).toHaveLength(2);
      expect(messages[0].content).toBe('Hello');
    });

    it('should clear localStorage on clearMessages', () => {
      useMessageStore.getState().enablePersistence(true);
      useMessageStore.getState().addUserMessage('Test');
      useMessageStore.getState().clearMessages();

      const stored = localStorage.getItem('exGpt-messages');
      expect(stored).toBeNull();
    });
  });

  describe('Memory Management', () => {
    it('should limit message history to MAX_MESSAGES', () => {
      const MAX_MESSAGES = 100;

      // Add 150 messages
      for (let i = 0; i < 150; i++) {
        useMessageStore.getState().addUserMessage(`Message ${i}`);
      }

      const { messages } = useMessageStore.getState();
      expect(messages.length).toBeLessThanOrEqual(MAX_MESSAGES);
    });

    it('should keep most recent messages when limit reached', () => {
      const MAX_MESSAGES = 100;

      for (let i = 0; i < 150; i++) {
        useMessageStore.getState().addUserMessage(`Message ${i}`);
      }

      const { messages } = useMessageStore.getState();
      // Should keep last 100 messages
      expect(messages[0].content).toBe(`Message ${150 - MAX_MESSAGES}`);
      expect(messages[messages.length - 1].content).toBe('Message 149');
    });
  });

  describe('Security - XSS Prevention', () => {
    it('should sanitize user message with XSS attempt', () => {
      const xssMessage = '<script>alert("XSS")</script>';
      useMessageStore.getState().addUserMessage(xssMessage);

      const { messages } = useMessageStore.getState();
      expect(messages[0].content).not.toContain('<script>');
    });

    it('should sanitize assistant message with XSS attempt', () => {
      const xssData = {
        content: {
          response: '<img src=x onerror="alert(1)">'
        }
      };

      useMessageStore.getState().addAssistantMessage(xssData);

      const { messages } = useMessageStore.getState();
      expect(messages[0].content).not.toContain('onerror');
    });

    it('should handle malicious localStorage data', () => {
      const maliciousData = [
        { role: 'user', content: '<script>alert("XSS")</script>' }
      ];
      localStorage.setItem('exGpt-messages', JSON.stringify(maliciousData));

      useMessageStore.getState().enablePersistence(true);
      useMessageStore.getState().initMessages();

      const { messages } = useMessageStore.getState();
      expect(messages[0].content).not.toContain('<script>');
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty message gracefully', () => {
      useMessageStore.getState().addUserMessage('');

      const { messages } = useMessageStore.getState();
      expect(messages).toHaveLength(0); // Should not add empty message
    });

    it('should handle null/undefined assistant data', () => {
      useMessageStore.getState().addAssistantMessage(null);

      const { messages } = useMessageStore.getState();
      expect(messages).toHaveLength(0);
    });

    it('should handle corrupted JSON in localStorage', () => {
      localStorage.setItem('exGpt-messages', 'invalid json {');

      useMessageStore.getState().enablePersistence(true);
      useMessageStore.getState().initMessages();

      const { messages } = useMessageStore.getState();
      expect(messages).toEqual([]); // Should default to empty
    });

    it('should handle very long messages', () => {
      const longMessage = 'a'.repeat(100000);
      useMessageStore.getState().addUserMessage(longMessage);

      const { messages } = useMessageStore.getState();
      expect(messages[0].content.length).toBeLessThanOrEqual(50000); // Should truncate
    });
  });

  describe('Metadata Preservation', () => {
    it('should preserve raw data in assistant messages', () => {
      const chatData = {
        content: {
          response: 'Answer'
        },
        metadata: {
          tokens_used: 123,
          response_time_ms: 1500
        },
        sources: [
          { filename: 'doc.pdf', relevance_score: 0.95 }
        ]
      };

      useMessageStore.getState().addAssistantMessage(chatData);

      const { messages } = useMessageStore.getState();
      expect(messages[0].raw).toEqual(chatData);
      expect(messages[0].raw.metadata.tokens_used).toBe(123);
      expect(messages[0].raw.sources).toHaveLength(1);
    });
  });
});
